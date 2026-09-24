from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus
from core.schemas.safety import (
    SafetyAnalysisContext,
    SafetyAnalyticsQuery,
    SafetyContextMetadata,
    SafetyEventFact,
    UnavailableField,
    source_reference,
)
from core.schemas.safety_report import (
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
from services.safety_report_grounding_validator import (
    SafetyReportGroundingValidator,
)

FIXED_CLOCK = lambda: datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)

UNAVAILABLE_FIELDS = (
    UnavailableField(
        field="metrics.alert_delivery",
        reason_code="NO_ALERT_TELEMETRY_TABLE",
        reason="No delivery telemetry.",
    ),
    UnavailableField(
        field="metrics.cross_session_identity",
        reason_code="NO_AUTHORITATIVE_IDENTITY_SOURCE",
        reason="No cross-session identity.",
    ),
    UnavailableField(
        field="metrics.per_event_source_attribution",
        reason_code="SOURCE_NOT_IN_EVENT_PROJECTION",
        reason="No per-event source projection.",
    ),
    UnavailableField(
        field="metrics.unique_person_count",
        reason_code="TRACK_ID_NOT_STABLE_IDENTITY",
        reason="Track IDs are tracker-scoped.",
    ),
    UnavailableField(
        field="metrics.violation_duration",
        reason_code="NO_PERSISTED_DURATION_FIELD",
        reason="No duration field.",
    ),
)


def _fact(
    event_id: str,
    *,
    occurred_at: str,
    track_id: int,
    event_type: ComplianceEventType,
    snapshot_ref: str | None = None,
    source_ref: str | None = None,
) -> SafetyEventFact:
    return SafetyEventFact(
        fact_id=f"EVT:{event_id}",
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        confidence=0.91,
        track_id=track_id,
        source_ref=source_ref,
        status=EventStatus.OPEN,
        snapshot_ref=snapshot_ref,
        evidence_available=snapshot_ref is not None,
    )


