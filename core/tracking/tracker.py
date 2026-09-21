"""Person tracking boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class PersonTracker:
    """Contract for ByteTrack-backed person tracking."""

    def update(self, detections: list[Any], frame: Any) -> list[Any]:
        raise NotImplementedError(
            "ByteTrack integration belongs to Phase 5 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
