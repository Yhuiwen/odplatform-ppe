"""Phase 4 detection output contract.

This module is intentionally free of model-runtime dependencies. It defines
only the stable data exchanged by future inference input adapters, detector
wrappers, renderers, and downstream phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.detection.schemas import Detection

__all__ = ["Detection", "DetectionResult"]


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """A single detection tied to its frame and input source."""

    frame_id: int
    timestamp: float
    source: str
    detection: Detection

    def __post_init__(self) -> None:
        if self.frame_id < 0:
            raise ValueError("frame_id cannot be negative")
        if self.timestamp < 0:
            raise ValueError("timestamp cannot be negative")
        if not self.source:
            raise ValueError("source cannot be empty")

    @property
    def class_id(self) -> int:
        return self.detection.class_id

    @property
    def class_name(self) -> str:
        return self.detection.class_name

    @property
    def confidence(self) -> float:
        return self.detection.confidence

    @property
    def bbox(self):
        return self.detection.bbox

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable, flat representation."""

        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": {
                "x1": self.bbox.x1,
                "y1": self.bbox.y1,
                "x2": self.bbox.x2,
                "y2": self.bbox.y2,
            },
        }