def _context(*, empty: bool = False) -> SafetyAnalysisContext:
    if empty:
        facts = ()
        total = 0
        first = None
        last = None
        track_counts = ()
        evidence_available = 0
        evidence_missing = 0
    else:
        source_a = source_reference("mp4:site-a.mp4")
        source_b = source_reference("mp4:site-b.mp4")
        facts = (
            _fact(
                "EVT-A",
                occurred_at="2026-09-23T12:00:00Z",
                track_id=7,
                event_type=ComplianceEventType.NO_HELMET,
                snapshot_ref="20260923/event_EVT-A.jpg",
                source_ref=source_a,
            ),
            _fact(
                "EVT-B",
                occurred_at="2026-09-23T13:00:00Z",
                track_id=8,
                event_type=ComplianceEventType.NO_VEST,
                source_ref=source_b,
            ),
        )
        total = 2
        first = "2026-09-23T12:00:00Z"
        last = "2026-09-23T13:00:00Z"
        track_counts = ((7, 1), (8, 1))
        evidence_available = 1
        evidence_missing = 1

    query = SafetyAnalyticsQuery(
        start_at="2026-09-23T00:00:00Z",
        end_at="2026-09-23T23:59:59Z",
    )
    metadata = SafetyContextMetadata(
        context_version="phase8-context-v1",
        analytics_version="phase8-analytics-v1",
        generated_at="2026-09-24T13:00:00Z",
        reporting_period=query.reporting_period,
        query_filters=(),
        event_schema_version="phase7-event-v1",
        source_of_truth="test double",
        detail_selection_policy="all_matching_events_no_silent_truncation",
        provider_data_policy="structured_event_metadata_only",
    )

    from core.schemas.safety import MetricValue

    metrics = [
        MetricValue(
            metric_id="analytics.event_total_count",
            name="Total event count",
            value=total,
            unit="events",
            definition="Count of persisted events.",
            sample_size=total,
        ),
        MetricValue(
            metric_id="analytics.evidence.available_count",
            name="Evidence available count",
            value=evidence_available,
            unit="events",
            definition="Events with evidence.",
            sample_size=total,
        ),
        MetricValue(
            metric_id="analytics.evidence.missing_count",
            name="Evidence missing count",
            value=evidence_missing,
            unit="events",
            definition="Events without evidence.",
            sample_size=total,
        ),
        MetricValue(
            metric_id="analytics.first_occurrence",
            name="First occurrence",
            value=first,
            unit="utc_timestamp",
            definition="Earliest event.",
            sample_size=total,
        ),
        MetricValue(
            metric_id="analytics.last_occurrence",
            name="Last occurrence",
            value=last,
            unit="utc_timestamp",
            definition="Latest event.",
            sample_size=total,
        ),
    ]
    for event_type in ComplianceEventType:
        metrics.append(
            MetricValue(
                metric_id=f"analytics.event_count.by_type.{event_type.value}",
                name=f"Count for {event_type.value}",
                value=sum(
                    1 for fact in facts if fact.event_type is event_type
                ),
                unit="events",
                definition="Count grouped by event type.",
                sample_size=total,
            )
        )
    for track_id, count in track_counts:
        metrics.append(
            MetricValue(
                metric_id=f"analytics.event_count.by_track.{track_id}",
                name=f"Count for track {track_id}",
                value=count,
                unit="events",
                definition="Count grouped by tracker-scoped ID.",
                sample_size=total,
            )
        )
    for source_ref in sorted(
        {
            fact.source_ref
            for fact in facts
            if fact.source_ref is not None
        }
    ):
        metrics.append(
            MetricValue(
                metric_id=(
                    "analytics.event_count.by_source_ref."
                    f"{source_ref}"
                ),
                name=f"Count for source {source_ref}",
                value=sum(
                    1 for fact in facts if fact.source_ref == source_ref
                ),
                unit="events",
                definition="Count grouped by opaque source reference.",
                sample_size=total,
            )
        )
    return SafetyAnalysisContext(
        metadata=metadata,
        observed_facts=facts,
        calculated_metrics=tuple(metrics),
        unavailable_fields=UNAVAILABLE_FIELDS,
    )


def _limitations() -> tuple[ReportLimitation, ...]:
    return tuple(
        ReportLimitation(
            field=field.field,
            reason_code=field.reason_code,
            statement=field.reason,
        )
        for field in UNAVAILABLE_FIELDS
    )


def _claim(
    claim_id: str,
    *,
    kind: str = "observation",
    **kwargs,
) -> SafetyReportClaim:
    return SafetyReportClaim(
        claim_id=claim_id,
        kind=kind,
        statement=kwargs.pop("statement", "Deterministic report claim."),
        **kwargs,
    )


def _report(
    context: SafetyAnalysisContext,
    *overrides,
    **kwargs,
) -> StructuredSafetyReport:
    source_a = next(
        (
            fact.source_ref
            for fact in context.observed_facts
            if fact.source_ref is not None
        ),
        None,
    )
    default_claim = _claim(
        "finding-total",
        fact_refs=(
            ("EVT:EVT-A", "EVT:EVT-B")
            if context.observed_facts
            else ()
        ),
        metric_refs=("analytics.event_total_count",),
        event_refs=(
            ("EVT-A", "EVT-B") if context.observed_facts else ()
        ),
        track_refs=(
            (TrackReference(7), TrackReference(8))
            if len(context.observed_facts) > 1
            else ()
        ),
        source_refs=(source_a,) if source_a else (),
        evidence_refs=("EVID:EVT-A",) if len(context.observed_facts) > 1 else (),
        numeric_claims=(
            MetricNumericClaim(
                metric_ref="analytics.event_total_count",
                value=len(context.observed_facts),
            ),
        ),
    )
    evidence = (
        (
            ReportEvidenceReference(
                evidence_ref="EVID:EVT-A",
                event_id="EVT-A",
                track_id=7,
                snapshot_ref="20260923/event_EVT-A.jpg",
                occurred_at="2026-09-23T12:00:00Z",
            ),
        )
        if len(context.observed_facts) > 1
        else ()
    )
    report = StructuredSafetyReport(
        source_context_sha256=SafetyContextBuilder.fingerprint(context),
        reporting_period=context.metadata.reporting_period,
        generation=ReportGeneration(mode=GenerationMode.LLM),
        executive_summary=(),
        key_findings=(default_claim,),
        risk_observations=(),
        recommendations=(
            ReportRecommendation(
                recommendation_id="rec-1",
                action="Review the deterministic finding.",
                priority="medium",
                basis_finding_refs=("finding-total",),
            ),
        ),
        evidence_references=evidence,
        limitations=_limitations(),
        grounding_status=GroundingStatus.UNVALIDATED,
    )
    for override in overrides:
        report = replace(report, **override)
    if kwargs:
        report = replace(report, **kwargs)
    return report


