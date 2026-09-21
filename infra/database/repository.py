"""Violation event repository boundary.

NOT IMPLEMENTED - FUTURE PHASE
"""

from __future__ import annotations

from typing import Any


class ViolationRepository:
    def save(self, event: Any) -> None:
        raise NotImplementedError(
            "Violation repository persistence belongs to Phase 7 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )

    def list_events(self) -> list[Any]:
        raise NotImplementedError(
            "Violation history queries belong to Phase 7 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
