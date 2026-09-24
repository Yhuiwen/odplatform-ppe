# Phase 07 — Web & Alerts

## 1. 阶段目标

【LOCKED】SQLite + Snapshot + TTS + Streamlit。

## 2. 进入条件

- Phase 6 Gate 全部 PASS。
- 事件对象和截图触发点已稳定定义。

## 3. 当前子任务

Phase 7-0 Architecture Freeze、Phase 7-1 Event Storage、Phase 7-2
Evidence Snapshot 与 Phase 7-3 Dashboard & Alerts 已通过人工审核；
Phase 7-4 Camera / RTSP Input 和 Phase 7-5 Runtime Validation 也已通过
人工审核。基础 Phase 7 release commit 与 tag 已存在；Phase 7-6
finalization 已实现 TTS、service-owned monitoring loop 和 Streamlit
realtime 页面，并完成真实 runtime validation。M-007 annotated demo video
工具已实现，已完成 47/47 帧真实 MP4 渲染、帧数校验、hash 校验、输出完整性
验证和人工审核。Phase 7 final release closure 已完成，最终 annotated tag
为 `phase-7-release-freeze-complete`；Charter M-007 状态仍按治理规则保持
`待实现`，Phase 8 尚未开始。冻结设计见
`docs/designs/phase-07/PHASE_7_TARGET_ARCHITECTURE.md`、
`docs/designs/phase-07/PHASE_7_DATA_CONTRACTS.md` 和
`docs/reports/phase-07/PHASE_7_ARCHITECTURE_FREEZE_REPORT.md`。
Phase 7-1 实现与测试证据见
`docs/reports/phase-07/PHASE_7_1_EVENT_STORAGE_REPORT.md`。
Phase 7-2 实现与测试证据见
`docs/reports/phase-07/PHASE_7_2_EVIDENCE_SNAPSHOT_REPORT.md`。
Phase 7-3 实现与测试证据见
`docs/reports/phase-07/PHASE_7_3_DASHBOARD_ALERT_REPORT.md`。
Phase 7-4 实现与测试证据见
`docs/reports/phase-07/PHASE_7_4_CAMERA_RTSP_REPORT.md`。
Phase 7-5 运行证据见
`docs/reports/phase-07/PHASE_7_5_RUNTIME_VALIDATION_REPORT.md`。
Phase 7-6 运行验证结果见
`docs/reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_RESULT.md`。
Phase 7 release freeze 报告见
`docs/reports/phase-07/PHASE_07_FINAL_RELEASE_REPORT.md`。
M-007 annotated demo video 工具设计见
`docs/designs/phase-07/PHASE_7_M007_ANNOTATED_DEMO_VIDEO_DESIGN.md`。
M-007 实现与真实 MP4 验证报告见
`docs/reports/phase-07/PHASE_7_M007_IMPLEMENTATION_REPORT.md`。
Phase 7 Release Preparation Audit 证据见
`docs/reports/phase-07/PHASE_7_RELEASE_AUDIT_REPORT.md`。
Phase 7 final release、tag 与 remote verification 见
`docs/reports/phase-07/PHASE_07_RELEASE_COMPLETE_REPORT.md`。

冻结子阶段：

| Subphase | Scope | Status |
| --- | --- | --- |
| 7-0 | Architecture Freeze | COMPLETE / HUMAN REVIEW PASS |
| 7-1 | SQLite Event Storage | COMPLETE / HUMAN REVIEW PASS |
| 7-2 | Evidence Snapshot | COMPLETE / HUMAN REVIEW PASS |
| 7-3 | Dashboard and Alerts | COMPLETE / HUMAN REVIEW PASS |
| 7-4 | Camera / RTSP Input | COMPLETE / HUMAN REVIEW PASS |
| 7-4b | Monitoring integration and annotated video rendering | COMPLETE / REAL MP4 RUNTIME PASS / HUMAN REVIEW PASS |
| 7-5 | Runtime Validation | COMPLETE / HUMAN REVIEW PASS |
| 7-Release | Release audit and publication | FINAL RELEASE COMPLETE; base tag `phase-7-web-alert-platform-complete`; final freeze tag `phase-7-release-freeze-complete` |
| 7-6 | Release finalization: TTS, monitoring loop and real-source validation | COMPLETE / RUNTIME VALIDATION PASS / HUMAN REVIEW PASS |

