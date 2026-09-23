from datetime import datetime, timezone

import pytest
from PIL import Image

from core.schemas.compliance import ComplianceEvent, ComplianceEventType
from core.schemas.events import StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage
from services.event_ingest_service import EventIngestService
from services.snapshot_service import (
    SnapshotService,
    SnapshotServiceEventNotFoundError,
)


def _event() -> ComplianceEvent:
    return ComplianceEvent(
        event_id="EVT-integration-01",
        track_id=7,
        event_type=ComplianceEventType.NO_HELMET,
        confidence=0.91,
        timestamp=12.5,
        evidence=("helmet=no_hardhat",),
    )


def test_event_snapshot_integration_preserves_identity_and_relative_path(
    tmp_path,
) -> None:
    database = Database(tmp_path / "events.sqlite3")
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    storage = SnapshotStorage(tmp_path / "evidence")
    ingest_service = EventIngestService(
        event_repository,
        clock=lambda: datetime(2026, 9, 23, 12, 34, 56, tzinfo=timezone.utc),
    )
    snapshot_service = SnapshotService(
        event_repository,
        snapshot_repository,
        storage,
        clock=lambda: datetime(2026, 9, 23, 12, 35, 0, tzinfo=timezone.utc),
    )
    event = _event()

    persisted = ingest_service.ingest(event, source="video:verified.mp4")
    snapshot = snapshot_service.capture(
        event.event_id,
        Image.new("RGB", (40, 30), color=(4, 5, 6)),
    )

    assert snapshot.event_id == event.event_id
    assert persisted.id == event.event_id
    assert event_repository.get(event.event_id).snapshot == snapshot.relative_path
    assert "\\" not in snapshot.relative_path
    assert storage.resolve_path(snapshot.relative_path).is_file()
    with database.connection() as connection:
        row = connection.execute(
            """
            SELECT event_id, relative_path
            FROM snapshots
            WHERE event_id = ?
            """,
            (event.event_id,),
        ).fetchone()
    assert row["event_id"] == event.event_id
    assert row["relative_path"] == snapshot.relative_path
    assert not row["relative_path"].startswith(("/", "\\"))
    assert ":" not in row["relative_path"]
    assert event.to_dict() == {
        "type": "NO_HELMET",
        "track_id": 7,
        "confidence": 0.91,
        "timestamp": 12.5,
    }


def test_snapshot_service_duplicate_and_missing_event_behavior(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    service = SnapshotService(
        event_repository,
        snapshot_repository,
        SnapshotStorage(tmp_path / "evidence"),
        clock=lambda: datetime(2026, 9, 23, 12, 35, 0, tzinfo=timezone.utc),
    )
    event_repository.insert(
        StoredEvent(
            id="EVT-01",
            timestamp="2026-09-23T12:34:56Z",
            track_id=7,
            type=ComplianceEventType.NO_VEST,
            confidence=0.8,
            source_timestamp=12.5,
            source="mp4:sample.mp4",
        )
    )
    image = Image.new("RGB", (20, 20), color=(1, 1, 1))

    first = service.capture("EVT-01", image)
    second = service.capture("EVT-01", image)

    assert first == second
    with pytest.raises(SnapshotServiceEventNotFoundError, match="does not exist"):
        service.capture("EVT-missing", image)
