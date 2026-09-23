"""Stable database boundary exceptions."""

from __future__ import annotations

__all__ = [
    "DatabaseError",
    "DatabaseOpenError",
    "DatabaseQueryError",
    "DatabaseWriteError",
    "MigrationError",
]


class DatabaseError(RuntimeError):
    """Base class for database failures with a stable machine code."""

    code = "DB_ERROR"


class DatabaseOpenError(DatabaseError):
    code = "DB_OPEN_FAILED"


class MigrationError(DatabaseError):
    code = "DB_MIGRATION_FAILED"


class DatabaseWriteError(DatabaseError):
    code = "DB_WRITE_FAILED"


class DatabaseQueryError(DatabaseError):
    code = "DB_QUERY_FAILED"
