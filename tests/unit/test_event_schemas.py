from datetime import datetime, timezone

import pytest

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import (
    EventPage,
    EventQuery,
    EventStatus,
    PersistedEvent,
    StoredEvent,
    format_utc_timestamp,
)


def test_persisted_event_serializes_frozen_projection() -> None:
    event = PersistedEvent(
        id="EVT-01",
        timestamp="2026-09-23T12:34:56Z",
        track_id=7,
        type=ComplianceEventType.NO_HELMET,
        confidence=0.91,
        snapshot="20260923/event_EVT-01.jpg",
        status=EventStatus.OPEN,
    )

    assert event.to_dict() == {
        "id": "EVT-01",
        "timestamp": "2026-09-23T12:34:56Z",
        "track_id": 7,
        "type": "NO_HELMET",
        "confidence": 0.91,
        "snapshot": "20260923/event_EVT-01.jpg",
        "status": "open",
    }


def test_persisted_event_rejects_absolute_snapshot_path() -> None:
    with pytest.raises(ValueError, match="relative POSIX path"):
        PersistedEvent(
            id="EVT-01",
            timestamp="2026-09-23T12:34:56Z",
            track_id=7,
            type=ComplianceEventType.NO_HELMET,
            confidence=0.91,
            snapshot="C:/evidence/event.jpg",
            status=EventStatus.OPEN,
        )


def test_stored_event_keeps_source_time_separate_from_wall_clock() -> None:
    record = StoredEvent(
        id="EVT-01",
        timestamp="2026-09-23T12:34:56Z",
        track_id=7,
        type=ComplianceEventType.NO_VEST,
        confidence=0.8,
        source_timestamp=12.5,
        source="mp4:sample.mp4",
        frame_id=300,
        bbox={"x1": 1, "y1": 2, "x2": 3, "y2": 4},
    )

    assert record.timestamp == "2026-09-23T12:34:56Z"
    assert record.source_timestamp == 12.5
    assert record.bbox_json == '{"x1":1,"x2":3,"y1":2,"y2":4}'


def test_event_query_is_validated() -> None:
    query = EventQuery(
        start_at="2026-09-23T00:00:00Z",
        event_type="NO_HELMET",
        status="open",
        limit=25,
    )

    assert query.event_type is ComplianceEventType.NO_HELMET
    assert query.status is EventStatus.OPEN
    with pytest.raises(ValueError, match="start_at cannot be after end_at"):
        EventQuery(
            start_at="2026-09-24T00:00:00Z",
            end_at="2026-09-23T00:00:00Z",
        )


def test_utc_timestamp_formatting_is_canonical() -> None:
    assert format_utc_timestamp(
        datetime(2026, 9, 23, 12, 34, 56, tzinfo=timezone.utc)
    ) == "2026-09-23T12:34:56Z"


def test_event_page_serializes_items() -> None:
    event = PersistedEvent(
        id="EVT-01",
        timestamp="2026-09-23T12:34:56Z",
        track_id=7,
        type=ComplianceEventType.PPE_UNKNOWN,
        confidence=0.5,
        snapshot=None,
        status=EventStatus.ACKNOWLEDGED,
    )
    page = EventPage(
        items=(event,),
        total_count=1,
        generated_at="2026-09-23T12:35:00Z",
        limit=10,
        offset=0,
    )

    assert page.to_dict()["items"][0]["status"] == "acknowledged"
