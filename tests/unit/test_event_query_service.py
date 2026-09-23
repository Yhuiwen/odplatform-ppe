from datetime import datetime, timezone

from PIL import Image

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventQuery, EventStatus, StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage
from services.event_query_service import EventQueryService
from services.snapshot_service import SnapshotService


def _record(
    event_id: str,
    *,
    track_id: int,
    event_type: ComplianceEventType,
    occurred_at: str,
    source: str,
    status: EventStatus = EventStatus.OPEN,
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


def test_dashboard_query_filtering_and_statistics(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")
    event_repository = EventRepository(database)
    event_repository.insert(
        _record(
            "EVT-01",
            track_id=7,
            event_type=ComplianceEventType.NO_HELMET,
            occurred_at="2026-09-23T12:00:00Z",
            source="mp4:a.mp4",
        )
    )
    event_repository.insert(
        _record(
            "EVT-02",
            track_id=8,
            event_type=ComplianceEventType.NO_VEST,
            occurred_at="2026-09-24T12:00:00Z",
            source="mp4:b.mp4",
            status=EventStatus.RESOLVED,
        )
    )
    service = EventQueryService(event_repository)

    filtered = service.list_events(
        event_type="NO_VEST",
        status="resolved",
    )
    assert filtered.total_count == 1
    assert filtered.items[0].id == "EVT-02"

    by_type = service.statistics(
        EventQuery(
            start_at="2026-09-23T00:00:00Z",
            end_at="2026-09-24T23:59:59Z",
        )
    )
    assert by_type.total_count == 2
    assert dict(by_type.by_type) == {
        ComplianceEventType.NO_HELMET: 1,
        ComplianceEventType.NO_VEST: 1,
    }
    assert dict(by_type.by_status) == {
        EventStatus.OPEN: 1,
        EventStatus.RESOLVED: 1,
    }
    assert dict(by_type.by_day) == {
        "2026-09-23": 1,
        "2026-09-24": 1,
    }
    assert service.sources() == ("mp4:a.mp4", "mp4:b.mp4")


def test_dashboard_evidence_view_uses_metadata_and_file(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    storage = SnapshotStorage(tmp_path / "evidence")
    event_repository.insert(
        _record(
            "EVT-01",
            track_id=7,
            event_type=ComplianceEventType.NO_HELMET,
            occurred_at="2026-09-23T12:00:00Z",
            source="mp4:a.mp4",
        )
    )
    SnapshotService(
        event_repository,
        snapshot_repository,
        storage,
        clock=lambda: datetime(2026, 9, 23, 12, 1, tzinfo=timezone.utc),
    ).capture(
        "EVT-01",
        Image.new("RGB", (18, 12), color=(30, 40, 50)),
    )
    service = EventQueryService(
        event_repository,
        snapshot_repository,
        storage,
    )

    evidence = service.evidence("EVT-01")

    assert evidence is not None
    assert evidence.verified is True
    assert evidence.snapshot is not None
    assert evidence.file_path is not None and evidence.file_path.is_file()
    assert service.snapshot_events()[0].id == "EVT-01"