Phase 7-4 implements the source adapter layer only: MP4, USB Camera and RTSP
share one `VideoSource` lifecycle and observable status contract. It does not
open a real camera or stream during its own review, run reconnect
orchestration, integrate a monitoring loop, render annotations, enforce
retention or implement TTS. Phase 7-5 later validates the integrated MP4
runtime path, all four dashboard pages and a real USB Camera lifecycle, but
does not run real RTSP. M-015 through M-020 and deferred M-007/M-008 remain
`待实现` in the locked Charter until their full acceptance criteria are met.
The historical release audit confirmed the repository and documentation
boundaries. The base release was subsequently published as commit
`a30b73c080c18d010fbaa08642868e86acb68022` and tag
`phase-7-web-alert-platform-complete`. Phase 7-6 finalization and the M-007
annotated demo video implementation subsequently received human review PASS
and were included in the final Phase 7 release closure. M-007 remains
`待实现` in the locked Charter until full Phase 9 acceptance.


### Deferred MUST delivery ownership (ADR-019)

Phase 7 owns M-007 annotated video rendering through video page/service
integration and M-008 live-input integration for real-time monitoring.
These are deferred MUST implementations from Phase 4, not Extensions.
Deliver and verify them before accepting the corresponding page integrations;
retain the Charter's Camera OR RTSP criterion and observable failure behavior.
Phase 9 performs final full-Charter acceptance. This allocation does not change
this phase's locked goal or Phase 7-1's storage-only scope.

## 4. 实现设计

Repository 隔离数据库访问；事件与截图文件保持一致引用；TTS 失败不阻塞
事件写入；Streamlit 页面只调用服务层，不内嵌业务算法。

Phase 7-0 freezes:

- SQLite first with `workers`, `events`, `snapshots`, `statistics` and
  versioned migrations.
- One `VideoSource` contract for MP4, USB Camera and RTSP. Only source
  adapters may call `cv2.VideoCapture`; no silent fallback or synthetic frame.
- Evidence path
  `artifacts/events/snapshots/YYYYMMDD/event_<event-id>.jpg`, with relative
  path, SHA256 and image metadata recorded in SQLite.
- A separate persisted-event DTO with
  `id`, `timestamp`, `track_id`, `type`, `confidence`, `snapshot`, `status`.
  The frozen Phase 6 JSONL wire contract remains unchanged at exactly
  `type`, `track_id`, `confidence`, `timestamp`.
- Console and Web alert adapters as first implementation priority, plus TTS
  as a required M-017 adapter. Email, WeChat and SMS remain future Extension
  adapters.
- Streamlit for V1. FastAPI + Vue is a future replacement path, not current
  scope.
- Event persistence precedes alert fan-out. Alert/TTS failure is isolated and
  must not corrupt or block event history.

Phase 7-1 implementation:

- `core/schemas/events.py` defines the separate persisted-event projection,
  internal storage row, query contract and lifecycle status vocabulary.
- `infra/database/migrations/0001_phase7_events.sql` creates the frozen
  `schema_migrations`, `workers`, `events`, `snapshots` and `statistics`
  schema with required indexes and checks.
- `Database` owns SQLite configuration, `PRAGMA foreign_keys = ON`, WAL,
  busy timeout, short `BEGIN IMMEDIATE` transactions and migration execution.
- `EventRepository` provides parameterized insert/get/query/status operations,
  explicit duplicate handling and idempotent `event_id` ingestion.
- `EventIngestService` preserves the Phase 6 `event_id`, stores the original
  numeric source timestamp separately and assigns a UTC wall-clock display
  timestamp.

Phase 7-2 implementation:

