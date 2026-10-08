"""Explicit write boundary for operator event handling."""

from __future__ import annotations

from core.schemas.events import EventStatus, PersistedEvent
from infra.database.repository import EventRepository


class EventStatusService:
    def __init__(self, repository: EventRepository) -> None:
        if not isinstance(repository, EventRepository):
            raise TypeError("repository must be an EventRepository")
        self.repository = repository

    def set_handled(self, event_id: str, *, handled: bool) -> PersistedEvent:
        if not isinstance(handled, bool):
            raise TypeError("handled must be bool")
        return self.repository.update_status(
            event_id,
            EventStatus.RESOLVED if handled else EventStatus.OPEN,
        )
