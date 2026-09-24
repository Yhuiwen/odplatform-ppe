"""Deterministic grounding validation for ``phase8-report-v1``."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from core.schemas.safety import (
    MetricValue,
    SafetyAnalysisContext,
    SafetyEventFact,
)
from core.schemas.safety_report import (
    MetricNumericClaim,
    ReportEvidenceReference,
    ReportRecommendation,
    SafetyReportClaim,
    StructuredSafetyReport,
    is_sha256,
)
from services.safety_context_builder import SafetyContextBuilder

__all__ = [
    "ReportValidationIssue",
    "ReportValidationResult",
    "SafetyReportGroundingValidator",
]


_WINDOWS_ABSOLUTE_PATH = re.compile(
    r'(?:^|[\s"\'(\[{=:,])(?:'
    r"[A-Za-z]:[\\/](?:[^\\/\s\"']+[\\/])*[^\\/\s\"']+"
    r"|\\\\[^\\/\s\"']+\\[^\\/\s\"']+"
    r")"
)
_POSIX_ABSOLUTE_PATH = re.compile(
    r"(?:^|[\s\"'(\[{=:,])/(?:[^/\s\"'`]+/)+[^/\s\"'`]+"
)
_DATABASE_PATH = re.compile(
    r"(?i)(?:^|[^\w])(?:[^\s\"']+\.(?:db|sqlite|sqlite3))"
)
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|"
    r"password|passwd|credential|authorization|bearer)\b\s*[:=]"
)
_BEARER_TOKEN = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/\-=]{8,}"
)
_CREDENTIAL_URI = re.compile(
    r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@"
)

_CODE_ORDER = (
    "REPORT_SCHEMA_INVALID",
    "CONTEXT_FINGERPRINT_MISMATCH",
    "UNKNOWN_FACT_REFERENCE",
    "UNKNOWN_METRIC_REFERENCE",
    "UNKNOWN_EVENT_REFERENCE",
    "UNKNOWN_TRACK_REFERENCE",
    "UNKNOWN_EVIDENCE_REFERENCE",
    "NUMERIC_VALUE_MISMATCH",
    "UNGROUNDED_FINDING",
    "UNGROUNDED_RISK_OBSERVATION",
    "INVALID_RECOMMENDATION_BASIS",
    "UNAVAILABLE_FIELD_CLAIM",
    "PATH_LEAK_DETECTED",
)
_CODE_RANK = {code: index for index, code in enumerate(_CODE_ORDER)}


@dataclass(frozen=True, slots=True)
class ReportValidationIssue:
    """One deterministic validation error or warning."""

    code: str
    path: str
    message: str

    def __post_init__(self) -> None:
        if self.code not in _CODE_RANK:
            raise ValueError("code is unsupported")
        if not isinstance(self.path, str) or not self.path:
            raise ValueError("path must be a non-empty string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string")

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ReportValidationResult:
    """Fail-closed report validation outcome."""

    valid: bool
    errors: tuple[ReportValidationIssue, ...] = ()
    warnings: tuple[ReportValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        errors = tuple(self.errors)
        warnings = tuple(self.warnings)
        if any(not isinstance(item, ReportValidationIssue) for item in errors):
            raise TypeError("errors must contain ReportValidationIssue objects")
        if any(not isinstance(item, ReportValidationIssue) for item in warnings):
            raise TypeError("warnings must contain ReportValidationIssue objects")
        if not isinstance(self.valid, bool):
            raise TypeError("valid must be a boolean")
        if self.valid != (len(errors) == 0):
            raise ValueError("valid must match whether errors is empty")
        object.__setattr__(self, "errors", _sort_issues(errors))
        object.__setattr__(self, "warnings", _sort_issues(warnings))

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [item.to_dict() for item in self.errors],
            "warnings": [item.to_dict() for item in self.warnings],
        }

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


def _sort_issues(
    values: Iterable[ReportValidationIssue],
) -> tuple[ReportValidationIssue, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (_CODE_RANK[item.code], item.path, item.message),
        )
    )


def _issue(code: str, path: str, message: str) -> ReportValidationIssue:
    return ReportValidationIssue(code=code, path=path, message=message)


class SafetyReportGroundingValidator:
    """Validate report references against one deterministic context."""

    def __init__(
        self,
        context_builder: type[SafetyContextBuilder] = SafetyContextBuilder,
    ) -> None:
        if not callable(getattr(context_builder, "fingerprint", None)):
            raise TypeError("context_builder must expose fingerprint(context)")
        self.context_builder = context_builder

    def validate(
        self,
        report: StructuredSafetyReport,
        context: SafetyAnalysisContext,
    ) -> ReportValidationResult:
        """Return a deterministic fail-closed validation result."""

        if not isinstance(context, SafetyAnalysisContext):
            return ReportValidationResult(
                valid=False,
                errors=(
                    _issue(
                        "REPORT_SCHEMA_INVALID",
                        "context",
                        "context must be a SafetyAnalysisContext",
                    ),
                ),
            )
        if not isinstance(report, StructuredSafetyReport):
            return ReportValidationResult(
                valid=False,
                errors=(
                    _issue(
                        "REPORT_SCHEMA_INVALID",
                        "report",
                        "report must be a StructuredSafetyReport",
                    ),
                ),
            )

        errors: list[ReportValidationIssue] = []
        warnings: list[ReportValidationIssue] = []
        self._validate_period(report, context, errors)
        self._validate_fingerprint(report, context, errors)

        fact_by_id = {fact.fact_id: fact for fact in context.observed_facts}
        event_by_id = {fact.event_id: fact for fact in context.observed_facts}
        metric_by_id = {
            metric.metric_id: metric for metric in context.calculated_metrics
        }
        unavailable_by_field = {
            field.field: field for field in context.unavailable_fields
        }
        evidence_by_ref = {
            evidence.evidence_ref: evidence
            for evidence in report.evidence_references
        }
        claim_lookup = {
            claim.claim_id: claim
            for claim in (
                *report.executive_summary,
                *report.key_findings,
                *report.risk_observations,
            )
        }

        self._validate_evidence_references(
            report.evidence_references,
            event_by_id,
            errors,
        )
        for path, claim in self._iter_claims(report):
            self._validate_claim(
                claim,
                path=path,
                fact_by_id=fact_by_id,
                event_by_id=event_by_id,
                metric_by_id=metric_by_id,
                unavailable_by_field=unavailable_by_field,
                evidence_by_ref=evidence_by_ref,
                errors=errors,
            )
        self._validate_recommendations(
            report.recommendations,
            claim_lookup=claim_lookup,
            fact_by_id=fact_by_id,
            metric_by_id=metric_by_id,
            errors=errors,
        )
        self._validate_limitations(
            report,
            unavailable_by_field=unavailable_by_field,
            errors=errors,
            warnings=warnings,
        )
        self._validate_privacy(report, errors)

        return ReportValidationResult(
            valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _iter_claims(
        report: StructuredSafetyReport,
    ) -> Iterable[tuple[str, SafetyReportClaim]]:
        for claim in report.executive_summary:
            yield f"executive_summary[{claim.claim_id}]", claim
        for claim in report.key_findings:
            yield f"key_findings[{claim.claim_id}]", claim
        for claim in report.risk_observations:
            yield f"risk_observations[{claim.claim_id}]", claim

    @staticmethod
    def _validate_period(
        report: StructuredSafetyReport,
        context: SafetyAnalysisContext,
        errors: list[ReportValidationIssue],
    ) -> None:
        if report.reporting_period != context.metadata.reporting_period:
            errors.append(
                _issue(
                    "REPORT_SCHEMA_INVALID",
                    "reporting_period",
                    "reporting_period must match the source context",
                )
            )

    def _validate_fingerprint(
        self,
        report: StructuredSafetyReport,
        context: SafetyAnalysisContext,
        errors: list[ReportValidationIssue],
    ) -> None:
        if not is_sha256(report.source_context_sha256):
            errors.append(
                _issue(
                    "CONTEXT_FINGERPRINT_MISMATCH",
                    "source_context_sha256",
                    "source_context_sha256 must be a lowercase SHA256 digest",
                )
            )
            return
        expected = self.context_builder.fingerprint(context)
        if report.source_context_sha256 != expected:
            errors.append(
                _issue(
                    "CONTEXT_FINGERPRINT_MISMATCH",
                    "source_context_sha256",
                    "source_context_sha256 does not match the source context",
                )
            )

    def _validate_evidence_references(
        self,
        references: tuple[ReportEvidenceReference, ...],
        event_by_id: dict[str, SafetyEventFact],
        errors: list[ReportValidationIssue],
    ) -> None:
        for reference in references:
            path = f"evidence_references[{reference.evidence_ref}]"
            fact = event_by_id.get(reference.event_id)
            if fact is None:
                errors.append(
                    _issue(
                        "UNKNOWN_EVENT_REFERENCE",
                        path,
                        f"unknown event_id: {reference.event_id}",
                    )
                )
                continue
            if fact.snapshot_ref is None or not fact.evidence_available:
                errors.append(
                    _issue(
                        "UNKNOWN_EVIDENCE_REFERENCE",
                        path,
                        "the referenced event has no available snapshot",
                    )
                )
            if reference.track_id != fact.track_id:
                errors.append(
                    _issue(
                        "UNKNOWN_TRACK_REFERENCE",
                        path,
                        "evidence track_id does not belong to the event",
                    )
                )
            if reference.snapshot_ref != fact.snapshot_ref:
                errors.append(
                    _issue(
                        "UNKNOWN_EVIDENCE_REFERENCE",
                        path,
                        "snapshot_ref does not match the event evidence",
                    )
                )
            if reference.occurred_at != fact.occurred_at:
                errors.append(
                    _issue(
                        "UNKNOWN_EVENT_REFERENCE",
                        path,
                        "occurred_at does not match the event fact",
                    )
                )

    def _validate_claim(
        self,
        claim: SafetyReportClaim,
        *,
        path: str,
        fact_by_id: dict[str, SafetyEventFact],
        event_by_id: dict[str, SafetyEventFact],
        metric_by_id: dict[str, MetricValue],
        unavailable_by_field: dict[str, Any],
        evidence_by_ref: dict[str, ReportEvidenceReference],
        errors: list[ReportValidationIssue],
    ) -> None:
        referenced_facts: set[SafetyEventFact] = set()
        for fact_ref in claim.fact_refs:
            fact = fact_by_id.get(fact_ref)
            if fact is None:
                errors.append(
                    _issue(
                        "UNKNOWN_FACT_REFERENCE",
                        f"{path}.fact_refs",
                        f"unknown fact_ref: {fact_ref}",
                    )
                )
            else:
                referenced_facts.add(fact)

        for event_ref in claim.event_refs:
            fact = event_by_id.get(event_ref)
            if fact is None:
                errors.append(
                    _issue(
                        "UNKNOWN_EVENT_REFERENCE",
                        f"{path}.event_refs",
                        f"unknown event_id: {event_ref}",
                    )
                )
            else:
                referenced_facts.add(fact)

        allowed_tracks = {
            fact.track_id for fact in referenced_facts
        }
        allowed_sources = {
            fact.source_ref
            for fact in referenced_facts
            if fact.source_ref is not None
        }
        for metric_ref in claim.metric_refs:
            if metric_ref in unavailable_by_field:
                errors.append(
                    _issue(
                        "UNAVAILABLE_FIELD_CLAIM",
                        f"{path}.metric_refs",
                        f"metric_ref is unavailable: {metric_ref}",
                    )
                )
                continue
            metric = metric_by_id.get(metric_ref)
            if metric is None:
                errors.append(
                    _issue(
                        "UNKNOWN_METRIC_REFERENCE",
                        f"{path}.metric_refs",
                        f"unknown metric_ref: {metric_ref}",
                    )
                )
                continue
            track_id = self._track_from_metric_id(metric.metric_id)
            if track_id is not None:
                allowed_tracks.add(track_id)
            metric_source_ref = self._source_from_metric_id(metric.metric_id)
            if metric_source_ref is not None:
                allowed_sources.add(metric_source_ref)

        for source_ref in claim.source_refs:
            if source_ref not in allowed_sources:
                errors.append(
                    _issue(
                        "UNKNOWN_EVIDENCE_REFERENCE",
                        f"{path}.source_refs",
                        f"source_ref is not grounded by referenced facts: "
                        f"{source_ref}",
                    )
                )

        for track_ref in claim.track_refs:
            if track_ref.track_id not in allowed_tracks:
                errors.append(
                    _issue(
                        "UNKNOWN_TRACK_REFERENCE",
                        f"{path}.track_refs",
                        f"track_id is not grounded by referenced facts or "
                        f"metrics: {track_ref.track_id}",
                    )
                )

        for evidence_ref in claim.evidence_refs:
            if evidence_ref not in evidence_by_ref:
                errors.append(
                    _issue(
                        "UNKNOWN_EVIDENCE_REFERENCE",
                        f"{path}.evidence_refs",
                        f"unknown evidence_ref: {evidence_ref}",
                    )
                )

        for numeric_claim in claim.numeric_claims:
            self._validate_numeric_claim(
                numeric_claim,
                path=f"{path}.numeric_claims",
                metric_by_id=metric_by_id,
                unavailable_by_field=unavailable_by_field,
                errors=errors,
            )

        if not claim.fact_refs and not claim.metric_refs:
            code = (
                "UNGROUNDED_RISK_OBSERVATION"
                if claim.kind.value == "risk"
                else "UNGROUNDED_FINDING"
            )
            errors.append(
                _issue(
                    code,
                    path,
                    "claim requires at least one fact_ref or metric_ref",
                )
            )

    @staticmethod
    def _track_from_metric_id(metric_id: str) -> int | None:
        prefix = "analytics.event_count.by_track."
        if not metric_id.startswith(prefix):
            return None
        value = metric_id[len(prefix):]
        if not value.isdigit():
            return None
        return int(value)

    @staticmethod
    def _source_from_metric_id(metric_id: str) -> str | None:
        prefix = "analytics.event_count.by_source_ref."
        if not metric_id.startswith(prefix):
            return None
        source_ref = metric_id[len(prefix):]
        return source_ref or None

    @staticmethod
    def _validate_numeric_claim(
        claim: MetricNumericClaim,
        *,
        path: str,
        metric_by_id: dict[str, MetricValue],
        unavailable_by_field: dict[str, Any],
        errors: list[ReportValidationIssue],
    ) -> None:
        if claim.metric_ref in unavailable_by_field:
            errors.append(
                _issue(
                    "UNAVAILABLE_FIELD_CLAIM",
                    path,
                    f"numeric claim targets unavailable field: "
                    f"{claim.metric_ref}",
                )
            )
            return
        metric = metric_by_id.get(claim.metric_ref)
        if metric is None:
            errors.append(
                _issue(
                    "UNKNOWN_METRIC_REFERENCE",
                    path,
                    f"unknown metric_ref: {claim.metric_ref}",
                )
            )
            return
        if metric.value is None or isinstance(metric.value, str):
            errors.append(
                _issue(
                    "NUMERIC_VALUE_MISMATCH",
                    path,
                    "numeric claim must reference a numeric metric",
                )
            )
            return
        if metric.value != claim.value:
            errors.append(
                _issue(
                    "NUMERIC_VALUE_MISMATCH",
                    path,
                    f"claim value {claim.value!r} does not match metric value "
                    f"{metric.value!r}",
                )
            )

    @staticmethod
    def _validate_recommendations(
        recommendations: tuple[ReportRecommendation, ...],
        *,
        claim_lookup: dict[str, SafetyReportClaim],
        fact_by_id: dict[str, SafetyEventFact],
        metric_by_id: dict[str, MetricValue],
        errors: list[ReportValidationIssue],
    ) -> None:
        for recommendation in recommendations:
            path = f"recommendations[{recommendation.recommendation_id}]"
            if not (
                recommendation.basis_finding_refs
                or recommendation.basis_fact_refs
                or recommendation.basis_metric_refs
            ):
                errors.append(
                    _issue(
                        "INVALID_RECOMMENDATION_BASIS",
                        path,
                        "recommendation requires at least one basis reference",
                    )
                )
            for finding_ref in recommendation.basis_finding_refs:
                if finding_ref not in claim_lookup:
                    errors.append(
                        _issue(
                            "INVALID_RECOMMENDATION_BASIS",
                            f"{path}.basis_finding_refs",
                            f"unknown finding_ref: {finding_ref}",
                        )
                    )
            for fact_ref in recommendation.basis_fact_refs:
                if fact_ref not in fact_by_id:
                    errors.append(
                        _issue(
                            "INVALID_RECOMMENDATION_BASIS",
                            f"{path}.basis_fact_refs",
                            f"unknown fact_ref: {fact_ref}",
                        )
                    )
            for metric_ref in recommendation.basis_metric_refs:
                if metric_ref not in metric_by_id:
                    errors.append(
                        _issue(
                            "INVALID_RECOMMENDATION_BASIS",
                            f"{path}.basis_metric_refs",
                            f"unknown metric_ref: {metric_ref}",
                        )
                    )

    @staticmethod
    def _validate_limitations(
        report: StructuredSafetyReport,
        *,
        unavailable_by_field: dict[str, Any],
        errors: list[ReportValidationIssue],
        warnings: list[ReportValidationIssue],
    ) -> None:
        report_fields = {item.field for item in report.limitations}
        for limitation in report.limitations:
            path = f"limitations[{limitation.field}]"
            expected = unavailable_by_field.get(limitation.field)
            if expected is None:
                errors.append(
                    _issue(
                        "UNAVAILABLE_FIELD_CLAIM",
                        path,
                        "limitation does not exist in the source context",
                    )
                )
                continue
            if limitation.reason_code != expected.reason_code:
                errors.append(
                    _issue(
                        "UNAVAILABLE_FIELD_CLAIM",
                        path,
                        "limitation reason_code does not match the source "
                        "context",
                    )
                )
        for field_name in sorted(set(unavailable_by_field) - report_fields):
            errors.append(
                _issue(
                    "UNAVAILABLE_FIELD_CLAIM",
                    "limitations",
                    f"missing context limitation: {field_name}",
                )
            )
        if warnings:
            warnings[:] = list(_sort_issues(warnings))

    @staticmethod
    def _validate_privacy(
        report: StructuredSafetyReport,
        errors: list[ReportValidationIssue],
    ) -> None:
        payload = report.to_dict()
        for path, value in _iter_strings(payload):
            checks = (
                (_WINDOWS_ABSOLUTE_PATH, "absolute Windows path"),
                (_POSIX_ABSOLUTE_PATH, "absolute POSIX path"),
                (_DATABASE_PATH, "database path"),
                (_CREDENTIAL_ASSIGNMENT, "credential-like field"),
                (_BEARER_TOKEN, "bearer token"),
                (_CREDENTIAL_URI, "credential-bearing URI"),
            )
            for pattern, label in checks:
                if pattern.search(value):
                    errors.append(
                        _issue(
                            "PATH_LEAK_DETECTED",
                            path,
                            f"report contains prohibited {label}",
                        )
                    )


def _iter_strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key in sorted(value):
            yield from _iter_strings(value[key], f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from _iter_strings(item, f"{path}[{index}]")
