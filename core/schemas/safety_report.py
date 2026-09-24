"""Phase 8 provider-independent structured safety report contracts.

The report schema is deliberately free of provider, prompt, model and network
dependencies. Grounding is represented by explicit machine-readable references
so report validation never depends on natural-language interpretation.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.schemas.events import normalize_utc_timestamp
from core.schemas.safety import ReportingPeriod

__all__ = [
    "REPORT_SCHEMA_VERSION",
    "ClaimKind",
    "GenerationMode",
    "GroundingStatus",
    "MetricNumericClaim",
    "ReportEvidenceReference",
    "ReportGeneration",
    "ReportLimitation",
    "ReportRecommendation",
    "SafetyReportClaim",
    "StructuredSafetyReport",
    "TrackReference",
]

REPORT_SCHEMA_VERSION = "phase8-report-v1"

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,159}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_EVIDENCE_REF_PATTERN = re.compile(r"^EVID:.+$")


def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _validate_identifier(value: str, field_name: str) -> str:
    normalized = _validate_text(value, field_name)
    if _IDENTIFIER_PATTERN.fullmatch(normalized) is None:
        raise ValueError(
            f"{field_name} must be a stable identifier using letters, "
            "digits, dot, underscore, colon or hyphen"
        )
    return normalized


def _normalize_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(
        sorted(
            {
                _validate_identifier(value, field_name)
                for value in values
            }
        )
    )
    return normalized


def _normalize_track_refs(
    values: tuple[TrackReference, ...],
) -> tuple[TrackReference, ...]:
    normalized: list[TrackReference] = []
    seen: set[int] = set()
    for value in values:
        if not isinstance(value, TrackReference):
            raise TypeError("track_refs must contain TrackReference objects")
        if value.track_id in seen:
            raise ValueError("track_refs cannot contain duplicate track_id values")
        seen.add(value.track_id)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda item: item.track_id))


def _normalize_numeric_claims(
    values: tuple[MetricNumericClaim, ...],
) -> tuple[MetricNumericClaim, ...]:
    normalized: list[MetricNumericClaim] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, MetricNumericClaim):
            raise TypeError(
                "numeric_claims must contain MetricNumericClaim objects"
            )
        if value.metric_ref in seen:
            raise ValueError(
                "numeric_claims cannot contain duplicate metric_ref values"
            )
        seen.add(value.metric_ref)
        normalized.append(value)
    return tuple(
        sorted(normalized, key=lambda item: item.metric_ref)
    )


class ClaimKind(str, Enum):
    """Frozen claim role vocabulary."""

    OBSERVATION = "observation"
    RISK = "risk"


class GenerationMode(str, Enum):
    """Future report generation modes."""

    LLM = "LLM"
    TEMPLATE_FALLBACK = "TEMPLATE_FALLBACK"
    REPORT_UNAVAILABLE = "REPORT_UNAVAILABLE"


class GroundingStatus(str, Enum):
    """Caller-visible grounding state before or after validation."""

    UNVALIDATED = "unvalidated"
    VALID = "valid"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ReportGeneration:
    """Non-secret metadata describing how a report was produced."""

    mode: GenerationMode | str
    degraded: bool = False
    provider_ref: str | None = None
    failure_code: str | None = None

    def __post_init__(self) -> None:
        try:
            mode = GenerationMode(self.mode)
        except ValueError as exc:
            raise ValueError("mode must be a supported generation mode") from exc
        object.__setattr__(self, "mode", mode)
        if not isinstance(self.degraded, bool):
            raise TypeError("degraded must be a boolean")
        if self.provider_ref is not None:
            object.__setattr__(
                self,
                "provider_ref",
                _validate_identifier(self.provider_ref, "provider_ref"),
            )
        if self.failure_code is not None:
            object.__setattr__(
                self,
                "failure_code",
                _validate_identifier(self.failure_code, "failure_code"),
            )
        if self.mode is GenerationMode.REPORT_UNAVAILABLE:
            if self.failure_code is None:
                raise ValueError(
                    "REPORT_UNAVAILABLE generation requires failure_code"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "degraded": self.degraded,
            "provider_ref": self.provider_ref,
            "failure_code": self.failure_code,
        }


@dataclass(frozen=True, slots=True)
class TrackReference:
    """A tracker-scoped reference that cannot claim stable person identity."""

    track_id: int
    track_scope: str = "tracker_scoped"

    def __post_init__(self) -> None:
        if isinstance(self.track_id, bool) or not isinstance(self.track_id, int):
            raise TypeError("track_id must be an integer")
        if self.track_id < 0:
            raise ValueError("track_id cannot be negative")
        if self.track_scope != "tracker_scoped":
            raise ValueError("track_scope must be tracker_scoped")

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "track_scope": self.track_scope,
        }


@dataclass(frozen=True, slots=True)
class MetricNumericClaim:
    """One structured numeric assertion tied to a deterministic metric."""

    metric_ref: str
    value: int | float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metric_ref",
            _validate_identifier(self.metric_ref, "metric_ref"),
        )
        if isinstance(self.value, bool) or not isinstance(
            self.value, (int, float)
        ):
            raise TypeError("numeric claim value must be an integer or float")
        normalized = float(self.value)
        if not math.isfinite(normalized):
            raise ValueError("numeric claim value must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_ref": self.metric_ref,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True)
class SafetyReportClaim:
    """A grounded observation or risk claim with explicit references."""

    claim_id: str
    kind: ClaimKind | str
    statement: str
    fact_refs: tuple[str, ...] = ()
    metric_refs: tuple[str, ...] = ()
    event_refs: tuple[str, ...] = ()
    track_refs: tuple[TrackReference, ...] = ()
    source_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    numeric_claims: tuple[MetricNumericClaim, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "claim_id",
            _validate_identifier(self.claim_id, "claim_id"),
        )
        try:
            kind = ClaimKind(self.kind)
        except ValueError as exc:
            raise ValueError("kind must be observation or risk") from exc
        object.__setattr__(self, "kind", kind)
        object.__setattr__(
            self,
            "statement",
            _validate_text(self.statement, "statement"),
        )
        for field_name in (
            "fact_refs",
            "metric_refs",
            "event_refs",
            "source_refs",
            "evidence_refs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_refs(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "track_refs",
            _normalize_track_refs(self.track_refs),
        )
        object.__setattr__(
            self,
            "numeric_claims",
            _normalize_numeric_claims(self.numeric_claims),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "kind": self.kind.value,
            "statement": self.statement,
            "fact_refs": list(self.fact_refs),
            "metric_refs": list(self.metric_refs),
            "event_refs": list(self.event_refs),
            "track_refs": [item.to_dict() for item in self.track_refs],
            "source_refs": list(self.source_refs),
            "evidence_refs": list(self.evidence_refs),
            "numeric_claims": [
                item.to_dict() for item in self.numeric_claims
            ],
        }


@dataclass(frozen=True, slots=True)
class ReportRecommendation:
    """A non-factual recommendation grounded in report findings or facts."""

    recommendation_id: str
    action: str
    priority: str
    basis_finding_refs: tuple[str, ...] = ()
    basis_fact_refs: tuple[str, ...] = ()
    basis_metric_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recommendation_id",
            _validate_identifier(self.recommendation_id, "recommendation_id"),
        )
        object.__setattr__(
            self,
            "action",
            _validate_text(self.action, "action"),
        )
        object.__setattr__(
            self,
            "priority",
            _validate_identifier(self.priority, "priority"),
        )
        for field_name in (
            "basis_finding_refs",
            "basis_fact_refs",
            "basis_metric_refs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_refs(getattr(self, field_name), field_name),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "action": self.action,
            "priority": self.priority,
            "basis_finding_refs": list(self.basis_finding_refs),
            "basis_fact_refs": list(self.basis_fact_refs),
            "basis_metric_refs": list(self.basis_metric_refs),
        }


@dataclass(frozen=True, slots=True)
class ReportEvidenceReference:
    """Opaque evidence metadata bound to one context event fact."""

    evidence_ref: str
    event_id: str
    track_id: int
    snapshot_ref: str
    occurred_at: str

    def __post_init__(self) -> None:
        evidence_ref = _validate_identifier(
            self.evidence_ref,
            "evidence_ref",
        )
        if _EVIDENCE_REF_PATTERN.fullmatch(evidence_ref) is None:
            raise ValueError("evidence_ref must use the EVID:<event_id> convention")
        object.__setattr__(self, "evidence_ref", evidence_ref)
        event_id = _validate_identifier(self.event_id, "event_id")
        object.__setattr__(self, "event_id", event_id)
        if evidence_ref != f"EVID:{event_id}":
            raise ValueError("evidence_ref must match its event_id")
        if isinstance(self.track_id, bool) or not isinstance(self.track_id, int):
            raise TypeError("track_id must be an integer")
        if self.track_id < 0:
            raise ValueError("track_id cannot be negative")
        object.__setattr__(
            self,
            "snapshot_ref",
            _validate_text(self.snapshot_ref, "snapshot_ref"),
        )
        object.__setattr__(
            self,
            "occurred_at",
            normalize_utc_timestamp(self.occurred_at),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_ref": self.evidence_ref,
            "event_id": self.event_id,
            "track_id": self.track_id,
            "track_scope": "tracker_scoped",
            "snapshot_ref": self.snapshot_ref,
            "occurred_at": self.occurred_at,
        }


@dataclass(frozen=True, slots=True)
class ReportLimitation:
    """One limitation copied from the deterministic context."""

    field: str
    reason_code: str
    statement: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "field",
            _validate_identifier(self.field, "field"),
        )
        object.__setattr__(
            self,
            "reason_code",
            _validate_identifier(self.reason_code, "reason_code"),
        )
        object.__setattr__(
            self,
            "statement",
            _validate_text(self.statement, "statement"),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field,
            "reason_code": self.reason_code,
            "statement": self.statement,
        }


@dataclass(frozen=True, slots=True)
class StructuredSafetyReport:
    """Canonical ``phase8-report-v1`` contract."""

    source_context_sha256: str
    reporting_period: ReportingPeriod
    generation: ReportGeneration
    executive_summary: tuple[SafetyReportClaim, ...]
    key_findings: tuple[SafetyReportClaim, ...]
    risk_observations: tuple[SafetyReportClaim, ...]
    recommendations: tuple[ReportRecommendation, ...]
    evidence_references: tuple[ReportEvidenceReference, ...]
    limitations: tuple[ReportLimitation, ...]
    grounding_status: GroundingStatus | str = GroundingStatus.UNVALIDATED
    schema_version: str = REPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != REPORT_SCHEMA_VERSION:
            raise ValueError("unsupported schema_version")
        if not isinstance(self.reporting_period, ReportingPeriod):
            raise TypeError("reporting_period must be a ReportingPeriod")
        if not isinstance(self.generation, ReportGeneration):
            raise TypeError("generation must be a ReportGeneration")
        if not isinstance(self.source_context_sha256, str):
            raise TypeError("source_context_sha256 must be a string")
        try:
            grounding_status = GroundingStatus(self.grounding_status)
        except ValueError as exc:
            raise ValueError("grounding_status is unsupported") from exc
        object.__setattr__(self, "grounding_status", grounding_status)

        for field_name, expected_kind in (
            ("executive_summary", ClaimKind.OBSERVATION),
            ("key_findings", ClaimKind.OBSERVATION),
            ("risk_observations", ClaimKind.RISK),
        ):
            values = tuple(getattr(self, field_name))
            seen_ids: set[str] = set()
            for value in values:
                if not isinstance(value, SafetyReportClaim):
                    raise TypeError(
                        f"{field_name} must contain SafetyReportClaim objects"
                    )
                if value.kind is not expected_kind:
                    raise ValueError(
                        f"{field_name} contains a claim with the wrong kind"
                    )
                if value.claim_id in seen_ids:
                    raise ValueError(
                        f"{field_name} contains duplicate claim_id values"
                    )
                seen_ids.add(value.claim_id)
            object.__setattr__(
                self,
                field_name,
                tuple(sorted(values, key=lambda item: item.claim_id)),
            )

        recommendations = tuple(self.recommendations)
        recommendation_ids: set[str] = set()
        for recommendation in recommendations:
            if not isinstance(recommendation, ReportRecommendation):
                raise TypeError(
                    "recommendations must contain ReportRecommendation objects"
                )
            if recommendation.recommendation_id in recommendation_ids:
                raise ValueError(
                    "recommendations contain duplicate recommendation_id values"
                )
            recommendation_ids.add(recommendation.recommendation_id)
        object.__setattr__(
            self,
            "recommendations",
            tuple(
                sorted(
                    recommendations,
                    key=lambda item: item.recommendation_id,
                )
            ),
        )

        evidence_references = tuple(self.evidence_references)
        evidence_refs: set[str] = set()
        for reference in evidence_references:
            if not isinstance(reference, ReportEvidenceReference):
                raise TypeError(
                    "evidence_references must contain "
                    "ReportEvidenceReference objects"
                )
            if reference.evidence_ref in evidence_refs:
                raise ValueError(
                    "evidence_references contain duplicate evidence_ref values"
                )
            evidence_refs.add(reference.evidence_ref)
        object.__setattr__(
            self,
            "evidence_references",
            tuple(
                sorted(
                    evidence_references,
                    key=lambda item: item.evidence_ref,
                )
            ),
        )

        limitations = tuple(self.limitations)
        limitation_fields: set[str] = set()
        for limitation in limitations:
            if not isinstance(limitation, ReportLimitation):
                raise TypeError(
                    "limitations must contain ReportLimitation objects"
                )
            if limitation.field in limitation_fields:
                raise ValueError("limitations contain duplicate field values")
            limitation_fields.add(limitation.field)
        object.__setattr__(
            self,
            "limitations",
            tuple(sorted(limitations, key=lambda item: item.field)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_context_sha256": self.source_context_sha256,
            "reporting_period": self.reporting_period.to_dict(),
            "generation": self.generation.to_dict(),
            "executive_summary": [
                item.to_dict() for item in self.executive_summary
            ],
            "key_findings": [item.to_dict() for item in self.key_findings],
            "risk_observations": [
                item.to_dict() for item in self.risk_observations
            ],
            "recommendations": [
                item.to_dict() for item in self.recommendations
            ],
            "evidence_references": [
                item.to_dict() for item in self.evidence_references
            ],
            "limitations": [item.to_dict() for item in self.limitations],
            "grounding_status": self.grounding_status.value,
        }

    def to_canonical_json(self) -> str:
        """Return deterministic UTF-8 JSON for the same logical report."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


def is_sha256(value: object) -> bool:
    """Return whether a value is a canonical lowercase SHA256 digest."""

    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None
