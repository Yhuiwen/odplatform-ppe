"""SQLite connection, PRAGMA and transaction boundary."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from infra.database.errors import DatabaseOpenError
from infra.database.migrations import applied_migrations, run_migrations
from utils.paths import PROJECT_ROOT

__all__ = ["DEFAULT_DATABASE_PATH", "Database"]

DEFAULT_DATABASE_PATH = PROJECT_ROOT / "artifacts" / "events" / "odplatform.sqlite3"


class Database:
    """Own one SQLite database path and enforce the connection policy."""

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        auto_migrate: bool = True,
        busy_timeout_ms: int = 5000,
    ) -> None:
        if isinstance(busy_timeout_ms, bool) or not isinstance(busy_timeout_ms, int):
            raise TypeError("busy_timeout_ms must be an integer")
        if busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms cannot be negative")

        raw_path = DEFAULT_DATABASE_PATH if path is None else path
        if str(raw_path) == ":memory:":
            self.path: Path | None = None
        else:
            self.path = Path(raw_path).expanduser().resolve()
        self.auto_migrate = bool(auto_migrate)
        self.busy_timeout_ms = busy_timeout_ms
        self._memory_connection: sqlite3.Connection | None = None

    @property
    def display_path(self) -> str:
        return ":memory:" if self.path is None else str(self.path)

    def _configure(self, connection: sqlite3.Connection) -> None:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")

    def _new_connection(self) -> sqlite3.Connection:
        if self.path is None:
            if self._memory_connection is None:
                try:
                    self._memory_connection = sqlite3.connect(
                        ":memory:",
                        isolation_level=None,
                        check_same_thread=False,
                    )
                    self._configure(self._memory_connection)
                except sqlite3.Error as exc:
                    raise DatabaseOpenError("could not open in-memory SQLite") from exc
            return self._memory_connection

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(
                str(self.path),
                timeout=self.busy_timeout_ms / 1000,
                isolation_level=None,
                check_same_thread=False,
            )
            self._configure(connection)
            return connection
        except (OSError, sqlite3.Error) as exc:
            raise DatabaseOpenError(
                f"could not open SQLite database at {self.path}"
            ) from exc

    def connect(
        self,
        path: str | Path | None = None,
    ) -> sqlite3.Connection:
        """Open and configure a connection, applying pending migrations."""

        if path is not None:
            raw_path = str(path)
            if raw_path == ":memory:":
                self.path = None
            else:
                self.path = Path(path).expanduser().resolve()
            if self._memory_connection is not None:
                self._memory_connection.close()
                self._memory_connection = None

        connection = self._new_connection()
        if self.auto_migrate:
            run_migrations(connection)
        return connection

    def initialize(self) -> tuple[str, ...]:
        """Apply pending migrations and return newly applied versions."""

        with self.connection() as connection:
            return run_migrations(connection)

    def migrate(self) -> tuple[str, ...]:
        """Alias for explicit migration initialization."""

        return self.initialize()

    def applied_migrations(self) -> tuple[str, ...]:
        """Return applied migration versions in order."""

        with self.connection() as connection:
            return tuple(applied_migrations(connection))

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield one connection and close file-backed connections on exit."""

        connection = self.connect()
        try:
            yield connection
        finally:
            if self.path is not None:
                connection.close()

    @contextmanager
    def transaction(
        self,
        *,
        immediate: bool = True,
    ) -> Iterator[sqlite3.Connection]:
        """Yield one short write transaction and roll back on failure."""

        connection = self.connect()
        owns_transaction = not connection.in_transaction
        if owns_transaction:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        try:
            yield connection
        except Exception:
            if owns_transaction and connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        else:
            if owns_transaction and connection.in_transaction:
                connection.execute("COMMIT")
        finally:
            if self.path is not None:
                connection.close()

    def close(self) -> None:
        """Close an in-memory connection owned by this database object."""

        if self._memory_connection is not None:
            self._memory_connection.close()
            self._memory_connection = None

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
