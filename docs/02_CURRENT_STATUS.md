# Current Status

This is the single entry point for the latest project state. Historical
implementation and validation details are preserved in the
[Phase 4 → Phase 5 handover](worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md)
and the linked phase reports. Earlier snapshots may describe past pending
reviews; the statuses below reflect the current accepted records.

## Current Phase

- Phase 7 COMPLETE / RELEASED — Web & Alerts. Base commit
  `a30b73c080c18d010fbaa08642868e86acb68022` carries annotated tag
  `phase-7-web-alert-platform-complete`; final release closure publishes
  annotated tag `phase-7-release-freeze-complete`. Phase 7-0 through Phase 7-6
  are human-reviewed PASS. Phase 7-6 adds the TTS alert adapter, a
  service-owned MP4/USB/RTSP monitoring loop and the Streamlit realtime page;
  MP4, USB Camera, native TTS, browser Streamlit and controlled local RTSP
  validation all passed. M-007 annotated demo video is implemented, validated
  on a real 47/47-frame MP4 and human-reviewed PASS. M-007 remains `待实现`
  in the locked Charter pending Phase 9 acceptance. Remote RTSP reconnect
  behavior, reconciliation automation and retention remain pending.
  M-015 through M-020 remain `待实现` in the locked Charter until full
  acceptance. Phase 8 is not started.
- Phase 6 COMPLETE / RELEASED — PPE Compliance Event Engine. Release tag
  `phase-6-compliance-event-engine-complete` targets
  `e24e31ae635e5d5cd1129a9fb519a59b7014f802`.
- Phase 5 COMPLETE / RELEASED — Tracking & Association. Release tag
  `phase-5-tracking-association-complete` targets
  `6da6213f0cc541765f231c81b4264a98f01d5f4a`.
- P5-0, P5-1 and P5-2 are human-reviewed PASS. P5-3 synthetic pipeline
  validation is PASS. The frozen-checkpoint/video runtime validation is
  prepared with an execution-disabled config and passed static preflight, but
  is `BLOCKED / NOT RUN` because this host has no `torch` or `ultralytics`.
- Historical state: Phase 5 IN PROGRESS during P5-0 through the final audit.
  P5-3-G5 was originally recorded as `BLOCKED / NOT RUN`. A subsequent
  explicit human release authorization created the annotated tag
  `phase-5-tracking-association-complete` at commit
  `6da6213f0cc541765f231c81b4264a98f01d5f4a`; the current documentation is
  now synchronized to `COMPLETE / RELEASED`.
- Phase 4 remains `Offline Inference COMPLETE` for its released offline scope.
- Current next allowed step: `PHASE 8 NOT STARTED / WAIT FOR AUTHORIZATION`.

## Last Completed

- Phase 2 Training: `已经实现`; EXP-001 baseline training completed using its
  single authorized run. M-004：已经实现.
- Phase 3 Evaluation: `已经实现`; model comparison, selection and independent
  evaluation were completed and human review passed. M-005：已经实现.
- Phase 4 Offline Inference: `已经实现` for the scope in ADR-018; offline release
  gates are PASS. Full M-006/M-007 acceptance was not implied by that release.
- Phase 5 Tracking & Association: `已经实现（COMPLETE / RELEASED）`; P5-0 froze `TrackResult`,
  `AssociationResult`, person-only ByteTrack boundaries and unknown-safe
  containment/IoU policy. P5-1 implements the person-only ByteTrack adapter
  behind that boundary. P5-2 implements conservative Person-PPE association
  with explicit `unknown`. P5-3 validates the complete adapter composition
  with deterministic synthetic frames; at the Phase 5 release point, real
  runtime and integrated video verification were blocked by missing runtime
  dependencies. Phase 7-5 later executed one real MP4 path with Ultralytics
  ByteTrack and the association adapter, so M-009 and M-010 now have
  `IMPLEMENTED / Phase 7-5 Runtime Evidence Recorded / Charter Acceptance
  Pending` status. The locked Charter statuses remain `待实现` until full
  acceptance is reviewed. The release tag records the implemented,
  synthetically validated and human-authorized Phase 5 package; it does not
  retroactively convert the historical P5-3-G5 block into a Phase 5 PASS.
