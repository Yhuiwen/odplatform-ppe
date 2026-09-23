# Phase 7 Target Architecture

Date: 2026-09-23

Status: FROZEN FOR IMPLEMENTATION DESIGN

## 1. Goal

Phase 7 delivers the V1 Web and alert platform around the released
detection, tracking, association and compliance pipeline:

```text
SQLite + Snapshot + TTS + Streamlit
```

Phase 7 turns confirmed `ComplianceEvent` values into queryable history,
traceable evidence and observable alerts. It does not change detector,
tracking, association, compliance, dataset, model or training behavior.

## 2. Target Pipeline

```text
MP4 / USB Camera / RTSP
          |
          v
      VideoSource
          |
          v
  FrameData / VideoFrame
          |
          v
  InferenceService
          |
          v
  DetectionResult
          |
          v
  PersonTrackingAdapter
          |
          v
  TrackResult + PPE DetectionResult
          |
          v
  PPEAssociationAdapter
          |
          v
  AssociationResult
          |
          v
  AssociationAdapter -> ComplianceEngine -> EventEngine
          |
          v
  ComplianceEvent
          |
          +----------------------+
          |                      |
          v                      v
  Phase 6 JSONEventStore   Phase 7 EventIngestService
  (unchanged wire log)          |
                                +--> SnapshotStorage
                                |
                                +--> SQLite repository
                                         |
                          +--------------+--------------+
                          |                             |
                          v                             v
                    Dashboard/query                AlertService
                                                      |
                                      +---------------+--------------+
                                      |               |              |
                                      v               v              v
                                  Console            Web            TTS
```

Phase 6 JSONL remains the append-only wire evidence. SQLite becomes the
queryable application source for Phase 7 history, status and statistics.

## 3. Architecture Boundaries

The existing dependency direction is retained:

```text
web/scripts -> services -> core/infra -> utils
```

No `src/` package is introduced.

| Layer | Responsibility | Must not do |
| --- | --- | --- |
| `web/` | Streamlit pages, filters and rendering | Run inference, query SQL directly, implement rules or open video sources |
| `services/` | Orchestration, session lifecycle, ingestion, evidence, queries and alerts | Return Ultralytics objects or copy detector/tracker/rule logic |
| `core/` | Stable contracts and domain behavior | Import Streamlit, SQLite or Ultralytics runtime objects |
| `infra/` | SQLite, filesystem evidence, TTS and alert adapters | Own business decisions or mutate upstream schemas |
| `utils/` | Paths, config, logging, timing and system helpers | Become a second domain layer |

## 4. Planned Module Boundaries

The following files and responsibilities are design targets, not
implementations in Phase 7-0:

| Area | Planned module | Responsibility |
| --- | --- | --- |
| Event contract | `core/schemas/events.py` | Persisted event DTO, status enum, snapshot reference and API projection |
| Event mapping | `services/event_ingest_service.py` | Map one in-memory `ComplianceEvent` into a persisted event without changing Phase 6 |
| Database | `infra/database/database.py` | Connection, PRAGMAs, transaction and migration entry point |
| Repository | `infra/database/repository.py` | Insert/read/update/list events, snapshots and statistics |
| Migrations | `infra/database/migrations/` | Versioned SQL migrations; future implementation only |
| Snapshot | `infra/storage/snapshot_storage.py` | Atomic evidence write, metadata and integrity verification |
| Snapshot render | `core/evidence/snapshot_renderer.py` | Deterministic annotation of frame and violation metadata |
| Video source | `core/video/video_source.py` | Shared source protocol and source status values |
| MP4 source | `core/video/mp4_source.py` | Adapt the existing `VideoReader`; no duplicate decoding |
| USB source | `core/video/usb_camera_source.py` | Bounded camera lifecycle; only this adapter may call `cv2.VideoCapture` |
| RTSP source | `core/video/rtsp_source.py` | Bounded RTSP lifecycle, URI redaction and observable failure |
| Monitoring | `services/monitoring_service.py` | One service-owned source/pipeline session with start/status/stop |
| Query | `services/event_query_service.py` | Read-only projections and filters for dashboard pages |
| Alert | `services/alert_service.py` | Ordered alert fan-out and failure isolation |
| Alert adapters | `infra/alerts/` | Console, Web and TTS adapters behind one interface |
| TTS | `infra/tts/tts_service.py` | Chinese TTS adapter with timeout/failure isolation |
| Dashboard | `web/Home.py`, `web/pages/` | Streamlit rendering and user actions only |

## 5. A. Event Storage

### 5.1 Decision

Use SQLite first. It is local, transactional, restart-persistent and
appropriate for a single-host V1 deployment. No external database is
introduced for V1.

### 5.2 Logical schema

`schema_migrations`:

