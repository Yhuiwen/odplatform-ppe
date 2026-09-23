# Phase 7 Data Contracts

Date: 2026-09-23

Status: FROZEN FOR IMPLEMENTATION DESIGN

## 1. Compatibility Rule

Phase 7 consumes, but does not modify, the released Phase 4 through Phase 6
contracts.

The Phase 6 `ComplianceEvent.to_dict()` JSONL wire representation remains
exactly:

```json
{
  "type": "NO_HELMET",
  "track_id": 7,
  "confidence": 0.91,
  "timestamp": 12.5
}
```

No `event_id`, snapshot path, status, database field or UI field may be added
to that wire representation.

## 2. Existing Upstream Contracts

### 2.1 DetectionResult

Stable fields:

```text
frame_id: integer
timestamp: non-negative number
source: non-empty string
class_id: integer
class_name: string
confidence: number in [0, 1]
bbox: x1, y1, x2, y2
```

### 2.2 TrackResult

Stable fields:

```text
track_id: non-negative integer
detection: person DetectionResult
frame_id
timestamp
source
confidence
bbox
```

### 2.3 AssociationResult

Stable fields:

```text
frame_id
timestamp
source
tracks: tuple[TrackResult, ...]
associations: tuple[PPEAssociation, ...]
```

Each association is either `associated` with one existing person track or
`unknown`. An unknown association cannot carry a person assignment.

### 2.4 ComplianceInput

Stable fields:

```text
frame_id
timestamp
tracks
associations
```

### 2.5 ComplianceResult

Stable fields:

```text
frame_id
timestamp
findings: per-track/event_type findings
```

### 2.6 ComplianceEvent

Stable in-memory fields:

```text
event_id
track_id
event_type
confidence
timestamp
evidence
```

Frozen event types:

```text
NO_HELMET
NO_VEST
PPE_UNKNOWN
```

## 3. Persisted Event Projection

Phase 7 adds a separate `PersistedEvent` projection for SQLite and UI output.
It is not a replacement for `ComplianceEvent`.

### 3.1 Storage model

```text
id: string
timestamp: ISO 8601 UTC string
track_id: integer
type: NO_HELMET | NO_VEST | PPE_UNKNOWN
confidence: number in [0, 1]
snapshot: repository-relative path or null
status: open | acknowledged | resolved | dismissed
```

Internal storage also retains:

```text
source_timestamp: original Phase 6 numeric timestamp
source: source identifier
frame_id: integer or null
bbox: JSON object or null
worker_id: optional assigned worker ID
created_at: UTC ISO 8601
updated_at: UTC ISO 8601
```

### 3.2 Event JSON example

```json
{
  "id": "EVT-01f2c3d4e5f6",
  "timestamp": "2026-09-23T12:34:56Z",
  "track_id": 7,
  "type": "NO_HELMET",
  "confidence": 0.91,
  "snapshot": "20260923/event_EVT-01f2c3d4e5f6.jpg",
  "status": "open"
}
```

The snapshot path is relative. Absolute paths and secrets are forbidden.

### 3.3 Mapping

| Phase 6 field | Phase 7 field | Rule |
| --- | --- | --- |
| `event_id` | `id` | Direct identity; do not regenerate at persistence |
| `event_type` | `type` | Preserve enum value |
| `track_id` | `track_id` | Preserve integer |
| `confidence` | `confidence` | Preserve validated range |
| `timestamp` | `source_timestamp` | Preserve original numeric value |
| not present | `timestamp` | Set from Phase 7 ingestion/frame wall-clock time |
| not present | `snapshot` | Set only after evidence file verification |
| not present | `status` | Initial `open` |

The wall-clock `timestamp` must not be derived by pretending the
media-relative Phase 6 timestamp is a Unix epoch.

## 4. SnapshotReference

```text
snapshot_id: string
event_id: string
relative_path: string
sha256: string
width: positive integer
height: positive integer
mime_type: image/jpeg
captured_at: ISO 8601 UTC string
```

Constraints:

- one snapshot per confirmed event in V1;
- `event_id` must reference an existing event;
- the path is relative to the configured evidence root;
- the file must exist and its SHA256 must match before a snapshot is marked
  complete;
- screenshot content is evidence, not a model input.

## 5. Video Source Contracts

### 5.1 SourceMetadata

```text
source_id: string
source_type: mp4 | usb_camera | rtsp
display_name: string
width: integer or null
height: integer or null
fps: number or null
frame_count: integer or null for live sources
```

### 5.2 FrameData

The existing `core.schemas.video.FrameData` contract is reused:

```text
frame_id: non-negative integer
timestamp: non-negative number
image: frame payload
```

The source adapter does not perform detection.

### 5.3 SourceStatus

```text
state: idle | opening | live | degraded | ended | failed | closed
last_frame_id: integer or null
last_frame_at: ISO 8601 UTC or null
error_code: string or null
error_message: string or null
reconnect_count: non-negative integer
```

RTSP credentials, query secrets and raw stream URIs must not be logged.

## 6. Alert Contracts

### 6.1 AlertMessage

```text
event_id: string
timestamp: ISO 8601 UTC string
track_id: integer
alert_type: NO_HELMET | NO_VEST | PPE_UNKNOWN
confidence: number in [0, 1]
snapshot: repository-relative path or null
message: non-empty Chinese alert text
```

### 6.2 AlertResult

```text
event_id: string
adapter: console | web | tts | future adapter
status: delivered | failed | skipped
timestamp: ISO 8601 UTC string
error_code: string or null
error_message: string or null
```

`skipped` is allowed for a duplicate event or a disabled non-required
adapter. It is not allowed for M-017 TTS when the TTS adapter is enabled.

## 7. Query Contracts

The dashboard-facing query DTO is read-only:

```text
EventQuery:
  start_at: ISO 8601 UTC or null
  end_at: ISO 8601 UTC or null
  track_id: integer or null
  event_type: string or null
  status: string or null
  source: string or null
  limit: positive integer
  offset: non-negative integer
```

The stable query result is a page of `PersistedEvent` projections plus:

```text
total_count
generated_at
```

Statistics are derived from the same event filters. The dashboard must show
the source query's generated time and must not silently use stale values.

## 8. Error and Failure Contract

Failure codes are stable machine-readable strings. Candidate V1 codes:

```text
DB_OPEN_FAILED
DB_MIGRATION_FAILED
DB_WRITE_FAILED
DB_QUERY_FAILED
SNAPSHOT_RENDER_FAILED
SNAPSHOT_WRITE_FAILED
SNAPSHOT_HASH_MISMATCH
SOURCE_OPEN_FAILED
SOURCE_READ_FAILED
SOURCE_TIMEOUT
SOURCE_DISCONNECTED
ALERT_ADAPTER_FAILED
TTS_UNAVAILABLE
UNSUPPORTED_INPUT
```

A failure must be explicit in logs and status. It must not be converted into
a successful event, a synthetic frame or a silent empty result.

## 9. Versioning

- Phase 6 wire contract version: frozen, no changes.
- Phase 7 persisted event schema: `phase7-event-v1`.
- SQLite schema: migration `0001_phase7_events`.
- Changes to field meaning, status vocabulary, path rules or alert semantics
  require a new ADR and migration review.
