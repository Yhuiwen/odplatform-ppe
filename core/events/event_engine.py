"""Violation event engine boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class EventEngine:
    """Contract for violation creation, deduplication, and lifecycle."""

    def process(self, confirmed_violations: list[Any]) -> list[Any]:
        raise NotImplementedError(
            "Event engine behavior belongs to Phase 6 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
