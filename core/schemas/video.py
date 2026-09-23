"""Phase 4B-2 video inference data contracts.

These schemas are intentionally free of OpenCV, Torch, Ultralytics and other
model-runtime dependencies. They define data only; video decoding and inference
remain future implementation work.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from core.schemas.detection import DetectionResult

__all__ = [
    "FrameData",
    "FrameInferenceResult",
    "VideoInferenceResult",
    "VideoMetadata",
]


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