def _codes(result) -> list[str]:
    return [issue.code for issue in result.errors]


def test_valid_fully_grounded_report_matches_context_fingerprint() -> None:
    context = _context()
    report = _report(context)

    result = SafetyReportGroundingValidator().validate(report, context)

    assert result.valid
    assert result.errors == ()
    assert report.source_context_sha256 == SafetyContextBuilder.fingerprint(
        context
    )


def test_context_fingerprint_mismatch_is_rejected() -> None:
    context = _context()
    report = _report(context)
    mismatched = replace(report, source_context_sha256="0" * 64)

    result = SafetyReportGroundingValidator().validate(mismatched, context)

    assert not result.valid
    assert "CONTEXT_FINGERPRINT_MISMATCH" in _codes(result)


def test_invalid_report_schema_is_rejected_without_exception() -> None:
    result = SafetyReportGroundingValidator().validate(
        object(),
        _context(),
    )

    assert _codes(result) == ["REPORT_SCHEMA_INVALID"]


def test_unknown_fact_metric_event_track_evidence_and_source_refs_are_rejected() -> None:
    context = _context()
    report = _report(context)
    base = report.key_findings[0]
    invalid = _claim(
        "bad-refs",
        fact_refs=("EVT:UNKNOWN",),
        metric_refs=("analytics.unknown_metric",),
        event_refs=("EVT-UNKNOWN",),
        track_refs=(TrackReference(999),),
        source_refs=("SRC-0000000000000000",),
        evidence_refs=("EVID:EVT-UNKNOWN",),
        numeric_claims=(
            MetricNumericClaim(
                metric_ref="metrics.violation_duration",
                value=15,
            ),
        ),
    )
    invalid_report = replace(report, key_findings=(invalid,))

    result = SafetyReportGroundingValidator().validate(invalid_report, context)

    assert {
        "UNKNOWN_FACT_REFERENCE",
        "UNKNOWN_METRIC_REFERENCE",
        "UNKNOWN_EVENT_REFERENCE",
        "UNKNOWN_TRACK_REFERENCE",
        "UNKNOWN_EVIDENCE_REFERENCE",
        "UNAVAILABLE_FIELD_CLAIM",
    }.issubset(_codes(result))
    assert base.claim_id != invalid.claim_id


def test_numeric_claim_matches_metric_exactly_and_mismatch_is_rejected() -> None:
    context = _context()
    report = _report(context)
    valid = SafetyReportGroundingValidator().validate(report, context)
    bad_claim = _claim(
        "bad-number",
        fact_refs=("EVT:EVT-A",),
        metric_refs=("analytics.event_total_count",),
        numeric_claims=(
            MetricNumericClaim(
                metric_ref="analytics.event_total_count",
                value=99,
            ),
        ),
    )
    invalid = replace(report, key_findings=(bad_claim,))

    mismatch = SafetyReportGroundingValidator().validate(invalid, context)

    assert valid.valid
    assert "NUMERIC_VALUE_MISMATCH" in _codes(mismatch)


