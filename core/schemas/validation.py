"""Phase 4C real-inference validation evidence contracts.

These schemas are model-independent and contain no inference execution logic.
They define the records that a future authorized validation run may emit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

__all__ = [
    "ImageValidationRecord",
    "InferenceValidationReport",
    "VideoValidationRecord",
]


def _validate_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA256 hex digest")


def _normalize_class_counts(
    class_counts: Mapping[str, int] | tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    items = (
        tuple(class_counts.items())
        if isinstance(class_counts, Mapping)
        else tuple(class_counts)
    )
    normalized: list[tuple[str, int]] = []
    for class_name, count in items:
        if not class_name:
            raise ValueError("class name cannot be empty")
        if count < 0:
            raise ValueError("class counts cannot be negative")
        normalized.append((str(class_name), int(count)))
    return tuple(normalized)


def _class_counts_dict(
    class_counts: tuple[tuple[str, int], ...],
) -> dict[str, int]:
    return {class_name: count for class_name, count in class_counts}


@dataclass(frozen=True, slots=True)
class ImageValidationRecord:
    """Evidence for one real image inference attempt."""

    source_label: str
    model_sha256: str
    load_success: bool
    width: int
    height: int
    detection_count: int
    class_counts: Mapping[str, int] | tuple[tuple[str, int], ...]
    confidences: tuple[float, ...]
    latency_ms: float
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not self.source_label:
            raise ValueError("source_label cannot be empty")
        _validate_sha256(self.model_sha256, "model_sha256")
        if self.latency_ms < 0 or not math.isfinite(self.latency_ms):
            raise ValueError("latency_ms must be finite and non-negative")
        if self.width < 0 or self.height < 0:
            raise ValueError("image dimensions cannot be negative")
        if self.detection_count < 0:
            raise ValueError("detection_count cannot be negative")
        if self.detection_count != len(self.confidences):
            raise ValueError("detection_count must match the confidence count")

        normalized_counts = _normalize_class_counts(self.class_counts)
        if sum(count for _, count in normalized_counts) != self.detection_count:
            raise ValueError("class counts must sum to detection_count")
        for confidence in self.confidences:
            if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
                raise ValueError("confidences must be finite values in [0, 1]")

        if self.load_success:
            if self.error_code is not None:
                raise ValueError("successful image load cannot have an error_code")
            if self.width <= 0 or self.height <= 0:
                raise ValueError("successful image load requires positive dimensions")
        else:
            if not self.error_code:
                raise ValueError("failed image load requires an error_code")
            if self.detection_count != 0 or normalized_counts:
                raise ValueError("failed image load cannot contain detections")

        object.__setattr__(self, "class_counts", normalized_counts)

    @property
    def status(self) -> str:
        return "success" if self.load_success else "failed"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable image validation record."""

        return {
            "source_label": self.source_label,
            "model_sha256": self.model_sha256,
            "status": self.status,
            "load_success": self.load_success,
            "width": self.width,
            "height": self.height,
            "detection_count": self.detection_count,
            "class_counts": _class_counts_dict(self.class_counts),
            "confidences": list(self.confidences),
            "latency_ms": self.latency_ms,
            "error_code": self.error_code,
        }


@dataclass(frozen=True, slots=True)
class VideoValidationRecord:
    """Evidence for one real sequential MP4 inference attempt."""

    source_label: str
    model_sha256: str
    source_fps: float
    declared_frame_count: int | None
    processed_frames: int
    processing_time_seconds: float
    total_detections: int
    frames_with_detections: int
    class_counts: Mapping[str, int] | tuple[tuple[str, int], ...]
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not self.source_label:
            raise ValueError("source_label cannot be empty")
        _validate_sha256(self.model_sha256, "model_sha256")
        if self.source_fps <= 0 or not math.isfinite(self.source_fps):
            raise ValueError("source_fps must be finite and positive")
        if self.declared_frame_count is not None and self.declared_frame_count < 0:
            raise ValueError("declared_frame_count cannot be negative")
        if self.processed_frames < 0:
            raise ValueError("processed_frames cannot be negative")
        if (
            self.processing_time_seconds < 0
            or not math.isfinite(self.processing_time_seconds)
        ):
            raise ValueError("processing_time_seconds must be finite and non-negative")
        if self.total_detections < 0:
            raise ValueError("total_detections cannot be negative")
        if not 0 <= self.frames_with_detections <= self.processed_frames:
            raise ValueError("frames_with_detections must be within processed_frames")

        normalized_counts = _normalize_class_counts(self.class_counts)
        if sum(count for _, count in normalized_counts) != self.total_detections:
            raise ValueError("class counts must sum to total_detections")

        if self.error_code is None:
            if self.processed_frames == 0:
                raise ValueError("successful video validation requires processed frames")
            if (
                self.declared_frame_count is not None
                and self.declared_frame_count != self.processed_frames
            ):
                raise ValueError(
                    "processed_frames must match declared_frame_count on success"
                )
        elif not self.error_code:
            raise ValueError("error_code cannot be empty when provided")

        object.__setattr__(self, "class_counts", normalized_counts)

    @property
    def status(self) -> str:
        return "success" if self.error_code is None else "failed"

    @property
    def processing_fps(self) -> float | None:
        if self.processing_time_seconds == 0:
            return None
        return self.processed_frames / self.processing_time_seconds

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable video validation record."""

        return {
            "source_label": self.source_label,
            "model_sha256": self.model_sha256,
            "status": self.status,
            "source_fps": self.source_fps,
            "declared_frame_count": self.declared_frame_count,
            "processed_frames": self.processed_frames,
            "processing_time_seconds": self.processing_time_seconds,
            "processing_fps": self.processing_fps,
            "total_detections": self.total_detections,
            "frames_with_detections": self.frames_with_detections,
            "class_counts": _class_counts_dict(self.class_counts),
            "error_code": self.error_code,
        }


@dataclass(frozen=True, slots=True)
class InferenceValidationReport:
    """Aggregate evidence for one Phase 4C validation run."""

    validation_id: str
    model_sha256: str
    runtime_id: str
    image_records: tuple[ImageValidationRecord, ...] = ()
    video_records: tuple[VideoValidationRecord, ...] = ()

    def __post_init__(self) -> None:
        if not self.validation_id:
            raise ValueError("validation_id cannot be empty")
        _validate_sha256(self.model_sha256, "model_sha256")
        if not self.runtime_id:
            raise ValueError("runtime_id cannot be empty")

        normalized_images = tuple(self.image_records)
        normalized_videos = tuple(self.video_records)
        if any(
            not isinstance(record, ImageValidationRecord)
            for record in normalized_images
        ):
            raise TypeError("image_records must contain ImageValidationRecord objects")
        if any(
            not isinstance(record, VideoValidationRecord)
            for record in normalized_videos
        ):
            raise TypeError("video_records must contain VideoValidationRecord objects")

        object.__setattr__(self, "image_records", normalized_images)
        object.__setattr__(self, "video_records", normalized_videos)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable validation report."""

        return {
            "validation_id": self.validation_id,
            "model_sha256": self.model_sha256,
            "runtime_id": self.runtime_id,
            "image_records": [record.to_dict() for record in self.image_records],
            "video_records": [record.to_dict() for record in self.video_records],
        }
