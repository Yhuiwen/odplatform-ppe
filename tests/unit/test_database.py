import sqlite3

import pytest

from infra.database.database import Database
from infra.database.errors import MigrationError
from infra.database.migrations import discover_migrations, run_migrations


def test_database_applies_versioned_schema(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")

    assert database.applied_migrations() == ("0001_phase7_events",)
    with database.connection() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }
        indexes = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                """
            )
        }
        assert {
            "schema_migrations",
            "workers",
            "events",
            "snapshots",
            "statistics",
        } <= tables
        assert {
            "idx_events_occurred_at",
            "idx_events_type_occurred_at",
            "idx_events_status_occurred_at",
            "idx_events_track_occurred_at",
            "idx_events_worker_occurred_at",
            "idx_snapshots_event_id",
            "idx_statistics_bucket",
        } <= indexes
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1


def test_database_migration_is_idempotent(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")

    assert database.initialize() == ()
    with database.connection() as connection:
        row = connection.execute(
            """
            SELECT version, checksum
            FROM schema_migrations
            WHERE version = '0001_phase7_events'
            """
        ).fetchone()
        assert row["version"] == "0001_phase7_events"
        assert len(row["checksum"]) == 64


def test_database_transaction_rolls_back_on_failure(tmp_path) -> None:
    database = Database(tmp_path / "events.sqlite3")

    with pytest.raises(RuntimeError, match="stop"):
        with database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO workers (
                    worker_id, worker_code, display_name, created_at, updated_at
                ) VALUES ('worker-1', 'W-1', NULL, '2026-09-23T00:00:00Z',
                          '2026-09-23T00:00:00Z')
                """
            )
            raise RuntimeError("stop")

    with database.connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM workers"
        ).fetchone()[0]
    assert count == 0


def test_migration_checksum_drift_is_rejected(tmp_path) -> None:
    migration_path = tmp_path / "0001_test.sql"
    migration_path.write_text(
        "-- description: test migration\nCREATE TABLE sample(id INTEGER);\n",
        encoding="utf-8",
    )
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.row_factory = sqlite3.Row

    assert run_migrations(
        connection, discover_migrations(tmp_path)
    ) == ("0001_test",)
    migration_path.write_text(
        "-- description: changed migration\nCREATE TABLE sample(id INTEGER);\n",
        encoding="utf-8",
    )
    with pytest.raises(MigrationError, match="checksum mismatch"):
        run_migrations(connection, discover_migrations(tmp_path))
