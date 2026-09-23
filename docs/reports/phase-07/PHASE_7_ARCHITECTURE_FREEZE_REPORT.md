# PHASE_7_ARCHITECTURE_FREEZE_REPORT

Date: 2026-09-23

Result: COMPLETE FOR HUMAN REVIEW / DESIGN ONLY

## 1. Current Status

| Item | Value |
| --- | --- |
| Branch | `main` |
| HEAD at task entry | `b8aea3a3343da3342531e690b018fe5d37b3d379` |
| Phase 6 release tag | `phase-6-compliance-event-engine-complete` |
| Phase 6 tag target | `e24e31ae635e5d5cd1129a9fb519a59b7014f802` |
| Phase 6 status | COMPLETE / RELEASED |
| Phase 7 status | IN PROGRESS / DESIGN STARTED |
| Phase 7-0 status | COMPLETE FOR HUMAN REVIEW |
| Phase 7 implementation | NOT STARTED |
| Dataset | `CSS-PPE-10-V1` frozen |
| Release checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Frozen assets changed | NO |
| Commit / push / tag | NO / NO / NO |

## 2. Existing Architecture Audit

The released upstream flow is:

```text
DetectionResult
-> TrackResult
-> AssociationResult
-> ComplianceInput
-> ComplianceResult
-> ComplianceEvent
-> JSONEventStore
```

Audit result:

- the core, service, infra and web boundaries are suitable for Phase 7;
- `DetectionResult`, `TrackResult`, `AssociationResult`,
  `ComplianceInput`, `ComplianceResult` and `ComplianceEvent` are stable;
- the Phase 6 four-field JSONL wire contract is frozen and cannot be
  extended;
- SQLite, snapshot, VideoSource and AlertAdapter boundaries are missing and
  are the actual Phase 7 work;
- the historical Phase 5 real-runtime block and offline-only Phase 6
  evidence are carried risks for Phase 7-5, not reasons to redesign the
  upstream contracts.

Details are in
`docs/reports/phase-07/PHASE_7_ARCHITECTURE_AUDIT.md`.

## 3. Phase 7 Target Architecture

The target flow is:

```text
MP4 / USB Camera / RTSP
-> VideoSource
-> InferenceService
-> Detection/Tracking/Association/Compliance
-> ComplianceEvent
-> EventIngestService
-> SnapshotStorage + SQLite
-> Dashboard + AlertService
```

The locked V1 stack remains `SQLite + Snapshot + TTS + Streamlit`.

The architecture introduces no `src/` tree and preserves:

```text
web/scripts -> services -> core/infra -> utils
```

## 4. Module Design

| Module area | Frozen responsibility |
| --- | --- |
| `core/schemas/events.py` | Persisted event, snapshot reference and status contracts |
| `core/video/video_source.py` | Source protocol and status vocabulary |
| `core/evidence/snapshot_renderer.py` | Deterministic evidence rendering |
| `services/event_ingest_service.py` | Map Phase 6 event to Phase 7 persistence |
| `services/monitoring_service.py` | Service-owned source/pipeline lifecycle |
| `services/event_query_service.py` | Read-only dashboard queries |
| `services/alert_service.py` | Console/Web/TTS fan-out and failure isolation |
| `infra/database/` | SQLite connection, repositories and versioned migrations |
| `infra/storage/snapshot_storage.py` | Atomic evidence files and integrity metadata |
| `infra/alerts/` | Alert adapter implementations |
| `web/` | Streamlit rendering only |

Full design is in
`docs/designs/phase-07/PHASE_7_TARGET_ARCHITECTURE.md`.

## 5. Interface Contracts

The following interfaces are frozen:

- `VideoSource`: `open`, `read`, `status`, `close`; only adapters may call
  `cv2.VideoCapture`.
- `PersistedEvent`: `id`, `timestamp`, `track_id`, `type`, `confidence`,
  `snapshot`, `status`.
- `SnapshotReference`: event ID, relative path, SHA256, dimensions, MIME type
  and capture time.
- `AlertAdapter`: event-driven, idempotent delivery with isolated failure.
- Repository/service boundary: UI does not run business logic or SQL.

Full contract definitions are in
`docs/designs/phase-07/PHASE_7_DATA_CONTRACTS.md`.

## 6. Technology Decision

| Area | Decision |
| --- | --- |
| Persistence | SQLite first |
| Tables | `workers`, `events`, `snapshots`, `statistics`, plus `schema_migrations` |
| Evidence | `artifacts/events/snapshots/YYYYMMDD/event_<event-id>.jpg` |
| Dashboard | Streamlit V1 |
| Future UI | FastAPI + Vue replacement path behind services |
| Inputs | One `VideoSource` interface for MP4, USB Camera and RTSP |
| Alerts | Console, Web and required TTS adapters |
| Future alerts | Email, WeChat and SMS only as Extensions |

TTS remains required under M-017. The task's Console/Web-first implementation
priority does not remove or weaken TTS acceptance.

## 7. Risk Register

Recorded Phase 7 risks:

- RISK-020 SQLite schema/migration drift.
- RISK-021 Streamlit runtime/session coupling.
- RISK-022 Camera/RTSP instability and stale frames.
- RISK-023 evidence growth and file/database reconciliation.
- RISK-024 alert/TTS failure blocking the event path.
- RISK-025 Phase 6 event identity loss at the persistence boundary.
- RISK-026 statistics divergence from event history.

Detailed controls are in
`docs/reports/phase-07/PHASE_7_RISK_REGISTER.md` and the authoritative
`docs/08_RISK_REGISTER.md`.

## 8. Implementation Order

| Subphase | Scope |
| --- | --- |
| 7-1 | Event storage, migrations, repositories, ingestion and query tests |
| 7-2 | Evidence snapshot rendering, paths, integrity and reconciliation |
| 7-3 | Streamlit dashboard plus Console/Web/TTS alerts |
| 7-4 | MP4/USB Camera/RTSP `VideoSource` adapters and M-007/M-008 integration |
| 7-5 | Real runtime validation from source through event, evidence and alert |
| 7-Release | Audit, release commit/tag and push only after all Phase 7 gates pass |

No subphase may skip database identity or evidence integrity to make the UI
work first.

## 9. Blockers

No blocker exists for the Phase 7-0 architecture freeze.

Carried blockers/conditions for later Phase 7 gates:

- no real Phase 5 checkpoint/inference/ByteTrack runtime evidence has been
  executed on the current governance host;
- no real Camera or RTSP source has been selected or validated;
- annotated video rendering is not implemented;
- Phase 7-0 does not authorize implementation, model loading, inference,
  dataset changes or training.

## 10. Validation

Commands run at task close:

```text
git diff --check
python -m pytest
python -m compileall .
```

Results:

- `git diff --check`: PASS. Only line-ending conversion warnings were emitted
  by Git; there were no whitespace errors.
- `python -m pytest`: PASS, `332 passed, 1 skipped`. The skip is the existing
  optional Torch evaluation reference test because Torch is not installed.
- `python -m compileall .`: PASS.

Charter task diff: PASS, empty against `HEAD`. The historical `charter-v1`
comparison still contains the previously approved M-004/M-005 status changes;
this task did not modify the Charter.

No commit, push or tag was performed.

## 11. Final Decision

Phase 7-0 is `COMPLETE FOR HUMAN REVIEW / DESIGN ONLY`.

Next allowed step:

```text
WAIT FOR PHASE 7-0 HUMAN REVIEW
```

After explicit authorization, the next implementation step is `P7-1 EVENT
STORAGE`.
