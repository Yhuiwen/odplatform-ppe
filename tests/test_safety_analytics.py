from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import (
    EventPage,
    EventStatus,
    SnapshotReference,
    StoredEvent,
)
from core.schemas.safety import (
    CONTEXT_SCHEMA_VERSION,
    MetricValue,
    SafetyAnalysisContext,
    SafetyAnalyticsQuery,
    SafetyContextMetadata,
    SafetyEventFact,
    UnavailableField,
)
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from services.event_query_service import EventQueryService
from services.safety_analytics_service import (
    SafetyAnalyticsError,
    SafetyAnalyticsService,
)
from services.safety_context_builder import SafetyContextBuilder

FIXED_CLOCK = lambda: datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)


def _stored_event(
    event_id: str,
    *,
    occurred_at: str,
    event_type: ComplianceEventType = ComplianceEventType.NO_HELMET,
    track_id: int = 7,
    status: EventStatus = EventStatus.OPEN,
    source: str = "mp4:site-a.mp4",
) -> StoredEvent:
    return StoredEvent(
        id=event_id,
        timestamp=occurred_at,
        track_id=track_id,
        type=event_type,
        confidence=0.91,
        source_timestamp=12.5,
        source=source,
        status=status,
    )


def _analytics_service(
    tmp_path,
    events: tuple[StoredEvent, ...],
    *,
    snapshot_event_ids: tuple[str, ...] = (),
) -> SafetyAnalyticsService:
    database = Database(tmp_path / "events.sqlite3")
    repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    for event in events:
        repository.insert(event)
    for event_id in snapshot_event_ids:
        snapshot_repository.insert(
            SnapshotReference(
                snapshot_id=f"SNAP-{event_id}",
                event_id=event_id,
                relative_path=f"20260923/event_{event_id}.jpg",
                sha256="a" * 64,
                width=640,
                height=480,
                mime_type="image/jpeg",
                captured_at="2026-09-23T12:00:01Z",
            )
        )
    return SafetyAnalyticsService(EventQueryService(repository))


def _query(
    *,
    start_at: str = "2026-09-23T00:00:00Z",
    end_at: str = "2026-09-24T23:59:59Z",
    **kwargs,
) -> SafetyAnalyticsQuery:
    return SafetyAnalyticsQuery(start_at=start_at, end_at=end_at, **kwargs)


def _metrics_by_id(context: SafetyAnalysisContext) -> dict[str, MetricValue]:
    return {metric.metric_id: metric for metric in context.calculated_metrics}


def test_exact_count_type_status_track_day_evidence_and_occurrences(tmp_path) -> None:
    events = (
        _stored_event(
            "EVT-A",
            occurred_at="2026-09-23T12:00:00Z",
            event_type=ComplianceEventType.NO_HELMET,
            track_id=7,
            source="mp4:site-a.mp4",
        ),
        _stored_event(
            "EVT-B",
            occurred_at="2026-09-23T23:59:59Z",
            event_type=ComplianceEventType.NO_VEST,
            track_id=8,
            status=EventStatus.RESOLVED,
            source="mp4:site-b.mp4",
        ),
        _stored_event(
            "EVT-C",
            occurred_at="2026-09-24T12:00:00Z",
            event_type=ComplianceEventType.PPE_UNKNOWN,
            track_id=7,
            source="mp4:site-a.mp4",
        ),
        _stored_event(
            "EVT-OUTSIDE",
            occurred_at="2026-09-24T12:00:01Z",
            event_type=ComplianceEventType.NO_HELMET,
            track_id=9,
        ),
    )
    analytics = _analytics_service(
        tmp_path,
        events,
        snapshot_event_ids=("EVT-B",),
    ).analyze(
        _query(
            start_at="2026-09-23T12:00:00Z",
            end_at="2026-09-24T12:00:00Z",
        )
    )

    assert analytics.total_count == 3
    assert dict(analytics.counts_by_type) == {
        ComplianceEventType.NO_HELMET: 1,
        ComplianceEventType.NO_VEST: 1,
        ComplianceEventType.PPE_UNKNOWN: 1,
    }
    assert dict(analytics.counts_by_status) == {
        EventStatus.OPEN: 2,
        EventStatus.ACKNOWLEDGED: 0,
        EventStatus.RESOLVED: 1,
        EventStatus.DISMISSED: 0,
    }
    assert dict(analytics.counts_by_track) == {7: 2, 8: 1}
    assert dict(analytics.counts_by_day) == {
        "2026-09-23": 2,
        "2026-09-24": 1,
    }
    assert analytics.first_occurrence == "2026-09-23T12:00:00Z"
    assert analytics.last_occurrence == "2026-09-24T12:00:00Z"
    assert analytics.evidence_available_count == 1
    assert analytics.evidence_missing_count == 2
    assert [fact.event_id for fact in analytics.facts] == [
        "EVT-C",
        "EVT-B",
        "EVT-A",
    ]


