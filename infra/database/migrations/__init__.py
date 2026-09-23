"""Versioned SQLite migrations for the Phase 7 event store."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from infra.database.errors import MigrationError

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "Migration",
    "applied_migrations",
    "discover_migrations",
    "run_migrations",
]

CURRENT_SCHEMA_VERSION = "0001_phase7_events"
MIGRATIONS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class Migration:
    """One immutable migration file and its checksum."""

    version: str
    description: str
    path: Path
    checksum: str

    @property
    def sql(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise MigrationError(
                f"could not read migration {self.version}"
            ) from exc


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _description(sql: str, fallback: str) -> str:
    match = re.search(r"^--\s*description:\s*(.+?)\s*$", sql, re.MULTILINE)
    return match.group(1) if match else fallback


def discover_migrations(
    migrations_dir: str | Path = MIGRATIONS_DIR,
) -> tuple[Migration, ...]:
    """Load migration descriptors in stable version order."""

    root = Path(migrations_dir).expanduser().resolve()
    if not root.is_dir():
        raise MigrationError(f"migration directory does not exist: {root}")

    migrations: list[Migration] = []
    for path in sorted(root.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        version = path.stem
        sql = path.read_text(encoding="utf-8")
        migrations.append(
            Migration(
                version=version,
                description=_description(
                    sql, version.split("_", 1)[-1].replace("_", " ")
                ),
                path=path,
                checksum=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    if not migrations:
        raise MigrationError("no SQLite migrations were found")
    return tuple(migrations)


def _ensure_migration_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )


def applied_migrations(
    connection: sqlite3.Connection,
) -> dict[str, sqlite3.Row]:
    """Return applied migration rows keyed by version."""

    _ensure_migration_table(connection)
    rows = connection.execute(
        """
        SELECT version, description, checksum, applied_at
        FROM schema_migrations
        ORDER BY version
        """
    ).fetchall()
    return {str(row["version"]): row for row in rows}


def _execute_script(connection: sqlite3.Connection, sql: str) -> None:
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                connection.execute(statement)
            buffer = ""
    if buffer.strip():
        raise MigrationError("migration contains an incomplete SQL statement")


def _apply_one(
    connection: sqlite3.Connection,
    migration: Migration,
) -> None:
    owns_transaction = not connection.in_transaction
    if owns_transaction:
        connection.execute("BEGIN IMMEDIATE")
    try:
        _execute_script(connection, migration.sql)
        connection.execute(
            """
            INSERT INTO schema_migrations (
                version, description, checksum, applied_at
            ) VALUES (?, ?, ?, ?)
            """,
            (
                migration.version,
                migration.description,
                migration.checksum,
                _utc_now_iso(),
            ),
        )
        version_number = int(migration.version.split("_", 1)[0])
        connection.execute(f"PRAGMA user_version = {version_number}")
        if owns_transaction:
            connection.execute("COMMIT")
    except Exception as exc:
        if owns_transaction and connection.in_transaction:
            connection.execute("ROLLBACK")
        if isinstance(exc, MigrationError):
            raise
        raise MigrationError(
            f"migration {migration.version} failed"
        ) from exc


def run_migrations(
    connection: sqlite3.Connection,
    migrations: Iterable[Migration] | None = None,
) -> tuple[str, ...]:
    """Apply pending migrations and verify checksums for applied versions."""

    if not isinstance(connection, sqlite3.Connection):
        raise TypeError("connection must be a sqlite3.Connection")

    descriptors = tuple(
        discover_migrations() if migrations is None else migrations
    )
    seen_versions: set[str] = set()
    for migration in descriptors:
        if migration.version in seen_versions:
            raise MigrationError(f"duplicate migration version: {migration.version}")
        seen_versions.add(migration.version)

    _ensure_migration_table(connection)
    applied = applied_migrations(connection)
    known_versions = {migration.version for migration in descriptors}

    unknown = sorted(set(applied) - known_versions)
    if unknown:
        raise MigrationError(
            "database contains unknown applied migrations: " + ", ".join(unknown)
        )

    for migration in descriptors:
        row = applied.get(migration.version)
        if row is None:
            continue
        if row["checksum"] != migration.checksum:
            raise MigrationError(
                f"checksum mismatch for applied migration {migration.version}"
            )

    newly_applied: list[str] = []
    for migration in descriptors:
        if migration.version in applied:
            continue
        _apply_one(connection, migration)
        newly_applied.append(migration.version)
    return tuple(newly_applied)
