from datetime import datetime, timezone

from core.events.event_engine import EventEngine
from core.rules.compliance_engine import RuleDomainSettings, RuleSettings
from core.schemas.compliance import (
    ComplianceEventType,
    ComplianceFinding,
    ComplianceResult,
    ComplianceState,
)
from core.schemas.events import EventStatus
from infra.database.database import Database
from infra.database.repository import EventRepository
from services.event_ingest_service import EventIngestService


def _settings() -> RuleSettings:
    return RuleSettings(
        min_consecutive_frames=5,
        min_duration_seconds=1.0,
        recovery_frames=5,
        cooldown_seconds=30.0,
        helmet=RuleDomainSettings(
            enabled=True,
            required=True,
            positive_classes=("hardhat",),
            violation_classes=("no_hardhat",),
        ),
        vest=RuleDomainSettings(
            enabled=True,
            required=True,
            positive_classes=("vest",),
            violation_classes=("no_vest",),
        ),
    )


def _confirmed_event():
    engine = EventEngine(settings=_settings())
    events = []
    for frame_id in range(5):
        result = ComplianceResult(
            frame_id=frame_id,
            timestamp=float(frame_id),
            findings=(
                ComplianceFinding(
                    track_id=7,
                    event_type=ComplianceEventType.NO_HELMET,
                    state=ComplianceState.VIOLATION,
                    confidence=0.91,
                    timestamp=float(frame_id),
                    evidence=("helmet=no_hardhat",),
                ),
            ),
        )
        events.extend(engine.process(result))
    assert len(events) == 1
    return events[0]


def test_phase6_event_persists_across_database_restart(tmp_path) -> None:
    path = tmp_path / "events.sqlite3"
    database = Database(path)
    repository = EventRepository(database)
    service = EventIngestService(
        repository,
        clock=lambda: datetime(2026, 9, 23, 12, 34, 56, tzinfo=timezone.utc),
    )
    event = _confirmed_event()

    assert set(event.to_dict()) == {
        "type",
        "track_id",
        "confidence",
        "timestamp",
    }
    persisted = service.ingest(event, source="video/verified.mp4", frame_id=42)
    database.close()

    reopened = EventRepository(Database(path))
    loaded = reopened.get(persisted.id)
    stored = reopened.get_record(persisted.id)

    assert loaded is not None
    assert loaded.id == event.event_id
    assert loaded.type is event.event_type
    assert loaded.timestamp == "2026-09-23T12:34:56Z"
    assert stored is not None
    assert stored.source_timestamp == event.timestamp
    assert stored.source == "video/verified.mp4"


def test_reingestion_after_restart_does_not_duplicate_event(tmp_path) -> None:
    path = tmp_path / "events.sqlite3"
    event = _confirmed_event()
    first_service = EventIngestService(
        EventRepository(Database(path)),
        clock=lambda: datetime(2026, 9, 23, 12, 34, 56, tzinfo=timezone.utc),
    )
    first_service.ingest(event, source="video/verified.mp4", frame_id=42)

    reopened_repository = EventRepository(Database(path))
    second_service = EventIngestService(
        reopened_repository,
        clock=lambda: datetime(2026, 9, 23, 13, 0, 0, tzinfo=timezone.utc),
    )
    second = second_service.ingest(
        event,
        source="video/verified.mp4",
        frame_id=42,
    )

    assert second.timestamp == "2026-09-23T12:34:56Z"
    assert len(reopened_repository.list_events()) == 1
    updated = reopened_repository.update_status(
        event.event_id,
        EventStatus.ACKNOWLEDGED,
    )
    assert updated.status is EventStatus.ACKNOWLEDGED
    assert len(reopened_repository.list_events(status="acknowledged")) == 1
