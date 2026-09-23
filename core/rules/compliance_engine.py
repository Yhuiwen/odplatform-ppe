"""Conservative Helmet/Vest compliance rule engine."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from core.schemas.association import AssociationStatus, PPEAssociation
from core.schemas.compliance import (
    ComplianceEventType,
    ComplianceFinding,
    ComplianceInput,
    ComplianceResult,
    ComplianceState,
)
from core.schemas.tracking import TrackResult
from utils.config_loader import load_config


class ComplianceError(RuntimeError):
    """Base compliance error with a stable machine-readable code."""

    code = "compliance_error"


class ComplianceConfigurationError(ComplianceError):
    code = "invalid_compliance_configuration"


class ComplianceExecutionDisabledError(ComplianceError):
    code = "execution_disabled"


class ComplianceInputError(ComplianceError):
    code = "invalid_compliance_input"


@dataclass(frozen=True, slots=True)
class RuleDomainSettings:
    enabled: bool
    required: bool
    positive_classes: tuple[str, ...]
    violation_classes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuleSettings:
    min_consecutive_frames: int
    min_duration_seconds: float
    recovery_frames: int
    cooldown_seconds: float
    helmet: RuleDomainSettings
    vest: RuleDomainSettings


__all__ = [
    "ComplianceConfigurationError",
    "ComplianceEngine",
    "ComplianceError",
    "ComplianceExecutionDisabledError",
    "ComplianceInputError",
    "RuleDomainSettings",
    "RuleSettings",
    "load_rule_settings",
]


class ComplianceEngine:
    """Evaluate one frame of person-track and PPE-association evidence."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        execution_enabled: bool | None = None,
    ) -> None:
        config = load_config(config_path or "rules")
        rules = config.get("rules")
        if not isinstance(rules, dict):
            raise ComplianceConfigurationError(
                "Rules configuration requires a 'rules' mapping"
            )
        self._execution_enabled = (
            bool(rules.get("execution_enabled", False))
            if execution_enabled is None
            else bool(execution_enabled)
        )
        self.settings = load_rule_settings(config_path)

    def evaluate(self, input_result: ComplianceInput) -> ComplianceResult:
        """Return deterministic findings without making unsafe assignments."""

        if not self._execution_enabled:
            raise ComplianceExecutionDisabledError(
                "Compliance evaluation is disabled by configs/rules.yaml"
            )
        if not isinstance(input_result, ComplianceInput):
            raise ComplianceInputError(
                "ComplianceEngine input must be a ComplianceInput"
            )

        findings: list[ComplianceFinding] = []
        unknown_domains: list[tuple[str, ComplianceFinding]] = []
        for track in input_result.tracks:
            track_associations = tuple(
                association
                for association in input_result.associations
                if association.track_id == track.track_id
            )
            helmet = self._evaluate_domain(
                track,
                track_associations,
                domain_name="helmet",
                event_type=ComplianceEventType.NO_HELMET,
                settings=self.settings.helmet,
            )
            vest = self._evaluate_domain(
                track,
                track_associations,
                domain_name="vest",
                event_type=ComplianceEventType.NO_VEST,
                settings=self.settings.vest,
            )
            for finding in (helmet, vest):
                if finding.state is ComplianceState.UNKNOWN:
                    unknown_domains.append(
                        (finding.evidence[0].split("=", 1)[0], finding)
                    )
                else:
                    findings.append(finding)

        if unknown_domains:
            grouped: dict[int, list[ComplianceFinding]] = {}
            for _, finding in unknown_domains:
                grouped.setdefault(finding.track_id, []).append(finding)
            for track_id, domain_findings in grouped.items():
                evidence = tuple(
                    item
                    for finding in domain_findings
                    for item in finding.evidence
                )
                findings.append(
                    ComplianceFinding(
                        track_id=track_id,
                        event_type=ComplianceEventType.PPE_UNKNOWN,
                        state=ComplianceState.UNKNOWN,
                        confidence=max(
                            finding.confidence for finding in domain_findings
                        ),
                        timestamp=input_result.timestamp,
                        evidence=evidence,
                    )
                )

        return ComplianceResult(
            frame_id=input_result.frame_id,
            timestamp=input_result.timestamp,
            findings=tuple(findings),
        )

    @staticmethod
    def _evaluate_domain(
        track: TrackResult,
        associations: Sequence[PPEAssociation],
        *,
        domain_name: str,
        event_type: ComplianceEventType,
        settings: RuleDomainSettings,
    ) -> ComplianceFinding:
        relevant = tuple(
            association
            for association in associations
            if association.ppe.class_name
            in settings.positive_classes + settings.violation_classes
        )
        positive = tuple(
            association
            for association in relevant
            if association.status is AssociationStatus.ASSOCIATED
            and association.ppe.class_name in settings.positive_classes
        )
        violations = tuple(
            association
            for association in relevant
            if association.status is AssociationStatus.ASSOCIATED
            and association.ppe.class_name in settings.violation_classes
        )
        uncertain = tuple(
            association
            for association in relevant
            if association.status is AssociationStatus.UNKNOWN
        )

        if not relevant:
            return ComplianceFinding(
                track_id=track.track_id,
                event_type=event_type,
                state=ComplianceState.UNKNOWN,
                confidence=0.0,
                timestamp=track.timestamp,
                evidence=(f"{domain_name}=missing_evidence",),
            )
        if uncertain:
            return ComplianceFinding(
                track_id=track.track_id,
                event_type=event_type,
                state=ComplianceState.UNKNOWN,
                confidence=max(
                    association.ppe.confidence for association in uncertain
                ),
                timestamp=track.timestamp,
                evidence=(f"{domain_name}=unknown_association",),
            )
        if positive and violations:
            return ComplianceFinding(
                track_id=track.track_id,
                event_type=event_type,
                state=ComplianceState.UNKNOWN,
                confidence=max(
                    association.ppe.confidence
                    for association in positive + violations
                ),
                timestamp=track.timestamp,
                evidence=(f"{domain_name}=conflicting_evidence",),
            )
        if violations:
            return ComplianceFinding(
                track_id=track.track_id,
                event_type=event_type,
                state=ComplianceState.VIOLATION,
                confidence=max(
                    association.ppe.confidence for association in violations
                ),
                timestamp=track.timestamp,
                evidence=(
                    f"{domain_name}="
                    f"{violations[0].ppe.class_name}",
                ),
            )
        return ComplianceFinding(
            track_id=track.track_id,
            event_type=event_type,
            state=ComplianceState.COMPLIANT,
            confidence=max(
                association.ppe.confidence for association in positive
            ),
            timestamp=track.timestamp,
            evidence=(
                f"{domain_name}="
                f"{positive[0].ppe.class_name}",
            ),
        )


