"""Phase 4B-2 video inference data contracts.

These schemas are intentionally free of OpenCV, Torch, Ultralytics and other
model-runtime dependencies. They define data only; video decoding and inference
remain future implementation work.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.schemas.detection import DetectionResult
from core.schemas.events import normalize_utc_timestamp

__all__ = [
    "FrameData",
    "FrameInferenceResult",
    "SourceMetadata",
    "SourceState",
    "SourceStatus",
    "SourceType",
    "VideoInferenceResult",
    "VideoMetadata",
]


class SourceType(str, Enum):
    """Stable input-source categories for the Phase 7 source boundary."""

    MP4 = "mp4"
    USB_CAMERA = "usb_camera"
    RTSP = "rtsp"


class SourceState(str, Enum):
    """Observable lifecycle states shared by every video source adapter."""

    IDLE = "idle"
    OPENING = "opening"
    LIVE = "live"
    DEGRADED = "degraded"
    ENDED = "ended"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    """Immutable metadata reported after a source opens successfully."""

    source_id: str
    source_type: SourceType
    display_name: str
    width: int | None
    height: int | None
    fps: float | None
    frame_count: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id cannot be empty")
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ValueError("display_name cannot be empty")
        try:
            source_type = SourceType(self.source_type)
        except ValueError as exc:
            raise ValueError("source_type must be mp4, usb_camera or rtsp") from exc
        object.__setattr__(self, "source_id", self.source_id.strip())
        object.__setattr__(self, "source_type", source_type)
        object.__setattr__(self, "display_name", self.display_name.strip())

        for field_name in ("width", "height"):
            value = getattr(self, field_name)
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise TypeError(f"{field_name} must be an integer or None")
                if value <= 0:
                    raise ValueError(f"{field_name} must be positive")

        if self.fps is not None:
            if isinstance(self.fps, bool) or not isinstance(self.fps, (int, float)):
                raise TypeError("fps must be numeric or None")
            normalized_fps = float(self.fps)
            if not math.isfinite(normalized_fps) or normalized_fps <= 0:
                raise ValueError("fps must be finite and positive")
            object.__setattr__(self, "fps", normalized_fps)

        if self.frame_count is not None:
            if isinstance(self.frame_count, bool) or not isinstance(
                self.frame_count, int
            ):
                raise TypeError("frame_count must be an integer or None")
            if self.frame_count < 0:
                raise ValueError("frame_count cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "display_name": self.display_name,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frame_count": self.frame_count,
        }


@dataclass(frozen=True, slots=True)
class SourceStatus:
    """Observable status for one source adapter without frame payloads."""

    state: SourceState
    last_frame_id: int | None = None
    last_frame_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    reconnect_count: int = 0

    def __post_init__(self) -> None:
        try:
            state = SourceState(self.state)
        except ValueError as exc:
            raise ValueError("state must be a supported source state") from exc
        object.__setattr__(self, "state", state)

        if self.last_frame_id is not None:
            if isinstance(self.last_frame_id, bool) or not isinstance(
                self.last_frame_id, int
            ):
                raise TypeError("last_frame_id must be an integer or None")
            if self.last_frame_id < 0:
                raise ValueError("last_frame_id cannot be negative")

        if self.last_frame_at is not None:
            object.__setattr__(
                self,
                "last_frame_at",
                normalize_utc_timestamp(self.last_frame_at),
            )

        if self.error_code is not None and (
            not isinstance(self.error_code, str) or not self.error_code.strip()
        ):
            raise ValueError("error_code must be a non-empty string or None")
        if self.error_message is not None and (
            not isinstance(self.error_message, str) or not self.error_message.strip()
        ):
            raise ValueError("error_message must be a non-empty string or None")
        if state in {SourceState.DEGRADED, SourceState.FAILED} and (
            self.error_code is None
        ):
            raise ValueError("degraded or failed sources require an error_code")

        if isinstance(self.reconnect_count, bool) or not isinstance(
            self.reconnect_count, int
        ):
            raise TypeError("reconnect_count must be an integer")
        if self.reconnect_count < 0:
            raise ValueError("reconnect_count cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "last_frame_id": self.last_frame_id,
            "last_frame_at": self.last_frame_at,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "reconnect_count": self.reconnect_count,
        }


@dataclass(frozen=True, slots=True)
class FrameData:
    """One decoded video frame supplied to the inference boundary."""

    frame_id: int
    timestamp: float
    image: Any

    def __post_init__(self) -> None:
        if self.frame_id < 0:
            raise ValueError("frame_id cannot be negative")
        if self.timestamp < 0 or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite and non-negative")
        if self.image is None:
            raise ValueError("image cannot be None")


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    """Source metadata recorded when an MP4 video is opened."""

    source: str
    fps: float
    width: int
    height: int
    frame_count: int | None = None
    duration_seconds: float | None = None

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source cannot be empty")
        if self.fps <= 0 or not math.isfinite(self.fps):
            raise ValueError("fps must be finite and positive")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("video dimensions must be positive")
        if self.frame_count is not None and self.frame_count < 0:
            raise ValueError("frame_count cannot be negative")
        if self.duration_seconds is not None and (
            self.duration_seconds < 0 or not math.isfinite(self.duration_seconds)
        ):
            raise ValueError("duration_seconds must be finite and non-negative")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable metadata representation."""

        return {
            "source": self.source,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "frame_count": self.frame_count,
            "duration_seconds": self.duration_seconds,
        }


@dataclass(frozen=True, slots=True)
class FrameInferenceResult:
    """All detections produced for one ordered video frame."""

    frame_id: int
    timestamp: float
    detections: tuple[DetectionResult, ...] = ()

    def __post_init__(self) -> None:
        if self.frame_id < 0:
            raise ValueError("frame_id cannot be negative")
        if self.timestamp < 0 or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite and non-negative")

        normalized = tuple(self.detections)
        for detection in normalized:
            if not isinstance(detection, DetectionResult):
                raise TypeError("detections must contain DetectionResult objects")
            if detection.frame_id != self.frame_id:
                raise ValueError("detection frame_id must match its frame result")
            if detection.timestamp != self.timestamp:
                raise ValueError(
                    "detection timestamp must match its frame result"
                )
        object.__setattr__(self, "detections", normalized)

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable frame result."""

        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "detection_count": self.detection_count,
            "detections": [item.to_dict() for item in self.detections],
        }


@dataclass(frozen=True, slots=True)
class VideoInferenceResult:
    """Complete ordered result for one local MP4 inference run."""

    metadata: VideoMetadata
    frames: tuple[FrameInferenceResult, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(self.frames)
        previous_timestamp = -1.0
        for expected_frame_id, frame in enumerate(normalized):
            if not isinstance(frame, FrameInferenceResult):
                raise TypeError("frames must contain FrameInferenceResult objects")
            if frame.frame_id != expected_frame_id:
                raise ValueError(
                    "frames must be contiguous and ordered from frame_id 0"
                )
            if frame.timestamp < previous_timestamp:
                raise ValueError("frame timestamps must be non-decreasing")
            previous_timestamp = frame.timestamp

        if (
            self.metadata.frame_count is not None
            and self.metadata.frame_count != len(normalized)
        ):
            raise ValueError("frame_count must match the number of frame results")

        object.__setattr__(self, "frames", normalized)

    @property
    def processed_frames(self) -> int:
        return len(self.frames)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable video inference result."""

        return {
            "video": self.metadata.to_dict(),
            "processed_frames": self.processed_frames,
            "frame_results": [frame.to_dict() for frame in self.frames],
        }
