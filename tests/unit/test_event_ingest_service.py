from datetime import datetime, timezone

import pytest

from core.schemas.compliance import ComplianceEvent, ComplianceEventType
from infra.database.database import Database
from infra.database.repository import EventConflictError, EventRepository
from services.event_ingest_service import EventIngestService


def _event(*, confidence: float = 0.91) -> ComplianceEvent:
    return ComplianceEvent(
        event_id="EVT-01",
        track_id=7,
        event_type=ComplianceEventType.NO_HELMET,
        confidence=confidence,
        timestamp=12.5,
        evidence=("helmet=no_hardhat",),
    )


def _service(tmp_path) -> tuple[EventIngestService, EventRepository]:
    repository = EventRepository(Database(tmp_path / "events.sqlite3"))
    service = EventIngestService(
        repository,
        clock=lambda: datetime(2026, 9, 23, 12, 34, 56, tzinfo=timezone.utc),
    )
    return service, repository


def test_ingest_maps_phase6_identity_without_regenerating(tmp_path) -> None:
    service, repository = _service(tmp_path)

    persisted = service.ingest(
        _event(),
        source="mp4:sample.mp4",
        frame_id=300,
        bbox={"x1": 1, "y1": 2, "x2": 3, "y2": 4},
    )
    stored = repository.get_record("EVT-01")

    assert persisted.id == "EVT-01"
    assert persisted.timestamp == "2026-09-23T12:34:56Z"
    assert persisted.snapshot is None
    assert stored is not None
    assert stored.source_timestamp == 12.5
    assert stored.source == "mp4:sample.mp4"
    assert stored.frame_id == 300
    assert stored.bbox == {"x1": 1, "y1": 2, "x2": 3, "y2": 4}


def test_ingest_is_idempotent_and_conflicts_are_rejected(tmp_path) -> None:
    service, repository = _service(tmp_path)

    first = service.ingest(_event())
    second = service.ingest(_event())
    assert first == second
    assert len(repository.list_events()) == 1

    with pytest.raises(EventConflictError):
        service.ingest(_event(confidence=0.5))