def test_reporting_interval_is_inclusive_at_both_boundaries(tmp_path) -> None:
    service = _analytics_service(
        tmp_path,
        (
            _stored_event("EVT-BEFORE", occurred_at="2026-09-23T11:59:59Z"),
            _stored_event("EVT-START", occurred_at="2026-09-23T12:00:00Z"),
            _stored_event("EVT-END", occurred_at="2026-09-23T13:00:00Z"),
            _stored_event("EVT-AFTER", occurred_at="2026-09-23T13:00:01Z"),
        ),
    )

    result = service.analyze(
        _query(
            start_at="2026-09-23T12:00:00Z",
            end_at="2026-09-23T13:00:00Z",
        )
    )

    assert [fact.event_id for fact in result.facts] == [
        "EVT-END",
        "EVT-START",
    ]


def test_empty_interval_is_successful_and_explicit(tmp_path) -> None:
    service = _analytics_service(
        tmp_path,
        (_stored_event("EVT-A", occurred_at="2026-09-23T12:00:00Z"),),
    )
    result = service.analyze(
        _query(
            start_at="2026-10-01T00:00:00Z",
            end_at="2026-10-02T00:00:00Z",
        )
    )
    context = SafetyContextBuilder(clock=FIXED_CLOCK).build(result)
    metrics = _metrics_by_id(context)

    assert result.total_count == 0
    assert result.facts == ()
    assert result.first_occurrence is None
    assert result.last_occurrence is None
    assert dict(result.counts_by_type) == {
        ComplianceEventType.NO_HELMET: 0,
        ComplianceEventType.NO_VEST: 0,
        ComplianceEventType.PPE_UNKNOWN: 0,
    }
    assert metrics["analytics.event_total_count"].value == 0
    assert metrics["analytics.first_occurrence"].value is None
    assert metrics["analytics.last_occurrence"].value is None
    assert context.observed_facts == ()
    assert {item.field for item in context.unavailable_fields} == {
        "metrics.alert_delivery",
        "metrics.cross_session_identity",
        "metrics.per_event_source_attribution",
        "metrics.unique_person_count",
        "metrics.violation_duration",
    }


def test_source_counts_use_opaque_references_without_leaking_raw_paths(
    tmp_path,
) -> None:
    service = _analytics_service(
        tmp_path,
        (
            _stored_event(
                "EVT-A",
                occurred_at="2026-09-23T12:00:00Z",
                source=r"C:\private\camera-a.mp4",
            ),
            _stored_event(
                "EVT-B",
                occurred_at="2026-09-23T13:00:00Z",
                source=r"C:\private\camera-b.mp4",
            ),
            _stored_event(
                "EVT-C",
                occurred_at="2026-09-23T14:00:00Z",
                source=r"C:\private\camera-a.mp4",
            ),
        ),
    )

    result = service.analyze(_query())
    context = SafetyContextBuilder(clock=FIXED_CLOCK).build(result)
    source_metrics = [
        metric
        for metric in context.calculated_metrics
        if metric.metric_id.startswith("analytics.event_count.by_source_ref.")
    ]
    canonical = context.to_canonical_json()

    assert len(result.counts_by_source_ref) == 2
    assert sorted(count for _, count in result.counts_by_source_ref) == [1, 2]
    assert len(source_metrics) == 2
    assert all(
        metric.metric_id.split(".")[-1].startswith("SRC-")
        for metric in source_metrics
    )
    assert "C:\\private" not in canonical
    assert "camera-a.mp4" not in canonical
    assert "camera-b.mp4" not in canonical


def test_query_validation_rejects_invalid_intervals_and_timestamps() -> None:
    with pytest.raises(ValueError, match="start_at cannot be after end_at"):
        SafetyAnalyticsQuery(
            start_at="2026-09-24T00:00:00Z",
            end_at="2026-09-23T00:00:00Z",
        )

    with pytest.raises(ValueError, match="valid ISO 8601"):
        SafetyAnalyticsQuery(
            start_at="not-a-timestamp",
            end_at="2026-09-23T00:00:00Z",
        )


def test_event_fact_requires_track_id() -> None:
    with pytest.raises(TypeError):
        SafetyEventFact(
            fact_id="EVT:EVT-A",
            event_id="EVT-A",
            occurred_at="2026-09-23T12:00:00Z",
            event_type=ComplianceEventType.NO_HELMET,
            confidence=0.9,
            source_ref=None,
            status=EventStatus.OPEN,
            snapshot_ref=None,
            evidence_available=False,
        )


