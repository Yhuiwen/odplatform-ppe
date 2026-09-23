"""Phase 5 tracking adapter contract."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult

__all__ = ["PersonTrackingAdapter"]


@runtime_checkable
class PersonTrackingAdapter(Protocol):
    """Stateful ByteTrack adapter contract for person-only tracking."""

    def update(
        self,
        detections: Sequence[DetectionResult],
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> tuple[TrackResult, ...]:
        """Update tracker state and return person tracks for one frame."""
