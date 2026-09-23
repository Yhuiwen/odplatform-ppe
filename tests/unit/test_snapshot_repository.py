import pytest

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import SnapshotReference, StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import (
    SnapshotConflictError,
    SnapshotEventNotFoundError,
    SnapshotRepository,
)


def _event(event_id: str = "EVT-01") -> StoredEvent:
    return StoredEvent(
        id=event_id,
        timestamp="2026-09-23T12:34:56Z",
        track_id=7,
        type=ComplianceEventType.NO_HELMET,
        confidence=0.91,
        source_timestamp=12.5,
        source="mp4:sample.mp4",
    )


def _snapshot(
    event_id: str = "EVT-01",
    *,
    sha256: str = "a" * 64,
    relative_path: str = "20260923/event_EVT-01.jpg",
) -> SnapshotReference:
    return SnapshotReference(
        snapshot_id=f"SNP-{event_id}",
        event_id=event_id,
        relative_path=relative_path,
        sha256=sha256,
        width=32,
        height=24,
        mime_type="image/jpeg",
        captured_at="2026-09-23T12:34:56Z",
    )


def test_snapshot_repository_associates_metadata_with_event(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    event_repository.insert(_event())

    stored = snapshot_repository.insert(_snapshot())

    assert snapshot_repository.get_by_event("EVT-01") == stored
    assert stored.relative_path == "20260923/event_EVT-01.jpg"
    assert event_repository.get("EVT-01").snapshot == stored.relative_path


def test_snapshot_repository_rejects_missing_event(tmp_path) -> None:
    repository = SnapshotRepository(Database(tmp_path / "events.sqlite3"))

    with pytest.raises(SnapshotEventNotFoundError):
        repository.insert(_snapshot("EVT-missing"))


def test_snapshot_repository_duplicate_is_idempotent_but_conflict_fails(
    tmp_path,
) -> None:
    database = Database(tmp_path / "events.sqlite3")
    EventRepository(database).insert(_event())
    repository = SnapshotRepository(database)
    first = repository.get_or_insert(_snapshot())
    second = repository.get_or_insert(_snapshot())

    assert first == second
    with pytest.raises(SnapshotConflictError):
        repository.get_or_insert(_snapshot(sha256="b" * 64))
