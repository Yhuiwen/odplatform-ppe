# PHASE_7_1_EVENT_STORAGE_REPORT

Date: 2026-09-23

Result: COMPLETE FOR HUMAN REVIEW

## 1. Scope

Phase 7-1 implements the SQLite event-storage boundary frozen by Phase 7-0.
It does not implement evidence snapshot rendering or file writes, dashboard,
alerts/TTS, Camera/RTSP or runtime acceptance.

The Phase 6 `ComplianceEvent` object, Phase 6 event engine, Phase 5 tracking
and association code, model, dataset, mapping and training configuration were
not modified.

## 2. Changed Files

Core contracts and services:

- `core/schemas/events.py`
- `services/event_ingest_service.py`

SQLite storage:

- `infra/database/__init__.py`
- `infra/database/errors.py`
- `infra/database/database.py`
- `infra/database/repository.py`
- `infra/database/schema.sql`
- `infra/database/migrations/__init__.py`
- `infra/database/migrations/0001_phase7_events.sql`

Tests:

- `tests/unit/test_event_schemas.py`
- `tests/unit/test_database.py`
- `tests/unit/test_event_repository.py`
- `tests/unit/test_event_ingest_service.py`
- `tests/integration/test_event_storage_integration.py`
- `tests/unit/test_imports.py`
- `tests/unit/test_placeholders.py`
- `tests/unit/test_structure.py`

Supporting files:

- `.gitignore`
- `pyproject.toml`

## 3. Database Schema

Migration version:

```text
0001_phase7_events
```

Migration SHA256:

```text
c83c59e91f1278b01cecbf75a4236032c21a0e82009d5f15d65cd65366eac9f4
```

Tables:

| Table | Purpose |
| --- | --- |
| `schema_migrations` | Authoritative migration version, description, checksum and UTC applied time |
| `workers` | Optional operator-facing worker registry; track ID is not treated as worker identity |
| `events` | Authoritative event history keyed by the Phase 6 `event_id` |
| `snapshots` | One-to-one evidence metadata boundary; file rendering/writes remain Phase 7-2 |
| `statistics` | Rebuildable aggregate cache; `events` remains source of truth |

Required indexes are present for occurred time, event type, status, track,
worker, snapshot event and statistics bucket queries.

Connection policy:

- `PRAGMA foreign_keys = ON`
- WAL journal mode
- bounded busy timeout
- parameterized SQL
- short `BEGIN IMMEDIATE` write transactions
- UTC ISO 8601 database timestamps

## 4. Event Mapping and Compatibility

The separate persisted-event projection is:

```json
{
  "id": "EVT-...",
  "timestamp": "2026-09-23T12:34:56Z",
  "track_id": 7,
  "type": "NO_HELMET",
  "confidence": 0.91,
  "snapshot": null,
  "status": "open"
}
```

Mapping:

| Phase 6 field | Storage field | Rule |
| --- | --- | --- |
| `event_id` | `events.event_id` | Direct identity; never regenerated |
| `event_type` | `events.event_type` | Frozen value preserved |
| `timestamp` | `events.source_timestamp` | Original numeric video/media time preserved |
| none | `events.occurred_at` | Phase 7 UTC wall-clock display timestamp |
| none | `events.status` | Initial `open` |
| none | `snapshots.relative_path` | Deferred to Phase 7-2 |

The Phase 6 JSONL wire representation remains exactly:

```json
{
  "type": "NO_HELMET",
  "track_id": 7,
  "confidence": 0.91,
  "timestamp": 12.5
}
```

No `event_id`, snapshot, status or database field was added to
`ComplianceEvent.to_dict()`.

## 5. Migration Behavior

- Empty databases apply `0001_phase7_events` once and record its checksum.
- Re-running initialization applies no migration and returns an empty tuple.
- Applied migration checksums are revalidated on every connection.
- A changed applied migration raises `MigrationError` (`DB_MIGRATION_FAILED`).
- Unknown applied migration versions are rejected.
- `PRAGMA user_version` is set to `1`.

## 6. Tests

Commands:

```text
python -m pytest
python -m compileall .
git diff --check
git diff HEAD -- docs/00_PROJECT_CHARTER.md
```

Results:

- `python -m pytest`: `352 passed, 1 skipped`.
- `python -m compileall .`: PASS.
- `git diff --check`: PASS; only Git line-ending notices were emitted.
- Charter diff: PASS, empty.
- Skip: existing optional Torch evaluation test because Torch is not installed.

Coverage includes schema validation, migration idempotency/checksum drift,
transaction rollback, repository duplicate/conflict handling, filters,
status updates, restart persistence, event identity preservation, source
timestamp separation and Phase 6 wire compatibility.

## 7. Gates

| Gate | Status |
| --- | --- |
| P7-1-G1 SQLite schema and connection policy | PASS |
| P7-1-G2 Versioned checksum-protected migrations | PASS |
| P7-1-G3 Restart-persistent event repository | PASS |
| P7-1-G4 Event identity and source-time preservation | PASS |
| P7-1-G5 Phase 6 JSONL wire compatibility | PASS |
| P7-1-G6 Unit and integration tests | PASS |
| P7-1-G7 Scope and frozen assets unchanged | PASS |
| P7-1-G8 No commit, push or tag | PASS |

## 8. Known Limitations

- Snapshot files are not rendered or written in Phase 7-1.
- `snapshots` exists as schema only; no snapshot repository/file integrity
  workflow is claimed.
- `statistics` exists as a rebuildable schema boundary; aggregation writers
  and visibility time handling remain later work.
- Worker assignment is schema-ready but no worker-management service exists.
- Dashboard, alerts/TTS, Camera/RTSP and runtime validation remain pending.
- M-015 remains `待实现` in the locked Charter until full acceptance evidence
  exists.

## 9. Final Decision

Phase 7-1 is `COMPLETE FOR HUMAN REVIEW`.

Next allowed step:

```text
WAIT FOR PHASE 7-1 HUMAN REVIEW
```

Commit, push and tag: `NO`.
