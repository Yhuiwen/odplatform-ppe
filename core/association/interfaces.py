"""Phase 5 Person-PPE association contract."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from core.schemas.association import AssociationResult
from core.schemas.detection import DetectionResult
from core.schemas.tracking import TrackResult

__all__ = ["PPEAssociationAdapter"]


@runtime_checkable
class PPEAssociationAdapter(Protocol):
    """Associate PPE detections with person tracks conservatively."""

    def associate(
        self,
        tracks: Sequence[TrackResult],
        ppe_detections: Sequence[DetectionResult],
        *,
        frame_id: int,
        timestamp: float,
        source: str,
    ) -> AssociationResult:
        """Return explicit associated or unknown outcomes for one frame."""
