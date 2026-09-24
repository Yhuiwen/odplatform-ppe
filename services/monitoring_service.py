"""Service-owned realtime monitoring session for MP4, camera and RTSP input."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic
from typing import Any, Callable, Mapping

from core.schemas.compliance import ComplianceEvent
from core.schemas.detection import DetectionResult
from core.schemas.events import PersistedEvent, format_utc_timestamp
from core.schemas.tracking import PERSON_CLASS_ID, PERSON_CLASS_NAME
from core.schemas.video import FrameData, SourceMetadata, SourceType
from core.video.mp4_source import MP4VideoSource
from core.video.rtsp_source import RTSPVideoSource
from core.video.usb_camera_source import USBCameraSource
from core.video.video_source import VideoSource, VideoSourceError

__all__ = [
    "MonitoringAlreadyRunningError",
    "MonitoringConfigurationError",
    "MonitoringError",
    "MonitoringService",
    "MonitoringSourceRequest",
    "MonitoringState",
    "MonitoringStatus",
    "build_video_source",
]


class MonitoringError(RuntimeError):
    """Base monitoring failure with a stable machine-readable code."""

    code = "MONITORING_FAILED"


class MonitoringConfigurationError(MonitoringError):
    code = "MONITORING_CONFIGURATION_INVALID"


class MonitoringAlreadyRunningError(MonitoringError):
    code = "MONITORING_ALREADY_RUNNING"


class MonitoringState(str, Enum):
    """Observable state of one service-owned monitoring session."""

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MonitoringSourceRequest:
    """Validated input request accepted by the monitoring service."""

    source_type: SourceType
    location: str | int

    def __post_init__(self) -> None:
        try:
            source_type = SourceType(self.source_type)
        except ValueError as exc:
            raise MonitoringConfigurationError(
                "source_type must be mp4, usb_camera or rtsp"
            ) from exc
        object.__setattr__(self, "source_type", source_type)

        if source_type is SourceType.USB_CAMERA:
            if isinstance(self.location, bool) or not isinstance(self.location, int):
                raise MonitoringConfigurationError(
                    "USB camera location must be a non-negative integer"
                )
            if self.location < 0:
                raise MonitoringConfigurationError(
                    "USB camera location cannot be negative"
                )
            return

        if not isinstance(self.location, (str, Path)) or not str(
            self.location
        ).strip():
            raise MonitoringConfigurationError(
                "MP4 and RTSP locations must be non-empty strings"
            )
        object.__setattr__(self, "location", str(self.location).strip())


@dataclass(frozen=True, slots=True)
class MonitoringStatus:
    """Thread-safe status projection rendered by the Streamlit page."""

    state: MonitoringState = MonitoringState.IDLE
    source_type: SourceType | None = None
    source_id: str | None = None
    display_name: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    frames_processed: int = 0
    detections: int = 0
    tracks: int = 0
    associations: int = 0
    unknown_associations: int = 0
    events_generated: int = 0
    alerts_delivered: int = 0
    alerts_failed: int = 0
    started_at: str | None = None
    stopped_at: str | None = None
    latest_frame_id: int | None = None
    latest_frame_timestamp: float | None = None
    latest_frame_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    recent_events: tuple[dict[str, Any], ...] = ()
    latest_frame: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", MonitoringState(self.state))
        if self.source_type is not None:
            object.__setattr__(
                self,
                "source_type",
                SourceType(self.source_type),
            )
        for field_name in (
            "frames_processed",
            "detections",
            "tracks",
            "associations",
            "unknown_associations",
            "events_generated",
            "alerts_delivered",
            "alerts_failed",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")
        if self.latest_frame_timestamp is not None and (
            not math.isfinite(self.latest_frame_timestamp)
            or self.latest_frame_timestamp < 0
        ):
            raise ValueError("latest_frame_timestamp must be finite and non-negative")
        object.__setattr__(self, "recent_events", tuple(self.recent_events))

    @property
    def active(self) -> bool:
        return self.state in {
            MonitoringState.STARTING,
            MonitoringState.RUNNING,
            MonitoringState.STOPPING,
        }

    def to_dict(self, *, include_preview: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "state": self.state.value,
            "source_type": (
                None if self.source_type is None else self.source_type.value
            ),
            "source_id": self.source_id,
            "display_name": self.display_name,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frames_processed": self.frames_processed,
            "detections": self.detections,
            "tracks": self.tracks,
            "associations": self.associations,
            "unknown_associations": self.unknown_associations,
            "events_generated": self.events_generated,
            "alerts_delivered": self.alerts_delivered,
            "alerts_failed": self.alerts_failed,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "latest_frame_id": self.latest_frame_id,
            "latest_frame_timestamp": self.latest_frame_timestamp,
            "latest_frame_at": self.latest_frame_at,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "recent_events": [dict(item) for item in self.recent_events],
            "has_preview": self.latest_frame is not None,
        }
        if include_preview:
            payload["latest_frame"] = self.latest_frame
        return payload


SourceFactory = Callable[[MonitoringSourceRequest], VideoSource]
EventLoader = Callable[[str], PersistedEvent | None]


def build_video_source(request: MonitoringSourceRequest) -> VideoSource:
    """Create one frozen input adapter without opening it."""

    if not isinstance(request, MonitoringSourceRequest):
        raise TypeError("request must be a MonitoringSourceRequest")
    if request.source_type is SourceType.MP4:
        return MP4VideoSource(str(request.location))
    if request.source_type is SourceType.USB_CAMERA:
        assert isinstance(request.location, int)
        return USBCameraSource(request.location)
    if request.source_type is SourceType.RTSP:
        return RTSPVideoSource(str(request.location))
    raise MonitoringConfigurationError("unsupported monitoring source")


class MonitoringService:
    """Run one source/pipeline session in a service-owned worker thread."""

    def __init__(
        self,
        *,
        inference_service: Any,
        tracker: Any,
        association_adapter: Any,
        compliance_service: Any,
        event_service: Any,
        ingest_service: Any,
        snapshot_service: Any,
        alert_service: Any,
        source_factory: SourceFactory = build_video_source,
        event_loader: EventLoader | None = None,
        execution_enabled: bool = True,
        stop_timeout_seconds: float = 5.0,
        max_recent_events: int = 20,
        clock: Callable[[], datetime] | None = None,
        monotonic_clock: Callable[[], float] | None = None,
    ) -> None:
        self.inference_service = self._require_callable(
            inference_service,
            "infer_frame",
            "inference_service",
        )
        self.tracker = self._require_callable(tracker, "update", "tracker")
        self.association_adapter = self._require_callable(
            association_adapter,
            "associate",
            "association_adapter",
        )
        self.compliance_service = self._require_callable(
            compliance_service,
            "evaluate",
            "compliance_service",
        )
        self.event_service = self._require_callable(
            event_service,
            "process",
            "event_service",
        )
        self.ingest_service = self._require_callable(
            ingest_service,
            "ingest",
            "ingest_service",
        )
        self.snapshot_service = self._require_callable(
            snapshot_service,
            "capture",
            "snapshot_service",
        )
        self.alert_service = self._require_callable(
            alert_service,
            "dispatch_event",
            "alert_service",
        )
        if not callable(source_factory):
            raise TypeError("source_factory must be callable")
        if event_loader is not None and not callable(event_loader):
            raise TypeError("event_loader must be callable or None")
        if isinstance(stop_timeout_seconds, bool) or not isinstance(
            stop_timeout_seconds, (int, float)
        ):
            raise TypeError("stop_timeout_seconds must be numeric")
        normalized_stop_timeout = float(stop_timeout_seconds)
        if normalized_stop_timeout <= 0:
            raise ValueError("stop_timeout_seconds must be positive")
        if isinstance(max_recent_events, bool) or not isinstance(
            max_recent_events, int
        ):
            raise TypeError("max_recent_events must be an integer")
        if max_recent_events <= 0:
            raise ValueError("max_recent_events must be positive")

        self.source_factory = source_factory
        self.event_loader = event_loader
        self.execution_enabled = bool(execution_enabled)
        self.stop_timeout_seconds = normalized_stop_timeout
        self.max_recent_events = max_recent_events
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.monotonic_clock = monotonic_clock or monotonic
        self._status = MonitoringStatus()
        self._status_lock = Lock()
        self._lifecycle_lock = Lock()
        self._stop_event = Event()
        self._finished_event = Event()
        self._thread: Thread | None = None

    @staticmethod
    def _require_callable(value: Any, method: str, name: str) -> Any:
        if not callable(getattr(value, method, None)):
            raise TypeError(f"{name} must expose {method}()")
        return value

    def status(self) -> MonitoringStatus:
        """Return the latest immutable status projection."""

        with self._status_lock:
            return self._status

    def start(self, request: MonitoringSourceRequest) -> MonitoringStatus:
        """Start one session and return immediately."""

        if not isinstance(request, MonitoringSourceRequest):
            raise TypeError("request must be a MonitoringSourceRequest")
        if not self.execution_enabled:
            raise MonitoringConfigurationError(
                "Realtime monitoring is disabled by configs/monitoring.yaml"
            )
        with self._lifecycle_lock:
            if self._thread is not None and self._thread.is_alive():
                raise MonitoringAlreadyRunningError(
                    "a monitoring session is already running"
                )
            source = self.source_factory(request)
            self._reset_runtime()
            started_at = format_utc_timestamp(self.clock())
            with self._status_lock:
                self._status = MonitoringStatus(
                    state=MonitoringState.STARTING,
                    source_type=request.source_type,
                    display_name=self._display_name(request),
                    started_at=started_at,
                )
            self._stop_event.clear()
            self._finished_event.clear()
            self._thread = Thread(
                target=self._run,
                args=(request, source),
                name=f"phase7-monitoring-{request.source_type.value}",
                daemon=True,
            )
            self._thread.start()
            return self.status()

    def stop(self, *, timeout: float | None = None) -> MonitoringStatus:
        """Request a graceful stop and wait up to the configured timeout."""

        wait_seconds = self.stop_timeout_seconds if timeout is None else timeout
        if isinstance(wait_seconds, bool) or not isinstance(
            wait_seconds, (int, float)
        ):
            raise TypeError("timeout must be numeric or None")
        if wait_seconds < 0:
            raise ValueError("timeout cannot be negative")

        with self._lifecycle_lock:
            thread = self._thread
            if thread is None or not thread.is_alive():
                return self.status()
            self._stop_event.set()
            with self._status_lock:
                self._status = self._replace_status(
                    self._status,
                    state=MonitoringState.STOPPING,
                )
        thread.join(timeout=float(wait_seconds))
        if thread.is_alive():
            with self._status_lock:
                self._status = self._replace_status(
                    self._status,
                    error_code="MONITORING_STOP_TIMEOUT",
                    error_message="monitoring worker did not stop before timeout",
                )
        return self.status()

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for the current session to finish without requesting stop."""

        with self._lifecycle_lock:
            thread = self._thread
        if thread is None:
            return True
        thread.join(timeout=timeout)
        return not thread.is_alive()

    def _run(
        self,
        request: MonitoringSourceRequest,
        source: VideoSource,
    ) -> None:
        source_metadata: SourceMetadata | None = None
        failure: Exception | None = None
        try:
            source_metadata = source.open()
            with self._status_lock:
                self._status = self._replace_status(
                    self._status,
                    state=MonitoringState.RUNNING,
                    source_id=source_metadata.source_id,
                    display_name=source_metadata.display_name,
                    width=source_metadata.width,
                    height=source_metadata.height,
                    fps=source_metadata.fps,
                )

            while not self._stop_event.is_set():
                frame = source.read()
                if frame is None:
                    break
                self._process_frame(frame, source_metadata)
        except Exception as exc:
            failure = exc
        finally:
            try:
                source.close()
            except Exception as exc:
                if failure is None:
                    failure = exc

        stopped_at = format_utc_timestamp(self.clock())
        with self._status_lock:
            current = self._status
            if failure is not None:
                self._status = self._replace_status(
                    current,
                    state=MonitoringState.FAILED,
                    stopped_at=stopped_at,
                    error_code=str(
                        getattr(failure, "code", "MONITORING_RUNTIME_FAILED")
                    ),
                    error_message=f"{type(failure).__name__}: {failure}",
                )
            elif self._stop_event.is_set():
                self._status = self._replace_status(
                    current,
                    state=MonitoringState.STOPPED,
                    stopped_at=stopped_at,
                )
            else:
                self._status = self._replace_status(
                    current,
                    state=MonitoringState.COMPLETED,
                    stopped_at=stopped_at,
                )
        self._finished_event.set()

    def _process_frame(
        self,
        frame: FrameData,
        source_metadata: SourceMetadata,
    ) -> None:
        detections = self.inference_service.infer_frame(
            frame,
            source=source_metadata.source_id,
        )
        normalized_detections = self._validate_detections(
            detections,
            frame=frame,
            source=source_metadata.source_id,
        )
        people = tuple(
            detection
            for detection in normalized_detections
            if detection.class_id == PERSON_CLASS_ID
            and detection.class_name == PERSON_CLASS_NAME
        )
        ppe = tuple(
            detection
            for detection in normalized_detections
            if detection.class_id in {1, 2, 3, 4}
        )
        tracks = self.tracker.update(
            people,
            frame_id=frame.frame_id,
            timestamp=frame.timestamp,
            source=source_metadata.source_id,
        )
        association = self.association_adapter.associate(
            tracks,
            ppe,
            frame_id=frame.frame_id,
            timestamp=frame.timestamp,
            source=source_metadata.source_id,
        )
        compliance = self.compliance_service.evaluate(association)
        new_events = self.event_service.process(compliance)

        recent_events: list[dict[str, Any]] = []
        delivered = 0
        failed = 0
        for event in new_events:
            persisted = self._persist_event(
                event,
                frame=frame,
                source=source_metadata.source_id,
                tracks=tracks,
            )
            snapshot = self.snapshot_service.capture(event.event_id, frame.image)
            latest = self._load_persisted_event(event.event_id)
            persisted = latest or persisted
            alert_results = tuple(self.alert_service.dispatch_event(persisted))
            delivered += sum(result.delivered for result in alert_results)
            failed += sum(
                result.status.value == "failed" for result in alert_results
            )
            recent_events.append(
                {
                    "event_id": event.event_id,
                    "type": event.event_type.value,
                    "track_id": event.track_id,
                    "confidence": event.confidence,
                    "frame_id": frame.frame_id,
                    "snapshot": snapshot.relative_path,
                    "alerts": [result.to_dict() for result in alert_results],
                }
            )

        with self._status_lock:
            current = self._status
            combined_recent = (
                *recent_events,
                *current.recent_events,
            )[: self.max_recent_events]
            self._status = self._replace_status(
                current,
                frames_processed=current.frames_processed + 1,
                detections=current.detections + len(normalized_detections),
                tracks=current.tracks + len(tracks),
                associations=current.associations + len(association.associations),
                unknown_associations=(
                    current.unknown_associations + association.unknown_count
                ),
                events_generated=current.events_generated + len(new_events),
                alerts_delivered=current.alerts_delivered + delivered,
                alerts_failed=current.alerts_failed + failed,
                latest_frame_id=frame.frame_id,
                latest_frame_timestamp=frame.timestamp,
                latest_frame_at=format_utc_timestamp(self.clock()),
                recent_events=combined_recent,
                latest_frame=frame.image,
            )

    def _persist_event(
        self,
        event: ComplianceEvent,
        *,
        frame: FrameData,
        source: str,
        tracks: Any,
    ) -> PersistedEvent:
        track = next(
            (
                item
                for item in tracks
                if getattr(item, "track_id", None) == event.track_id
            ),
            None,
        )
        bbox = None
        if track is not None:
            item_bbox = track.bbox
            bbox = {
                "x1": item_bbox.x1,
                "y1": item_bbox.y1,
                "x2": item_bbox.x2,
                "y2": item_bbox.y2,
            }
        return self.ingest_service.ingest(
            event,
            source=source,
            frame_id=frame.frame_id,
            bbox=bbox,
        )

    def _load_persisted_event(self, event_id: str) -> PersistedEvent | None:
        loader = self.event_loader
        if loader is None:
            repository = getattr(self.ingest_service, "repository", None)
            loader = getattr(repository, "get", None)
        if not callable(loader):
            return None
        loaded = loader(event_id)
        if loaded is not None and not isinstance(loaded, PersistedEvent):
            raise MonitoringError(
                "event_loader must return PersistedEvent or None"
            )
        return loaded

    @staticmethod
    def _validate_detections(
        detections: Any,
        *,
        frame: FrameData,
        source: str,
    ) -> tuple[DetectionResult, ...]:
        normalized = tuple(detections)
        for detection in normalized:
            if not isinstance(detection, DetectionResult):
                raise MonitoringError(
                    "inference service returned a non-DetectionResult value"
                )
            if (
                detection.frame_id != frame.frame_id
                or detection.timestamp != frame.timestamp
                or detection.source != source
            ):
                raise MonitoringError(
                    "detection frame context does not match monitoring input"
                )
        return normalized

    def _reset_runtime(self) -> None:
        for name in ("tracker", "event_service"):
            target = getattr(self, name)
            reset = getattr(target, "reset", None)
            if callable(reset):
                reset()
        engine = getattr(self.event_service, "engine", None)
        reset = getattr(engine, "reset", None)
        if callable(reset):
            reset()
        close = getattr(self.inference_service, "close", None)
        if callable(close):
            close()

    @staticmethod
    def _display_name(request: MonitoringSourceRequest) -> str:
        if request.source_type is SourceType.USB_CAMERA:
            return f"USB Camera {request.location}"
        if request.source_type is SourceType.RTSP:
            return "RTSP stream"
        return Path(str(request.location)).name

    @staticmethod
    def _replace_status(
        status: MonitoringStatus,
        **changes: Any,
    ) -> MonitoringStatus:
        values: Mapping[str, Any] = {
            field_name: getattr(status, field_name)
            for field_name in MonitoringStatus.__dataclass_fields__
        }
        values.update(changes)
        return MonitoringStatus(**values)
