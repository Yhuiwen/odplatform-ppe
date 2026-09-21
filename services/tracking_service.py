"""Tracking service boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class TrackingService:
    def track(self, detections: list[Any]) -> list[Any]:
        raise NotImplementedError(
            "Tracking and association boundaries belong to Phase 5 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