- `SnapshotStorage` normalizes supplied image payloads to JPEG, writes through
  a temporary file, atomically replaces the final path, computes SHA256 and
  records width, height and MIME type.
- The frozen relative path is
  `YYYYMMDD/event_<event-id>.jpg` below the configured evidence root. The
  database never receives an absolute path.
- `SnapshotRepository` persists and queries `SnapshotReference` metadata only;
  it does not encode, render, inspect or modify image files.
- `SnapshotService` first verifies that the Phase 6 `event_id` exists, reuses
  identical evidence idempotently, rejects conflicting replacement evidence
  and associates the verified relative path through the existing
  `EventRepository` snapshot join.
- A metadata-write failure after a successful file write remains an orphan
  candidate; Phase 7-2 does not silently delete evidence.

Phase 7-3 implementation:

- `EventQueryService` is the read-only dashboard boundary for event filtering,
  pagination, source discovery, statistics and verified evidence projection.
  It delegates to repositories and never lets a page execute SQL directly.
- `web/dashboard_support.py` assembles SQLite, snapshot and alert services
  without opening the database during import. Streamlit pages call only this
  support boundary and do not import inference, tracking, association or
  compliance implementations.
- `web/Home.py` explicitly registers Overview, Event Explorer, Evidence Viewer
  and Statistics. Overview shows recent events and event mix; Event Explorer
  supports type/status/source/track/date filters and pagination; Evidence
  Viewer verifies SHA256/dimensions before display; Statistics uses the same
  validated filter contract as event queries.
- `core/schemas/alerts.py` and `core/alerts/interfaces.py` define the stable
  `AlertMessage`, `AlertResult`, `AlertStatus` and `AlertAdapter` contracts.
  `services/alert_service.py` performs ordered fan-out with failure isolation.
- `infra/alerts/console.py` writes deterministic JSON lines to an injectable
  sink. `infra/alerts/web.py` publishes to a bounded in-process history for
  dashboard visibility. Both adapters are idempotent by the preserved Phase 6
  `event_id`.

Phase 7-4 implementation:

- `SourceType`, `SourceState`, `SourceMetadata` and `SourceStatus` are
  model-independent contracts in `core/schemas/video.py`.
- `VideoSource` defines one `open/read/status/close` lifecycle. `read()`
  returns project-owned `FrameData` or `None` at a finite end; live-source
  disconnect states raise structured source errors instead of returning a
  synthetic frame.
- `MP4VideoSource` delegates to the existing sequential `VideoReader` and
  preserves its frame order and timestamps.
- `USBCameraSource` accepts only a non-negative integer index. It owns capture
  creation, metadata extraction, read failure state and release cleanup.
- `RTSPVideoSource` accepts only `rtsp://` or `rtsps://`, applies bounded
  timeout values, strips credentials/query text from status and raises an
  observable disconnect error when frames stop.
- Business, dashboard and script modules contain no direct
  `cv2.VideoCapture` call; capture access is confined to source adapters.

Phase 7-5 implementation:

- `scripts/run_phase7_runtime_validation.py` composes the existing MP4
  `VideoSource`, inference service, person-only ByteTrack adapter,
  Person-PPE association adapter, compliance/event engine, Phase 6 JSONL,
  SQLite ingestion, snapshot service, event query service and Console/Web
  alerts. It changes no upstream logic.
- `scripts/validate_phase7_dashboard_runtime.py` executes Overview, Event
  Explorer, Evidence Viewer and Statistics with Streamlit `AppTest` against
  the run-specific SQLite database and snapshot root.
- Run `20260923T131111Z` processed 47/47 frames on CPU, produced 77
  detections, 66 track updates, one unknown association, 66 compliance
  findings and one persisted `PPE_UNKNOWN` event. The event JSONL, SQLite
  record, snapshot file and dashboard query all preserved the original Phase 6
  `event_id`.
- The frozen checkpoint, processed dataset, training configuration and
  inference configuration hashes were unchanged. Runtime evidence remains
  below Git-ignored `artifacts/validation/P7-5/`.