| Column | Type | Constraint |
| --- | --- | --- |
| `version` | TEXT | PRIMARY KEY |
| `description` | TEXT | NOT NULL |
| `checksum` | TEXT | NOT NULL |
| `applied_at` | TEXT | NOT NULL, UTC ISO 8601 |

`workers`:

| Column | Type | Constraint |
| --- | --- | --- |
| `worker_id` | TEXT | PRIMARY KEY, stable application ID |
| `worker_code` | TEXT | UNIQUE, optional operator-facing identifier |
| `display_name` | TEXT | NULL |
| `created_at` | TEXT | NOT NULL, UTC ISO 8601 |
| `updated_at` | TEXT | NOT NULL, UTC ISO 8601 |

`workers` is an optional identity registry for human assignment. It is not a
re-identification model. A track ID is ephemeral and must not be treated as a
worker identity.

`events`:

| Column | Type | Constraint |
| --- | --- | --- |
| `event_id` | TEXT | PRIMARY KEY; same value as Phase 6 `event_id` |
| `worker_id` | TEXT | NULL, foreign key to `workers.worker_id` |
| `track_id` | INTEGER | NOT NULL, Phase 6 track identity |
| `event_type` | TEXT | NOT NULL; `NO_HELMET`, `NO_VEST` or `PPE_UNKNOWN` |
| `confidence` | REAL | NOT NULL, `0.0 <= value <= 1.0` |
| `source_timestamp` | REAL | NOT NULL, original Phase 6 timestamp |
| `occurred_at` | TEXT | NOT NULL, UTC ISO 8601 event time |
| `source` | TEXT | NOT NULL, source identifier |
| `frame_id` | INTEGER | NULL |
| `bbox_json` | TEXT | NULL, person/evidence bounding box |
| `status` | TEXT | NOT NULL; initial `open` |
| `created_at` | TEXT | NOT NULL, UTC ISO 8601 |
| `updated_at` | TEXT | NOT NULL, UTC ISO 8601 |

`snapshots`:

| Column | Type | Constraint |
| --- | --- | --- |
| `snapshot_id` | TEXT | PRIMARY KEY |
| `event_id` | TEXT | NOT NULL, UNIQUE, foreign key to `events.event_id` |
| `relative_path` | TEXT | NOT NULL, UNIQUE, repository-relative POSIX path |
| `sha256` | TEXT | NOT NULL |
| `width` | INTEGER | NOT NULL, positive |
| `height` | INTEGER | NOT NULL, positive |
| `mime_type` | TEXT | NOT NULL, initially `image/jpeg` |
| `captured_at` | TEXT | NOT NULL, UTC ISO 8601 |
| `created_at` | TEXT | NOT NULL, UTC ISO 8601 |

`statistics`:

| Column | Type | Constraint |
| --- | --- | --- |
| `stat_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `bucket_start` | TEXT | NOT NULL, UTC ISO 8601 |
| `bucket_end` | TEXT | NOT NULL, UTC ISO 8601 |
| `granularity` | TEXT | NOT NULL; `hour`, `day` or `month` |
| `event_type` | TEXT | NULL aggregates all types when null |
| `status` | TEXT | NULL aggregates all statuses when null |
| `total_count` | INTEGER | NOT NULL, non-negative |
| `updated_at` | TEXT | NOT NULL |

`statistics` is a rebuildable cache. `events` is the source of truth.

### 5.3 Indexes

Required indexes:

- `events(occurred_at)`
- `events(event_type, occurred_at)`
- `events(status, occurred_at)`
- `events(track_id, occurred_at)`
- `events(worker_id, occurred_at)` when not null
- `snapshots(event_id)`
- `statistics(granularity, bucket_start, event_type, status)`

### 5.4 Foreign keys and transaction policy

- Enable `PRAGMA foreign_keys = ON` per connection.
- Use parameterized SQL only.
- Use short transactions with `BEGIN IMMEDIATE` for event/snapshot metadata
  writes.
- Keep filesystem work outside the transaction except for the final metadata
  insert.
- Do not write absolute filesystem paths into the database.
- Use UTC ISO 8601 timestamps for database fields.

### 5.5 Migration strategy

- Schema version `0001` is the first Phase 7 migration.
- Every migration has a stable version, description and checksum.
- The migration runner records applied versions in `schema_migrations`.
- Prefer additive migrations.
- A destructive migration requires a backup, a documented migration note and
  explicit approval.
- Tests must prove migration from an empty database and from the previous
  version.
- `PRAGMA user_version` may be used as a quick compatibility check, but
  `schema_migrations` remains the authoritative history.

## 6. B. Evidence Snapshot System

### 6.1 Logical path

```text
events/
  YYYYMMDD/
    event_<event-id>.jpg