- Phase 6 PPE Compliance Event Engine: `已经实现（COMPLETE / RELEASED）`;
  `AssociationResult -> ComplianceInput -> ComplianceResult ->
  ComplianceEvent` is implemented with conservative Helmet/Vest/Unknown
  rules, five-frame and one-second confirmation, event deduplication,
  recovery, cooldown and JSONL storage. M-011 through M-014 remain
  `待实现` until the full Charter acceptance evidence is reviewed.
- Phase 7-0 Architecture Freeze: `COMPLETE / HUMAN REVIEW PASS`.
  The audit, target architecture, data contracts, technology decision, risk
  register and implementation order are recorded. No SQLite, snapshot,
  Streamlit, Camera/RTSP or alert implementation was created.
- Phase 7-1 Event Storage: `COMPLETE / HUMAN REVIEW PASS`. Added the persisted
  event DTO, SQLite connection/transaction boundary, checksummed migration
  `0001_phase7_events`, event repository with query/status support and
  idempotent `EventIngestService`. Phase 6 JSONL remains unchanged. Snapshot
  files remained pending at this review point.
- Phase 7-2 Evidence Snapshot: `COMPLETE / HUMAN REVIEW PASS`. Added atomic JPEG
  storage below `artifacts/events/snapshots/YYYYMMDD/`, relative-path and
  SHA256/dimension metadata, a separate snapshot repository, idempotent
  duplicate policy and event association through the existing persisted-event
  query projection.
- Phase 7-3 Dashboard & Alerts: `COMPLETE / HUMAN REVIEW PASS`. Added a read-only
  event query/statistics service, four Streamlit page sources, a verified
  evidence viewer, explicit navigation, Console and Web alert adapters, and
  service-boundary tests. Streamlit, Pandas and Plotly are not installed on
  this host, so actual browser rendering was not executed. TTS, Camera/RTSP,
  annotation rendering, reconciliation automation and retention remain
  pending.
- Phase 7-4 Camera/RTSP Input: `COMPLETE / HUMAN REVIEW PASS`. Added
  `SourceMetadata`/`SourceStatus`, the `VideoSource` lifecycle protocol and
  MP4, USB Camera and RTSP adapters. Status transitions, connection failures,
  release cleanup and RTSP URI redaction are tested with injected captures.
  At Phase 7-4 review time, real Camera/RTSP devices or streams were not
  opened; M-008 remains `待实现`. Phase 7-5 later opened a real USB Camera,
  but no real RTSP endpoint.
- Phase 7-5 Runtime Validation: `COMPLETE / HUMAN REVIEW PASS`. Executed one
  CPU-only MP4 smoke path with the frozen checkpoint and changed the event
  path through inference, tracking, association, compliance, JSONL, SQLite,
  snapshot evidence, dashboard queries and Console/Web alert delivery.
  Processed 47/47 frames, generated one `PPE_UNKNOWN` event, verified one
  snapshot and found no runtime errors. Streamlit AppTest passed all four
  pages, a local Streamlit health/root check passed, and a real USB Camera
  open/read/close lifecycle passed. Real RTSP, TTS, annotated rendering and
  M-007/M-008 final acceptance remain pending.
- Phase 7 Release Preparation Audit: `AUDIT COMPLETE FOR HUMAN REVIEW`.
  Verified the uncommitted release change set, empty staged area, Git-ignore
  boundary, generated-artifact exclusions, absence of model/media/database
  files, credential/token scan, documentation status consistency and the
  complete repository test baseline. Publication remains unauthorized.
- Phase 7-6 Release Finalization: `COMPLETE / RUNTIME VALIDATION PASS /
  HUMAN REVIEW PASS`. Added the lazy, injectable TTS service and cooldown/isolation
  adapter; added `MonitoringService`, session-scoped dashboard assembly and a
  realtime Streamlit page for MP4, USB Camera and RTSP. Runtime evidence now
  includes MP4 regression, real USB Camera, native `pyttsx3`/Windows SAPI,
  browser-driven Streamlit pages and a real local MediaMTX RTSP stream. The
  subsequent authorized release closure committed and published this work.
- Phase 7 Release Freeze Preparation: `COMPLETE / HUMAN REVIEW PASS`. Audited Phase 7 subphase status, the base release identity,
  the P7-6 runtime evidence and frozen asset hashes. Added the M-007 annotated
  demo video tool design and the final release report. The Charter M-007
  status remains `待实现`; no model, dataset, training, inference or core
  pipeline was changed. The authorized final release closure followed.
