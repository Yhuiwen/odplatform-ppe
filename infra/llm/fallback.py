"""Deterministic local report fallback for ``phase8-report-v1``.

The fallback is intentionally provider-independent and contains no generative
logic. It only restates values already present in a ``phase8-context-v1``
payload and fails closed when required analytics are missing or inconsistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.schemas.compliance import ComplianceEventType
from core.schemas.safety import (
    MetricValue,
    SafetyAnalysisContext,
)
from core.schemas.safety_report import (
    ClaimKind,
    GenerationMode,
    GroundingStatus,
    MetricNumericClaim,
    ReportEvidenceReference,
    ReportGeneration,
    ReportLimitation,
    ReportRecommendation,
    SafetyReportClaim,
    StructuredSafetyReport,
    TrackReference,
)
from services.safety_context_builder import SafetyContextBuilder

__all__ = ["TemplateFallback", "TemplateFallbackError"]


_REQUIRED_METRIC_IDS = (
    "analytics.event_total_count",
    "analytics.evidence.available_count",
    "analytics.evidence.missing_count",
    "analytics.first_occurrence",
    "analytics.last_occurrence",
    "analytics.event_count.by_type.NO_HELMET",
    "analytics.event_count.by_type.NO_VEST",
    "analytics.event_count.by_type.PPE_UNKNOWN",
)


@dataclass
class TemplateFallbackError(ValueError):
    """A deterministic fail-closed fallback error."""

    code: str
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("message must be a non-empty string")
        super().__init__(self.message)


class TemplateFallback:
    """Build a grounded report using deterministic local templates only."""

    def generate(
        self,
        context: SafetyAnalysisContext,
    ) -> StructuredSafetyReport:
        if not isinstance(context, SafetyAnalysisContext):
            raise TemplateFallbackError(
                code="REPORT_SCHEMA_INVALID",
                message="context must be a SafetyAnalysisContext",
            )

        metrics = self._validate_context_metrics(context)
        total = self._integer_metric(
            metrics,
            "analytics.event_total_count",
        )
        if total != len(context.observed_facts):
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=(
                    "analytics.event_total_count does not match the number "
                    "of observed facts"
                ),
            )

        evidence_available = self._integer_metric(
            metrics,
            "analytics.evidence.available_count",
        )
        evidence_missing = self._integer_metric(
            metrics,
            "analytics.evidence.missing_count",
        )
        self._validate_evidence_counts(
            context,
            available=evidence_available,
            missing=evidence_missing,
        )

        type_counts = {
            event_type: self._integer_metric(
                metrics,
                f"analytics.event_count.by_type.{event_type.value}",
            )
            for event_type in ComplianceEventType
        }
        if sum(type_counts.values()) != total:
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message="event type counts must sum to the total event count",
            )

        first_occurrence = self._timestamp_metric(
            metrics,
            "analytics.first_occurrence",
        )
        last_occurrence = self._timestamp_metric(
            metrics,
            "analytics.last_occurrence",
        )
        self._validate_occurrences(
            context,
            first_occurrence=first_occurrence,
            last_occurrence=last_occurrence,
        )
        track_counts = self._validate_track_metrics(context, metrics)

        total_metric = "analytics.event_total_count"
        total_numeric = self._numeric_claim(total_metric, total)
        executive_summary = (
            self._claim(
                "summary-010-reporting-period",
                statement=self._summary_statement(context, total),
                metric_refs=(total_metric,),
                numeric_claims=(total_numeric,),
            ),
        )

        key_findings: list[SafetyReportClaim] = [
            self._claim(
                "finding-010-total-events",
                statement=(
                    f"The filtered event set contains {total} persisted "
                    "compliance events."
                ),
                metric_refs=(total_metric,),
                numeric_claims=(total_numeric,),
            )
        ]
        type_finding_refs = self._type_findings(
            key_findings,
            type_counts=type_counts,
        )

        if total:
            first_metric = "analytics.first_occurrence"
            last_metric = "analytics.last_occurrence"
            key_findings.append(
                self._claim(
                    "finding-030-first-occurrence",
                    statement=(
                        "The earliest persisted event timestamp in the "
                        f"reporting period is {first_occurrence}."
                    ),
                    metric_refs=(first_metric,),
                )
            )
            key_findings.append(
                self._claim(
                    "finding-040-last-occurrence",
                    statement=(
                        "The latest persisted event timestamp in the "
                        f"reporting period is {last_occurrence}."
                    ),
                    metric_refs=(last_metric,),
                )
            )

        evidence_available_ref = (
            "analytics.evidence.available_count"
        )
        evidence_missing_ref = "analytics.evidence.missing_count"
        key_findings.append(
            self._claim(
                "finding-050-evidence-availability",
                statement=(
                    "Persisted evidence references are available for "
                    f"{evidence_available} events and missing for "
                    f"{evidence_missing} events."
                ),
                metric_refs=(
                    evidence_available_ref,
                    evidence_missing_ref,
                ),
                numeric_claims=(
                    self._numeric_claim(
                        evidence_available_ref,
                        evidence_available,
                    ),
                    self._numeric_claim(
                        evidence_missing_ref,
                        evidence_missing,
                    ),
                ),
            )
        )

        if track_counts:
            track_ids = sorted(track_counts)
            key_findings.append(
                self._claim(
                    "finding-060-track-scope-recurrence",
                    statement=(
                        "Confirmed events were grouped across "
                        f"{len(track_ids)} tracker-scoped track_id values. "
                        "These track_id values are tracker-scoped and are "
                        "not stable person identity."
                    ),
                    metric_refs=tuple(
                        "analytics.event_count.by_track."
                        f"{track_id}"
                        for track_id in track_ids
                    ),
                    track_refs=tuple(
                        TrackReference(track_id=track_id)
                        for track_id in track_ids
                    ),
                    numeric_claims=tuple(
                        self._numeric_claim(
                            (
                                "analytics.event_count.by_track."
                                f"{track_id}"
                            ),
                            track_counts[track_id],
                        )
                        for track_id in track_ids
                    ),
                )
            )

        return StructuredSafetyReport(
            source_context_sha256=(
                SafetyContextBuilder.fingerprint(context)
            ),
            reporting_period=context.metadata.reporting_period,
            generation=ReportGeneration(
                mode=GenerationMode.TEMPLATE_FALLBACK,
                degraded=True,
            ),
            executive_summary=executive_summary,
            key_findings=tuple(key_findings),
            risk_observations=self._risk_observations(type_counts),
            recommendations=self._recommendations(
                type_counts,
                type_finding_refs,
            ),
            evidence_references=self._evidence_references(context),
            limitations=tuple(
                ReportLimitation(
                    field=field.field,
                    reason_code=field.reason_code,
                    statement=field.reason,
                )
                for field in context.unavailable_fields
            ),
            grounding_status=GroundingStatus.UNVALIDATED,
        )

    @staticmethod
    def _summary_statement(
        context: SafetyAnalysisContext,
        total: int,
    ) -> str:
        period = context.metadata.reporting_period
        if total:
            return (
                "The reporting period contains "
                f"{total} persisted events in the inclusive interval from "
                f"{period.start_at} to {period.end_at}."
            )
        return (
            "The reporting period contains 0 persisted events in the "
            "inclusive interval from "
            f"{period.start_at} to {period.end_at}; no activity is inferred "
            "for this period."
        )

    @classmethod
    def _type_findings(
        cls,
        key_findings: list[SafetyReportClaim],
        *,
        type_counts: dict[ComplianceEventType, int],
    ) -> dict[ComplianceEventType, str]:
        find_refs: dict[ComplianceEventType, str] = {}
        for index, (event_type, count) in enumerate(
            sorted(
                type_counts.items(),
                key=lambda item: (-item[1], item[0].value),
            ),
            start=1,
        ):
            if count == 0:
                continue
            claim_id = f"finding-020-type-{index:03d}"
            metric_ref = (
                f"analytics.event_count.by_type.{event_type.value}"
            )
            key_findings.append(
                cls._claim(
                    claim_id,
                    statement=(
                        f"Recorded events of type {event_type.value}: "
                        f"{count}."
                    ),
                    metric_refs=(metric_ref,),
                    numeric_claims=(
                        cls._numeric_claim(metric_ref, count),
                    ),
                )
            )
            find_refs[event_type] = claim_id
        return find_refs

    @staticmethod
    def _claim(
        claim_id: str,
        *,
        statement: str,
        **kwargs: Any,
    ) -> SafetyReportClaim:
        return SafetyReportClaim(
            claim_id=claim_id,
            kind=ClaimKind.OBSERVATION,
            statement=statement,
            **kwargs,
        )

    @staticmethod
    def _numeric_claim(
        metric_ref: str,
        value: int,
    ) -> MetricNumericClaim:
        return MetricNumericClaim(
            metric_ref=metric_ref,
            value=value,
        )

    @staticmethod
    def _integer_metric(
        metrics: dict[str, MetricValue],
        metric_id: str,
    ) -> int:
        metric = metrics.get(metric_id)
        if metric is None:
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=f"required context metric is missing: {metric_id}",
            )
        value = metric.value
        if isinstance(value, bool) or not isinstance(value, int):
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=(
                    "required context metric is not an integer: "
                    f"{metric_id}"
                ),
            )
        if value < 0:
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=(
                    "required context metric cannot be negative: "
                    f"{metric_id}"
                ),
            )
        return value

    @staticmethod
    def _timestamp_metric(
        metrics: dict[str, MetricValue],
        metric_id: str,
    ) -> str | None:
        metric = metrics.get(metric_id)
        if metric is None:
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=f"required context metric is missing: {metric_id}",
            )
        value = metric.value
        if value is not None and not isinstance(value, str):
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=(
                    f"required timestamp metric is malformed: {metric_id}"
                ),
            )
        return value

    @staticmethod
    def _validate_context_metrics(
        context: SafetyAnalysisContext,
    ) -> dict[str, MetricValue]:
        metrics = {
            metric.metric_id: metric
            for metric in context.calculated_metrics
        }
        missing = [
            metric_id
            for metric_id in _REQUIRED_METRIC_IDS
            if metric_id not in metrics
        ]
        if missing:
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=(
                    "required context metrics are missing: "
                    + ", ".join(missing)
                ),
            )
        return metrics

    @staticmethod
    def _validate_evidence_counts(
        context: SafetyAnalysisContext,
        *,
        available: int,
        missing: int,
    ) -> None:
        observed_available = sum(
            fact.evidence_available for fact in context.observed_facts
        )
        observed_missing = len(context.observed_facts) - observed_available
        if (
            available != observed_available
            or missing != observed_missing
            or available + missing != len(context.observed_facts)
        ):
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=(
                    "evidence metrics do not match observed context facts"
                ),
            )

    @staticmethod
    def _validate_occurrences(
        context: SafetyAnalysisContext,
        *,
        first_occurrence: str | None,
        last_occurrence: str | None,
    ) -> None:
        if context.observed_facts:
            expected_first = min(
                fact.occurred_at for fact in context.observed_facts
            )
            expected_last = max(
                fact.occurred_at for fact in context.observed_facts
            )
        else:
            expected_first = None
            expected_last = None
        if (
            first_occurrence != expected_first
            or last_occurrence != expected_last
        ):
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=(
                    "occurrence metrics do not match observed context facts"
                ),
            )

    @staticmethod
    def _validate_track_metrics(
        context: SafetyAnalysisContext,
        metrics: dict[str, MetricValue],
    ) -> dict[int, int]:
        expected: dict[int, int] = {}
        for fact in context.observed_facts:
            expected[fact.track_id] = expected.get(fact.track_id, 0) + 1

        actual: dict[int, int] = {}
        prefix = "analytics.event_count.by_track."
        for metric in context.calculated_metrics:
            if not metric.metric_id.startswith(prefix):
                continue
            suffix = metric.metric_id[len(prefix):]
            if not suffix.isdigit():
                raise TemplateFallbackError(
                    code="FALLBACK_FAILED",
                    message=(
                        "track metric identifier is malformed: "
                        f"{metric.metric_id}"
                    ),
                )
            track_id = int(suffix)
            value = TemplateFallback._integer_metric(
                metrics,
                metric.metric_id,
            )
            if track_id in actual:
                raise TemplateFallbackError(
                    code="FALLBACK_FAILED",
                    message=(
                        "duplicate track metric identifier: "
                        f"{metric.metric_id}"
                    ),
                )
            actual[track_id] = value

        if actual != expected:
            raise TemplateFallbackError(
                code="FALLBACK_FAILED",
                message=(
                    "track metrics do not match observed context facts"
                ),
            )
        return actual

    @staticmethod
    def _risk_observations(
        type_counts: dict[ComplianceEventType, int],
    ) -> tuple[SafetyReportClaim, ...]:
        positive = [
            (event_type, count)
            for event_type, count in type_counts.items()
            if count > 0
        ]
        if not positive:
            return ()
        ordered = sorted(
            positive,
            key=lambda item: (-item[1], item[0].value),
        )
        if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
            return ()

        event_type, count = ordered[0]
        metric_ref = (
            f"analytics.event_count.by_type.{event_type.value}"
        )
        return (
            SafetyReportClaim(
                claim_id="risk-010-dominant-event-type",
                kind=ClaimKind.RISK,
                statement=(
                    "The most frequent recorded event type is "
                    f"{event_type.value} with {count} events. This statement "
                    "is limited to observed frequency and does not establish "
                    "severity, legal causation or employee identity."
                ),
                metric_refs=(metric_ref,),
                numeric_claims=(
                    MetricNumericClaim(
                        metric_ref=metric_ref,
                        value=count,
                    ),
                ),
            ),
        )

    @staticmethod
    def _recommendations(
        type_counts: dict[ComplianceEventType, int],
        type_finding_refs: dict[ComplianceEventType, str],
    ) -> tuple[ReportRecommendation, ...]:
        recommendations: list[ReportRecommendation] = []
        rule_by_type = (
            (
                ComplianceEventType.NO_HELMET,
                "rec-010-no-helmet",
                "Review helmet-use procedures and the relevant recorded "
                "evidence for NO_HELMET events.",
                "high",
            ),
            (
                ComplianceEventType.NO_VEST,
                "rec-020-no-vest",
                "Review high-visibility vest procedures and the relevant "
                "recorded evidence for NO_VEST events.",
                "medium",
            ),
            (
                ComplianceEventType.PPE_UNKNOWN,
                "rec-030-ppe-unknown",
                "Review uncertain PPE detections and their evidence before "
                "taking operational action.",
                "medium",
            ),
        )
        for event_type, recommendation_id, action, priority in rule_by_type:
            if type_counts[event_type] <= 0:
                continue
            metric_ref = (
                f"analytics.event_count.by_type.{event_type.value}"
            )
            recommendations.append(
                ReportRecommendation(
                    recommendation_id=recommendation_id,
                    action=action,
                    priority=priority,
                    basis_finding_refs=(
                        type_finding_refs[event_type],
                    ),
                    basis_metric_refs=(metric_ref,),
                )
            )
        return tuple(recommendations)

    @staticmethod
    def _evidence_references(
        context: SafetyAnalysisContext,
    ) -> tuple[ReportEvidenceReference, ...]:
        references = []
        for fact in context.observed_facts:
            if not fact.evidence_available or fact.snapshot_ref is None:
                continue
            references.append(
                ReportEvidenceReference(
                    evidence_ref=f"EVID:{fact.event_id}",
                    event_id=fact.event_id,
                    track_id=fact.track_id,
                    snapshot_ref=fact.snapshot_ref,
                    occurred_at=fact.occurred_at,
                )
            )
        return tuple(
            sorted(references, key=lambda item: item.evidence_ref)
        )