```

The initial physical root is:

```text
artifacts/events/snapshots/
```

This path is already Git-ignored. The database stores only the relative path
from the configured evidence root, never an absolute path.

Example relative path:

```text
20260923/event_EVT-01f2c3d4.jpg
```

### 6.2 Snapshot contents

The rendered evidence must preserve:

- original frame pixels;
- person/evidence bounding box when available;
- `track_id`;
- violation type;
- confidence;
- event timestamp and source frame ID.

If the triggering PPE box is uncertain, the renderer must show the
person/unknown context without inventing a PPE class.

### 6.3 Integrity and write ordering

1. Validate the event and frame.
2. Render to a temporary file under the evidence root.
3. Compute image metadata and SHA256.
4. Atomically rename to the final relative path.
5. Insert event and snapshot metadata in one SQLite transaction.
6. If the transaction fails, retain the event in the existing JSONL evidence
   and mark the file as an orphan candidate for reconciliation.

No automatic deletion is authorized in V1. Disk usage is monitored and a
retention policy must be explicit before cleanup is enabled.

## 7. C. Dashboard

### 7.1 Comparison

| Criterion | Streamlit | FastAPI + Vue |
| --- | --- | --- |
| Development cost | Low; Python-only and compatible with existing repository | High; API, frontend build and two deployment surfaces |
| V1 delivery speed | High | Medium to Low |
| Data dashboard | Strong enough with Plotly/Altair | Strongest for complex interaction |
| Real-time monitoring | Workable when service-owned state is enforced | Easier for persistent multi-user sessions |
| Testing | Streamlit/session tests plus service tests | Separate frontend and API testing |
| Future scaling | Service boundaries permit later replacement | Better long-term separation |
| Locked phase fit | Directly matches `Streamlit` | Conflicts with the locked Phase 7 goal |

### 7.2 Recommendation

Use Streamlit for V1. The page layer must only call `services/` and must not
run SQL, inference, tracking, association or alert policy directly.

The UI must support:

- live monitoring start/status/stop;
- empty-model and disconnected-source states;
- image/video detection views;
- historical event filters by time, person/track, type and status;
- evidence detail with a verified file reference;
- statistics consistent with SQLite queries.

FastAPI + Vue is retained as a future replacement path behind the same
service contracts, not as V1 scope.

## 8. D. Video Source Interface

`VideoSource` is a project-owned protocol with lifecycle methods equivalent
to:

```text
open() -> SourceMetadata
read() -> FrameData | end-of-stream
status() -> SourceStatus
close()
```

Required adapters:

- MP4: delegates to the existing sequential `VideoReader`.
- USB Camera: accepts a bounded device index and owns camera open/close.
- RTSP: accepts an RTSP URI, redacts credentials in logs and owns
  disconnect/reconnect behavior.

Only a source adapter may call `cv2.VideoCapture`. Business services, rule
engines and Streamlit pages must never call it.

Required source states:

```text
idle
opening
live
degraded
ended
failed
closed
```

Failure rules:

- no synthetic frames;
- no silent fallback from RTSP to a local file;
- no silent class or source remapping;
- disconnect and timeout are observable in status and logs;
- reconnect attempts and timeouts are configuration-bound and validated in
  Phase 7-4.

M-008 accepts Camera OR RTSP. The implementation may provide both adapters,
but final acceptance only needs one real source path with observable failure
behavior.

## 9. E. Alert System

### 9.1 Common interface

`AlertAdapter.send(message) -> AlertResult` is the common contract.

`AlertMessage` contains:

- `event_id`;
- `timestamp`;
- `track_id`;
- alert type;
- confidence;
- optional snapshot reference;
- a human-readable Chinese message.

V1 adapters:

- `ConsoleAlertAdapter`: first-stage implementation.
- `WebAlertAdapter`: first-stage implementation; publishes a web-visible
  notification/event view without requiring a separate frontend stack.
- `TTSAlertAdapter`: required by M-017; Chinese speech is dispatched after
  event persistence and obeys event deduplication/cooldown.

Future adapters, not V1:

- Email;
- WeChat;
- SMS.

The adapters are idempotent by `event_id`. A failed adapter records a
structured failure and does not block other adapters or the event-write path.
No adapter may claim delivery without an observable success result.

### 9.2 Ordering

```text
ComplianceEvent
-> event persistence
-> snapshot reference
-> alert fan-out
-> dashboard visibility
```

The event main path is persistence-first. Alert delivery is isolated.

## 10. Non-Goals

Phase 7 does not implement:

- LLM reports or Agent behavior;
- model retraining or evaluation changes;
- dataset or mapping changes;
- Re-ID or cross-camera identity;
- email, WeChat or SMS integrations;
- cloud multi-user deployment;
- automatic evidence deletion;
- a separate `src/` architecture.
