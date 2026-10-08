"""Deterministic full-service chain; real model acceptance lives in P9-B script."""

from core.association.ppe_person_association import PPEPersonAssociationAdapter
from core.events.event_engine import EventEngine
from core.schemas.video import SourceType
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.json_event_store import JSONEventStore
from infra.storage.snapshot_storage import SnapshotStorage
from services.compliance_service import ComplianceService
from services.event_ingest_service import EventIngestService
from services.event_query_service import EventQueryService
from services.event_service import EventService
from services.monitoring_service import MonitoringService, MonitoringSourceRequest, MonitoringState
from services.snapshot_service import SnapshotService
from tests.integration.test_monitoring_service import _Alerts, _FakeSource, _Inference, _Tracker, _frame


def test_full_service_pipeline_preserves_event_and_evidence_identity(tmp_path):
    """Only input, detector and tracking boundary are deterministic fakes."""

    source = _FakeSource([_frame(index) for index in range(12)])
    database = Database(tmp_path / "events.sqlite3")
    events = EventRepository(database)
    snapshots = SnapshotRepository(database)
    storage = SnapshotStorage(tmp_path / "snapshots")
    alerts = _Alerts()
    service = MonitoringService(
        inference_service=_Inference(),
        tracker=_Tracker(),
        association_adapter=PPEPersonAssociationAdapter(),
        compliance_service=ComplianceService(),
        event_service=EventService(
            engine=EventEngine(),
            store=JSONEventStore(tmp_path / "events.jsonl"),
        ),
        ingest_service=EventIngestService(events),
        snapshot_service=SnapshotService(events, snapshots, storage),
        alert_service=alerts,
        source_factory=lambda _request: source,
        event_loader=events.get,
    )
    service.start(MonitoringSourceRequest(SourceType.MP4, "test.mp4"))
    assert service.wait(timeout=5)
    status = service.status()
    assert status.state is MonitoringState.COMPLETED
    assert source.read_frame_ids == list(range(12))
    assert source.closed
    assert status.frames_processed == 12
    assert status.events_generated == 1
    assert status.alerts_delivered == 1

    reopened = Database(tmp_path / "events.sqlite3")
    query = EventQueryService(
        EventRepository(reopened), SnapshotRepository(reopened), storage
    )
    page = query.list_events()
    assert page.total_count == 1
    event = page.items[0]
    assert event.id == alerts.events[0].id
    assert event.snapshot == alerts.events[0].snapshot
    assert query.evidence(event.id).verified