- Phase 7 M-007 Annotated Demo Video: `COMPLETE / REAL MP4 RUNTIME PASS /
  HUMAN REVIEW PASS`. Added deterministic frame annotation,
  staged atomic MP4 writing, decoded frame-count and dimension verification,
  metadata artifacts and rollback. A frozen-checkpoint CPU run processed
  47/47 frames into a 47-frame 1280x720 MP4 with SHA256
  `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949`.
  The Charter M-007 status remains `待实现`; the authorized Phase 7 release
  closure committed and published the reviewed implementation.
- Phase 1 Data remains `实现中` in the Master Plan. M-001, M-002 and M-003
  remain `待实现` in the Charter; completed data substeps are not a claim of
  their final acceptance.

## Completed Capabilities

- Frozen `CSS-PPE-10-V1` data artifact, Strategy C mapping and processed
  dataset are recorded; data quality was assessed without source mutation.
- EXP-001 YOLO11n training and Phase 3 test evaluation/model selection have
  reproducible evidence. Selected release checkpoint: EXP-001 `best.pt`.
- Single-image structured inference through `InferenceService` and
  `YOLODetector`; real-image validation used the frozen checkpoint.
- Sequential local MP4 structured inference through `VideoReader` and
  `VideoInferenceService`; real validation processed all 47/47 source frames.
- P5-1 person-only ByteTrack adapter: lazy backend isolation, class-0 filtering,
  confidence filtering, fail-closed errors and project-owned `TrackResult`
  output. Adapter behavior is tested with an injected backend; real
  Ultralytics ByteTrack execution is not verified.
- P5-2 conservative Person-PPE association: containment `0.50`, IoU `0.10`,
  confidence `0.25`, ambiguity margin `0.10`, deterministic ranking and
  explicit `unknown`. Synthetic tests cover single/multiple people, wrong
  candidates, ambiguity, missing PPE and empty input; real video integration
  is not verified.
- P5-3 integrated synthetic validation: the full
  `DetectionResult -> TrackResult -> AssociationResult` adapter chain passes
  single-person, multi-person, PPE-present, missing-PPE and ambiguous cases.
  A validation-only config and script prepare frozen checkpoint/video
  execution and report dependency readiness without loading the model.
- P5 release final audit: completed evidence, frozen identities, limitations
  and gates are consolidated in the Phase 5 final audit report. M-009 and
  M-010 are implemented at the audit layer. The historical P5-3-G5 block
  remains recorded, while the later explicit release authorization is
  recorded by `phase-5-tracking-association-complete`.
- Phase 6 compliance/events: Project-owned `ComplianceInput`,
  `ComplianceResult` and `ComplianceEvent` contracts; conservative
  Helmet/Vest/Unknown rules; five-frame/one-second temporal confirmation;
  active-cycle deduplication; recovery/cooldown; and Git-ignored JSONL event
  storage are implemented. The offline fixture and tests require no model
  runtime, GPU, camera or network stream.
- LLM and Agent remain outside completed scope. The dashboard, Console/Web/TTS
  alert adapters, service-owned monitoring loop and source adapter layer are
  implemented. Phase 7-6 adds real local RTSP runtime evidence. ByteTrack and
  association adapters are implemented and synthetically integrated; Phase 7-5
  additionally exercised them in one real MP4 runtime path, but stable-ID
  quality and broad association acceptance remain unverified.
- Phase 7 architecture is frozen: SQLite-first storage, date-partitioned
  snapshot evidence, Streamlit V1, one `VideoSource` boundary for MP4/USB
  Camera/RTSP, Console/Web/TTS alert adapters and a separate persisted-event
  projection. The frozen Phase 6 JSONL wire contract is unchanged.
- Phase 7-1 SQLite event storage persists the in-memory Phase 6 `event_id`,
  retains the original numeric `source_timestamp`, uses a separate wall-clock
  ISO 8601 `timestamp`, supports restart-persistent query/status operations
  and stores deterministic bbox metadata without changing the four-field
  JSONL wire record.
- Phase 7-2 evidence storage writes caller-supplied frames as JPEG through an
  atomic temporary file, partitions by UTC capture date, stores only relative
  POSIX paths, records SHA256/dimensions/MIME type and makes
  `PersistedEvent.snapshot` point to the verified file. Identical retries are
  idempotent; conflicting evidence replacement is rejected. Metadata-write
  failure leaves an orphan candidate rather than deleting evidence.
