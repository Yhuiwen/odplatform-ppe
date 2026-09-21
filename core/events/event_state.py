"""Event state schemas and future state manager boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EventLifecycle(str, Enum):
    NEW = "new"
    ACTIVE = "active"
    RECOVERED = "recovered"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class EventState:
    event_id: str
    lifecycle: EventLifecycle
    first_seen_frame: int
    last_seen_frame: int


class EventStateManager:
    """Contract for maintaining event state across frames.

    NOT IMPLEMENTED - FUTURE PHASE
    """

    def update(self, event: Any) -> EventState:
        raise NotImplementedError(
            "Event state management belongs to Phase 6 "
            "(NOT IMPLEMENTED - FUTURE PHASE)"
        )
