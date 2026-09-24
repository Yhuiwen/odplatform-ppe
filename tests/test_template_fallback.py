from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus
from core.schemas.safety import (
    SafetyAnalysisContext,
    SafetyAnalyticsQuery,
    SafetyAnalyticsResult,
    SafetyEventFact,
    UnavailableField,
)
from core.schemas.safety_report import (
    GenerationMode,
    GroundingStatus,
)
from infra.llm.fallback import TemplateFallback, TemplateFallbackError
from services.report_service import ReportService, ReportServiceError
from services.safety_context_builder import SafetyContextBuilder
from services.safety_report_grounding_validator import (
    ReportValidationIssue,
    ReportValidationResult,
    SafetyReportGroundingValidator,
)

FIXED_CLOCK = lambda: datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)

UNAVAILABLE_FIELDS = (
    UnavailableField(
        field="metrics.alert_delivery",
        reason_code="NO_ALERT_TELEMETRY_TABLE",
        reason="No delivery telemetry is persisted.",
    ),
    UnavailableField(
        field="metrics.cross_session_identity",
        reason_code="NO_AUTHORITATIVE_IDENTITY_SOURCE",
        reason="No authoritative cross-session identity source exists.",
    ),
    UnavailableField(
        field="metrics.per_event_source_attribution",
        reason_code="SOURCE_NOT_IN_EVENT_PROJECTION",
        reason="The event projection has no per-event source attribution.",
    ),
    UnavailableField(
        field="metrics.unique_person_count",
        reason_code="TRACK_ID_NOT_STABLE_IDENTITY",
        reason="Track IDs are tracker-scoped and not stable identity.",
    ),
    UnavailableField(
        field="metrics.violation_duration",
        reason_code="NO_PERSISTED_DURATION_FIELD",
        reason="No persisted violation-duration field exists.",
    ),
)


def _fact(
    event_id: str,
    *,
    occurred_at: str,
    event_type: ComplianceEventType,
    track_id: int,
    snapshot_ref: str | None = None,
) -> SafetyEventFact:
    return SafetyEventFact(
        fact_id=f"EVT:{event_id}",
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        confidence=0.91,
        track_id=track_id,
        source_ref=None,
        status=EventStatus.OPEN,
        snapshot_ref=snapshot_ref,
        evidence_available=snapshot_ref is not None,
    )


def _context(
    facts: tuple[SafetyEventFact, ...],
) -> SafetyAnalysisContext:
    query = SafetyAnalyticsQuery(
        start_at="2026-09-23T00:00:00Z",
        end_at="2026-09-23T23:59:59Z",
    )
    counts_by_type = tuple(
        (
            event_type,
            sum(1 for fact in facts if fact.event_type is event_type),
        )
        for event_type in ComplianceEventType
    )
    counts_by_status = tuple(
        (
            status,
            sum(1 for fact in facts if fact.status is status),
        )
        for status in EventStatus
    )
    counts_by_track = tuple(
        (track_id, sum(1 for fact in facts if fact.track_id == track_id))
        for track_id in sorted({fact.track_id for fact in facts})
    )
    counts_by_day = tuple(
        (
            day,
            sum(
                1
                for fact in facts
                if fact.occurred_at.startswith(day)
            ),
        )
        for day in sorted(
            {fact.occurred_at[:10] for fact in facts}
        )
    )
    counts_by_source_ref = tuple(
        (source_ref, 1)
        for source_ref in sorted(
            {
                fact.source_ref
                for fact in facts
                if fact.source_ref is not None
            }
        )
    )
    occurrences = [fact.occurred_at for fact in facts]
    analytics = SafetyAnalyticsResult(
        query=query,
        facts=facts,
        counts_by_type=counts_by_type,
        counts_by_status=counts_by_status,
        counts_by_track=counts_by_track,
        counts_by_day=counts_by_day,
        counts_by_source_ref=counts_by_source_ref,
        first_occurrence=min(occurrences) if occurrences else None,
        last_occurrence=max(occurrences) if occurrences else None,
        evidence_available_count=sum(
            fact.evidence_available for fact in facts
        ),
        evidence_missing_count=sum(
            not fact.evidence_available for fact in facts
        ),
        unavailable_fields=UNAVAILABLE_FIELDS,
    )
    return SafetyContextBuilder(clock=FIXED_CLOCK).build(analytics)


