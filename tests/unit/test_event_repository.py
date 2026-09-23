import pytest

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventQuery, EventStatus, StoredEvent
from infra.database.database import Database
from infra.database.errors import DatabaseWriteError
from infra.database.repository import (
    DuplicateEventError,
    EventConflictError,
    ViolationRepository,
)


def _record(
    event_id: str = "EVT-01",
    *,
    confidence: float = 0.91,
    track_id: int = 7,
    occurred_at: str = "2026-09-23T12:34:56Z",
) -> StoredEvent:
    return StoredEvent(
        id=event_id,
        timestamp=occurred_at,
        track_id=track_id,
        type=ComplianceEventType.NO_HELMET,
        confidence=confidence,
        source_timestamp=12.5,
        source="mp4:sample.mp4",
        frame_id=300,
        bbox={"x1": 1, "y1": 2, "x2": 3, "y2": 4},
    )


def test_repository_insert_and_get_projection(tmp_path) -> None:
    repository = ViolationRepository(Database(tmp_path / "events.sqlite3"))

    persisted = repository.save(_record())
    loaded = repository.get("EVT-01")

    assert loaded == persisted
    assert persisted.id == "EVT-01"
    assert persisted.timestamp == "2026-09-23T12:34:56Z"
    assert persisted.snapshot is None
    assert persisted.status is EventStatus.OPEN


def test_repository_duplicate_id_is_explicit(tmp_path) -> None:
    repository = ViolationRepository(Database(tmp_path / "events.sqlite3"))
    repository.insert(_record())

    with pytest.raises(DuplicateEventError):
        repository.insert(_record())


def test_repository_get_or_insert_is_idempotent_but_rejects_conflict(
    tmp_path,
) -> None:
    repository = ViolationRepository(Database(tmp_path / "events.sqlite3"))

    first = repository.get_or_insert(_record())
    second = repository.get_or_insert(_record())
    assert first == second

    with pytest.raises(EventConflictError):
        repository.get_or_insert(_record(confidence=0.5))


def test_repository_query_filters_and_status_update(tmp_path) -> None:
    repository = ViolationRepository(Database(tmp_path / "events.sqlite3"))
    repository.insert(_record("EVT-01", track_id=7))
    repository.insert(
        _record(
            "EVT-02",
            track_id=8,
            occurred_at="2026-09-23T13:34:56Z",
        )
    )

    page = repository.query(
        EventQuery(
            track_id=8,
            event_type=ComplianceEventType.NO_HELMET,
        )
    )
    assert page.total_count == 1
    assert page.items[0].id == "EVT-02"

    updated = repository.update_status("EVT-02", EventStatus.RESOLVED)
    assert updated.status is EventStatus.RESOLVED
    assert repository.list_events(status="resolved") == [updated]


def test_repository_rejects_unknown_worker_identity(tmp_path) -> None:
    repository = ViolationRepository(Database(tmp_path / "events.sqlite3"))
    record = StoredEvent(
        id="EVT-01",
        timestamp="2026-09-23T12:34:56Z",
        track_id=7,
        type=ComplianceEventType.NO_HELMET,
        confidence=0.91,
        source_timestamp=12.5,
        source="mp4:sample.mp4",
        worker_id="worker-missing",
    )

    with pytest.raises(DatabaseWriteError):
        repository.insert(record)
