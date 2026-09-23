-- ODPlatform-PPE Phase 7 event storage schema.
-- Canonical migration: infra/database/migrations/0001_phase7_events.sql

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    worker_code TEXT UNIQUE,
    display_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    worker_id TEXT,
    track_id INTEGER NOT NULL CHECK (track_id >= 0),
    event_type TEXT NOT NULL CHECK (
        event_type IN ('NO_HELMET', 'NO_VEST', 'PPE_UNKNOWN')
    ),
    confidence REAL NOT NULL CHECK (
        confidence >= 0.0 AND confidence <= 1.0
    ),
    source_timestamp REAL NOT NULL CHECK (source_timestamp >= 0.0),
    occurred_at TEXT NOT NULL,
    source TEXT NOT NULL CHECK (length(trim(source)) > 0),
    frame_id INTEGER CHECK (frame_id IS NULL OR frame_id >= 0),
    bbox_json TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (
        status IN ('open', 'acknowledged', 'resolved', 'dismissed')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (worker_id)
        REFERENCES workers(worker_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    relative_path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    width INTEGER NOT NULL CHECK (width > 0),
    height INTEGER NOT NULL CHECK (height > 0),
    mime_type TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (event_id)
        REFERENCES events(event_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS statistics (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket_start TEXT NOT NULL,
    bucket_end TEXT NOT NULL,
    granularity TEXT NOT NULL CHECK (
        granularity IN ('hour', 'day', 'month')
    ),
    event_type TEXT CHECK (
        event_type IS NULL
        OR event_type IN ('NO_HELMET', 'NO_VEST', 'PPE_UNKNOWN')
    ),
    status TEXT CHECK (
        status IS NULL
        OR status IN ('open', 'acknowledged', 'resolved', 'dismissed')
    ),
    total_count INTEGER NOT NULL CHECK (total_count >= 0),
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_occurred_at
    ON events(occurred_at);

CREATE INDEX IF NOT EXISTS idx_events_type_occurred_at
    ON events(event_type, occurred_at);

CREATE INDEX IF NOT EXISTS idx_events_status_occurred_at
    ON events(status, occurred_at);

CREATE INDEX IF NOT EXISTS idx_events_track_occurred_at
    ON events(track_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_events_worker_occurred_at
    ON events(worker_id, occurred_at)
    WHERE worker_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_snapshots_event_id
    ON snapshots(event_id);

CREATE INDEX IF NOT EXISTS idx_statistics_bucket
    ON statistics(granularity, bucket_start, event_type, status);