def _mixed_context() -> SafetyAnalysisContext:
    return _context(
        (
            _fact(
                "EVT-A",
                occurred_at="2026-09-23T12:00:00Z",
                event_type=ComplianceEventType.NO_HELMET,
                track_id=7,
                snapshot_ref="20260923/event_EVT-A.jpg",
            ),
            _fact(
                "EVT-B",
                occurred_at="2026-09-23T13:00:00Z",
                event_type=ComplianceEventType.NO_VEST,
                track_id=8,
            ),
            _fact(
                "EVT-C",
                occurred_at="2026-09-23T14:00:00Z",
                event_type=ComplianceEventType.NO_HELMET,
                track_id=7,
            ),
        )
    )


def _all_type_context() -> SafetyAnalysisContext:
    return _context(
        (
            _fact(
                "EVT-A",
                occurred_at="2026-09-23T12:00:00Z",
                event_type=ComplianceEventType.NO_HELMET,
                track_id=7,
            ),
            _fact(
                "EVT-B",
                occurred_at="2026-09-23T13:00:00Z",
                event_type=ComplianceEventType.NO_VEST,
                track_id=8,
            ),
            _fact(
                "EVT-C",
                occurred_at="2026-09-23T14:00:00Z",
                event_type=ComplianceEventType.PPE_UNKNOWN,
                track_id=9,
            ),
        )
    )


def test_fallback_is_deterministic_grounded_and_service_marks_valid() -> None:
    context = _mixed_context()
    fallback = TemplateFallback()

    first = fallback.generate(context)
    second = fallback.generate(context)
    result = SafetyReportGroundingValidator().validate(first, context)
    served = ReportService().generate(context)

    assert first.to_canonical_json() == second.to_canonical_json()
    assert result.valid
    assert served.grounding_status is GroundingStatus.VALID
    assert served.generation.mode is GenerationMode.TEMPLATE_FALLBACK
    assert served.generation.degraded is True
    assert served.source_context_sha256 == (
        SafetyContextBuilder.fingerprint(context)
    )


def test_findings_use_exact_metrics_and_deterministic_tie_order() -> None:
    context = _all_type_context()
    report = TemplateFallback().generate(context)
    type_findings = [
        finding
        for finding in report.key_findings
        if finding.claim_id.startswith("finding-020-type-")
    ]

    assert [
        finding.claim_id for finding in type_findings
    ] == [
        "finding-020-type-001",
        "finding-020-type-002",
        "finding-020-type-003",
    ]
    assert [
        finding.numeric_claims[0].value for finding in type_findings
    ] == [1, 1, 1]
    assert report.risk_observations == ()


def test_event_track_and_evidence_references_are_valid() -> None:
    context = _mixed_context()
    report = TemplateFallback().generate(context)
    result = SafetyReportGroundingValidator().validate(report, context)

    assert result.valid
    assert {
        reference.event_id for reference in report.evidence_references
    } == {"EVT-A"}
    assert {
        reference.track_id
        for finding in report.key_findings
        for reference in finding.track_refs
    } == {7, 8}
    assert [item.evidence_ref for item in report.evidence_references] == [
        "EVID:EVT-A"
    ]


def test_empty_context_produces_valid_zero_event_report() -> None:
    context = _context(())
    fallback_report = TemplateFallback().generate(context)
    report = ReportService().generate(context)
    result = SafetyReportGroundingValidator().validate(
        fallback_report,
        context,
    )

    assert result.valid
    assert report.executive_summary[0].numeric_claims[0].value == 0
    assert report.evidence_references == ()
    assert report.risk_observations == ()
    assert report.recommendations == ()
    assert all(
        not finding.fact_refs
        for finding in report.key_findings
    )


