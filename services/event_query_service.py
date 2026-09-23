"""Read-only dashboard queries over persisted events and evidence metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.schemas.events import (
    EventPage,
    EventQuery,
    EventStatistics,
    PersistedEvent,
    SnapshotReference,
)
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from infra.storage.snapshot_storage import SnapshotStorage, SnapshotStorageError

__all__ = ["EvidenceView", "EventQueryService"]


@dataclass(frozen=True, slots=True)
class EvidenceView:
    """Dashboard-facing evidence projection with an explicit integrity state."""

    event: PersistedEvent
    snapshot: SnapshotReference | None
    file_path: Path | None
    verified: bool
    error_message: str | None = None


class EventQueryService:
    """Read-only boundary used by Streamlit instead of direct SQL."""

    def __init__(
        self,
        event_repository: EventRepository,
        snapshot_repository: SnapshotRepository | None = None,
        storage: SnapshotStorage | None = None,
    ) -> None:
        if not isinstance(event_repository, EventRepository):
            raise TypeError("event_repository must be an EventRepository")
        if snapshot_repository is not None and not isinstance(
            snapshot_repository, SnapshotRepository
        ):
            raise TypeError(
                "snapshot_repository must be a SnapshotRepository or None"
            )
        if storage is not None and not isinstance(storage, SnapshotStorage):
            raise TypeError("storage must be a SnapshotStorage or None")
        self.event_repository = event_repository
        self.snapshot_repository = snapshot_repository
        self.storage = storage

    def query_events(self, query: EventQuery) -> EventPage:
        """Return one validated dashboard page."""

        return self.event_repository.query(query)

    def list_events(
        self,
        *,
        start_at: str | None = None,
        end_at: str | None = None,
        track_id: int | None = None,
        event_type: str | None = None,
        status: str | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> EventPage:
        """Return a dashboard page without exposing repository details."""

        return self.event_repository.query(
            EventQuery(
                start_at=start_at,
                end_at=end_at,
                track_id=track_id,
                event_type=event_type,
                status=status,
                source=source,
                limit=limit,
                offset=offset,
            )
        )

    def statistics(self, query: EventQuery | None = None) -> EventStatistics:
        """Return aggregates using the same validated filter contract."""

        normalized = query or EventQuery(limit=1000)
        return self.event_repository.statistics(normalized)

    def get_event(self, event_id: str) -> PersistedEvent | None:
        return self.event_repository.get(event_id)

    def sources(self) -> tuple[str, ...]:
        return self.event_repository.sources()

    def snapshot_events(
        self,
        *,
        query: EventQuery | None = None,
    ) -> tuple[PersistedEvent, ...]:
        """Return events that currently advertise a snapshot reference."""

        normalized = query or EventQuery(limit=1000)
        page = self.event_repository.query(normalized)
        return tuple(item for item in page.items if item.snapshot is not None)

    def evidence(self, event_id: str) -> EvidenceView | None:
        """Resolve and verify one event snapshot without mutating it."""

        event = self.event_repository.get(event_id)
        if event is None:
            return None
        if event.snapshot is None:
            return EvidenceView(
                event=event,
                snapshot=None,
                file_path=None,
                verified=False,
                error_message="event has no snapshot reference",
            )
        if self.snapshot_repository is None or self.storage is None:
            return EvidenceView(
                event=event,
                snapshot=None,
                file_path=None,
                verified=False,
                error_message="snapshot services are not configured",
            )

        snapshot = self.snapshot_repository.get_by_event(event_id)
        if snapshot is None:
            return EvidenceView(
                event=event,
                snapshot=None,
                file_path=None,
                verified=False,
                error_message="snapshot metadata is missing",
            )
        path = self.storage.resolve_path(snapshot.relative_path)
        try:
            verified = self.storage.verify(
                snapshot.relative_path,
                expected_sha256=snapshot.sha256,
                expected_width=snapshot.width,
                expected_height=snapshot.height,
            )
        except SnapshotStorageError as exc:
            return EvidenceView(
                event=event,
                snapshot=snapshot,
                file_path=path if path.is_file() else None,
                verified=False,
                error_message=f"{exc.code}: {exc}",
            )
        return EvidenceView(
            event=event,
            snapshot=snapshot,
            file_path=self.storage.resolve_path(verified.relative_path),
            verified=True,
        )
