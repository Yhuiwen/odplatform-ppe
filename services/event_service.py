"""Application orchestration for compliance event creation and storage."""

from __future__ import annotations

from pathlib import Path

from core.events.event_engine import EventEngine
from core.schemas.compliance import ComplianceEvent, ComplianceResult
from infra.storage.json_event_store import JSONEventStore

__all__ = ["EventService"]


class EventService:
    """Process compliance results and append newly created events."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        engine: EventEngine | None = None,
        store: JSONEventStore | None = None,
    ) -> None:
        self.engine = engine or EventEngine(config_path)
        self.store = store or JSONEventStore()

    def process(
        self, result: ComplianceResult
    ) -> tuple[ComplianceEvent, ...]:
        """Return and persist only newly confirmed events."""

        events = self.engine.process(result)
        self.store.append_many(events)
        return events

    def read_events(self) -> list[dict[str, object]]:
        """Read the current JSONL event evidence."""

        return self.store.read_all()