def test_ungrounded_finding_and_risk_observation_are_rejected() -> None:
    context = _context()
    report = _report(context)
    ungrounded = replace(
        report,
        key_findings=(_claim("ungrounded-finding"),),
        risk_observations=(_claim("ungrounded-risk", kind="risk"),),
    )

    result = SafetyReportGroundingValidator().validate(ungrounded, context)

    assert "UNGROUNDED_FINDING" in _codes(result)
    assert "UNGROUNDED_RISK_OBSERVATION" in _codes(result)


def test_recommendation_basis_is_validated() -> None:
    context = _context()
    report = _report(context)
    invalid = replace(
        report,
        recommendations=(
            ReportRecommendation(
                recommendation_id="rec-bad",
                action="Review an unknown basis.",
                priority="high",
                basis_finding_refs=("missing-finding",),
                basis_fact_refs=("EVT:missing",),
                basis_metric_refs=("analytics.missing",),
            ),
        ),
    )

    result = SafetyReportGroundingValidator().validate(invalid, context)

    assert "INVALID_RECOMMENDATION_BASIS" in _codes(result)
    assert len(
        [
            issue
            for issue in result.errors
            if issue.code == "INVALID_RECOMMENDATION_BASIS"
        ]
    ) == 3


def test_unavailable_context_limitations_are_required_and_exact() -> None:
    context = _context()
    report = _report(context)
    missing = replace(report, limitations=report.limitations[:-1])
    mismatch = replace(
        report,
        limitations=(
            replace(
                report.limitations[0],
                reason_code="WRONG_REASON",
            ),
            *report.limitations[1:],
        ),
    )

    missing_result = SafetyReportGroundingValidator().validate(
        missing,
        context,
    )
    mismatch_result = SafetyReportGroundingValidator().validate(
        mismatch,
        context,
    )

    assert "UNAVAILABLE_FIELD_CLAIM" in _codes(missing_result)
    assert "UNAVAILABLE_FIELD_CLAIM" in _codes(mismatch_result)


def test_empty_context_allows_valid_zero_event_report() -> None:
    context = _context(empty=True)
    report = _report(context)

    result = SafetyReportGroundingValidator().validate(report, context)

    assert result.valid
    assert report.key_findings[0].numeric_claims[0].value == 0


def test_empty_context_rejects_fabricated_event_reference() -> None:
    context = _context(empty=True)
    report = _report(context)
    fabricated = replace(
        report,
        key_findings=(
            _claim(
                "fabricated-empty",
                fact_refs=("EVT:EVT-FABRICATED",),
                metric_refs=("analytics.event_total_count",),
            ),
        ),
    )

    result = SafetyReportGroundingValidator().validate(fabricated, context)

    assert "UNKNOWN_FACT_REFERENCE" in _codes(result)


def test_validation_error_order_is_stable() -> None:
    context = _context()
    invalid = replace(
        _report(context, source_context_sha256="0" * 64),
        key_findings=(
            _claim(
                "multi-error",
                fact_refs=("EVT:UNKNOWN",),
                metric_refs=("analytics.unknown_metric",),
                event_refs=("EVT-UNKNOWN",),
                track_refs=(TrackReference(404),),
            ),
        ),
    )

    first = SafetyReportGroundingValidator().validate(invalid, context)
    second = SafetyReportGroundingValidator().validate(invalid, context)

    assert first.to_canonical_json() == second.to_canonical_json()
    assert _codes(first) == sorted(
        _codes(first),
        key=lambda code: {
            "REPORT_SCHEMA_INVALID": 0,
            "CONTEXT_FINGERPRINT_MISMATCH": 1,
            "UNKNOWN_FACT_REFERENCE": 2,
            "UNKNOWN_METRIC_REFERENCE": 3,
            "UNKNOWN_EVENT_REFERENCE": 4,
            "UNKNOWN_TRACK_REFERENCE": 5,
            "UNKNOWN_EVIDENCE_REFERENCE": 6,
            "NUMERIC_VALUE_MISMATCH": 7,
            "UNGROUNDED_FINDING": 8,
            "UNGROUNDED_RISK_OBSERVATION": 9,
            "INVALID_RECOMMENDATION_BASIS": 10,
            "UNAVAILABLE_FIELD_CLAIM": 11,
            "PATH_LEAK_DETECTED": 12,
        }[code],
    )


