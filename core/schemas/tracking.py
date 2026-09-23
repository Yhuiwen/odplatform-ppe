"""Phase 5 tracking output contracts.

This module intentionally depends only on the Phase 4 detection contract. The
ByteTrack adapter and its runtime dependencies are implemented in a later
subphase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.schemas.detection import DetectionResult

PERSON_CLASS_ID = 0
PERSON_CLASS_NAME = "person"

__all__ = ["PERSON_CLASS_ID", "PERSON_CLASS_NAME", "TrackResult"]


@dataclass(frozen=True, slots=True)
class TrackResult:
    """A stable track ID bound to one person detection."""

    track_id: int
    detection: DetectionResult

    def __post_init__(self) -> None:
        if not isinstance(self.detection, DetectionResult):
            raise TypeError("detection must be a DetectionResult")
        if self.track_id < 0:
            raise ValueError("track_id cannot be negative")
        if (
            self.detection.class_id != PERSON_CLASS_ID
            or self.detection.class_name != PERSON_CLASS_NAME
        ):
            raise ValueError("TrackResult can only wrap a person detection")

    @property
    def frame_id(self) -> int:
        return self.detection.frame_id

    @property
    def timestamp(self) -> float:
        return self.detection.timestamp

    @property
    def source(self) -> str:
        return self.detection.source

    @property
    def confidence(self) -> float:
        return self.detection.confidence

    @property
    def bbox(self):
        return self.detection.bbox

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable track record."""

        return {
            "track_id": self.track_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "class_id": PERSON_CLASS_ID,
            "class_name": PERSON_CLASS_NAME,
            "confidence": self.confidence,
            "bbox": {
                "x1": self.bbox.x1,
                "y1": self.bbox.y1,
                "x2": self.bbox.x2,
                "y2": self.bbox.y2,
            },
        }
