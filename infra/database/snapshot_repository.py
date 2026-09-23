"""SQLite metadata repository for evidence snapshot files."""

from __future__ import annotations

import sqlite3

from core.schemas.events import SnapshotReference
from infra.database.database import Database
from infra.database.errors import DatabaseQueryError, DatabaseWriteError

__all__ = [
    "SnapshotConflictError",
    "SnapshotEventNotFoundError",
    "SnapshotRepository",
    "SnapshotRepositoryError",
]


class SnapshotRepositoryError(RuntimeError):
    """Base snapshot metadata repository failure."""

    code = "SNAPSHOT_REPOSITORY_FAILED"


class SnapshotConflictError(SnapshotRepositoryError):
    code = "SNAPSHOT_ALREADY_EXISTS"


class SnapshotEventNotFoundError(SnapshotRepositoryError):
    code = "SNAPSHOT_EVENT_NOT_FOUND"


class SnapshotRepository:
    """Persist and query snapshot metadata without processing image files."""

    def __init__(self, database: Database) -> None:
        if not isinstance(database, Database):
            raise TypeError("database must be a Database")
        self.database = database

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> SnapshotReference:
        return SnapshotReference(
            snapshot_id=str(row["snapshot_id"]),
            event_id=str(row["event_id"]),
            relative_path=str(row["relative_path"]),
            sha256=str(row["sha256"]),
            width=int(row["width"]),
            height=int(row["height"]),
            mime_type=str(row["mime_type"]),
            captured_at=str(row["captured_at"]),
        )

    @staticmethod
    def _select_sql() -> str:
        return """
            SELECT
                snapshot_id,
                event_id,
                relative_path,
                sha256,
                width,
                height,
                mime_type,
                captured_at
            FROM snapshots
        """

    def _get_by_event(
        self,
        connection: sqlite3.Connection,
        event_id: str,
    ) -> SnapshotReference | None:
        row = connection.execute(
            self._select_sql() + " WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return None if row is None else self._record_from_row(row)

    def _get_by_path(
        self,
        connection: sqlite3.Connection,
        relative_path: str,
    ) -> SnapshotReference | None:
        row = connection.execute(
            self._select_sql() + " WHERE relative_path = ?",
            (relative_path,),
        ).fetchone()
        return None if row is None else self._record_from_row(row)

    @staticmethod
    def _insert_record(
        connection: sqlite3.Connection,
        snapshot: SnapshotReference,
    ) -> None:
        connection.execute(
            """
            INSERT INTO snapshots (
                snapshot_id,
                event_id,
                relative_path,
                sha256,
                width,
                height,
                mime_type,
                captured_at,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.snapshot_id,
                snapshot.event_id,
                snapshot.relative_path,
                snapshot.sha256,
                snapshot.width,
                snapshot.height,
                snapshot.mime_type,
                snapshot.captured_at,
                snapshot.captured_at,
            ),
        )

    @staticmethod
    def _is_event_foreign_key_error(exc: sqlite3.IntegrityError) -> bool:
        return "foreign key" in str(exc).lower()

    @staticmethod
    def _is_snapshot_conflict(exc: sqlite3.IntegrityError) -> bool:
        message = str(exc)
        return any(
            marker in message
            for marker in (
                "snapshots.event_id",
                "snapshots.relative_path",
                "snapshots.snapshot_id",
            )
        )

    def insert(self, snapshot: SnapshotReference) -> SnapshotReference:
        """Insert one verified snapshot metadata row."""

        if not isinstance(snapshot, SnapshotReference):
            raise TypeError("snapshot must be a SnapshotReference")
        try:
            with self.database.transaction() as connection:
                self._insert_record(connection, snapshot)
        except sqlite3.IntegrityError as exc:
            if self._is_event_foreign_key_error(exc):
                raise SnapshotEventNotFoundError(
                    f"snapshot event does not exist: {snapshot.event_id}"
                ) from exc
            if self._is_snapshot_conflict(exc):
                raise SnapshotConflictError(
                    f"snapshot identity already exists: {snapshot.snapshot_id}"
                ) from exc
            raise DatabaseWriteError(
                f"could not insert snapshot {snapshot.snapshot_id}"
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseWriteError(
                f"could not insert snapshot {snapshot.snapshot_id}"
            ) from exc
        return snapshot

    def save(self, snapshot: SnapshotReference) -> SnapshotReference:
        """Compatibility alias for :meth:`insert`."""

        return self.insert(snapshot)

    def get_or_insert(
        self,
        snapshot: SnapshotReference,
    ) -> SnapshotReference:
        """Return identical metadata or reject a conflicting event snapshot."""

        if not isinstance(snapshot, SnapshotReference):
            raise TypeError("snapshot must be a SnapshotReference")
        try:
            with self.database.transaction() as connection:
                existing = self._get_by_event(connection, snapshot.event_id)
                if existing is not None:
                    if existing.has_same_identity(snapshot):
                        return existing
                    raise SnapshotConflictError(
                        "event already has different snapshot metadata: "
                        f"{snapshot.event_id}"
                    )

                path_owner = self._get_by_path(
                    connection,
                    snapshot.relative_path,
                )
                if path_owner is not None:
                    raise SnapshotConflictError(
                        "snapshot path already belongs to another event: "
                        f"{snapshot.relative_path}"
                    )
                self._insert_record(connection, snapshot)
        except sqlite3.IntegrityError as exc:
            if self._is_event_foreign_key_error(exc):
                raise SnapshotEventNotFoundError(
                    f"snapshot event does not exist: {snapshot.event_id}"
                ) from exc
            if self._is_snapshot_conflict(exc):
                with self.database.connection() as connection:
                    existing = self._get_by_event(
                        connection,
                        snapshot.event_id,
                    )
                    if existing is not None and existing.has_same_identity(
                        snapshot
                    ):
                        return existing
                raise SnapshotConflictError(
                    f"snapshot identity already exists: {snapshot.snapshot_id}"
                ) from exc
            raise DatabaseWriteError(
                f"could not insert snapshot {snapshot.snapshot_id}"
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseWriteError(
                f"could not insert snapshot {snapshot.snapshot_id}"
            ) from exc
        return snapshot

    def get_by_event(self, event_id: str) -> SnapshotReference | None:
        """Return the one snapshot associated with an event, if present."""

        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event_id cannot be empty")
        try:
            with self.database.connection() as connection:
                return self._get_by_event(connection, event_id)
        except sqlite3.Error as exc:
            raise DatabaseQueryError(
                f"could not query snapshot for event {event_id}"
            ) from exc

    def get_by_path(self, relative_path: str) -> SnapshotReference | None:
        """Return snapshot metadata by its evidence-relative POSIX path."""

        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError("relative_path cannot be empty")
        try:
            with self.database.connection() as connection:
                return self._get_by_path(connection, relative_path)
        except sqlite3.Error as exc:
            raise DatabaseQueryError(
                f"could not query snapshot path {relative_path}"
            ) from exc
