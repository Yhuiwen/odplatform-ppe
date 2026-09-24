from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from PIL import Image

from core.detection.schemas import BoundingBox, Detection
from core.schemas.alerts import AlertResult, AlertStatus
from core.schemas.association import AssociationResult
from core.schemas.compliance import (
    ComplianceEvent,
    ComplianceEventType,
    ComplianceResult,
)
from core.schemas.detection import DetectionResult
from core.schemas.events import EventStatus, PersistedEvent, StoredEvent
from core.schemas.tracking import TrackResult
from core.schemas.video import (
    FrameData,
    SourceMetadata,
    SourceState,
    SourceStatus,
    SourceType,
)
from core.video.video_source import VideoSourceOpenError
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage
from services.event_ingest_service import EventIngestService
from services.monitoring_service import (
    MonitoringService,
    MonitoringSourceRequest,
    MonitoringState,
)
from services.snapshot_service import SnapshotService


class _FakeSource:
    source_type = SourceType.MP4

    def __init__(self, frames: list[FrameData]) -> None:
        self.frames = list(frames)
        self.metadata = SourceMetadata(
            source_id="mp4:test.mp4",
            source_type=SourceType.MP4,
            display_name="test.mp4",
            width=320,
            height=240,
            fps=10.0,
            frame_count=len(frames),
        )
        self.read_frame_ids: list[int] = []
        self.closed = False
        self._state = SourceState.IDLE

    def open(self) -> SourceMetadata:
        self._state = SourceState.LIVE
        return self.metadata

    def read(self) -> FrameData | None:
        if not self.frames:
            self._state = SourceState.ENDED
            return None
        frame = self.frames.pop(0)
        self.read_frame_ids.append(frame.frame_id)
        return frame

    def status(self) -> SourceStatus:
        return SourceStatus(state=self._state)

    def close(self) -> None:
        self.closed = True
        self._state = SourceState.CLOSED


class _FailingSource(_FakeSource):
    def open(self) -> SourceMetadata:
        self._state = SourceState.FAILED
        raise VideoSourceOpenError("source unavailable")


class _Inference:
    def infer_frame(
        self,
        frame: FrameData,
        *,
        source: str,
    ) -> list[DetectionResult]:
        return [
            DetectionResult(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                source=source,
                detection=Detection(
                    bbox=BoundingBox(10, 10, 100, 180),
                    class_id=0,
                    class_name="person",
                    confidence=0.9,
                ),
            )
        ]