def test_fact_order_uses_timestamp_descending_then_event_id_ascending(
    tmp_path,
) -> None:
    service = _analytics_service(
        tmp_path,
        (
            _stored_event("EVT-C", occurred_at="2026-09-23T12:00:00Z"),
            _stored_event("EVT-A", occurred_at="2026-09-23T12:00:00Z"),
            _stored_event("EVT-B", occurred_at="2026-09-23T12:00:00Z"),
        ),
    )

    result = service.analyze(_query())

    assert [fact.event_id for fact in result.facts] == [
        "EVT-A",
        "EVT-B",
        "EVT-C",
    ]


class _ReversingEventQueryService(EventQueryService):
    def query_events(self, query):
        page = super().query_events(query)
        return EventPage(
            items=tuple(reversed(page.items)),
            total_count=page.total_count,
            generated_at=page.generated_at,
            limit=page.limit,
            offset=page.offset,
        )


def test_query_row_order_does_not_change_analytics_or_context(tmp_path) -> None:
    events = (
        _stored_event("EVT-A", occurred_at="2026-09-23T12:00:00Z", track_id=8),
        _stored_event("EVT-B", occurred_at="2026-09-23T13:00:00Z", track_id=7),
        _stored_event("EVT-C", occurred_at="2026-09-23T14:00:00Z", track_id=9),
    )
    service = _analytics_service(tmp_path, events)
    query = _query()

    normal_result = service.analyze(query)
    reversed_service = _ReversingEventQueryService(
        service.event_query_service.event_repository
    )
    reversed_result = SafetyAnalyticsService(reversed_service).analyze(query)

    builder = SafetyContextBuilder(clock=FIXED_CLOCK)
    normal_context = builder.build(normal_result)
    reversed_context = builder.build(reversed_result)

    assert normal_result == reversed_result
    assert normal_context.to_canonical_json() == reversed_context.to_canonical_json()
    assert builder.fingerprint(normal_context) == builder.fingerprint(
        reversed_context
    )


class _DuplicateEventQueryService(EventQueryService):
    def query_events(self, query):
        page = super().query_events(query)
        return EventPage(
            items=page.items + page.items,
            total_count=page.total_count * 2,
            generated_at=page.generated_at,
            limit=page.limit,
            offset=page.offset,
        )


def test_duplicate_event_identity_is_rejected(tmp_path) -> None:
    service = _analytics_service(
        tmp_path,
        (_stored_event("EVT-A", occurred_at="2026-09-23T12:00:00Z"),),
    )
    duplicate_service = _DuplicateEventQueryService(
        service.event_query_service.event_repository
    )

    with pytest.raises(SafetyAnalyticsError) as error:
        SafetyAnalyticsService(duplicate_service).analyze(_query())

    assert error.value.code == "DUPLICATE_EVENT_ID"


class _UnsupportedEventQueryService(EventQueryService):
    def query_events(self, query):
        return EventPage(
            items=(object(),),
            total_count=1,
            generated_at="2026-09-23T00:00:00Z",
            limit=1000,
            offset=0,
        )