- Phase 7-3 dashboard queries SQLite through `EventQueryService`; Streamlit
  pages do not import the inference, tracking, association or compliance
  pipeline. Event filtering, source/type/status filters, pagination,
  statistics and verified snapshot evidence display are implemented at the
  source/service contract level.
- Phase 7-3 alerts use an ordered `AlertService` and `AlertAdapter` contract
  with Console and in-process Web implementations. Adapters are idempotent by
  the preserved Phase 6 `event_id`, isolate failures and return structured
  delivered/failed/skipped results.
- Phase 7-4 source adapters expose `idle`, `opening`, `live`, `degraded`,
  `ended`, `failed` and `closed` states. MP4 delegates to the frozen
  `VideoReader`; USB Camera and RTSP own capture lifecycle; RTSP logs/status
  use credential- and query-free URIs. Business, dashboard and script layers
  do not call `cv2.VideoCapture` directly.
- Phase 7-5 composes the existing runtime boundaries into an end-to-end MP4
  smoke path without modifying upstream logic. The test run used the frozen
  `best.pt` and `configs/inference.yaml`, produced 77 detections, 66 track
  updates, one unknown association, 66 compliance findings and one persisted
  event, then verified JSONL, SQLite, snapshot SHA256/dimensions, dashboard
  queries, Console delivery and in-process Web delivery. The run ID is
  `20260923T131111Z`; evidence remains under Git-ignored
  `artifacts/validation/P7-5/`.
- Phase 7-6 reuses those frozen boundaries in `MonitoringService` instead of
  duplicating detector, tracker, association or compliance logic. The
  service owns one background worker, exposes immutable status, preserves
  persist-before-alert ordering and reloads the persisted snapshot reference
  before fan-out. TTS uses stable event idempotency, per-track/type cooldown
  and structured failure isolation.
- The M-007 annotated demo tool composes `VideoReader` and `InferenceService`
  into sequential frame inference and deterministic box/label rendering.
  `AnnotatedVideoWriter` stages all five artifacts, decodes the MP4 for
  frame-count and dimension verification, then publishes by one atomic
  directory rename. The real run processed 47/47 frames and produced output
  SHA256 `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949`.
- The Phase 7 release audit found no forbidden pending artifact. All changed
  files are source, tests, configuration or documentation; the largest
  pending file is approximately 75 KB, no tracked file exceeds 256 KB, and
  model, data, validation evidence and generated event outputs remain ignored.

## Current Runtime

- Phase 4 runtime ID: `INF-RUNTIME-001`; Windows x86_64, Python `3.10.4`,
  PyTorch `2.5.1+cpu`, torchvision `0.20.1`, Ultralytics `8.4.157`.
- Runtime policy: CPU only. Frozen `configs/inference.yaml` keeps
  `execution_enabled: false`; real validation used separate explicit configs.
- The P5-3 preflight host is Python `3.13.6` with OpenCV `5.0.0`; `torch`,
  `torchvision` and `ultralytics` are not installed. The frozen P5-3
  validation config remains `execution_enabled: false`.
- Phase 6 validation ran on the same Python `3.13.6` governance host using
  only project-owned schemas and standard-library JSONL storage; no model
  runtime dependency was added.
- Phase 7-5 validation used an isolated Windows CPU-only environment with
  Python `3.12.1`, PyTorch `2.5.1+cpu`, torchvision `0.20.1+cpu`,
  Ultralytics `8.4.157`, OpenCV `5.0.0`, NumPy `2.2.6`, Streamlit `1.64.0`,
  Pandas `3.0.6` and lap `0.5.12`. Python 3.12.1 differs from frozen
  `INF-RUNTIME-001` Python 3.10.4 and is recorded as a release limitation.
- M-007 validation used the frozen `INF-RUNTIME-001` Python `3.10.4`,
  PyTorch `2.5.1+cpu`, Ultralytics `8.4.157`, OpenCV `5.0.0` runtime and
  NumPy `2.2.6` environment.
- Training used a separately frozen AutoDL RTX 4090 environment. The
  EXP-001 one-run authorization is `CONSUMED`; it does not authorize retraining.

## Frozen Assets

- Dataset: `CSS-PPE-10-V1`, source identity and manifests in
  [Dataset Card](06_DATASET_CARD.md) and `docs/dataset_contracts/`.
