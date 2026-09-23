"""Person-only ByteTrack adapter.

The Ultralytics runtime is imported only when the real backend is first used.
All external tracker objects stay behind this adapter boundary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Protocol, Sequence

from core.schemas.detection import DetectionResult
from core.schemas.tracking import PERSON_CLASS_ID, PERSON_CLASS_NAME, TrackResult
from utils.config_loader import load_config


class TrackingError(RuntimeError):
    """Base tracking error with a stable machine-readable code."""

    code = "tracking_error"


class TrackingConfigurationError(TrackingError):
    code = "invalid_tracking_configuration"


class TrackingExecutionDisabledError(TrackingError):
    code = "execution_disabled"


class InvalidTrackingClassError(TrackingError):
    code = "invalid_tracking_class"


class TrackingFrameContextError(TrackingError):
    code = "invalid_frame_context"


class ByteTrackRuntimeError(TrackingError):
    code = "bytetrack_runtime_unavailable"


class ByteTrackBackendError(TrackingError):
    code = "bytetrack_backend_error"


@dataclass(frozen=True, slots=True)
class TrackerSettings:
    """Frozen ByteTrack settings parsed from ``configs/tracker.yaml``."""

    expected_ultralytics_version: str
    dependency_source: str
    track_high_thresh: float
    track_low_thresh: float
    new_track_thresh: float
    track_buffer: int
    match_thresh: float
    fuse_score: bool
    person_class_id: int
    person_class_name: str
    min_confidence: float


@dataclass(frozen=True, slots=True)
class ByteTrackMatch:
    """One backend match from a detection index to a ByteTrack ID."""

    detection_index: int
    track_id: int


class ByteTrackBackend(Protocol):
    """Internal backend contract; never exposed outside the adapter."""

    def update(
        self, detections: Sequence[DetectionResult]
    ) -> Sequence[ByteTrackMatch]:
        """Update one frame and return matched detection/track pairs."""

    def reset(self) -> None:
        """Reset all tracker state and ID allocation."""


BackendFactory = Callable[[TrackerSettings], ByteTrackBackend]

__all__ = [
    "BackendFactory",
    "ByteTrackBackend",
    "ByteTrackBackendError",
    "ByteTrackMatch",
    "ByteTrackPersonTrackingAdapter",
    "ByteTrackRuntimeError",
    "InvalidTrackingClassError",
    "TrackerSettings",
    "TrackingConfigurationError",
    "TrackingError",
    "TrackingExecutionDisabledError",
    "TrackingFrameContextError",
]


class ByteTrackPersonTrackingAdapter:
    """Adapt structured person detections to project-owned ``TrackResult`` values."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        execution_enabled: bool | None = None,
        backend: ByteTrackBackend | None = None,
        backend_factory: BackendFactory | None = None,
    ) -> None:
        config = load_config(config_path or "tracker")
        tracker = config.get("tracker")
        if not isinstance(tracker, dict):
            raise TrackingConfigurationError(
                "Tracker configuration requires a 'tracker' mapping"
            )
        if backend is not None and backend_factory is not None:
            raise TrackingConfigurationError(
                "Provide either backend or backend_factory, not both"
            )

        self._execution_enabled = (
            bool(tracker.get("execution_enabled", False))
            if execution_enabled is None
            else bool(execution_enabled)
        )
        self._settings = self._parse_settings(tracker)
        self._backend = backend
        self._backend_factory = backend_factory

    @property
    def settings(self) -> TrackerSettings:
        return self._settings

    def update(
        self,
        detections: Sequence[DetectionResult],
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> tuple[TrackResult, ...]:
        """Track only person detections for one ordered frame."""

        self._ensure_execution_enabled()
        self._validate_frame_context(
            frame_id=frame_id,
            timestamp=timestamp,
            source=source,
        )

        person_detections: list[DetectionResult] = []
        for detection in detections:
            if not isinstance(detection, DetectionResult):
                raise TypeError("detections must contain DetectionResult objects")
            if (
                detection.frame_id != frame_id
                or detection.timestamp != timestamp
                or detection.source != source
            ):
                raise TrackingFrameContextError(
                    "Detection frame context does not match tracker input"
                )
            if (
                detection.class_id != PERSON_CLASS_ID
                or detection.class_name != PERSON_CLASS_NAME
            ):
                raise InvalidTrackingClassError(
                    "ByteTrack adapter accepts person class_id=0 only"
                )
            if detection.confidence >= self._settings.min_confidence:
                person_detections.append(detection)

        backend = self._get_backend()
        try:
            matches = tuple(backend.update(person_detections))
        except TrackingError:
            raise
        except Exception as exc:
            raise ByteTrackBackendError("ByteTrack backend update failed") from exc

        tracks: list[TrackResult] = []
        detection_indexes: set[int] = set()
        track_ids: set[int] = set()
        for match in matches:
            if not isinstance(match, ByteTrackMatch):
                raise ByteTrackBackendError(
                    "ByteTrack backend must return ByteTrackMatch objects"
                )
            if (
                match.detection_index < 0
                or match.detection_index >= len(person_detections)
            ):
                raise ByteTrackBackendError(
                    "ByteTrack backend returned an invalid detection index"
                )
            if match.track_id < 0:
                raise ByteTrackBackendError(
                    "ByteTrack backend returned a negative track ID"
                )
            if (
                match.detection_index in detection_indexes
                or match.track_id in track_ids
            ):
                raise ByteTrackBackendError(
                    "ByteTrack backend returned duplicate matches"
                )

            detection_indexes.add(match.detection_index)
            track_ids.add(match.track_id)
            tracks.append(
                TrackResult(
                    track_id=match.track_id,
                    detection=person_detections[match.detection_index],
                )
            )

        return tuple(tracks)

    def reset(self) -> None:
        """Reset the active backend and discard all track state."""

        if self._backend is not None:
            self._backend.reset()

    def _ensure_execution_enabled(self) -> None:
        if not self._execution_enabled:
            raise TrackingExecutionDisabledError(
                "ByteTrack execution is disabled by configs/tracker.yaml"
            )

    def _get_backend(self) -> ByteTrackBackend:
        if self._backend is None:
            if self._backend_factory is None:
                self._backend = _UltralyticsByteTrackBackend(self._settings)
            else:
                self._backend = self._backend_factory(self._settings)
        return self._backend

    @staticmethod
    def _validate_frame_context(
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> None:
        if frame_id < 0:
            raise TrackingFrameContextError("frame_id cannot be negative")
        if timestamp < 0 or not math.isfinite(timestamp):
            raise TrackingFrameContextError(
                "timestamp must be finite and non-negative"
            )
        if not source:
            raise TrackingFrameContextError("source cannot be empty")

    @staticmethod
    def _parse_settings(tracker: dict[str, Any]) -> TrackerSettings:
        implementation = tracker.get("implementation")
        parameters = tracker.get("parameters")
        person_filter = tracker.get("person_filter")
        if not all(
            isinstance(value, dict)
            for value in (implementation, parameters, person_filter)
        ):
            raise TrackingConfigurationError(
                "Tracker configuration requires implementation, parameters and "
                "person_filter mappings"
            )

        try:
            settings = TrackerSettings(
                expected_ultralytics_version=str(implementation["version"]),
                dependency_source=str(implementation["dependency_source"]),
                track_high_thresh=float(parameters["track_high_thresh"]),
                track_low_thresh=float(parameters["track_low_thresh"]),
                new_track_thresh=float(parameters["new_track_thresh"]),
                track_buffer=int(parameters["track_buffer"]),
                match_thresh=float(parameters["match_thresh"]),
                fuse_score=bool(parameters["fuse_score"]),
                person_class_id=int(person_filter["class_id"]),
                person_class_name=str(person_filter["class_name"]),
                min_confidence=float(person_filter["min_confidence"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TrackingConfigurationError(
                "Tracker configuration contains invalid or missing fields"
            ) from exc

        for field_name, value in (
            ("track_high_thresh", settings.track_high_thresh),
            ("track_low_thresh", settings.track_low_thresh),
            ("new_track_thresh", settings.new_track_thresh),
            ("match_thresh", settings.match_thresh),
            ("min_confidence", settings.min_confidence),
        ):
            if not 0.0 <= value <= 1.0:
                raise TrackingConfigurationError(
                    f"{field_name} must be between 0 and 1"
                )
        if settings.track_buffer <= 0:
            raise TrackingConfigurationError("track_buffer must be positive")
        if settings.person_class_id != PERSON_CLASS_ID:
            raise TrackingConfigurationError(
                "Frozen tracker configuration must use person class_id=0"
            )
        if settings.person_class_name != PERSON_CLASS_NAME:
            raise TrackingConfigurationError(
                "Frozen tracker configuration must use class_name=person"
            )
        return settings


class _UltralyticsByteTrackBackend:
    """Lazy adapter around Ultralytics ``BYTETracker``."""

    def __init__(self, settings: TrackerSettings) -> None:
        self._settings = settings
        self._tracker: Any | None = None

    def update(
        self, detections: Sequence[DetectionResult]
    ) -> tuple[ByteTrackMatch, ...]:
        tracker = self._get_tracker()
        try:
            import numpy as np
        except ImportError as exc:
            raise ByteTrackRuntimeError("NumPy is not installed") from exc

        results = _DetectionResults.from_detections(detections, np)
        rows = np.asarray(tracker.update(results))
        if rows.size == 0:
            return ()
        if rows.ndim != 2 or rows.shape[1] < 8:
            raise ByteTrackBackendError(
                "Ultralytics BYTETracker returned an unexpected output shape"
            )

        matches: list[ByteTrackMatch] = []
        for row in rows:
            detection_index = int(row[7])
            if not 0 <= detection_index < len(detections):
                raise ByteTrackBackendError(
                    "Ultralytics BYTETracker returned an invalid detection index"
                )
            matches.append(
                ByteTrackMatch(
                    detection_index=detection_index,
                    track_id=int(row[4]),
                )
            )
        return tuple(matches)

    def reset(self) -> None:
        if self._tracker is not None:
            self._tracker.reset()
        self._tracker = None

    def _get_tracker(self) -> Any:
        if self._tracker is not None:
            return self._tracker

        try:
            observed_version = version("ultralytics")
        except PackageNotFoundError as exc:
            raise ByteTrackRuntimeError(
                "Ultralytics is not installed in the frozen runtime"
            ) from exc
        if observed_version != self._settings.expected_ultralytics_version:
            raise ByteTrackRuntimeError(
                "Ultralytics version mismatch: "
                f"expected {self._settings.expected_ultralytics_version}, "
                f"observed {observed_version}"
            )

        try:
            from ultralytics.trackers.byte_tracker import BYTETracker
        except ImportError as exc:
            raise ByteTrackRuntimeError(
                "Ultralytics ByteTrack runtime is unavailable"
            ) from exc

        args = SimpleNamespace(
            track_high_thresh=self._settings.track_high_thresh,
            track_low_thresh=self._settings.track_low_thresh,
            new_track_thresh=self._settings.new_track_thresh,
            track_buffer=self._settings.track_buffer,
            match_thresh=self._settings.match_thresh,
            fuse_score=self._settings.fuse_score,
        )
        try:
            self._tracker = BYTETracker(args=args)
        except Exception as exc:
            raise ByteTrackRuntimeError(
                "Could not initialize Ultralytics BYTETracker"
            ) from exc
        return self._tracker


@dataclass(frozen=True, slots=True)
class _DetectionResults:
    """Minimal Results-like payload accepted by Ultralytics BYTETracker."""

    xyxy: Any
    xywh: Any
    conf: Any
    cls: Any

    @classmethod
    def from_detections(
        cls,
        detections: Sequence[DetectionResult],
        np: Any,
    ) -> "_DetectionResults":
        if not detections:
            empty = np.empty((0, 4), dtype=np.float32)
            return cls(
                xyxy=empty,
                xywh=empty,
                conf=np.empty((0,), dtype=np.float32),
                cls=np.empty((0,), dtype=np.float32),
            )

        xyxy = np.asarray(
            [
                (
                    detection.bbox.x1,
                    detection.bbox.y1,
                    detection.bbox.x2,
                    detection.bbox.y2,
                )
                for detection in detections
            ],
            dtype=np.float32,
        )
        widths = xyxy[:, 2] - xyxy[:, 0]
        heights = xyxy[:, 3] - xyxy[:, 1]
        xywh = np.column_stack(
            (
                xyxy[:, 0] + widths / 2.0,
                xyxy[:, 1] + heights / 2.0,
                widths,
                heights,
            )
        ).astype(np.float32)
        conf = np.asarray(
            [detection.confidence for detection in detections],
            dtype=np.float32,
        )
        classes = np.asarray(
            [detection.class_id for detection in detections],
            dtype=np.float32,
        )
        return cls(xyxy=xyxy, xywh=xywh, conf=conf, cls=classes)

    def __len__(self) -> int:
        return len(self.conf)

    def __getitem__(self, mask: Any) -> "_DetectionResults":
        return _DetectionResults(
            xyxy=self.xyxy[mask],
            xywh=self.xywh[mask],
            conf=self.conf[mask],
            cls=self.cls[mask],
        )