Phase 7 release audit:

- Audited the complete uncommitted Phase 7 change set, staged area, ignored
  paths, large files, generated artifacts, credentials/tokens and
  publication file boundaries.
- Confirmed that the pending change set contains source, tests, configuration
  and documentation only, with no model, media, database, snapshot, archive
  or environment file.
- Confirmed that model, dataset, validation and generated event paths remain
  covered by `.gitignore` and are outside the pending release set.
- Synchronized Phase 7 documentation so 7-0 through 7-5 are recorded as
  human-reviewed PASS and 7-Release is audit-complete but not published.

Phase 7-6 release finalization:

- `TTSService` uses a lazy optional `pyttsx3` backend and an injectable
  speaker. `TTSAlertAdapter` preserves event idempotency, applies a
  per-track/type cooldown and returns structured failed/skipped results
  without blocking event persistence.
- `MonitoringService` owns one background worker per session, reuses the
  existing inference, person-only tracker, association, compliance, event,
  SQLite ingest, snapshot and alert boundaries, and exposes immutable status
  plus recent events for Streamlit.
- `web/pages/1_实时监控.py` starts and stops the service, refreshes status
  periodically, renders the latest frame and shows detection/event/alert
  counters. The page does not import or invoke detector, tracker, association
  or compliance implementations directly.
- `configs/monitoring.yaml` freezes sequential processing, no frame skipping,
  no batch inference, no local fallback and persistence-before-alert.
  `configs/p7_6_validation.yaml` defines real Camera/RTSP validation with
  `execution_enabled: false`, frozen checkpoint identity and Git-ignored
  evidence.
- Phase 7-6 tests pass with an injected speaker and fake source/pipeline
  boundaries. The initial implementation review used the governance host,
  which had no Streamlit, Torch, Ultralytics or `pyttsx3`. A subsequent
  runtime validation used an isolated environment and executed browser
  Streamlit, native Windows SAPI TTS and a controlled local MediaMTX RTSP
  stream; see
  `docs/reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_RESULT.md`.

Phase 7 release freeze preparation:

- The release audit confirms the published base release identity and the
  P7-6 runtime-validation boundary. The preparation change set remains
  uncommitted.
- The M-007 annotated demo video tool design freezes a future offline MP4
  pipeline using `VideoReader`, `InferenceService`, deterministic frame
  rendering and an atomic MP4 writer.
- The design output contract is `demo.mp4`, `run.json`, `frames.jsonl`,
  `summary.json` and `renderer.log` below
  `artifacts/inference/annotated/<run-id>/`.
- The design excludes tracking, association, compliance, alerts, Camera/RTSP,
  E-005 clip retention, model download and any core-pipeline modification.
- M-007 implementation adds `AnnotatedFrameRenderer`,
  `AnnotatedVideoWriter` and `AnnotatedVideoService` without changing the
  frozen detector, video reader, schemas or upstream Phase 5/6 modules.
- The writer stages the complete five-file output directory, verifies the
  decoded MP4 frame count and dimensions, then publishes by one directory
  rename. A failed run removes its staging directory and leaves no partial
  `demo.mp4`.
- A real CPU-only run rendered all 47 source frames to 47 output frames at
  1280x720 with the frozen checkpoint. The output SHA256 is
  `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949`.
- M-007 remains `待实现` in the locked Charter until human review and Phase 9
  acceptance; the implementation and runtime evidence are not a Charter
  status change.

## 5. 测试要求

- SQLite 创建、写入、读取、重启持久化和查询过滤测试。
- P7-1 已覆盖 schema/migration checksum、数据库 transaction rollback、
  repository duplicate/conflict、查询过滤、状态更新、重启持久化和 Phase 6
  wire compatibility。
- P7-2 已覆盖 JPEG 保存、UTC 日期路径、SHA256/尺寸、重复证据幂等、冲突
  拒绝、缺失事件拒绝，以及 Phase 6 `event_id` 到 SQLite 和真实文件的
  integration。