def test_unsupported_or_missing_event_fields_are_rejected(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")
    repository = EventRepository(database)
    service = _UnsupportedEventQueryService(repository)

    with pytest.raises(SafetyAnalyticsError) as error:
        SafetyAnalyticsService(service).analyze(_query())

    assert error.value.code == "UNSUPPORTED_EVENT_RECORD"


def test_context_has_frozen_sections_and_no_provider_inputs(tmp_path) -> None:
    service = _analytics_service(
        tmp_path,
        (
            _stored_event(
                "EVT-A",
                occurred_at="2026-09-23T12:00:00Z",
                source=r"C:\private\camera-a.mp4",
            ),
        ),
    )
    context = SafetyContextBuilder(clock=FIXED_CLOCK).build(
        service.analyze(_query())
    )
    payload = context.to_dict()

    assert set(payload) == {
        "observed_facts",
        "calculated_metrics",
        "metadata",
        "unavailable_fields",
    }
    assert payload["metadata"]["schema_version"] == CONTEXT_SCHEMA_VERSION
    assert payload["observed_facts"][0]["source_ref"] is None
    canonical = context.to_canonical_json()
    assert "C:\\private" not in canonical
    assert "camera-a.mp4" not in canonical
    assert "image_bytes" not in canonical
    assert "stack_trace" not in canonical


def test_identical_input_produces_identical_context_and_fingerprint(tmp_path) -> None:
    service = _analytics_service(
        tmp_path,
        (
            _stored_event("EVT-A", occurred_at="2026-09-23T12:00:00Z"),
            _stored_event(
                "EVT-B",
                occurred_at="2026-09-23T13:00:00Z",
                event_type=ComplianceEventType.NO_VEST,
            ),
        ),
    )
    query = _query()
    builder = SafetyContextBuilder(clock=FIXED_CLOCK)

    first = builder.build(service.analyze(query))
    second = builder.build(service.analyze(query))

    assert first.to_canonical_json() == second.to_canonical_json()
    assert builder.fingerprint(first) == builder.fingerprint(second)


def test_fingerprint_is_stable_across_generated_at_and_changes_with_facts(
    tmp_path,
) -> None:
    service = _analytics_service(
        tmp_path,
        (_stored_event("EVT-A", occurred_at="2026-09-23T12:00:00Z"),),
    )
    query = _query()
    first = SafetyContextBuilder(
        clock=lambda: datetime(2026, 9, 24, 13, 0, tzinfo=timezone.utc)
    ).build(service.analyze(query))
    second = SafetyContextBuilder(
        clock=lambda: datetime(2026, 9, 24, 14, 0, tzinfo=timezone.utc)
    ).build(service.analyze(query))

    assert SafetyContextBuilder.fingerprint(first) == SafetyContextBuilder.fingerprint(
        second
    )

    changed = SafetyContextBuilder(clock=FIXED_CLOCK).build(
        _analytics_service(
            tmp_path / "changed",
            (
                _stored_event("EVT-A", occurred_at="2026-09-23T12:00:00Z"),
                _stored_event("EVT-B", occurred_at="2026-09-23T13:00:00Z"),
            ),
        ).analyze(query)
    )
    assert SafetyContextBuilder.fingerprint(first) != SafetyContextBuilder.fingerprint(
        changed
    )


def test_context_schema_rejects_duplicate_metrics() -> None:
    metric = MetricValue(
        metric_id="analytics.event_total_count",
        name="Total",
        value=0,
        unit="events",
        definition="Count of events.",
        sample_size=0,
    )
    metadata = SafetyContextMetadata(
        context_version=CONTEXT_SCHEMA_VERSION,
        analytics_version="phase8-analytics-v1",
        generated_at="2026-09-24T13:00:00Z",
        reporting_period=SafetyAnalyticsQuery(
            start_at="2026-09-23T00:00:00Z",
            end_at="2026-09-24T00:00:00Z",
        ).reporting_period,
        query_filters=(),
        event_schema_version="phase7-event-v1",
        source_of_truth="test",
        detail_selection_policy="all_matching_events_no_silent_truncation",
        provider_data_policy="structured_event_metadata_only",
    )

    with pytest.raises(ValueError, match="duplicate metric_id"):
        SafetyAnalysisContext(
            metadata=metadata,
            observed_facts=(),
            calculated_metrics=(metric, metric),
            unavailable_fields=(),
        )


def test_context_json_round_trip_is_machine_readable(tmp_path) -> None:
    service = _analytics_service(
        tmp_path,
        (_stored_event("EVT-A", occurred_at="2026-09-23T12:00:00Z"),),
    )
    context = SafetyContextBuilder(clock=FIXED_CLOCK).build(
        service.analyze(_query())
    )

    payload = json.loads(context.to_canonical_json())

    assert payload["observed_facts"][0]["event_id"] == "EVT-A"
    assert payload["observed_facts"][0]["track_scope"] == "tracker_scoped"
    assert payload["metadata"]["analytics_version"] == "phase8-analytics-v1"


def test_deterministic_modules_do_not_import_provider_or_llm_boundaries() -> None:
    project_root = Path(__file__).resolve().parents[1]
    paths = (
        project_root / "core" / "schemas" / "safety.py",
        project_root / "services" / "safety_analytics_service.py",
        project_root / "services" / "safety_context_builder.py",
    )
    forbidden = {
        "infra.llm",
        "langchain",
        "llama_index",
        "openai",
        "ollama",
        "requests",
        "urllib",
        "httpx",
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


def test_event_fact_rejects_non_tracker_scoped_identity_aliases() -> None:
    with pytest.raises(TypeError):
        SafetyEventFact(
            fact_id="EVT:EVT-A",
            event_id="EVT-A",
            occurred_at="2026-09-23T12:00:00Z",
            event_type=ComplianceEventType.NO_HELMET,
            confidence=0.9,
            track_id=7,
            source_ref=None,
            status=EventStatus.OPEN,
            snapshot_ref=None,
            evidence_available=False,
            employee_id="not-allowed",
        )


def test_unavailable_field_serializes_reason() -> None:
    field = UnavailableField(
        field="metrics.violation_duration",
        reason_code="NO_PERSISTED_DURATION_FIELD",
        reason="No duration field.",
    )

    assert field.to_dict()["reason_code"] == "NO_PERSISTED_DURATION_FIELD"
