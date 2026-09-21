"""Detector boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any

from core.detection.schemas import Detection, FrameMeta


class Detector:
    """Contract for YOLO11 image inference."""

    def detect(self, image: Any, frame_meta: FrameMeta) -> list[Detection]:
        raise NotImplementedError(
            "Detector implementation belongs to Phase 4 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