- P7-3 已覆盖 dashboard query filters/statistics、verified evidence view、
  page/service import boundary、alert fan-out、duplicate delivery、adapter
  failure isolation 和 schema serialization。
- P7-4 已覆盖 mock source protocol、MP4 lifecycle/order/EOF、USB open/read/
  release/disconnect、RTSP redaction/timeout、invalid input、idempotent
  release 和 business-layer capture boundary。
- P7-5 已验证 MP4 -> detection -> tracking -> association -> compliance ->
  JSONL -> SQLite -> snapshot -> dashboard -> alert 的集成路径，并额外执行
  真实 USB Camera open/read/close、Streamlit 四页 AppTest 和本地 server
  health/root HTTP check。真实 RTSP 未执行。
- P7-Release audit 已覆盖 staged/unstaged/untracked change set、generated
  artifact boundary、大文件、secret/token、documentation consistency，
  并复跑完整 repo tests、compileall 和 diff checks。
- 截图路径与事件记录一致性测试。
- TTS 成功/失败隔离测试。
- 页面服务交互、空状态、断流和停止行为测试。

## 6. Gate

| Gate | Requirement |
| --- | --- |
| P7-G1 | SQLite 事件持久化与历史查询通过 |
| P7-G2 | 截图留证可追踪且文件真实存在 |
| P7-G3 | TTS 实时告警有冷却且失败不破坏主流程 |
| P7-G4 | 实时监控、历史查询和数据大屏满足验收 |

Phase 7-0 architecture-freeze gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-0-G1 | Current released architecture audited without code changes | PASS |
| P7-0-G2 | Phase 7 target architecture and module boundaries frozen | PASS |
| P7-0-G3 | Detection/tracking/association/compliance/persisted-event contracts frozen | PASS |
| P7-0-G4 | SQLite, snapshot, dashboard, source and alert technology decisions recorded | PASS |
| P7-0-G5 | Phase 7 risk register recorded | PASS |
| P7-0-G6 | 7-0 through 7-Release implementation order defined | PASS |
| P7-0-G7 | No model, dataset, training, inference, tracking or event-engine change | PASS |
| P7-0-G8 | No commit, push or tag; validation commands complete | PASS |

Phase 7-1 event-storage gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-1-G1 | SQLite schema, foreign keys, indexes and migration version implemented | PASS |
| P7-1-G2 | Migration is idempotent and checksum drift is detected | PASS |
| P7-1-G3 | Event repository and query/status operations are restart-persistent | PASS |
| P7-1-G4 | `EventIngestService` preserves Phase 6 event identity and source time | PASS |
| P7-1-G5 | Four-field Phase 6 JSONL wire contract remains unchanged | PASS |
| P7-1-G6 | Unit and integration tests pass | PASS |
| P7-1-G7 | No model, dataset, mapping, training, evaluation or Phase 5/6 code changed | PASS |
| P7-1-G8 | No commit, push or tag; review waits for human approval | PASS |

Phase 7-2 evidence-snapshot gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-2-G1 | Atomic evidence file storage is implemented below the frozen root | PASS |
| P7-2-G2 | Snapshot metadata and relative path contract are immutable | PASS |
| P7-2-G3 | Event association preserves the Phase 6 `event_id` | PASS |
| P7-2-G4 | Duplicate and conflicting evidence behavior is deterministic | PASS |
| P7-2-G5 | Unit and integration tests pass | PASS |
| P7-2-G6 | No model, dataset, training, inference, tracking or Phase 6 contract change | PASS |
| P7-2-G7 | No commit, push or tag; human review remains required | PASS |

Phase 7-3 dashboard-and-alert gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-3-G1 | Streamlit page sources and navigation exist | PASS |
| P7-3-G2 | Dashboard reads through the event-query service boundary only | PASS |
| P7-3-G3 | Event filtering, pagination and statistics are implemented | PASS |
| P7-3-G4 | Evidence view verifies metadata and file integrity | PASS |
| P7-3-G5 | Console and Web alerts share one idempotent adapter contract | PASS |
| P7-3-G6 | Unit and integration tests pass | PASS |
| P7-3-G7 | Upstream model, dataset, training and Phase 6 contract remain unchanged | PASS |
| P7-3-G8 | No commit, push or tag; human review remains required | PASS |