- Mapping: Strategy C, seven training classes; five PPE compliance classes
  retain their locked order. See [ADR log](03_TECHNICAL_DECISIONS.md).
- Release checkpoint: `models/checkpoints/EXP-001/best.pt`, SHA256
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
- Training configuration and runtime: `configs/training/exp001_baseline.yaml`
  and `locks/EXP-001/`; inference config: `configs/inference.yaml`.
- Dataset, mapping, training assets, checkpoint and frozen inference config
  must remain unchanged without the applicable approval and new evidence.

## Current Risks

- [Risk Register](08_RISK_REGISTER.md) is authoritative for risk statuses.
  RISK-001 schedule pressure; RISK-004 PPE occlusion; RISK-005 Person-PPE
  misassignment; RISK-006 single-frame alert jitter; RISK-008 RTSP instability.
- Phase 7 architecture risks: RISK-020 SQLite migration drift; RISK-021
  Streamlit runtime coupling; RISK-022 Camera/RTSP instability; RISK-023
  evidence retention; RISK-024 alert/TTS failure isolation; RISK-025 event
  identity compatibility; RISK-026 statistics divergence.
- M-007 annotated-output integrity is tracked as RISK-027; one short MP4
  passed, while long-duration throughput, codec portability and visual
  annotation quality review remain open.
- Phase 7-5 reduces uncertainty for the MP4/SQLite/snapshot/dashboard/
  Console/Web path and real USB Camera lifecycle. Phase 7-6 adds a controlled
  local MediaMTX RTSP lifecycle and native Windows SAPI TTS call, but does not
  close RISK-008 or RISK-022 because remote RTSP, reconnect/backoff and
  stale-frame behavior remain untested. RISK-024 has TTS
  cooldown/failure-isolation tests plus a successful native backend call;
  long-running alert delivery remains unverified. Retention remains open.
- RISK-017 retains data-quality findings, including small-object performance
  and perceptual cross-split candidates. Candidates are not confirmed leaks.
- Remote RTSP behavior, reconnect/backoff and production monitoring remain
  unvalidated. Phase 7-6 validated a controlled local RTSP stream and
  MP4/USB/browser paths. M-007 annotated output is implemented and one short
  real MP4 was decoded, inspected and verified; this does not complete full
  M-007/M-008 acceptance or establish long-duration/codec coverage.

## Deferred Requirements

### Deferred MUST ownership

- M-007 annotated video rendering: `待实现`; the tool design is complete at
  `docs/designs/phase-07/PHASE_7_M007_ANNOTATED_DEMO_VIDEO_DESIGN.md` and the
  implementation passed one real 47/47-frame MP4 validation. Human review and
  Phase 9 final acceptance remain pending. Phase 7 owns delivery and Phase 9
  owns final Charter acceptance.
- M-008 Camera/RTSP: `待实现`; Phase 7 live-input/real-time monitoring
  integration owns delivery, Phase 9 owns final Charter acceptance.
- Neither requirement is an Extension. ADR-019 clarifies the assignment;
  Charter definitions and acceptance criteria remain unchanged.
- Phase 4 Offline Inference completion does not set P4-G3 to PASS or complete
  the full M-007/M-008 acceptance criteria.

## Latest Reports