class _Tracker:
    def update(
        self,
        detections,
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> tuple[TrackResult, ...]:
        return tuple(
            TrackResult(track_id=7, detection=detection)
            for detection in detections
        )


class _Association:
    def associate(
        self,
        tracks,
        ppe_detections,
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> AssociationResult:
        return AssociationResult(
            frame_id=frame_id,
            timestamp=timestamp,
            source=source,
            tracks=tuple(tracks),
        )


class _Compliance:
    def evaluate(self, result: AssociationResult) -> ComplianceResult:
        return ComplianceResult(
            frame_id=result.frame_id,
            timestamp=result.timestamp,
        )


class _Events:
    def __init__(self) -> None:
        self.emitted = False

    def process(self, result: ComplianceResult) -> tuple[ComplianceEvent, ...]:
        if self.emitted:
            return ()
        self.emitted = True
        return (
            ComplianceEvent(
                event_id="EVT-monitor-01",
                track_id=7,
                event_type=ComplianceEventType.NO_HELMET,
                confidence=0.9,
                timestamp=result.timestamp,
                evidence=("helmet=no_hardhat",),
            ),
        )


class _Alerts:
    def __init__(self) -> None:
        self.events: list[object] = []

    def dispatch_event(self, event) -> tuple[AlertResult, ...]:
        self.events.append(event)
        return (
            AlertResult(
                event_id=event.id,
                adapter="test",
                status=AlertStatus.DELIVERED,
                timestamp="2026-09-23T12:35:00Z",
            ),
        )


def _frame(frame_id: int) -> FrameData:
    return FrameData(
        frame_id=frame_id,
        timestamp=frame_id / 10.0,
        image=Image.new("RGB", (320, 240), color=(12, 34, 56)),
    )


def _service(
    source,
    *,
    event_loader=None,
) -> tuple[MonitoringService, _Alerts]:
    alerts = _Alerts()

    def persisted(event_id: str) -> PersistedEvent:
        return PersistedEvent(
            id=event_id,
            timestamp="2026-09-23T12:34:56Z",
            track_id=7,
            type=ComplianceEventType.NO_HELMET,
            confidence=0.9,
            snapshot=f"20260923/event_{event_id}.jpg",
            status=EventStatus.OPEN,
        )

    service = MonitoringService(
        inference_service=_Inference(),
        tracker=_Tracker(),
        association_adapter=_Association(),
        compliance_service=_Compliance(),
        event_service=_Events(),
        ingest_service=SimpleNamespace(
            ingest=lambda event, **kwargs: persisted(event.event_id),
        ),
        snapshot_service=SimpleNamespace(
            capture=lambda event_id, image: SimpleNamespace(
                relative_path=f"20260923/event_{event_id}.jpg"
            ),
        ),
        alert_service=alerts,
        source_factory=lambda request: source,
        event_loader=event_loader or persisted,
    )
    return service, alerts


def test_monitoring_service_processes_frames_in_order_and_releases_source() -> None:
    source = _FakeSource([_frame(0), _frame(1)])
    service, alerts = _service(source)

    service.start(
        MonitoringSourceRequest(
            source_type=SourceType.MP4,
            location="test.mp4",
        )
    )
    assert service.wait(timeout=2)

    status = service.status()
    assert status.state is MonitoringState.COMPLETED
    assert source.read_frame_ids == [0, 1]
    assert source.closed is True
    assert status.frames_processed == 2
    assert status.detections == 2
    assert status.tracks == 2
    assert status.events_generated == 1
    assert alerts.events[0].snapshot == "20260923/event_EVT-monitor-01.jpg"


def test_monitoring_service_reports_source_failure_and_closes() -> None:
    source = _FailingSource([])
    service, _ = _service(source)

    service.start(
        MonitoringSourceRequest(
            source_type=SourceType.RTSP,
            location="rtsp://example.com/live",
        )
    )
    assert service.wait(timeout=2)

    status = service.status()
    assert status.state is MonitoringState.FAILED
    assert status.error_code == "SOURCE_OPEN_FAILED"
    assert source.closed is True


def test_monitoring_service_persists_snapshot_before_alert_delivery(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")
    event_repository = EventRepository(database)
    snapshot_repository = SnapshotRepository(database)
    ingest = EventIngestService(
        event_repository,
        clock=lambda: datetime(
            2026,
            9,
            23,
            12,
            34,
            56,
            tzinfo=timezone.utc,
        ),
    )
    snapshot_service = SnapshotService(
        event_repository,
        snapshot_repository,
        SnapshotStorage(tmp_path / "snapshots"),
    )
    alerts = _Alerts()
    source = _FakeSource([_frame(0)])
    service = MonitoringService(
        inference_service=_Inference(),
        tracker=_Tracker(),
        association_adapter=_Association(),
        compliance_service=_Compliance(),
        event_service=_Events(),
        ingest_service=ingest,
        snapshot_service=snapshot_service,
        alert_service=alerts,
        source_factory=lambda request: source,
        event_loader=event_repository.get,
    )

    service.start(
        MonitoringSourceRequest(
            source_type=SourceType.MP4,
            location="test.mp4",
        )
    )
    assert service.wait(timeout=2)

    stored = event_repository.get_record("EVT-monitor-01")
    assert stored is not None
    assert stored.snapshot is not None
    assert alerts.events[0].id == "EVT-monitor-01"
    assert alerts.events[0].snapshot == stored.snapshot


def test_monitoring_service_preserves_existing_event_identity(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")
    repository = EventRepository(database)
    repository.insert(
        StoredEvent(
            id="EVT-monitor-01",
            timestamp="2026-09-23T12:34:56Z",
            track_id=7,
            type=ComplianceEventType.NO_HELMET,
            confidence=0.9,
            source_timestamp=0.0,
            source="mp4:test.mp4",
        )
    )
    source = _FakeSource([])
    service, _ = _service(source, event_loader=repository.get)

    service.start(
        MonitoringSourceRequest(
            source_type=SourceType.MP4,
            location="test.mp4",
        )
    )
    assert service.wait(timeout=2)

    assert repository.get("EVT-monitor-01").id == "EVT-monitor-01"