Phase 7-4 camera-and-rtsp-input gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-4-G1 | Unified VideoSource lifecycle exists | PASS |
| P7-4-G2 | MP4 adapter reuses the frozen reader | PASS |
| P7-4-G3 | USB Camera lifecycle and failures are observable | PASS |
| P7-4-G4 | RTSP source identity is redacted and timeouts are bounded | PASS |
| P7-4-G5 | Business code does not call cv2.VideoCapture directly | PASS |
| P7-4-G6 | Required tests pass | PASS |
| P7-4-G7 | Frozen upstream contracts and assets remain unchanged | PASS |
| P7-4-G8 | Real runtime and M-008 acceptance are not overclaimed | PASS |

Phase 7-5 runtime-validation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-5-G1 | Integrated MP4 smoke path completes | PASS |
| P7-5-G2 | Event passes Phase 6 JSONL, SQLite and snapshot identity/integrity checks | PASS |
| P7-5-G3 | Dashboard pages execute against runtime evidence | PASS |
| P7-5-G4 | Real USB Camera lifecycle passes | PASS |
| P7-5-G5 | Console and Web alert adapters deliver the preserved event identity | PASS |
| P7-5-G6 | Real RTSP and TTS are not overclaimed | PASS |
| P7-5-G7 | Frozen model/data/training/inference assets remain unchanged | PASS |
| P7-5-G8 | Phase 7 release remains waiting for human review | PASS |

Phase 7 release-preparation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-REL-G1 | Repository change set is audit complete | PASS |
| P7-REL-G2 | No forbidden model, media, database or credential artifact is pending | PASS |
| P7-REL-G3 | Generated evidence and asset paths remain outside Git | PASS |
| P7-REL-G4 | Phase 7 documentation consistently records 7-0 through 7-5 PASS | PASS |
| P7-REL-G5 | Full repository tests, compileall and diff checks pass | PASS |
| P7-REL-G6 | Publication remains unauthorized | PASS |

Phase 7-6 release-finalization gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-6-G1 | TTS adapter implemented with cooldown and failure isolation | PASS |
| P7-6-G2 | Service-owned MP4/USB/RTSP monitoring loop implemented | PASS |
| P7-6-G3 | Streamlit realtime page uses service boundaries only | PASS |
| P7-6-G4 | Real Camera/RTSP validation design and evidence policy documented | PASS |
| P7-6-G5 | Full repository tests, compileall and diff checks pass | PASS |
| P7-6-G6 | Frozen model, dataset, training and upstream core modules unchanged | PASS |
| P7-6-G7 | No commit, new tag or push performed by this task | PASS |
| P7-6-G8 | Real RTSP runtime evidence recorded | PASS |

Phase 7-6 result: `COMPLETE / RUNTIME VALIDATION PASS / HUMAN REVIEW PASS`.
Runtime evidence covers MP4, real USB Camera, native TTS, browser Streamlit
and a controlled local RTSP stream. Remote RTSP, reconnect/backoff and
long-running recovery remain unverified. The reviewed change set was included
in the final Phase 7 release closure.

Phase 7 release-freeze gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-FR-G1 | Phase 7 subphase and base-release identity are audited | PASS |
| P7-FR-G2 | P7-6 runtime evidence remains bounded and linked | PASS |
| P7-FR-G3 | M-007 annotated demo video tool design is complete | PASS |
| P7-FR-G4 | M-007 implementation is not overclaimed | PASS |
| P7-FR-G5 | Frozen assets remain unchanged | PASS |
| P7-FR-G6 | Repository validation passes | PASS |
| P7-FR-G7 | No commit, tag, push or Phase 8 action is performed | PASS |
| P7-FR-G8 | Locked Charter body remains unchanged | PASS; the requested status note was withheld by the hash guard, so M-007 remains `待实现` |