def load_rule_settings(config_path: str | Path | None = None) -> RuleSettings:
    """Load and validate the frozen Phase 6 rule settings."""

    config = load_config(config_path or "rules")
    rules = config.get("rules")
    if not isinstance(rules, dict):
        raise ComplianceConfigurationError(
            "Rules configuration requires a 'rules' mapping"
        )
    temporal = rules.get("temporal_confirmation")
    recovery = rules.get("recovery")
    cooldown = rules.get("cooldown")
    event_types = rules.get("event_types")
    if not all(
        isinstance(value, dict)
        for value in (temporal, recovery, cooldown)
    ):
        raise ComplianceConfigurationError(
            "Rules configuration requires temporal_confirmation, recovery "
            "and cooldown mappings"
        )
    if tuple(event_types or ()) != (
        "NO_HELMET",
        "NO_VEST",
        "PPE_UNKNOWN",
    ):
        raise ComplianceConfigurationError(
            "Rules configuration must freeze the Phase 6 event types"
        )

    try:
        settings = RuleSettings(
            min_consecutive_frames=int(temporal["min_consecutive_frames"]),
            min_duration_seconds=float(temporal["min_duration_seconds"]),
            recovery_frames=int(recovery["compliant_frames"]),
            cooldown_seconds=float(cooldown["seconds"]),
            helmet=_parse_domain(rules, "helmet"),
            vest=_parse_domain(rules, "vest"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ComplianceConfigurationError(
            "Rules configuration contains invalid or missing fields"
        ) from exc

    if settings.min_consecutive_frames < 2:
        raise ComplianceConfigurationError(
            "min_consecutive_frames must be at least 2"
        )
    if settings.recovery_frames < 1:
        raise ComplianceConfigurationError(
            "recovery compliant_frames must be at least 1"
        )
    for name, value in (
        ("min_duration_seconds", settings.min_duration_seconds),
        ("cooldown_seconds", settings.cooldown_seconds),
    ):
        if value < 0 or not math.isfinite(value):
            raise ComplianceConfigurationError(
                f"{name} must be finite and non-negative"
            )
    return settings


def _parse_domain(rules: dict[str, Any], name: str) -> RuleDomainSettings:
    domain = rules.get(name)
    if not isinstance(domain, dict):
        raise TypeError(f"{name} must be a mapping")
    positive = tuple(str(item) for item in domain["positive_classes"])
    violations = tuple(str(item) for item in domain["violation_classes"])
    if not positive or not violations:
        raise ValueError(f"{name} classes cannot be empty")
    return RuleDomainSettings(
        enabled=bool(domain.get("enabled", False)),
        required=bool(domain.get("required", False)),
        positive_classes=positive,
        violation_classes=violations,
    )
