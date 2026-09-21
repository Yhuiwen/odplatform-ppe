"""Multi-frame violation confirmation boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class TemporalViolationFilter:
    """Contract for removing single-frame false alarms."""

    def update(self, violations: list[Any], frame_meta: Any) -> list[Any]:
        raise NotImplementedError(
            "Temporal violation confirmation belongs to Phase 6 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