Phase 7 Release Freeze result: `PASS / HUMAN REVIEW PASS`.

Phase 7 M-007 annotated demo video gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-M007-G1 | Frozen checkpoint and inference contract are verified | PASS |
| P7-M007-G2 | Local MP4 input is processed sequentially without frame skipping | PASS |
| P7-M007-G3 | Deterministic clipped boxes and labels are rendered | PASS |
| P7-M007-G4 | Source, processed, written and decoded output frame counts are equal | PASS |
| P7-M007-G5 | Final output is published by atomic directory rename | PASS |
| P7-M007-G6 | Failure paths remove staging output and leave no partial demo | PASS |
| P7-M007-G7 | Unit tests and real MP4 output-integrity validation pass | PASS |
| P7-M007-G8 | Charter, model, dataset, training and Phase 5/6 modules remain unchanged | PASS |

Phase 7 M-007 result: `COMPLETE / REAL MP4 VALIDATION PASS / HUMAN REVIEW
PASS`. The reviewed implementation was included in the final Phase 7 release
closure.

## 7. 已知问题

并发写入、证据清理和长期运行稳定性尚待设计验证。

Additional frozen risks:

- SQLite schema or migration drift.
- Streamlit rerun/session coupling to long-running processing.
- USB Camera/RTSP timeout, disconnect and stale-frame behavior.
- evidence growth and database/file reconciliation.
- alert/TTS failure isolation.
- Phase 6 `event_id` not being present in the JSONL wire record.
- statistics divergence from the authoritative event table.
- Phase 7-1 does not render or write snapshot files; only schema and event
  persistence are implemented.
- Phase 7-2 saves caller-supplied frame/image evidence. It does not draw
  bounding boxes or render the deterministic annotation layer described for
  the later full evidence workflow.
- Snapshot/database reconciliation is manual at this stage. Failed metadata
  insertion can leave a retained orphan candidate, and no cleanup or retention
  action is authorized.
- Dashboard statistics query the authoritative `events` table directly; the
  rebuildable `statistics` cache table still has no aggregation writer.
- Streamlit, Pandas and Plotly are not installed on the current governance
  host. Dashboard source and service contracts were tested, but actual browser
  rendering and visual interaction were not executed.
- `EventQueryService.snapshot_events()` currently pages events before filtering
  to those with snapshot references. This is acceptable for the first
  dashboard slice but requires a repository-level predicate before large
  evidence sets are supported.
- Phase 7-4 source adapters are unit-tested with injected capture doubles.
  At Phase 7-4 review time, real USB Camera and RTSP streams were not opened.
  Phase 7-5 subsequently opened a real USB Camera successfully, but real
  RTSP, reconnect/backoff and stale-frame detection remain pending.
- The existing offline `VideoInferenceService` still uses `VideoReader`
  directly; monitoring-service integration with `VideoSource` belongs to the
  next subphase and was intentionally not changed in Phase 7-4.
- Phase 7-5 used Python `3.12.1`, while frozen `INF-RUNTIME-001` records
  Python `3.10.4`. The runtime was not re-frozen; this remains a release
  limitation.
- Phase 7-5 dashboard and alert validation used a short one-event runtime
  history. It does not establish large-history performance, retention
  behavior or long-running stability.
- TTS is implemented and tested with an injected speaker, and Phase 7-6
  executed a native Windows SAPI call through `pyttsx3`. This verifies the
  backend call path, not audio quality or long-running speech delivery. A
  controlled local RTSP stream was validated; remote RTSP, reconnect/backoff
  and stale-frame recovery remain untested. M-007/M-008 final acceptance
  remains pending. M-007 annotated rendering, output frame-count verification
  and real output inspection are implemented and passed one short public-domain
  MP4. Long-duration throughput, codec compatibility across other hosts and
  annotation quality review remain open.

Real Camera/RTSP and annotated video evidence is required before M-007/M-008
Phase 7 integration acceptance. Phase 9 remains the final Charter acceptance
owner.

