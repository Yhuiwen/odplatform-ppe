"""Map frozen Phase 6 events into Phase 7 SQLite persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Iterable, Mapping, Any

from core.schemas.compliance import ComplianceEvent
from core.schemas.events import PersistedEvent, StoredEvent, format_utc_timestamp
from infra.database.repository import EventRepository

__all__ = ["EventIngestService"]


class EventIngestService:
    """Persist events without changing the Phase 6 in-memory contract."""

    def __init__(
        self,
        repository: EventRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(repository, EventRepository):
            raise TypeError("repository must be an EventRepository")
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _ingestion_timestamp(self) -> str:
        return format_utc_timestamp(self.clock())

    def ingest(
        self,
        event: ComplianceEvent,
        *,
        source: str = "unknown",
        frame_id: int | None = None,
        bbox: Mapping[str, Any] | None = None,
        worker_id: str | None = None,
    ) -> PersistedEvent:
        """Persist one event and return its stable seven-field projection."""

        if not isinstance(event, ComplianceEvent):
            raise TypeError("event must be a ComplianceEvent")

        stored = StoredEvent(
            id=event.event_id,
            timestamp=self._ingestion_timestamp(),
            track_id=event.track_id,
            type=event.event_type,
            confidence=event.confidence,
            source_timestamp=event.timestamp,
            source=source,
            frame_id=frame_id,
            bbox=bbox,
            worker_id=worker_id,
        )
        return self.repository.get_or_insert(stored)

    def ingest_many(
        self,
        events: Iterable[ComplianceEvent],
        *,
        source: str = "unknown",
        frame_id: int | None = None,
        worker_id: str | None = None,
    ) -> tuple[PersistedEvent, ...]:
        """Persist an ordered batch with one shared frame context."""

        normalized = tuple(events)
        return tuple(
            self.ingest(
                event,
                source=source,
                frame_id=frame_id,
                worker_id=worker_id,
            )
            for event in normalized
        )
