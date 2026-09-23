# Phase 7 Architecture Audit

Date: 2026-09-23

## 1. Audit Scope

This audit covers the released architecture through Phase 6 and the existing
Phase 7 boundaries. It is read-only with respect to implementation.

The audit answers four questions:

1. Are current module boundaries clear enough for Phase 7?
2. Are downstream data structures stable and safe to consume?
3. Can Phase 7 be implemented without changing frozen upstream assets?
4. Which interfaces must be frozen before implementation begins?

## 2. Released Pipeline

The implemented and released flow is:

```text
Image / MP4
-> YOLODetector
-> DetectionResult
-> PersonTrackingAdapter
-> TrackResult
-> PPEAssociationAdapter
-> AssociationResult
-> AssociationAdapter
-> ComplianceInput
-> ComplianceEngine
-> ComplianceResult
-> TemporalViolationFilter
-> EventEngine
-> ComplianceEvent
-> JSONEventStore
```

Phase 5 is released at the phase-record layer with a preserved real-runtime
validation limitation. Phase 6 is released with deterministic offline
fixture validation.

## 3. Boundary Assessment

| Area | Existing boundary | Assessment | Phase 7 action |
| --- | --- | --- | --- |
| Dataset and model | Frozen artifact paths and SHA256 identities | Stable; Phase 7 must not mutate them | Consume only |
| Detection | `core/schemas/detection.py`, `services/inference_service.py` | Stable project-owned `DetectionResult`; no Ultralytics object escapes | Reuse unchanged |
| Tracking | `core/schemas/tracking.py`, person-only adapter | Stable `TrackResult`; real runtime evidence remains limited | Reuse unchanged |
| Association | `core/schemas/association.py` | Stable `AssociationResult`; unknown-safe and frozen thresholds | Reuse unchanged |
| Compliance | `core/schemas/compliance.py`, rule engine, temporal filter | Stable `ComplianceResult` and `ComplianceEvent` contracts | Consume unchanged |
| Event wire evidence | `infra/storage/json_event_store.py` | Frozen append-only JSONL with exactly `type`, `track_id`, `confidence`, `timestamp` | Preserve exactly |
| SQLite | `infra/database/` placeholders | No schema, migration path or repository behavior exists | Design and implement in P7-1 |
| Snapshot evidence | `infra/storage/snapshot_storage.py` placeholder | No path policy, rendering metadata or integrity contract exists | Design and implement in P7-2 |
| Video source | MP4 reader exists; Camera/RTSP do not | No shared source contract; direct `cv2.VideoCapture` reuse would leak infrastructure into business code | Freeze `VideoSource` boundary |
| Dashboard | Streamlit page placeholders only | No service or query boundary | Design and implement in P7-3 |
| Alerts | TTS placeholder only | No common alert contract, ordering or failure isolation | Freeze alert adapter boundary |

## 4. Stable Data Contracts

The following Phase 7 inputs are already stable:

| Contract | Required identity fields |
| --- | --- |
| `DetectionResult` | `frame_id`, `timestamp`, `source`, `class_id`, `class_name`, `confidence`, `bbox` |
| `TrackResult` | `track_id` plus one person `DetectionResult` |
| `AssociationResult` | frame context, person `tracks`, `associations`, explicit unknown outcomes |
| `ComplianceInput` | `frame_id`, `timestamp`, `tracks`, `associations` |
| `ComplianceResult` | frame context and per-track findings |
| `ComplianceEvent` | `event_id`, `track_id`, `event_type`, `confidence`, `timestamp`, `evidence` |

The Phase 6 persisted JSONL representation remains exactly:

```json
{"type":"NO_HELMET","track_id":7,"confidence":0.91,"timestamp":12.5}
```

Phase 7 must not add fields to that wire representation. It receives the
in-memory `ComplianceEvent` and maps it to a separate persisted-event DTO.

## 5. Architecture Findings

### 5.1 Clear separation

The existing dependency direction
`web/scripts -> services -> core/infra -> utils` is sufficient for Phase 7.
No `src/` tree is needed. Database, storage, TTS and alert adapters remain
under `infra/`; orchestration remains under `services/`; UI remains under
`web/`.

### 5.2 Missing Phase 7 boundaries

The following boundaries do not exist yet:

- `VideoSource` for MP4, USB Camera and RTSP lifecycle.
- `PersistedEvent` and `SnapshotReference`.
- Repository read/write/query contracts.
- Evidence path and lifecycle policy.
- `AlertAdapter` for Console, Web and TTS delivery.
- Dashboard query projections and service-owned monitoring session state.

These are design gaps, not evidence that the upstream pipeline must be
rewritten.

### 5.3 Event identity compatibility

Phase 6 creates `event_id` in memory, but its frozen JSONL wire record omits
that field. SQLite history therefore cannot be reconstructed from the JSONL
alone. Phase 7 must persist the in-memory `event_id` at the event-service
boundary while keeping JSONL unchanged.

The default mapping is:

```text
ComplianceEvent.event_id -> PersistedEvent.id
ComplianceEvent.event_type -> PersistedEvent.type
ComplianceEvent.timestamp -> internal source_timestamp
Phase 7 ingest wall clock -> PersistedEvent.timestamp
```

This avoids treating a media-relative timestamp as an absolute UTC time while
retaining the original Phase 6 value for diagnostics.

### 5.4 Runtime evidence limitation

The missing Phase 5 real runtime validation and the offline-only Phase 6
validation are significant release risks, but they do not block architecture
design. They become mandatory inputs to Phase 7-5 Runtime Validation.

### 5.5 Source and UI lifecycle risk

Streamlit reruns page code. A long-running source loop must not be owned by a
page-local blocking loop. Phase 7 must expose a service-owned monitoring
session with explicit `start`, `status`, `stop` and cleanup behavior. The page
only renders service state.

## 6. Required Interface Freezes

The following interfaces are frozen by this phase:

1. `VideoSource`: source lifecycle and frame reading; only adapters may call
   `cv2.VideoCapture`.
2. `PersistedEvent`: the seven-field JSON projection
   `id`, `timestamp`, `track_id`, `type`, `confidence`, `snapshot`, `status`.
3. `SnapshotReference`: event ID, relative evidence path, integrity metadata
   and capture time.
4. `AlertAdapter`: event-driven delivery for Console, Web and TTS with
   isolated failure and event-level idempotency.
5. Repository/service boundary: UI never runs SQL and never calls detector,
   tracker, rule engine or storage adapters directly.

## 7. Audit Result

Result: `PASS FOR ARCHITECTURE FREEZE`.

No existing module must be rewritten to add Phase 7. The required work is
additive:

- implement the existing `infra/` placeholders;
- add service orchestration above released core contracts;
- add a source adapter boundary without changing MP4 inference behavior;
- replace Streamlit placeholders with service-backed pages after
  authorization.

Blocking issues for Phase 7-0: none.

Conditions carried into implementation:

- preserve the Phase 6 JSONL wire contract;
- preserve frozen dataset, mapping, model, training and inference assets;
- obtain real Camera or RTSP evidence for M-008 and real annotated-video
  evidence for M-007 during Phase 7-4/7-5;
- keep TTS in scope as required by M-017.