def test_canonical_serialization_is_reproducible_across_equivalent_order() -> None:
    context = _context()
    report = _report(context)
    first_claim = _claim(
        "finding-a",
        fact_refs=("EVT:EVT-A",),
        metric_refs=("analytics.event_total_count",),
    )
    second_claim = _claim(
        "finding-b",
        fact_refs=("EVT:EVT-B",),
        metric_refs=("analytics.event_total_count",),
    )
    one = replace(report, key_findings=(first_claim, second_claim))
    two = replace(report, key_findings=(second_claim, first_claim))

    assert one.to_canonical_json() == two.to_canonical_json()


def test_absolute_windows_path_leak_is_rejected() -> None:
    context = _context()
    report = _report(context)
    leaked = replace(
        report,
        key_findings=(
            _claim(
                "windows-path",
                fact_refs=("EVT:EVT-A",),
                metric_refs=("analytics.event_total_count",),
                statement=r"Evidence was read from C:\private\event.jpg",
            ),
        ),
    )

    result = SafetyReportGroundingValidator().validate(leaked, context)

    assert "PATH_LEAK_DETECTED" in _codes(result)


def test_absolute_posix_path_leak_is_rejected() -> None:
    context = _context()
    report = _report(context)
    leaked = replace(
        report,
        key_findings=(
            _claim(
                "posix-path",
                fact_refs=("EVT:EVT-A",),
                metric_refs=("analytics.event_total_count",),
                statement="Database was read from /var/lib/odplatform/events.sqlite3",
            ),
        ),
    )

    result = SafetyReportGroundingValidator().validate(leaked, context)

    assert "PATH_LEAK_DETECTED" in _codes(result)


def test_source_metric_can_ground_an_opaque_source_reference() -> None:
    context = _context()
    source_ref = context.observed_facts[0].source_ref
    assert source_ref is not None
    report = _report(context)
    grounded = replace(
        report,
        recommendations=(),
        key_findings=(
            _claim(
                "source-metric",
                metric_refs=(
                    f"analytics.event_count.by_source_ref.{source_ref}",
                ),
                source_refs=(source_ref,),
                numeric_claims=(
                    MetricNumericClaim(
                        metric_ref=(
                            "analytics.event_count.by_source_ref."
                            f"{source_ref}"
                        ),
                        value=1,
                    ),
                ),
            ),
        ),
    )

    result = SafetyReportGroundingValidator().validate(grounded, context)

    assert result.valid


def test_credential_like_assignment_is_rejected() -> None:
    context = _context()
    report = _report(context)
    leaked = replace(
        report,
        key_findings=(
            _claim(
                "credential",
                fact_refs=("EVT:EVT-A",),
                metric_refs=("analytics.event_total_count",),
                statement="api_key=not-a-real-secret",
            ),
        ),
    )

    result = SafetyReportGroundingValidator().validate(leaked, context)

    assert "PATH_LEAK_DETECTED" in _codes(result)


def test_report_contract_and_validator_have_no_provider_or_network_dependency() -> None:
    root = Path(__file__).resolve().parents[1]
    paths = (
        root / "core" / "schemas" / "safety_report.py",
        root / "services" / "safety_report_grounding_validator.py",
    )
    forbidden = {
        "infra.llm",
        "openai",
        "deepseek",
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
            if any(item == name or item.startswith(f"{name}.") for name in forbidden)
        }


def test_track_reference_cannot_claim_stable_identity() -> None:
    import pytest

    with pytest.raises(ValueError, match="track_scope"):
        TrackReference(track_id=7, track_scope="employee")