def test_unavailable_fields_are_copied_exactly() -> None:
    context = _mixed_context()
    report = ReportService().generate(context)

    assert {
        (item.field, item.reason_code) for item in report.limitations
    } == {
        (item.field, item.reason_code)
        for item in context.unavailable_fields
    }


def test_tracker_scope_language_is_explicit() -> None:
    report = TemplateFallback().generate(_mixed_context())
    tracker_finding = next(
        finding
        for finding in report.key_findings
        if finding.claim_id == "finding-060-track-scope-recurrence"
    )

    assert "tracker-scoped" in tracker_finding.statement
    assert "not stable person identity" in tracker_finding.statement
    assert all(
        item.track_scope == "tracker_scoped"
        for item in tracker_finding.track_refs
    )


def test_all_recommendation_rules_are_deterministic() -> None:
    report = TemplateFallback().generate(_all_type_context())

    assert [
        recommendation.recommendation_id
        for recommendation in report.recommendations
    ] == [
        "rec-010-no-helmet",
        "rec-020-no-vest",
        "rec-030-ppe-unknown",
    ]


def test_unique_dominant_type_creates_frequency_only_risk_claim() -> None:
    report = TemplateFallback().generate(_mixed_context())

    assert len(report.risk_observations) == 1
    risk = report.risk_observations[0]
    assert risk.numeric_claims[0].value == 2
    assert "does not establish severity" in risk.statement


def test_missing_or_malformed_metrics_fail_closed() -> None:
    context = _mixed_context()
    total_metric = next(
        metric
        for metric in context.calculated_metrics
        if metric.metric_id == "analytics.event_total_count"
    )
    missing = replace(
        context,
        calculated_metrics=tuple(
            metric
            for metric in context.calculated_metrics
            if metric.metric_id != "analytics.event_total_count"
        ),
    )
    malformed = replace(
        context,
        calculated_metrics=tuple(
            replace(metric, value="3")
            if metric.metric_id == "analytics.event_total_count"
            else metric
            for metric in context.calculated_metrics
        ),
    )

    with pytest.raises(TemplateFallbackError) as missing_error:
        TemplateFallback().generate(missing)
    with pytest.raises(TemplateFallbackError) as malformed_error:
        TemplateFallback().generate(malformed)
    with pytest.raises(ReportServiceError) as service_error:
        ReportService().generate(missing)

    assert missing_error.value.code == "FALLBACK_FAILED"
    assert malformed_error.value.code == "FALLBACK_FAILED"
    assert service_error.value.code == "FALLBACK_FAILED"
    assert total_metric.value == 3


class _RejectingValidator:
    def validate(
        self,
        report,
        context,
    ) -> ReportValidationResult:
        return ReportValidationResult(
            valid=False,
            errors=(
                SafetyReportGroundingValidator()
                .validate(report, context)
                .errors
                or (
                    ReportValidationIssue(
                        code="UNGROUNDED_FINDING",
                        path="test",
                        message="forced rejection",
                    ),
                )
            ),
        )


def test_report_service_fails_closed_when_validation_rejects() -> None:
    with pytest.raises(ReportServiceError) as error:
        ReportService(validator=_RejectingValidator()).generate(
            _mixed_context()
        )

    assert error.value.code == "GROUNDING_VALIDATION_FAILED"


def test_fallback_does_not_import_provider_or_network_modules() -> None:
    project_root = Path(__file__).resolve().parents[1]
    paths = (
        project_root / "infra" / "llm" / "fallback.py",
        project_root / "services" / "report_service.py",
    )
    forbidden = {
        "openai",
        "anthropic",
        "ollama",
        "langchain",
        "llama_index",
        "requests",
        "urllib",
        "httpx",
        "socket",
    }

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert not {
            item
            for item in imports
            if any(
                item == name or item.startswith(f"{name}.")
                for name in forbidden
            )
        }


def test_report_contains_no_absolute_paths_or_credentials() -> None:
    context = _mixed_context()
    report = ReportService().generate(context)
    canonical = report.to_canonical_json().lower()

    assert "c:\\" not in canonical
    assert "/var/" not in canonical
    assert ".sqlite" not in canonical
    assert "api_key" not in canonical
    assert "bearer " not in canonical