## 8. 开发记录

- 2026-09-23: Phase 7 M-007 Annotated Demo Video implementation completed for
  human review. Added deterministic frame rendering, staged atomic MP4 output,
  frame-count verification, metadata artifacts, rollback behavior and a
  structured CLI. A real frozen-checkpoint MP4 run processed 47/47 frames and
  produced a 47-frame 1280x720 output with SHA256
  `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949`.
  No model, dataset, training, Phase 5/6 or Charter change occurred. No commit,
  tag or push was performed; human review remains pending.
- 2026-09-23: Phase 7 Release Freeze Preparation completed for human review.
  Audited the current Phase 7 status and frozen hashes, added the final
  release-freeze candidate report, and completed the M-007 annotated demo
  video tool design. M-007 remains `待实现`; no annotated video was rendered.
  No model, dataset, training, inference, core pipeline, commit, tag or push
  action occurred.
- 2026-09-23: Phase 7 Release Preparation Audit completed for human review.
  Audited the complete uncommitted change set, generated-artifact and secret
  boundaries, large files and documentation consistency. Confirmed 7-0
  through 7-5 as human-reviewed PASS and 7-Release as audit complete but not
  published. No commit, push or tag.
- 2026-09-23: Phase 7-5 Runtime Validation completed for human review. Added
  orchestration/validation scripts and a Git-ignored runtime evidence set.
  Verified MP4 through inference, tracking, association, compliance, JSONL,
  SQLite, snapshot, dashboard and Console/Web alerts; verified a real USB
  Camera lifecycle and all four Streamlit pages. Real RTSP, TTS, annotated
  rendering and M-007/M-008 acceptance remain pending. Phase 7 release is
  waiting. No commit, push or tag.
- 2026-09-23: Phase 7-4 Camera / RTSP Input completed for human review. Added
  the unified VideoSource protocol, MP4/USB Camera/RTSP adapters, source
  metadata/status contracts, connection failure handling, URI redaction and
  release cleanup tests. No real device or stream was opened; M-008 remains
  pending. No commit, push or tag.
- 2026-09-23: Phase 7-3 Dashboard & Alerts completed for human review. Added
  the read-only event query/statistics service, dashboard runtime support,
  Overview/Event Explorer/Evidence Viewer/Statistics Streamlit sources,
  Console/Web alert adapters and focused tests. Streamlit/Pandas/Plotly are
  not installed on this host, so browser rendering was not executed. TTS,
  Camera/RTSP, annotation rendering, reconciliation automation and retention
  remain pending. No commit, push or tag.
- 2026-09-23: Phase 7-2 Evidence Snapshot completed for human review. Added
  atomic JPEG evidence storage, UTC date partitions, relative POSIX paths,
  SHA256/dimension verification, separate snapshot metadata repository,
  idempotent/conflicting duplicate policy, event association service and
  unit/integration tests. Phase 6 event IDs and JSONL contract remain
  unchanged. Annotation rendering, reconciliation automation, dashboard,
  alerts/TTS and Camera/RTSP remain pending. No commit, push or tag.
- 2026-09-23: Phase 7-1 Event Storage completed for review. Added the
  persisted-event schema, SQLite migration/checksum mechanism, repository,
  event ingestion service, focused unit tests and a restart-persistence
  integration test. Phase 6 JSONL and all frozen model/data/training assets
  remain unchanged. Snapshot files, dashboard, alerts/TTS and Camera/RTSP
  remain pending. No commit, push or tag.
- 2026-09-23: Phase 7-0 Architecture Freeze completed for review. Added the
  pre-read, architecture audit, target architecture, data contracts, risk
  register and freeze report. Froze SQLite-first persistence, snapshot
  evidence, Streamlit V1, the `VideoSource` boundary, Console/Web/TTS alert
  adapters and the persisted-event projection while preserving the Phase 6
  JSONL contract. No implementation, model, dataset, training or upstream
  pipeline change occurred. No commit, push or tag.
- 2026-09-21: 计划建立，未开始实现。
