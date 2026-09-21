"""Event service boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class EventService:
    def process(self, confirmed_violations: list[Any]) -> list[Any]:
        raise NotImplementedError(
            "Violation event behavior belongs to Phase 6 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