- [Phase 7-0 architecture freeze report](reports/phase-07/PHASE_7_ARCHITECTURE_FREEZE_REPORT.md).
- [Phase 7-1 event storage report](reports/phase-07/PHASE_7_1_EVENT_STORAGE_REPORT.md).
- [Phase 7-2 evidence snapshot report](reports/phase-07/PHASE_7_2_EVIDENCE_SNAPSHOT_REPORT.md).
- [Phase 7-3 dashboard and alert report](reports/phase-07/PHASE_7_3_DASHBOARD_ALERT_REPORT.md).
- [Phase 7-4 camera and RTSP input report](reports/phase-07/PHASE_7_4_CAMERA_RTSP_REPORT.md).
- [Phase 7-5 runtime validation report](reports/phase-07/PHASE_7_5_RUNTIME_VALIDATION_REPORT.md).
- [Phase 7-6 release finalization report](reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_REPORT.md).
- [Phase 7-6 runtime validation result](reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_RESULT.md).
- [Phase 7 release freeze report](reports/phase-07/PHASE_07_FINAL_RELEASE_REPORT.md).
- [M-007 annotated demo video tool design](designs/phase-07/PHASE_7_M007_ANNOTATED_DEMO_VIDEO_DESIGN.md).
- [M-007 annotated demo video implementation report](reports/phase-07/PHASE_7_M007_IMPLEMENTATION_REPORT.md).
- [Phase 7 release complete report](reports/phase-07/PHASE_07_RELEASE_COMPLETE_REPORT.md).
- [Phase 7 release closure worklog](worklogs/2026/09/2026-09-24-01-phase7-release-closure.md).
- [Phase 7 M-007 implementation worklog](worklogs/2026/09/2026-09-23-18-phase7-m007-implementation.md).
- [Phase 7 release-freeze preparation worklog](worklogs/2026/09/2026-09-23-17-phase7-release-freeze-preparation.md).
- [Phase 7-6 release finalization worklog](worklogs/2026/09/2026-09-23-16-phase7-release-finalization.md).
- [Phase 7 release audit report](reports/phase-07/PHASE_7_RELEASE_AUDIT_REPORT.md).
- [Phase 7 architecture audit](reports/phase-07/PHASE_7_ARCHITECTURE_AUDIT.md).
- [Phase 7 target architecture](designs/phase-07/PHASE_7_TARGET_ARCHITECTURE.md).
- [Phase 7 data contracts](designs/phase-07/PHASE_7_DATA_CONTRACTS.md).
- [Phase 7 risk register](reports/phase-07/PHASE_7_RISK_REGISTER.md).
- [Phase 6 final release report](reports/phase-06/PHASE_06_FINAL_RELEASE_REPORT.md).
- [Phase 6 test report](reports/phase-06/PHASE_06_TEST_REPORT.md).
- [P5 final release preparation](reports/phase-05/P5_FINAL_RELEASE_REPORT.md).
- [P5 release final audit](reports/phase-05/P5_RELEASE_FINAL_AUDIT.md).
- [P5 documentation sync report](reports/phase-05/P5_DOCUMENTATION_SYNC_REPORT.md).
- [P5 release final audit worklog](worklogs/2026/09/2026-09-23-07-phase5-release-final-audit.md).
- [P5 final release worklog](worklogs/2026/09/2026-09-23-06-phase5-final-release-preparation.md).
- [P5-3 tracking and association validation](reports/phase-05/P5-3_VALIDATION_REPORT.md).
- [P5-3 validation worklog](worklogs/2026/09/2026-09-23-05-phase5-p5-3-validation.md).
- [P5-2 Person-PPE association implementation](reports/phase-05/P5-2_IMPLEMENTATION_REPORT.md).
- [P5-1 ByteTrack adapter implementation](reports/phase-05/P5-1_IMPLEMENTATION_REPORT.md).
- [Phase 4C-1 real-image validation](reports/phase-04/PHASE_04C1_IMAGE_VALIDATION_REPORT.md).
- [Phase 4C-2 real-MP4 validation](reports/phase-04/PHASE_04C2_VIDEO_VALIDATION_REPORT.md).
- [Phase 4 scope clarification](reports/maintenance/PHASE_SCOPE_CLARIFICATION_REPORT.md)
  and [Phase 4 phase document](phases/PHASE_04_INFERENCE.md).
- [Phase 2 training execution](reports/EXP-001_TRAINING_EXECUTION_REPORT.md)
  and [Phase 3 final release](reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md).
- [Phase 4 → Phase 5 handover](worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md)
  preserves the former 753-line status document in full.
- This documentation cleanup is recorded in
  [Phase B governance report](reports/maintenance/DOCUMENT_GOVERNANCE_PHASE_B_REPORT.md).

## Next Allowed Step

`PHASE 8 NOT STARTED / WAIT FOR AUTHORIZATION`.

The base Phase 7 release tag and remote commit already exist. The Phase 7-6
finalization and M-007 implementation passed the full repository test gate and
human review. The authorized release closure created the final freeze commit
and tag and pushed the release. Remote RTSP behavior, reconnect/backoff and
M-008 final acceptance remain pending. Native TTS and controlled local RTSP
were executed in the isolated validation runtime. The M-007 annotated demo
video implementation, real MP4 output validation and human review are complete,
but Phase 9 acceptance still does not change the Charter's `待实现` status.
The historical P5-3-G5 runtime block and all frozen model/data/training assets
remain unchanged. Phase 8 has not started.
