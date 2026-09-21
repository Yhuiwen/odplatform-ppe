"""Person-PPE association boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class PPEPersonAssociator:
    """Contract for associating PPE detections with tracked people."""

    def associate(
        self,
        person_tracks: list[Any],
        ppe_detections: list[Any],
    ) -> list[Any]:
        raise NotImplementedError(
            "Person-PPE association belongs to Phase 5 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
