"""SQLite repositories for persisted Phase 7 compliance events."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import (
    EventPage,
    EventQuery,
    EventStatistics,
    EventStatus,
    PersistedEvent,
    StoredEvent,
    format_utc_timestamp,
)
from infra.database.database import Database
from infra.database.errors import DatabaseQueryError, DatabaseWriteError

__all__ = [
    "DuplicateEventError",
    "EventConflictError",
    "EventNotFoundError",
    "EventRepository",
    "EventRepositoryError",
    "ViolationRepository",
]


class EventRepositoryError(RuntimeError):
    """Base class for repository failures."""

    code = "EVENT_REPOSITORY_FAILED"


class DuplicateEventError(EventRepositoryError):
    code = "EVENT_ALREADY_EXISTS"


class EventConflictError(EventRepositoryError):
    code = "EVENT_ID_CONFLICT"


class EventNotFoundError(EventRepositoryError):
    code = "EVENT_NOT_FOUND"


def _utc_now_iso() -> str:
    return format_utc_timestamp(datetime.now(timezone.utc))


class EventRepository:
    """Persist and query the authoritative event rows."""

    def __init__(self, database: Database) -> None:
        if not isinstance(database, Database):
            raise TypeError("database must be a Database")
        self.database = database

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> StoredEvent:
        raw_bbox = row["bbox_json"]
        bbox: dict[str, Any] | None = None
        if raw_bbox is not None:
            import json

            try:
                parsed = json.loads(raw_bbox)
            except json.JSONDecodeError as exc:
                raise DatabaseQueryError(
                    f"event {row['event_id']} contains invalid bbox JSON"
                ) from exc
            if not isinstance(parsed, dict):
                raise DatabaseQueryError(
                    f"event {row['event_id']} bbox must be a JSON object"
                )
            bbox = parsed

        return StoredEvent(
            id=str(row["event_id"]),
            timestamp=str(row["occurred_at"]),
            track_id=int(row["track_id"]),
            type=ComplianceEventType(row["event_type"]),
            confidence=float(row["confidence"]),
            source_timestamp=float(row["source_timestamp"]),
            source=str(row["source"]),
            snapshot=row["snapshot"],
            status=EventStatus(row["status"]),
            frame_id=row["frame_id"],
            bbox=bbox,
            worker_id=row["worker_id"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _select_sql() -> str:
        return """
            SELECT
                e.event_id,
                e.worker_id,
                e.track_id,
                e.event_type,
                e.confidence,
                e.source_timestamp,
                e.occurred_at,
                e.source,
                e.frame_id,
                e.bbox_json,
                e.status,
                e.created_at,
                e.updated_at,
                s.relative_path AS snapshot
            FROM events AS e
            LEFT JOIN snapshots AS s ON s.event_id = e.event_id
        """

    def _get_record(
        self,
        connection: sqlite3.Connection,
        event_id: str,
    ) -> StoredEvent | None:
        row = connection.execute(
            self._select_sql() + " WHERE e.event_id = ?",
            (event_id,),
        ).fetchone()
        return None if row is None else self._record_from_row(row)

    @staticmethod
    def _insert_record(
        connection: sqlite3.Connection,
        event: StoredEvent,
    ) -> None:
        connection.execute(
            """
            INSERT INTO events (
                event_id,
                worker_id,
                track_id,
                event_type,
                confidence,
                source_timestamp,
                occurred_at,
                source,
                frame_id,
                bbox_json,
                status,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.worker_id,
                event.track_id,
                event.type.value,
                event.confidence,
                event.source_timestamp,
                event.timestamp,
                event.source,
                event.frame_id,
                event.bbox_json,
                event.status.value,
                event.created_at,
                event.updated_at,
            ),
        )

    def insert(self, event: StoredEvent) -> PersistedEvent:
        """Insert one immutable event row."""

        if not isinstance(event, StoredEvent):
            raise TypeError("event must be a StoredEvent")
        try:
            with self.database.transaction() as connection:
                self._insert_record(connection, event)
        except sqlite3.IntegrityError as exc:
            if self._is_event_id_conflict(exc):
                raise DuplicateEventError(
                    f"event_id already exists: {event.id}"
                ) from exc
            raise DatabaseWriteError(
                f"could not insert event {event.id}"
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseWriteError(
                f"could not insert event {event.id}"
            ) from exc
        return event.to_persisted()

    def save(self, event: StoredEvent) -> PersistedEvent:
        """Compatibility alias for :meth:`insert`."""

        return self.insert(event)

    def get_or_insert(self, event: StoredEvent) -> PersistedEvent:
        """Idempotently persist an event and reject identity conflicts."""

        if not isinstance(event, StoredEvent):
            raise TypeError("event must be a StoredEvent")
        try:
            with self.database.transaction() as connection:
                existing = self._get_record(connection, event.id)
                if existing is not None:
                    if existing.has_same_identity(event):
                        return existing.to_persisted()
                    raise EventConflictError(
                        f"event_id already exists with different event data: "
                        f"{event.id}"
                    )
                self._insert_record(connection, event)
        except sqlite3.IntegrityError as exc:
            if self._is_event_id_conflict(exc):
                with self.database.connection() as connection:
                    existing = self._get_record(connection, event.id)
                if existing is not None and existing.has_same_identity(event):
                    return existing.to_persisted()
                raise EventConflictError(
                    f"event_id already exists with different event data: {event.id}"
                ) from exc
            raise DatabaseWriteError(
                f"could not insert event {event.id}"
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseWriteError(
                f"could not insert event {event.id}"
            ) from exc
        return event.to_persisted()

    @staticmethod
    def _is_event_id_conflict(exc: sqlite3.IntegrityError) -> bool:
        return "events.event_id" in str(exc)

    def get(self, event_id: str) -> PersistedEvent | None:
        """Return one persisted projection or ``None``."""

        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event_id cannot be empty")
        try:
            with self.database.connection() as connection:
                record = self._get_record(connection, event_id)
        except sqlite3.Error as exc:
            raise DatabaseQueryError(
                f"could not query event {event_id}"
            ) from exc
        return None if record is None else record.to_persisted()

    def get_record(self, event_id: str) -> StoredEvent | None:
        """Return the complete internal event row or ``None``."""

        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event_id cannot be empty")
        try:
            with self.database.connection() as connection:
                return self._get_record(connection, event_id)
        except sqlite3.Error as exc:
            raise DatabaseQueryError(
                f"could not query event {event_id}"
            ) from exc

    @staticmethod
    def _filter_clause(query: EventQuery) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if query.start_at is not None:
            clauses.append("e.occurred_at >= ?")
            parameters.append(query.start_at)
        if query.end_at is not None:
            clauses.append("e.occurred_at <= ?")
            parameters.append(query.end_at)
        if query.track_id is not None:
            clauses.append("e.track_id = ?")
            parameters.append(query.track_id)
        if query.event_type is not None:
            clauses.append("e.event_type = ?")
            parameters.append(query.event_type.value)
        if query.status is not None:
            clauses.append("e.status = ?")
            parameters.append(query.status.value)
        if query.source is not None:
            clauses.append("e.source = ?")
            parameters.append(query.source)
        if not clauses:
            return "", parameters
        return " WHERE " + " AND ".join(clauses), parameters

    def query(self, query: EventQuery) -> EventPage:
        """Return one filtered, deterministic page of event projections."""

        if not isinstance(query, EventQuery):
            raise TypeError("query must be an EventQuery")
        where, parameters = self._filter_clause(query)
        try:
            with self.database.connection() as connection:
                total_row = connection.execute(
                    "SELECT COUNT(*) AS total_count FROM events AS e" + where,
                    parameters,
                ).fetchone()
                rows = connection.execute(
                    self._select_sql()
                    + where
                    + " ORDER BY e.occurred_at DESC, e.event_id ASC"
                    + " LIMIT ? OFFSET ?",
                    (*parameters, query.limit, query.offset),
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseQueryError("could not query event history") from exc

        records = tuple(self._record_from_row(row) for row in rows)
        return EventPage(
            items=tuple(record.to_persisted() for record in records),
            total_count=int(total_row["total_count"]),
            generated_at=_utc_now_iso(),
            limit=query.limit,
            offset=query.offset,
        )

    def statistics(self, query: EventQuery) -> EventStatistics:
        """Return deterministic aggregates using the same event filters."""

        if not isinstance(query, EventQuery):
            raise TypeError("query must be an EventQuery")
        where, parameters = self._filter_clause(query)
        try:
            with self.database.connection() as connection:
                summary = connection.execute(
                    """
                    SELECT
                        COUNT(*) AS total_count,
                        MIN(e.occurred_at) AS earliest_at,
                        MAX(e.occurred_at) AS latest_at
                    FROM events AS e
                    """
                    + where,
                    parameters,
                ).fetchone()
                by_type = connection.execute(
                    """
                    SELECT e.event_type AS key, COUNT(*) AS total_count
                    FROM events AS e
                    """
                    + where
                    + """
                    GROUP BY e.event_type
                    ORDER BY total_count DESC, e.event_type ASC
                    """,
                    parameters,
                ).fetchall()
                by_status = connection.execute(
                    """
                    SELECT e.status AS key, COUNT(*) AS total_count
                    FROM events AS e
                    """
                    + where
                    + """
                    GROUP BY e.status
                    ORDER BY total_count DESC, e.status ASC
                    """,
                    parameters,
                ).fetchall()
                by_source = connection.execute(
                    """
                    SELECT e.source AS key, COUNT(*) AS total_count
                    FROM events AS e
                    """
                    + where
                    + """
                    GROUP BY e.source
                    ORDER BY total_count DESC, e.source ASC
                    """,
                    parameters,
                ).fetchall()
                by_day = connection.execute(
                    """
                    SELECT substr(e.occurred_at, 1, 10) AS key,
                           COUNT(*) AS total_count
                    FROM events AS e
                    """
                    + where
                    + """
                    GROUP BY substr(e.occurred_at, 1, 10)
                    ORDER BY key ASC
                    """,
                    parameters,
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseQueryError("could not aggregate event history") from exc

        return EventStatistics(
            total_count=int(summary["total_count"]),
            by_type=tuple(
                (
                    ComplianceEventType(row["key"]),
                    int(row["total_count"]),
                )
                for row in by_type
            ),
            by_status=tuple(
                (
                    EventStatus(row["key"]),
                    int(row["total_count"]),
                )
                for row in by_status
            ),
            by_source=tuple(
                (str(row["key"]), int(row["total_count"]))
                for row in by_source
            ),
            by_day=tuple(
                (str(row["key"]), int(row["total_count"]))
                for row in by_day
            ),
            earliest_at=summary["earliest_at"],
            latest_at=summary["latest_at"],
            generated_at=_utc_now_iso(),
        )

    def sources(self) -> tuple[str, ...]:
        """Return distinct event sources for dashboard filters."""

        try:
            with self.database.connection() as connection:
                rows = connection.execute(
                    """
                    SELECT DISTINCT source
                    FROM events
                    ORDER BY source ASC
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseQueryError("could not list event sources") from exc
        return tuple(str(row["source"]) for row in rows)

    def list_events(
        self,
        *,
        start_at: str | None = None,
        end_at: str | None = None,
        track_id: int | None = None,
        event_type: ComplianceEventType | str | None = None,
        status: EventStatus | str | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PersistedEvent]:
        """Return a filtered list for callers that do not need page metadata."""

        query = EventQuery(
            start_at=start_at,
            end_at=end_at,
            track_id=track_id,
            event_type=(
                None if event_type is None else ComplianceEventType(event_type)
            ),
            status=None if status is None else EventStatus(status),
            source=source,
            limit=limit,
            offset=offset,
        )
        return list(self.query(query).items)

    def update_status(
        self,
        event_id: str,
        status: EventStatus | str,
    ) -> PersistedEvent:
        """Update lifecycle status and return the current projection."""

        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event_id cannot be empty")
        normalized = EventStatus(status)
        updated_at = _utc_now_iso()
        try:
            with self.database.transaction() as connection:
                cursor = connection.execute(
                    """
                    UPDATE events
                    SET status = ?, updated_at = ?
                    WHERE event_id = ?
                    """,
                    (normalized.value, updated_at, event_id),
                )
                if cursor.rowcount == 0:
                    raise EventNotFoundError(f"event does not exist: {event_id}")
                record = self._get_record(connection, event_id)
                if record is None:
                    raise EventNotFoundError(f"event does not exist: {event_id}")
                return record.to_persisted()
        except sqlite3.Error as exc:
            raise DatabaseWriteError(
                f"could not update event {event_id}"
            ) from exc


class ViolationRepository(EventRepository):
    """Backward-compatible Phase 0 name for the Phase 7 event repository."""
