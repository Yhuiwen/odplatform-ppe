# Current Status

This is the single entry point for the latest project state. Historical
implementation and validation details are preserved in the
[Phase 4 → Phase 5 handover](worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md)
and the linked phase reports. Earlier snapshots may describe past pending
reviews; the statuses below reflect the current accepted records.

## Current Phase

- **V1.2-G 全链路验收（2026-10-10）：BLOCKED / HUMAN REVIEW PENDING。** 显示优化、八种图片真实推理、47/570逐帧输出/事件/双证据、混合FIFO及同模型三视频、四桌面尺寸40组合完成。Vue34 PASS/build PASS；独立API109 PASS；冻结819 PASS/12预期API文件跳过。首轮核验570帧素材再次CFR拒绝，根因未证实，保留G-CFR-01/RISK-030发布阻塞；后续通过不覆盖失败。FullHD/4K/长视频/长稳未验收，P9-C不变，无发布动作。[报告](reports/v1.2/V12_G_FINAL_ACCEPTANCE_REPORT.md)，[用户指南](V1_2_OFFLINE_USER_GUIDE.md)，[交接](worklogs/2026/10/2026-10-10-01-v12g-final-acceptance.md)。

- **V1.2-F 离线智能检测工作台（2026-10-09）：HUMAN REVIEW PASS（G授权确认；未提交）。** 三个Tab、真实上传/进度/取消/历史、图片对比、视频播放/时间轴/只读证据/下载；前端31 PASS/build PASS，API非模型106+真实资源5 PASS，冻结819 PASS/11独立API文件跳过。四种桌面尺寸和原七页无横向溢出。E审核已由F授权确认通过；B/C/D/E/F全部未提交；现行G与P9-C状态以上方记录为准。[报告](reports/v1.2/V12_F_FRONTEND_REPORT.md)，[交接](worklogs/2026/10/2026-10-09-06-v12f-offline-workbench.md)。

- **V1.2-E offline compliance events / key evidence (2026-10-09): HUMAN REVIEW PASS (confirmed in F authorization; uncommitted).** Job-owned frozen tracking/association/event lifecycle, reused SQLite repositories, dual original-size PNG evidence, verified JSON/CSV/ZIP and five read-only event/evidence APIs. Single-pass real47/570 videos generated1/2 events and2/4 images without realtime writes/alerts. Final API107 PASS; frozen819 PASS/10 expected file skips; Vue11 PASS/build PASS. Prior intermittent pre-inference CFR rejection remains recorded; no long stability acceptance; E did not include the subsequent F frontend. B/C/D work preserved, no release action. [Report](reports/v1.2/V12_E_EVENTS_EVIDENCE_REPORT.md), [handover](worklogs/2026/10/2026-10-09-05-v12e-events-evidence.md).

- **V1.2-C supplemental verification (2026-10-09): HUMAN REVIEW PENDING.** Inference timing, detection-context validation and input-integrity recheck added. Image/B/API 39 PASS, real image original-resolution chain PASS, Vue 11 PASS/build PASS. Existing D retained; no video encoding this run. [C report](reports/v1.2/V12_C_IMAGE_INFERENCE_REPORT.md).

- **V1.2-D full-frame MP4 inference / H.264 rendering (2026-10-09): HUMAN REVIEW PASS (confirmed in E authorization; still uncommitted).** The B/C single worker now processes images and videos with FIFO admission, original-resolution rendering, exact supported CFR timing, supervised FFmpeg and verified MP4/JSONL/JSON/ZIP publication. Real 47/570-frame inputs retained every frame at 1280×720, 24000/1001 and 30 FPS; browser playback and same-worker sequential reuse passed. 68 distinct API/unit/real-chain tests have passing evidence; frozen full rerun: 819 passed / 7 expected independent-API file skips; Vue: 11 passed/build passed. No events are created by D; confirmed_events/evidence_count remain null. Real FullHD inference, long stability and E remain outside validation. P9-C PARTIAL/FROZEN unchanged; B/C work preserved, no commit/push/tag. [D report](reports/v1.2/V12_D_VIDEO_RENDERING_REPORT.md), [handover](worklogs/2026/10/2026-10-09-03-v12d-video-rendering.md). The B/C entries below are historical stage snapshots; current video capability is described here.

- **V1.2-C image inference and original-size annotation (2026-10-09): HUMAN REVIEW PENDING.** The B-phase queue now dispatches images through the frozen `InferenceService`/YOLODetector and existing renderer, publishes verified PNG/JSON/ZIP outputs and keeps MP4 jobs queued. An isolated real 1024×766 construction image completed via HTTP with five detections and two single-frame candidates; three sequential jobs reused one model. Separate API environment: 37 passed; frozen V1 suite: 819 passed / 4 expected API skips; frontend: 11 passed and build passed. The frozen five-class filter leaves machinery/vehicle explicitly unevaluated. P9-C remains PARTIAL. [Report](reports/v1.2/V12_C_IMAGE_INFERENCE_REPORT.md), [handover](worklogs/2026/10/2026-10-09-02-v12c-image-inference.md).

- **V1.2-B offline job infrastructure (2026-10-09): HUMAN REVIEW PENDING.** Separate versioned SQLite task store, bounded JPG/PNG/MP4 upload, persisted state machine, single-process worker foundation, restart recovery, resource admission and verified artifact boundary are implemented. Production processor remains unavailable and real inference/encoding were not run. Independent API environment: 21 tests passed; frozen business environment: 816 passed / 2 expected API skips; frontend: 11 tests and build passed. P9-C remains PARTIAL. [Implementation report](reports/v1.2/V12_B_JOB_INFRA_REPORT.md), [handover](worklogs/2026/10/2026-10-09-01-v12b-offline-infrastructure.md).

- **V1.1 Vue/FastAPI frontend migration (2026-10-08): HUMAN REVIEW PENDING.** Seven real API-connected Vue pages, service-owned single monitoring instance, event/evidence/AI adapters, isolated API dependency environment and Streamlit fallback are implemented. Real isolated MP4: 47/47 frames, 74 detection observations, one PPE_UNKNOWN event, two channel deliveries and processed preview. Frontend build and three Vitest checks pass; API integration 2 pass; V1 frozen suite 810 pass, one expected API skip. Browser checks cover seven pages at 1366×768 and 1920×1080 without page overflow or new JS errors. USB/RTSP physical/remote input, live Provider and P9-C long stability remain open. [Migration report](reports/frontend-v1.1/V1_1_FRONTEND_MIGRATION_REPORT.md), [test report](reports/frontend-v1.1/FRONTEND_TEST_REPORT.md), [handover](worklogs/2026/10/2026-10-08-10-v1.1-frontend-migration.md).

- **P9-D Overview/source/time refinement (2026-10-07): targeted gate PASS.**
  Visible event tables hide IDs; time sorting is available in event, overview
  and monitoring views; source labels and grouped filters use `mp4`,
  `usb{id}` and `rtsp` while preserving raw database values. The new Overview
  presents pending work, persistent-event KPIs, trends and handling progress.
  Populated-page validation and full regression (786 passed) succeeded.
  Manual responsive browser review remains open. See the
  [report](reports/phase-09/P9D_OVERVIEW_SOURCE_SORT_REPORT.md) and
  [worklog](worklogs/2026/10/2026-10-07-09-overview-source-sort.md).

- **P9-D monitoring/event operator flow (2026-10-07): targeted gate PASS.**
  USB start/stop button state now updates after one click; alert KPI explains
  per-channel delivery counts. Event rows provide Chinese status/actions,
  persist `OPEN`/`RESOLVED`, and navigate to the selected event in Evidence
  Viewer. Redundant lower details and native English read-only table menus
  are removed. Full regression: 783 passed. Physical USB and manual narrow
  browser review remain open. See the [report](reports/phase-09/P9D_EVENT_OPERATOR_FLOW_REPORT.md)
  and [worklog](worklogs/2026/10/2026-10-07-08-event-operator-flow.md).

- **Realtime CPU speed target on the supplied MP4 (2026-10-07): PASS for
  the bounded local-video gate.** ADR-025 selects a 416-pixel OpenVINO
  monitoring profile derived from the same frozen checkpoint. Two corrected
  production-path 570-frame runs reached 28.836 and 29.414 processed FPS,
  with one `NO_HELMET` and one `NO_VEST` event each. A third run with real
  Console/Web/TTS alerts reached 26.000 FPS, with six delivered and none failed.
  The Streamlit service was restarted on port 8502. Full suite: 780 passed.
  Camera/RTSP throughput, browser display cadence, broad-scene accuracy and
  long-run resource stability are not verified; P9-C overall remains PARTIAL.
  See the [report](reports/phase-09/P9_CPU_24FPS_REPORT.md) and
  [worklog](worklogs/2026/10/2026-10-07-07-cpu-24fps-openvino.md).

- **P9-C.3i inference worker/session lifecycle isolation
  (2026-10-07): PASS as an attribution increment; P9-C overall
  PARTIAL.** Fresh 20-minute T0/T1 direct/persistent inference were
  near stable at +0.00144/+0.00231 MiB/cycle. T2 fresh inference
  worker per cycle without `MonitoringService` and T3 formal H0 grew
  at +0.10446/+0.10432 MiB/cycle. Conditional T4 retained H0
  session churn but routed inference through one persistent thread;
  it fell to +0.00331 MiB/cycle and a flat late window. Real inference
  × fresh worker-thread lifecycle is strongly supported for this
  20-minute growth; a material MonitoringService-specific increment
  is not supported. Retained owner and production unbounded leak are
  **NOT CONFIRMED**. Five semantic/exit gates, 762 tests and frozen
  checks passed. **P9-C.4 and P9-D/E/F remain unauthorized.** See the
  [P9-C.3i report](reports/phase-09/P9C3I_INFERENCE_WORKER_LIFECYCLE_REPORT.md)
  and [worklog](worklogs/2026/10/2026-10-07-02-p9c3i-worker-lifecycle.md).

- **P9-C.3h real-inference downstream boundary isolation
  (2026-10-07): PASS as an attribution increment; P9-C overall
  PARTIAL.** H0/H1/H2 fresh 10-minute screens completed 72/68/69
  real-inference, precomputed-track cycles at +0.10190/+0.10508/
  +0.10653 MiB/cycle. H0 omitted formal Association/Compliance/
  Event/SQLite/Snapshot/Alert yet already showed RP-scale growth.
  A fresh matched 20-minute H0/RP pair completed 142/150 cycles,
  with +0.10318/+0.10255 MiB/cycle and continuing late slopes.
  **FIRST MATERIAL DOWNSTREAM DIVERGENCE: NONE; H0 already at RP
  scale.** Formal business downstream is not required for this
  20-minute cached-frame rise; the P9-C.3g inference × downstream
  wording is superseded as a causal requirement. The specific
  inference/MonitoringService lifecycle owner and production
  unbounded leak remain **NOT CONFIRMED**. Full suite 755 PASS;
  frozen identities unchanged. **P9-C.4 and P9-D/E/F remain
  unauthorized.** See the [P9-C.3h report](reports/phase-09/P9C3H_INFERENCE_DOWNSTREAM_BOUNDARY_REPORT.md)
  and [worklog](worklogs/2026/10/2026-10-07-01-p9c3h-downstream-boundary.md).

- **P9-C.3g lean inference × tracker interaction matrix
  (2026-10-04): PASS as an attribution increment; P9-C overall
  PARTIAL.** Four fresh 20-minute cached-frame full-downstream controls
  completed PP/PR/RP/RR at 150/150/149/148 cycles. All one-cycle
  business signatures matched; 597 events, SQLite rows and verified
  snapshots, and 1,194 alert deliveries had zero failures. The
  2–20-minute RSS slopes were +0.01245/+0.00156/+0.10231/+0.10512
  MiB/cycle. Real inference has a strong increment with either tracker;
  real ByteTrack does not. **Inference × downstream interaction is
  SUPPORTED; tracker × downstream NOT SUPPORTED as a material positive
  effect; inference × tracker WEAK.** Cached-frame RP/RR growth means
  fresh source/decode is not required over this control. Production
  unbounded leak and retained owner remain **NOT CONFIRMED**. Full suite
  742 PASS; frozen identities and package inventory unchanged.
  **P9-C.4 and P9-D/E/F remain unauthorized; further attribution
  decision required.** See the [P9-C.3g report](reports/phase-09/P9C3G_LEAN_INTERACTION_MATRIX_REPORT.md)
  and [worklog](worklogs/2026/10/2026-10-04-01-p9c3g-lean-interaction-matrix.md).

- **P9-C.3f final lean real full-graph boundedness confirmation
  (2026-09-27): PARTIAL / SUSPICIOUS_CONTINUED_GROWTH.** A fresh
  process ran the real MP4 → YOLO → ByteTrack → association →
  compliance/event → SQLite/snapshot → Console/Web graph for 3602.625 s
  with only an external resource sampler. It completed 692 × 47 =
  32,524 frames, 692 unique events and verified snapshots, and 1,384
  successful alerts. Worker/source exit, four post-run Dashboard pages,
  731 tests, frozen hashes and package inventory passed. Warm RSS
  window means rose 469.88 → 483.40 → 496.78 → 510.16 → 521.17 MiB;
  30–60 min slope was +1.2200 MiB/min. Resource growth is reproduced
  under lean real full-graph observation, but a retained owner and
  unbounded production memory leak are **NOT CONFIRMED**. **P9-C overall
  remains PARTIAL. P9-D/E/F and P9-C.4 are not authorized; further
  decision is required.** See the [P9-C.3f report](reports/phase-09/P9C3F_FINAL_LEAN_FULL_GRAPH_STABILITY_REPORT.md)
  and [worklog](worklogs/2026/09/2026-09-27-04-p9c3f-final-lean-full-graph.md).

- **P9-C.3e N-harness bridge attribution (2026-09-27): PASS /
  DIAGNOSTIC HARNESS CONTRIBUTION SUPPORTED.** S4/H one-cycle business
  semantics matched, including compliance, event frame, SQLite,
  snapshot SHA256 and alerts. H reused N's observation assembly for
  150 cycles/events in 20 minutes and reproduced sustained RSS
  +0.03127 MiB/cycle, with traced slope +0.05637 MiB/min against
  historical N +0.0238 and +0.0566. Matched lean J also ran 150
  cycles/events in 20 minutes at +0.00408 MiB/cycle; its 10–20-minute
  slope was +0.02986 MiB/min versus H +0.22384. N remains a
  reproducible instrumented observation. No single diagnostic
  container leak or production downstream leak is confirmed.
  **At the P9-C.3e checkpoint**, P9-C overall was PARTIAL and lean real
  full-graph boundedness remained unverified. P9-C.3f was the next
  authorized confirmation at that time; its outcome is recorded above.
  P9-C.4 and P9-D/E/F remain unauthorized. See the
  [P9-C.3e report](reports/phase-09/P9C3E_N_HARNESS_BRIDGE_REPORT.md)
  and [worklog](worklogs/2026/09/2026-09-27-03-p9c3e-n-harness-bridge.md).

- **P9-C.3d Monitoring lifecycle/downstream isolation (2026-09-27):
  PASS / N RESIDUAL NOT REPRODUCED.** S0 ran 150 formal
  MonitoringService cycles in 20 minutes with 7050 cached real frames,
  balanced workers/sources and +0.000344 MiB/cycle warm RSS. S1–S4
  each ran 75 cycles in separate processes with slopes −0.00302,
  +0.000827, +0.00197 and +0.00464 MiB/cycle. S4 completed 75 SQLite
  rows, 75 snapshots and 150 delivered alerts, but did not reproduce
  historical N +0.0238 MiB/cycle. No material first stage divergence
  was evidenced; conditional 20-minute and tracker interaction pairs
  were therefore not run. N's observed/recorded harness differs from
  the lean staged control. **P9-C overall PARTIAL; production full-graph
  bound and unbounded-leak claim both unproven; P9-C.4 and P9-D/E/F
  unauthorized.** See the
  [P9-C.3d report](reports/phase-09/P9C3D_DOWNSTREAM_INTERACTION_ATTRIBUTION_REPORT.md)
  and [worklog](worklogs/2026/09/2026-09-27-02-p9c3d-monitoring-downstream-isolation.md).

- **P9-C.3c ByteTrack native lifecycle attribution (2026-09-27): PASS /
  NEITHER CLEARLY.** P persistent update, Q construct/reset only and R
  combined tracker-only each completed 149 paced cycles over 20 minutes.
  Warm RSS slopes were +0.00155, +0.00080 and +0.00168 MiB/cycle,
  respectively, far below L−N's directional +0.0192 MiB/cycle gap.
  Their late windows approached a plateau; no isolated path qualified
  for a 60-minute boundedness extension. The prior L/N reduction remains
  a valid directional observation, but P/Q/R do not identify a standalone
  tracker leak. Tracker/downstream interaction and N residual remain open.
  **P9-C overall PARTIAL; full-graph boundedness unproven; P9-C.4 and
  P9-D/E/F unauthorized.** See the
  [P9-C.3c report](reports/phase-09/P9C3C_TRACKER_NATIVE_ATTRIBUTION_REPORT.md)
  and [worklog](worklogs/2026/09/2026-09-27-01-p9c3c-tracker-native-attribution.md).

- **P9-C.3b inference/tracker isolation (2026-09-26): PASS / CONTRIBUTION
  NARROWED.** M ran real inference on all 47 cached MP4 frames for 125
  cycles/20.125 minutes; its warm RSS slope was +0.0470 MiB/min and
  +0.00736 MiB/cycle, weak as a standalone explanation of K−L.
  Independently reverified real tracks passed L/N one-cycle semantic
  equivalence. N ran 150 paced cycles/events in 20 minutes with the real
  downstream graph; RSS was +0.1779 MiB/min and +0.0238 MiB/cycle versus
  L's +0.3211 and +0.0430. Real ByteTrack update/reset is a supported
  contributor, while non-tracker residual and inference/downstream
  interaction remain unresolved. **Unbounded full-graph leak is not
  confirmed; P9-C overall remains PARTIAL.** P9-C.4 and P9-D/E/F remain
  unauthorized. See the [P9-C.3b report](reports/phase-09/P9C3B_INFERENCE_TRACKER_ISOLATION_REPORT.md)
  and [worklog](worklogs/2026/09/2026-09-26-03-p9c3b-inference-tracker-isolation.md).

- **P9-C.3a precomputed-detection control (2026-09-26): PASS /
  MULTI-CONTRIBUTOR PATTERN.** The real 47-frame fixture contains 77
  independently reverified detections. One-cycle K/L downstream semantics
  matched. Over 20 minutes, L completed 148 cycles/events versus K's 150;
  its RSS slope was +0.3211 versus +0.9737 MiB/min (about 67% lower),
  with nearly equal Python-traced slopes. Real inference or its downstream
  interaction contributes to K's larger growth, while residual L growth
  remains unexplained. This does not prove a YOLO leak or full-graph
  boundedness. **P9-C overall remains PARTIAL; P9-C.4 and P9-D/E/F are not
  authorized.** Full regression: 693 PASS. See the
  [P9-C.3a report](reports/phase-09/P9C3A_PRECOMPUTED_DETECTION_CONTROL_REPORT.md)
  and [worklog](worklogs/2026/09/2026-09-26-02-p9c3a-precomputed-detection-control.md).

- **P9-C.3 resource growth attribution (2026-09-26): PARTIAL / INCONCLUSIVE.** The
  full-chain 30-minute baseline reproduced rising MP4 RSS; Python-traced
  memory and alert idempotency state account for only a small fraction. A
  source-only 60-minute control reached a near-plateau in its final 30
  minutes, so it cannot establish a bound for the separate full-chain rise.
  A 20-minute predecoded-frame full-chain control still rose +0.9737
  MiB/min, so repeated source decoding is not the sole owner. The precise
  full-chain allocation owner remains unknown. P9-C remains PARTIAL;
  P9-D/E/F remain unauthorized. See the
  [P9-C.3 attribution report](reports/phase-09/P9C3_RESOURCE_GROWTH_ATTRIBUTION_REPORT.md).

- **Current P9-C.2 long-run result (2026-09-25): PARTIAL.** The bounded
  observer passed its 20,000-record cap test. USB Camera 0 completed an
  uninterrupted 60-minute chain and 40-second restart with consistent
  SQLite/evidence/alerts and warm RSS plateau (+0.0484 MiB/min). A separate
  60-minute MP4 process completed 675 full 47-frame cycles with consistent
  evidence, but its warm RSS rose monotonically (+1.2478 MiB/min) without a
  proven owner. **P9-C.3 RESOURCE LEAK ATTRIBUTION REQUIRED; P9-C overall is
  not PASS; P9-D/E/F are not authorized.** P9-A, P9-B and P9-C.1 remain PASS.
  See [P9-C.2 report](reports/phase-09/P9C2_LONG_RUN_STABILITY_REPORT.md)
  and [memory attribution](reports/phase-09/P9C2_MEMORY_ATTRIBUTION_REPORT.md).

- P9-B.3 human closure (2026-09-25): the user replied `pass` to the USB
  Camera 0 Realtime Monitoring visual checklist. **HUMAN VISUAL REVIEW PASS;
  G1–G13 PASS; P9-B RESULT: PASS.** M-008/M-009/M-010 satisfy the locked
  Charter acceptance criteria. The cold-inference Stop timeout and complex
  scene coverage remain documented limitations. **P9-C NOT AUTHORIZED**;
  Phase 9 final delivery acceptance remains pending. See the
  [P9-B.3 Charter gate report](reports/phase-09/P9B3_CHARTER_GATE_READJUDICATION_REPORT.md).

- P9-B.3 Charter re-adjudication (2026-09-25): the locked M-009/M-010 and
  M-008 criteria are satisfied by the existing real Camera, tracking,
  association and failure evidence. G8 and G10 are PASS on their stated
  technical criteria; controlled complex scenes and a five-second cold Stop
  bound are not locked acceptance clauses. A fresh full suite passed 684/684.
  **P9-B is READY FOR HUMAN VISUAL SIGN-OFF**, with user confirmation still
  pending; do not mark final P9-B PASS or Charter statuses accepted yet.
  P9-C is not authorized. See the
  [P9-B.3 Charter gate report](reports/phase-09/P9B3_CHARTER_GATE_READJUDICATION_REPORT.md).
  Handover: [P9-B.3 worklog](worklogs/2026/09/2026-09-25-04-p9b3-charter-gate-readjudication.md).

- P9-B.2 follow-up (2026-09-25): real browser inspection of USB Camera 0
  showed live preview, growing metrics, `NO_HELMET`/`NO_VEST` events,
  verified evidence and clean Stop/restart. Five processed-frame USB cycles
  exited normally, and a 103-frame scene now has per-frame tracking and PPE
  candidate geometry. The post-read Stop race was fixed. A Stop requested
  during noninterruptible cold inference can still exceed the five-second
  join, and controlled crossing/occlusion/re-entry or ambiguous multi-person
  evidence is unavailable. **P9-B remains PARTIAL (G8/G10); P9-C NOT READY.**
  See [stop lifecycle](reports/phase-09/P9B_MONITORING_STOP_LIFECYCLE_REPORT.md)
  and [M-008 assessment](reports/phase-09/P9B_M008_FINAL_ACCEPTANCE_REPORT.md).

- Phase 9 P9-B Full Chain Validation & Acceptance is `PARTIAL / HUMAN REVIEW
  PENDING` after authorized P9-B.1 (2026-09-25). The first real MP4 run
  exposed Ultralytics' lazy `lap` installation. The unpublished
  `FINAL-DEMO-RUNTIME-001` lock now pins `lap==0.5.13`; a second clean
  Python 3.12.1 environment repeated the real 47-frame MonitoringService
  chain without package drift, so the runtime is `RE-FROZEN / VERIFIED
  STABLE` for the exercised paths. The real MP4 produced a complete
  `PPE_UNKNOWN` trace. A 30-second USB full-chain run processed 143 frames
  and generated real `NO_HELMET` and `NO_VEST` Camera events, SQLite rows,
  verified snapshots and alerts. The same clean MP4 database reached four
  Dashboard pages, Analytics, Report and Agent. Controlled complex scenes,
  a sustained construction-site violation clip, live-page visual review and
  short cold-start stop reliability remain open. P9-C is not ready.
  Handover: [P9-B.1 worklog](worklogs/2026/09/2026-09-25-03-p9b1-runtime-repair.md).
  See [P9-B report](reports/phase-09/P9B_FULL_CHAIN_VALIDATION_REPORT.md).

- Phase 9 P9-A Final Audit & Runtime Freeze: `PASS / FINAL-DEMO-RUNTIME-001
  FROZEN / VALIDATED` on Windows 11 AMD64, Python 3.12.1, CPU only at its
  completion. Phase 8 remains FINAL RELEASED. P9-B was subsequently
  authorized; Phase 9 final Charter acceptance is pending. See the
  [P9-A.1 runtime freeze report](reports/phase-09/P9A_FINAL_DEMO_RUNTIME_FREEZE_REPORT.md)
  and [P9-A audit](reports/phase-09/P9A_FINAL_AUDIT_REPORT.md).

- Phase 8 COMPLETE / FINAL RELEASED — LLM & Agent. P8-0 Architecture and
  Contract Freeze is
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-1 Deterministic Safety
  Analytics and Context is `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`.
  P8-2 Structured Report Contract and Grounding Validator is
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-3 Deterministic Template
  Fallback is `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-4 Provider
  Adapter Boundary and Untrusted Output Parsing is
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-5 Real Provider E2E,
  Grounding Enforcement and Safe Fallback is
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-5D Sanitized Provider
  Schema Diagnostics is `HUMAN REVIEW PASS`. P8-5P Provider Prompt Schema
  Conformance Fix is `HUMAN REVIEW PASS`. P8-6 Basic Agent Architecture
  Freeze is `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. P8-6.1 Static
  Read-only Tool Registry and Permission Layer is `HUMAN REVIEW PASS`. P8-6.2
  Deterministic Agent Planner is `HUMAN REVIEW PASS`. P8-6.3 Agent Audit is
  `HUMAN REVIEW PASS`. P8-6.4 LLM-Assisted Agent Planning Architecture is
  `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. P8-6.4.1 Plan Candidate
  Parser and Validator is `HUMAN REVIEW PASS`. P8-6.4.2 LLM Planner Adapter
  is `HUMAN REVIEW PASS`. P8-6.4.3 AgentService Orchestration is
  `HUMAN REVIEW PASS`, and the P8-6 Agent implementation is released as the
  interim checkpoint `phase-8-controlled-agent-complete`; no real provider
  planning request, durable audit store, memory, autonomous loop or Phase 9
  work has started. The authoritative P8-6 design is
  `docs/designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md`; the original
  P8-0 design remains at
  `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`, and ADR-023 freezes a
  deterministic, read-only analytics/context path, provider-independent LLM
  boundary, grounded structured report, local fallback and allowlisted Basic
  Agent tools. P8-1 reads only through `EventQueryService` and builds canonical
  `phase8-context-v1` payloads. P8-2 adds the provider-independent
  `phase8-report-v1` contract, context-fingerprint binding and fail-closed
  reference/numeric/privacy validation. P8-3 adds deterministic local report
  generation over the same context and validates it through the unchanged
  P8-2 boundary. P8-4 adds a provider-independent request/transport boundary,
  strict bounded JSON parsing and candidate-plus-validation orchestration.
  P8-5 adds one configuration-driven OpenAI-compatible chat-completions
  transport, provider-first orchestration and deterministic provider-timeout,
  auth, rate-limit, malformed-output and semantic-failure fallback. An
  initial human-executed OpenAI-compatible request to `deepseek-flash`
  received a response, passed strict JSON syntax parsing, but was rejected
  during `phase8-report-v1` construction with `REPORT_SCHEMA_INVALID`; the
  unchanged fallback then passed. That failure remains historical evidence.
  P8-5D adds bounded sanitized schema diagnostics without weakening the
  report schema or grounding boundary. P8-5P upgrades only provider request
  construction to `phase8-provider-prompt-v2` with an exact schema description
  generated from the authoritative dataclasses and enums, without changing or
  weakening the report schema, parser, grounding validator or fallback. A
  final separately authorized manual request followed prompt v2 and returned
  `PROVIDER_VALIDATED`: transport, strict JSON, `phase8-report-v1` and
  grounding all passed with `PROVIDER`, `degraded=false` and fallback not
  used. P8-6 freezes only the Basic Agent boundary, static read-only tool
  registry, deny-by-default permissions, audit policy and unchanged P8-5
  fallback reuse. P8-6.1 implements the immutable registry, deny-by-default
  permission policy, bounded argument validation, four service adapters and
  non-persistent audit metadata, and has passed human review. P8-6.2 adds a
  deterministic planner with `AgentIntent`/`AgentPlan`, exact tool mapping,
  bounded argument validation, registry resolution and permission preflight;
  it never executes a tool and introduces no LLM tool calling, provider
  change or Agent framework, and has passed human review. P8-6.3 adds the
  immutable `phase8-agent-audit-v1` event, append-only in-memory store
  abstraction, bounded metadata sanitization and `AgentAuditService`; durable
  persistence remains unimplemented. P8-6.4 passed human review and defines
  the untrusted LLM candidate boundary, strict candidate validation,
  deterministic final-plan construction, registry-only execution, permission
  rechecks, audit integration and deterministic fallback. P8-6.4.1 implements
  the `phase8-agent-plan-candidate-v1` schema, bounded strict JSON parser,
  request-binding/intent/tool/argument/permission validation and deterministic
  conversion to `phase8-agent-plan-v1`; it never calls
  `ToolRegistry.execute`. P8-6.4.2 adds a provider-independent planner
  request builder, injected candidate-client boundary, strict validator
  integration, bounded audit metadata and deterministic fallback. Invalid or
  failed candidates fall back to the deterministic planner; forbidden
  candidate capabilities are refused without privilege escalation.
  P8-6.4.3 adds typed `AgentRequest`/`AgentResult`, `AgentService`
  orchestration, validated-plan-only registry execution, append-only audit
  recording for planner/tool outcomes, deterministic fallback support and
  audit-unavailable fail-closed behavior. P8-FI final integration architecture
  has passed human review. Its API boundary is
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`; the Web / Streamlit
  integration is `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`; the
  deterministic E2E demo is `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`.
  Phase 8 final integration is released under
  `phase-8-final-integration-complete`. M-021, M-022 and M-023 remain
  `待实现` in the locked Charter; durable audit storage, memory, autonomous
  loops and real provider planning requests remain not implemented, and
  Phase 9 P9-A is in progress; P9-B is not authorized.
- Phase 7 COMPLETE / RELEASED — Web & Alerts. Base commit
  `a30b73c080c18d010fbaa08642868e86acb68022` carries annotated tag
  `phase-7-web-alert-platform-complete`; final release closure publishes
  annotated tag `phase-7-release-freeze-complete`. Phase 7-0 through Phase 7-6
  are human-reviewed PASS. Phase 7-6 adds the TTS alert adapter, a
  service-owned MP4/USB/RTSP monitoring loop and the Streamlit realtime page;
  MP4, USB Camera, native TTS, browser Streamlit and controlled local RTSP
  validation all passed. M-007 annotated demo video is implemented, validated
  on a real 47/47-frame MP4 and human-reviewed PASS. M-007 Charter final
  acceptance remains pending in Phase 9. Remote RTSP reconnect
  behavior, reconciliation automation and retention remain pending.
  M-015 through M-020 remain `待实现` in the locked Charter until full
  acceptance.
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
- Current next allowed step: `P9-B PARTIAL / P9-C NOT READY / DO NOT
  START OR IMPLEMENT DURABLE AUDIT STORE, MEMORY, AUTONOMOUS LOOP OR REAL
  PROVIDER PLANNING CALLS WITHOUT NEW AUTHORIZATION`.

## Last Completed

- Phase 8 Final Integration Deterministic E2E Demo:
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS / FINAL RELEASED`. Added a fixture-driven
  validation path for
  `Web facade -> AgentApplicationService -> AgentService -> ToolRegistry ->
  AgentAuditService -> UI projection`. The demo covers summary, grounded
  `TEMPLATE_FALLBACK` report generation, forbidden-request refusal and
  UI-safe output without a provider call or model load. Focused E2E tests
  passed (`6 passed`); the combined E2E/structure/import slice passed
  (`94 passed`); the full repository gate passed (`667 passed, 1 skipped`);
  `compileall` and `git diff --check` passed. Frozen model, training,
  inference, dataset and Phase 8 contract hashes remain unchanged, and the
  Charter diff is empty.
- Phase 8 Final Integration Web / Streamlit:
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`. Added the reviewed
  `phase8-agent-api-v1` boundary, trusted identity resolution, bounded
  `AgentApiResponse` projection, `web/agent_support.py`, AI report and Safety
  Assistant pages, navigation entries and deterministic API/Web/integration
  tests. The Web composition uses the existing AgentService, static
  ToolRegistry, analytics, grounded report, fallback and append-only audit
  path with `provider_client=None`. The UI exposes exactly `answer`, `summary`,
  `evidence_references`, `recommendations` and `safe_status`, and pages import
  only the approved Web facade. Focused validation passed (`27 passed`). No
  model load, provider request, inference, training, durable audit storage,
  Phase 9, commit, tag or push was performed. Full repository validation
  passed (`660 passed, 1 skipped`); `compileall` and `git diff --check`
  passed.
- Phase 8 P8-6.3 Agent Audit:
  `HUMAN REVIEW PASS`. Added the immutable
  `phase8-agent-audit-v1` `AuditEvent`, frozen audit statuses, bounded
  allowlist metadata sanitization, an append-only in-memory store
  abstraction and `AgentAuditService`. The service records deterministic
  planner identities, tool success/failure/refusal projections and unknown
  tool attempts without retaining raw questions, arguments, provider output,
  credentials or filesystem/database paths. Durable audit storage remains
  unimplemented.
- Phase 8 P8-6.4.1 Plan Candidate Parser and Validator:
  `HUMAN REVIEW PASS`. Added the immutable
  `phase8-agent-plan-candidate-v1` contract, a bounded strict UTF-8 JSON
  parser, deterministic request binding and semantic checks for intent,
  tool name/version, arguments, registry existence and deny-by-default
  permissions. The validator constructs only a new
  `phase8-agent-plan-v1`; focused tests prove that
  `ToolRegistry.execute` is never called. No provider request,
  AgentService orchestration or tool execution was added.
- Phase 8 P8-6.4.2 LLM Planner Adapter:
  `HUMAN REVIEW PASS`. Added a deterministic
  provider-independent planner request builder, an injected candidate-client
  boundary returning untrusted bytes, strict parser/validator integration,
  bounded audit metadata and deterministic fallback. Invalid candidates and
  provider failures fall back to the deterministic planner; forbidden
  candidate capabilities are refused without reinterpretation. The adapter
  never calls `ToolRegistry.execute`, issues no real provider request and does
  not add AgentService orchestration.
- Phase 8 P8-6.4.3 AgentService Orchestration:
  `HUMAN REVIEW PASS`. Added the typed
  `phase8-agent-request-v1` and `phase8-agent-result-v1` contracts plus the
  `AgentService` orchestration boundary. The service accepts only a validated
  `phase8-agent-plan-v1`, executes at most one request through the static
  `ToolRegistry`, records planner and tool outcomes in the append-only audit
  model, preserves deterministic planner fallback, returns structured
  refusal/tool/audit failures and fails closed when a tool-result audit cannot
  be appended. It adds no direct candidate execution, provider call, durable
  audit store, memory, autonomous loop or dynamic tool capability. The
  implementation is included in interim checkpoint tag
  `phase-8-controlled-agent-complete`.
- Phase 8 P8-6.4 LLM-Assisted Agent Planning Architecture:
  `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. Separated the
  untrusted `phase8-agent-plan-candidate-v1` contract from the unchanged
  `phase8-agent-plan-v1`; froze strict parsing, deterministic validation,
  registry-only execution, deny-by-default permission rechecks, append-only
  audit integration, provider failure fallback and a bounded privacy boundary.
  The freeze added no planner implementation or provider request; P8-6.4.1
  subsequently implemented only the candidate parser/validator slice.
- Phase 8 P8-6.2 Deterministic Agent Planner:
  `HUMAN REVIEW PASS`. Added the versioned
  `AgentPlan` contract, deterministic supported/unknown/forbidden intent
  classification, exact mapping to the four frozen read-only tools, bounded
  question and argument validation, registry resolution and permission
  preflight. The planner cannot execute a tool and adds no LLM, network,
  provider or Agent framework dependency.
- Phase 8 P8-6.1 Static Read-only Tool Registry and Permission Layer:
  `HUMAN REVIEW PASS`. Exactly four immutable
  tools are registered; permissions are deny-by-default; unknown tools,
  forbidden capabilities and unknown or mutation-like arguments fail closed;
  all handlers delegate to existing services; each execution emits bounded
  audit metadata without persisting it yet.
- Phase 8 P8-6 Basic Agent Architecture Freeze:
  `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. The design defines a
  deterministic Agent planner, static
  read-only registry with `get_safety_summary`, `get_event_statistics`,
  `get_event_details` and `generate_safety_report`, deny-by-default
  permissions, bounded execution, append-only audit, explicit refusal
  behavior and reuse of the unchanged P8-5 provider/fallback path. No Agent
  code, LLM tool calling, provider request, dependency or upstream contract
  change was made.
- Phase 8 P8-5 Release Checkpoint:
  `P8-0 THROUGH P8-5 COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. The
  interim checkpoint records the deterministic analytics/context, grounded
  report, fallback, provider boundary, provider validation and documentation
  under annotated tag `phase-8-provider-pipeline-complete`. It is not the
  Phase 8 final release. No provider request was issued during this release
  task. At checkpoint creation, P8-6 was `READY / NOT STARTED`; its subsequent
  architecture freeze passed human review and is recorded above. P8-6.1
  implements the static registry and permission layer, and P8-6.2 adds the
  deterministic planner without tool execution. P8-6.3 adds append-only
  in-memory audit recording with privacy filtering. Basic Agent orchestration
  and Phase 9 remain not started.
- Phase 8 P8-5 Final Real Provider Validation:
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. A separately authorized
  manual request to the OpenAI-compatible
  `deepseek-flash` path returned `PROVIDER_VALIDATED` with transport PASS,
  strict JSON PASS, `phase8-report-v1` PASS, provider grounding VALID,
  `generation_path=PROVIDER`, `degraded=false`, no safe error, no schema
  diagnostics and no fallback. This audit issued no further provider request.
  Earlier configuration non-execution, schema rejection/fallback and prompt
  conformance evidence remain preserved. The validation audit itself performed
  no commit, tag or push; checkpoint publication is recorded separately above.
- Phase 8 P8-5P Provider Prompt Schema Conformance:
  `HUMAN REVIEW PASS`.
  Added a machine-derived compact schema description for the unchanged
  `phase8-report-v1` contract and embedded it in provider request
  construction. Prompt v2 now enumerates top-level and nested required fields,
  exact enum values, nullable-but-required fields, closed-object policy,
  empty-array behavior, provider candidate constants and reference policy.
  The change addresses the prior loose-prose prompt gap without modifying the
  report schema, strict parser, grounding validator, fallback behavior,
  context contract or fingerprint algorithm. Focused provider tests passed
  (`80 passed`) and the full repository gate passed (`539 passed, 1 skipped`).
  No real provider request or `--execute` was performed at that subphase.
- Phase 8 P8-5D Sanitized Provider Schema Diagnostics:
  `HUMAN REVIEW PASS`. Extended the existing
  strict parser failure path with a bounded, deterministic diagnostic model
  for `REPORT_SCHEMA_INVALID`. The public failure code remains unchanged, no
  invalid report is repaired or partially accepted, diagnostics are capped at
  20 with a `truncated` flag, and only safe JSON paths, project-owned
  categories, expected type or constraint and actual JSON type are exposed.
  Raw field values, unknown field names, raw provider content, prompts,
  context payloads, credentials and authorization headers are excluded.
  `ReportService` and the smoke CLI propagate only the sanitized metadata;
  provider failure still routes to the unchanged `TemplateFallback`. No real
  provider request or `--execute` was performed at that subphase.
- Phase 8 P8-5R Real Provider Post-Execution Audit:
  `REAL PROVIDER EXECUTED / PROVIDER REPORT SCHEMA REJECTED / TEMPLATE
  FALLBACK PASS / HUMAN REVIEW PENDING`. The human operator executed one
  OpenAI-compatible request against
  `https://api.deepseek.com/chat/completions` with model `deepseek-flash`.
  The provider response envelope and non-empty message content were received,
  and strict JSON parsing succeeded. `phase8-report-v1` construction then
  failed with `REPORT_SCHEMA_INVALID`, so provider grounding validation was not
  reached. The unchanged `TemplateFallback` generated a report and passed the
  unchanged grounding validator; that `valid` status belongs only to fallback.
  Raw provider content was not persisted, so the exact schema mismatch cannot
  be recovered. This audit issued no additional provider request.
- Phase 8 P8-5:
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`.
  Added one configuration-driven
  OpenAI-compatible chat-completions transport behind the frozen P8-4
  `ProviderTransport` boundary, environment-only credential resolution,
  finite timeout and bounded response handling. `ReportService` now provides
  provider-first orchestration: only a strictly parsed candidate that passes
  the unchanged P8-2 grounding validator can be returned as
  `PROVIDER_VALIDATED`. Semantic and operational failures route to the
  unchanged deterministic `TemplateFallback`; fallback failure returns
  `REPORT_UNAVAILABLE` without exposing an invalid report. Historical attempts
  include a configuration non-execution and a `REPORT_SCHEMA_INVALID`
  rejection with fallback PASS; these remain preserved. The final separately
  authorized manual request followed prompt v2 and passed strict parsing,
  schema construction and grounding, returning `PROVIDER_VALIDATED` with
  fallback not used. No credential value, provider SDK, model, dataset or
  upstream pipeline was changed.
- Phase 8 P8-4: `HUMAN REVIEW PASS`. Added the
  provider-independent `SafetyLLMClient`, deterministic request builder,
  injectable transport protocol and strict untrusted-output parser. Provider
  requests contain only the safe P8-1 context with construction time removed,
  preserve the frozen fingerprint, use fixed request/prompt/schema versions,
  require a finite timeout and enforce a `262144`-byte response limit. Provider
  responses must be exact bounded UTF-8 JSON, cannot contain duplicate keys or
  non-finite values, and are returned only as `unvalidated`
  `phase8-report-v1` candidates. `ReportService.generate_provider_report()`
  passes the candidate through the unchanged P8-2 validator without silently
  selecting fallback. No real provider, transport, SDK, API key, network call,
  model, dataset or upstream pipeline was changed.
- Phase 8 P8-3: `HUMAN REVIEW PASS`. Added the
  deterministic `TemplateFallback` and minimal `ReportService` orchestration.
  The fallback accepts only `phase8-context-v1`, reuses
  `SafetyContextBuilder.fingerprint(context)`, emits
  `TEMPLATE_FALLBACK` with `degraded=true`, copies all unavailable fields
  exactly, and reports only metrics/facts/evidence present in the context.
  `ReportService` runs the unchanged P8-2 grounding validator and returns
  `VALID` only on success; missing, malformed or inconsistent required metrics
  fail closed. No provider SDK, network call, real LLM invocation or upstream
  pipeline change was introduced.
- Phase 8 P8-2: `HUMAN REVIEW PASS`. Added the
  provider-independent `phase8-report-v1` schema and deterministic
  `SafetyReportGroundingValidator`. Reports bind to the P8-1 context
  fingerprint; fact, metric, event, tracker-scoped track, source, evidence and
  structured numeric references are validated against the supplied context.
  Invalid, unknown, unavailable, ungrounded, contradictory or path-leaking
  reports fail closed. No provider SDK, network call, LLM invocation, fallback
  implementation or upstream pipeline change was introduced.
- Phase 8 P8-1: `HUMAN REVIEW PASS`. Added
  deterministic `SafetyAnalyticsService`, read-only bounded analytics over
  `EventQueryService`, opaque source aggregation, `phase8-context-v1` schemas,
  canonical serialization and a method-level context fingerprint. Focused
  tests cover exact counts, interval boundaries, deterministic ordering, empty
  and partial data, source-path exclusion, missing required fields,
  schema validation and reproducibility. No provider, network call,
  dependency or upstream implementation was changed.
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
  M-007 is implemented, real-MP4 validated and human-reviewed; Charter final
  acceptance remains pending in Phase 9. The authorized Phase 7 release
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
- Phase 8 P8-5 was implemented and tested on Python `3.13.6` using the
  standard-library transport. No provider SDK is installed and no
  `PPE_LLM_ENDPOINT`, `PPE_LLM_MODEL` or `PPE_LLM_API_KEY` runtime value is
  configured.
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

- M-007 annotated video rendering: `IMPLEMENTED / REAL MP4 RUNTIME PASS /
  HUMAN REVIEW PASS / CHARTER FINAL ACCEPTANCE PENDING IN PHASE 9`. The design
  is at `docs/designs/phase-07/PHASE_7_M007_ANNOTATED_DEMO_VIDEO_DESIGN.md`;
  the implementation passed real 47/47-frame MP4 validation. Phase 7 owns
  delivery and Phase 9 owns final Charter acceptance.
- M-008 Camera/RTSP: `已经实现 / CHARTER ACCEPTANCE PASS IN P9-B`;
  Phase 7 live-input/real-time monitoring integration owns delivery, and
  Phase 9 recorded final M-008 Charter acceptance after the user's visual
  PASS. This does not claim final acceptance of Phase 9 as a whole.
- Neither requirement is an Extension. ADR-019 clarifies the assignment;
  Charter definitions and acceptance criteria remain unchanged.
- Phase 4 Offline Inference completion does not set P4-G3 to PASS or complete
  the full M-007/M-008 acceptance criteria.

## Latest Reports

- [Phase 8 final release audit report](reports/phase-08/PHASE_8_FINAL_RELEASE_REPORT.md).
- [Phase 8 final integration API report](reports/phase-08/PHASE_8_FINAL_INTEGRATION_API_REPORT.md).
- [Phase 8 final integration Web report](reports/phase-08/PHASE_8_FINAL_INTEGRATION_WEB_REPORT.md).
- [Phase 8 final integration worklog](worklogs/2026/09/2026-09-24-17-phase8-final-integration-web.md).
- [Phase 8 final integration E2E report](reports/phase-08/PHASE_8_FINAL_INTEGRATION_E2E_REPORT.md).
- [Phase 8 final integration E2E worklog](worklogs/2026/09/2026-09-24-18-phase8-final-integration-e2e.md).
- [Phase 8 final integration architecture](designs/phase-08/PHASE_8_FINAL_INTEGRATION_ARCHITECTURE.md).
- [Phase 8 final integration freeze report](reports/phase-08/PHASE_8_FINAL_INTEGRATION_FREEZE_REPORT.md).
- [Phase 8 P8-5 final real provider validation report](reports/phase-08/PHASE_8_P8_5_FINAL_VALIDATION_REPORT.md).
- [Phase 8 P8-5P prompt schema conformance report](reports/phase-08/PHASE_8_P8_5P_PROMPT_SCHEMA_CONFORMANCE_REPORT.md).
- [Phase 8 P8-5P prompt schema conformance worklog](worklogs/2026/09/2026-09-24-10-phase8-p8-5p-prompt-schema-conformance.md).
- [Phase 8 P8-5D schema diagnostics report](reports/phase-08/PHASE_8_P8_5D_SCHEMA_DIAGNOSTICS_REPORT.md).
- [Phase 8 P8-5D schema diagnostics worklog](worklogs/2026/09/2026-09-24-09-phase8-p8-5d-schema-diagnostics.md).
- [Phase 8 P8-5R post-execution audit](reports/phase-08/PHASE_8_P8_5R_POST_EXECUTION_AUDIT_REPORT.md).
- [Phase 8 P8-5 provider E2E report](reports/phase-08/PHASE_8_P8_5_PROVIDER_E2E_REPORT.md).
- [Phase 8 P8-5R real provider smoke worklog](worklogs/2026/09/2026-09-24-08-phase8-p8-5r-real-provider-smoke.md).
- [Phase 8 P8-5 worklog](worklogs/2026/09/2026-09-24-07-phase8-p8-5-provider-e2e.md).
- [Phase 8 P8-4 provider adapter report](reports/phase-08/PHASE_8_P8_4_PROVIDER_ADAPTER_REPORT.md).
- [Phase 8 P8-4 worklog](worklogs/2026/09/2026-09-24-06-phase8-p8-4-provider-adapter.md).
- [Phase 8 P8-2 report grounding validation report](reports/phase-08/PHASE_8_P8_2_REPORT_GROUNDING_VALIDATION_REPORT.md).
- [Phase 8 P8-2 worklog](worklogs/2026/09/2026-09-24-04-phase8-p8-2-report-grounding.md).
- [Phase 8 P8-3 template fallback report](reports/phase-08/PHASE_8_P8_3_TEMPLATE_FALLBACK_REPORT.md).
- [Phase 8 P8-3 worklog](worklogs/2026/09/2026-09-24-05-phase8-p8-3-template-fallback.md).
- [Phase 8 P8-1 deterministic analytics report](reports/phase-08/PHASE_8_P8_1_DETERMINISTIC_ANALYTICS_REPORT.md).
- [Phase 8 P8-1 worklog](worklogs/2026/09/2026-09-24-03-phase8-p8-1-deterministic-analytics.md).
- [Phase 8 P8-0 architecture freeze report](reports/phase-08/PHASE_8_P8_0_ARCHITECTURE_FREEZE_REPORT.md).
- [Phase 8 Safety Intelligence Agent architecture](designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md).
- [Phase 8 P8-6 Basic Safety Agent architecture](designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md).
- [Phase 8 P8-6 architecture freeze report](reports/phase-08/PHASE_8_P8_6_ARCHITECTURE_FREEZE_REPORT.md).
- [Phase 8 P8-6.1 tool registry report](reports/phase-08/PHASE_8_P8_6_1_TOOL_REGISTRY_REPORT.md).
- [Phase 8 P8-6.1 worklog](worklogs/2026/09/2026-09-24-12-phase8-p8-6-1-tool-registry.md).
- [Phase 8 P8-6.2 deterministic planner report](reports/phase-08/PHASE_8_P8_6_2_DETERMINISTIC_PLANNER_REPORT.md).
- [Phase 8 P8-6.3 Agent audit report](reports/phase-08/PHASE_8_P8_6_3_AGENT_AUDIT_REPORT.md).
- [Phase 8 P8-6.3 Agent audit worklog](worklogs/2026/09/2026-09-24-14-phase8-p8-6-3-agent-audit.md).
- [Phase 8 P8-6.4 LLM-assisted planning architecture](designs/phase-08/PHASE_8_P8_6_4_AGENT_PLANNING_ARCHITECTURE.md).
- [Phase 8 P8-6.4 architecture freeze report](reports/phase-08/PHASE_8_P8_6_4_ARCHITECTURE_FREEZE_REPORT.md).
- [Phase 8 P8-6.4.1 plan candidate validator report](reports/phase-08/PHASE_8_P8_6_4_1_PLAN_VALIDATOR_REPORT.md).
- [Phase 8 P8-6.4.2 LLM planner adapter report](reports/phase-08/PHASE_8_P8_6_4_2_LLM_PLANNER_ADAPTER_REPORT.md).
- [Phase 8 P8-6.4.3 AgentService orchestration report](reports/phase-08/PHASE_8_P8_6_4_3_AGENT_SERVICE_REPORT.md).
- [Phase 8 P8-6.4.3 AgentService worklog](worklogs/2026/09/2026-09-24-16-phase8-p8-6-4-3-agent-service.md).
- [Phase 8 Agent implementation checkpoint release report](reports/phase-08/PHASE_8_AGENT_CHECKPOINT_RELEASE_REPORT.md).
- [Phase 8 P8-0 worklog](worklogs/2026/09/2026-09-24-02-phase8-p8-0-architecture-freeze.md).
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

`P9-A PASS / P9-B PASS / P9-C.1 PASS / P9-C.2 PARTIAL /
P9-C.3 PARTIAL / P9-C.3a–e PASS / P9-C.3f PARTIAL / P9-C.3g PASS /
P9-C.3h PASS AS ATTRIBUTION INCREMENT / P9-C.3i PASS AS ATTRIBUTION
INCREMENT / P9-C OVERALL PARTIAL /
P9-D/E/F NOT AUTHORIZED`. The 60-minute lean full graph run reproduced
sustained RSS growth. The staged cached-frame controls found RP-scale
growth already in H0. P9-C.3i then reproduced that growth with real
inference in a fresh thread per cycle, without MonitoringService; a
persistent inference thread collapsed the rate even while H0 sessions
continued. The next minimal proposed step is separately authorized
thread-lifecycle boundedness/native-runtime attribution. No retained
production owner or unbounded leak is confirmed. P9-C.4 and P9-D/E/F
are not authorized.
Durable audit store, agent memory, autonomous loops and real provider
planning calls remain outside authorized Phase 9 work.

P8-0, P8-1, P8-2, P8-3 and P8-4 are human-reviewed PASS. P8-5 implements one
OpenAI-compatible provider transport behind the frozen P8-4 boundary and
provider-first orchestration with strict parsing, unchanged grounding
validation, deterministic fallback and `REPORT_UNAVAILABLE` handling. The
earlier P8-5R request was rejected as `REPORT_SCHEMA_INVALID` before provider
grounding; that failure remains historical evidence. P8-5D adds bounded
sanitized diagnostics for that failure class, and P8-5P replaces loose prompt
prose with a schema description derived from the authoritative report
dataclasses and enums. A later separately authorized manual request followed
prompt v2 and returned `PROVIDER_VALIDATED`: transport, strict JSON,
`phase8-report-v1`, and provider grounding all passed with `PROVIDER`,
`degraded=false`, no safe error, no schema diagnostics and fallback not used.
No further provider request may be executed. The P8-0 through P8-5 interim
checkpoint is released. P8-6 architecture passed human review and P8-6.1 now
implements and has passed review for the static read-only registry and
permission layer. P8-6.2 adds the deterministic planner and has passed human
review. P8-6.3 adds append-only in-memory audit events, privacy filtering and
the `AgentAuditService`, and has passed human review. P8-6.4 passed human
review and froze the LLM-assisted planning boundary and its untrusted
candidate/validation path. P8-6.4.1 implements the strict candidate parser,
validator and deterministic final-plan conversion only, and has passed human
review. P8-6.4.2 adds the provider-independent planner request builder,
injected candidate-client boundary, strict validator integration, bounded
audit metadata and deterministic fallback without real provider execution,
and has passed human review. P8-6.4.3 implements the typed request/result
boundary and `AgentService` orchestration over validated plans, the static
registry and append-only audit events; it has passed human review and is
released under interim checkpoint tag `phase-8-controlled-agent-complete`.
P8-FI final integration architecture passed human review. The typed
`phase8-agent-api-v1` boundary implements trusted identity resolution, one
existing `AgentService` call and bounded UI-safe response projection; it has
passed human review. The Web / Streamlit layer composes that boundary with no
provider client, renders only the five approved UI fields and has passed
human review. A deterministic fixture-driven E2E demo validates the complete
Web facade, Agent API, AgentService, ToolRegistry, append-only audit and UI
projection path; it is `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`.
Phase 8 final integration is `FINAL RELEASED` under
`phase-8-final-integration-complete`. Durable audit storage, memory,
autonomous loops and real provider planning execution remain not implemented,
and Phase 9 P9-A is PASS while P9-B remains PARTIAL. M-021,
M-022 and M-023 remain `待实现`.
# P9-D UI/UX polish — 2026-10-07

P9-D is **PARTIAL / AWAITING HUMAN UI REVIEW**. Seven formal Streamlit pages now use a shared Chinese presentation system. Empty-data AppTests and the full repository suite pass (`771 passed`); preflight, demo check, compileall, pip check, and diff check pass. The local browser displayed the existing 2026-09-23 event. Exact 1366×768 and 1920×1080 review and a completed UI MP4 demo remain open. P9-C remains **PARTIAL / FROZEN**, with no resource fix claimed. See [P9-D report](reports/phase-09/P9D_UI_UX_POLISH_REPORT.md) and [worklog](worklogs/2026/10/2026-10-07-01-p9d-ui-polish.md).
## 2026-10-07 P9-D follow-up: reflective vest confirmation

The user authorized ADR-024, a targeted `NO_VEST` temporal confirmation repair. The supplied 570-frame MP4 now produces the previously missing `NO_VEST` event plus the existing `NO_HELMET` event in an isolated full-chain smoke; both persisted with verified evidence and delivered alerts. Full suite: `773 passed`. This focused fix is **PASS for the supplied video**, with broader false-positive evaluation open. The prior P9-D UI status remains PARTIAL pending human responsive/demo review, and P9-C remains PARTIAL/FROZEN. See [repair report](reports/phase-09/P9D_VEST_CONFIRMATION_FIX_REPORT.md) and [handover](worklogs/2026/10/2026-10-07-02-vest-confirmation-repair.md).

## 2026-10-07 — AI report and assistant presentation follow-up

- Recognized Agent statistics display as Chinese event counts, types, statuses, and times. Report and assistant retain separate results across navigation.
- Focused Web boundary and page tests: 22 passed. Browser result-state visual review remains open. P9-D stays PARTIAL; P9-C is unchanged.
- [Worklog](worklogs/2026/10/2026-10-07-03-agent-result-pages.md).

## 2026-10-07 — AI report body localization

- Corrected the report page's remaining English fallback-template statements and recommendation text in the presentation layer. A fresh six-event browser report showed Chinese findings and three Chinese priority recommendations.
- Focused Web and page tests: 23 passed. P9-D remains PARTIAL; no report contract, provider or event data changed.
- [Worklog](worklogs/2026/10/2026-10-07-04-report-localization.md).

## 2026-10-07 — Realtime monitoring display cadence

- Monitoring preview fragment refreshes every 0.3 seconds instead of every 1.0 second; start/stop no longer request a redundant full rerun.
- A fresh localhost browser run processed all 47 frames of the short MP4 and displayed the preview while frame counts advanced. Focused regression: 22 passed.
- This improves display cadence only. The measured hot CPU inference baseline is about 7.3 FPS on the supplied 1280×720 MP4; model/runtime configuration and the P9-C resource status are unchanged.
- [Report](reports/phase-09/P9D_MONITORING_REFRESH_REPORT.md) and [worklog](worklogs/2026/10/2026-10-07-05-monitoring-refresh.md).

## 2026-10-07 — Processed-frame live preview

- Monitoring now draws frozen-class detection labels/boxes on a copy of each fully processed frame and publishes the newest JPEG to a session-tokenized loopback MJPEG stream. The Streamlit page mounts this image outside its statistics/event fragment, so later service-side frame-rate work does not require changing the page's 0.3-second refresh interval.
- The 47-frame real-MP4 service smoke completed 47/47 frames with 77 detections and a changed annotated last-frame image. Stream/projection and adjacent pipeline tests: 26 passed. Browser visual replay is pending because browser control was unavailable.
- This is a local-browser display path; remote browser access to the loopback preview is not verified. Frozen model, event schema and temporal rules are unchanged. P9-D UI review and P9-C resource work remain open.
- [Report](reports/phase-09/P9D_PROCESSED_FRAME_STREAM_REPORT.md) and [worklog](worklogs/2026/10/2026-10-07-06-processed-frame-stream.md).

## 2026-10-07 — API text language

- Generated alert API messages for `NO_HELMET`, `NO_VEST`, and `PPE_UNKNOWN` are English. Chinese TTS speech remains intact through an event-type-specific spoken projection, satisfying M-017. Agent API fixed fields, errors, and responses were inspected and already English; Chinese input parsing and localized pages remain.
- Focused regression: 23 passed. Full repository suite: 790 passed. Contract keys, enum values, and stored event schema are unchanged. [Report](reports/phase-09/P9D_API_ENGLISH_TEXT_REPORT.md); [worklog](worklogs/2026/10/2026-10-07-10-api-english-alerts.md).

## 2026-10-07 — English page URL paths

- Explicit Streamlit URL paths are `/Monitoring`, `/AI_Report`, and `/AI_Assistant` for the three pages shown by the user. Chinese sidebar labels and source filenames remain.
- Focused tests: 21 passed. Local HTTP requests returned 200 on all three paths. [Report](reports/phase-09/P9D_ENGLISH_PAGE_PATHS_REPORT.md); [worklog](worklogs/2026/10/2026-10-07-11-english-page-paths.md).

## 2026-10-08 — Chinese native toolbar and deployment chooser

Native Streamlit toolbar/menu/deployment text now displays in Chinese using a project-owned presentation script. Browser verification confirmed both surfaces and rerun/open/close behavior; 19 focused tests passed. Streamlit package files are untouched. [Report](reports/phase-09/P9D_CHINESE_SHELL_REPORT.md); [handover](worklogs/2026/10/2026-10-08-01-chinese-streamlit-shell.md).

## 2026-10-08 — DeepSeek report connection

The AI report runtime optionally connects the existing provider client through a server-owned report-only application router. The page distinguishes configured/unconfigured settings and validated LLM output from template fallback. Official DeepSeek Flash uses non-thinking mode. The secure local startup helper is `scripts/start_deepseek_demo.ps1`. Relevant tests: 81 passed. Real provider acceptance is pending: the process and Windows user environment lacked all three expected variables during verification. [Report](reports/phase-09/P9D_DEEPSEEK_REPORT_INTEGRATION.md); [handover](worklogs/2026/10/2026-10-08-02-deepseek-report.md).

## Latest increment: DeepSeek safety assistant (2026-10-08)

Safety assistant ASK now supports configured provider planning and Chinese presentation of verified local query results, with request-bound scope and failure fallback. 90 targeted tests passed. See [report](reports/phase-09/P9D_DEEPSEEK_ASSISTANT_INTEGRATION.md). Overall acceptance status remains unchanged.

## 2026-10-08 Local project LLM configuration

The authorized project credential is stored only in ignored local configuration; safety assistant and reports share the server resolver. 35 targeted tests passed; loaded configuration and absence from tracked files verified. [Handover](worklogs/2026/10/2026-10-08-04-local-llm-config.md). Live provider response remains unverified in this increment.

## 2026-10-08 Assistant repair

Resolved provider configuration changes rebuild the assistant session. Real DeepSeek HTTP 200 and full assistant success / assistant_llm verified using temporary fixture data; 37 targeted tests passed. [Worklog](worklogs/2026/10/2026-10-08-05-assistant-config-refresh.md). Existing browser sessions should refresh and submit again.

## Latest V1 completion increment (2026-10-08)

Implemented the audit closure items at the user's request, excluding RTSP and long stability. New split R2 resolves the reviewed valid/test near duplicates; train bytes and original frozen assets unchanged. Quality charts and supplemental 80-image evaluation PASS. Real report on 52 persisted events returned LLM / non-degraded / grounded-valid; same-scope fallback verified. Deployment/recovery and demo/defense index are provided. [Completion report](reports/phase-09/V1_COMPLETION_REPORT.md), [deployment guide](V1_DEPLOYMENT_GUIDE.md), [demo index](V1_DEMO_AND_DEFENSE.md). No unrestricted final Charter acceptance or long-stability closure is asserted.


## FE-8 响应式布局优化（2026-10-09）

固定导航/顶栏、主内容与数据区域滚动、七页响应式及图表容器监听已实现。49次真实浏览器尺寸测量无主内容横向溢出；前端4测试、API2测试、真实MP4验证通过。实际125%浏览器缩放未执行，现场助手Provider请求超时；不提升V1/P9-C完成状态。详见 [FE8报告](reports/frontend-v1.1/FE8_RESPONSIVE_LAYOUT_REPORT.md)。HUMAN REVIEW PENDING；未commit/push/tag。


## 2026-10-09 鼠标演示与交互修复

用户指定MP4真实鼠标启动/停止/完成验证：完整570帧、1777检测观测、2事件、4通道告警；事件处理与恢复持久化、证据校验/放大/复制、跨页详情和统计筛选通过。修复跨页选择、AI等待与日期范围、四个受控快捷问题及中文展示。真实Provider报告Grounding valid、助手统计与本地今日5条查询通过；前端8测试与API2测试通过。未知英文句型保留原文，P9-C风险保留。详见 [演示修复报告](reports/frontend-v1.1/FUNCTION_DEMO_FIX_REPORT.md)。HUMAN REVIEW PENDING；未commit/push/tag。


## 2026-10-09 相对时间查询与报告中文展示优化

- API 仅对完整匹配的安全事件问题适配最近分钟/小时/天查询（最长 7 天）；继续经过原只读 Agent。手动日期优先，追加删除指令不会被改写。
- 前端展示本地时间范围与无事件状态；补齐截图中的报告中文句式，未适配原文保留在明确标记的展开区域。
- 验证：前端 9 项通过；独立 API 环境 2 项通过（包括空范围、超限、危险追加指令）；生产构建通过；diff --check 通过。
- 运行实例重启被自动审批拒绝，因此当前 8765 后端尚未加载适配；实时端到端查询待手动重启验证。P9-C 原有风险保留。没有 commit/push/tag。

## 2026-10-09 报告证据与导航状态优化

报告数据依据可显示已校验的真实图片并点击放大；七个模块的界面状态在导航切换中保留。真实 Provider 报告和浏览器往返已验证；前端 10 测试、API 2 测试、构建通过。新版本在本机 8767 端口供审核；原 8765 实例仍在运行。详见 [专项记录](reports/frontend-v1.1/REPORT_EVIDENCE_NAV_STATE.md)与[交接记录](worklogs/2026/10/2026-10-09-04-report-evidence-navigation.md)。P9-C 原有风险和人工审核状态不变。

## 2026-10-09 监控最新事件窗口

近期事件以时间倒序展示在独立滚动的右侧卡片中，不再随数量增加撑高页面。真实浏览器测量与前端测试通过，详见 [专项记录](reports/frontend-v1.1/MONITOR_EVENTS_SCROLL_REPORT.md)与[交接记录](worklogs/2026/10/2026-10-09-05-monitor-event-scroll.md)。保持 V1.1 人工审核及 P9-C 原状态。

## 2026-10-09 监控预览指标与镜像

视频右上角显示实际 MJPEG 发布帧率和最新帧更新延迟，并可镜像预览；已移除画面下方说明。用户指定 MP4 实跑 570 帧，浏览器验证运行态数值及完成态空值。新版在本机 `127.0.0.1:8768` 供审核。详见 [专项记录](reports/frontend-v1.1/MONITOR_PREVIEW_TELEMETRY_REPORT.md)。V1.1 人工审核与 P9-C PARTIAL 不变。

## 2026-10-09 V1.1 前端发布门禁

用户已授权提交和远端发布 V1.1 前端版本。发布前检查：旧冻结环境全量回归 812 PASS / 1 SKIP，独立 API 环境 4 PASS，前端 11 PASS 且构建通过；冻结环境预检 PASS，设计图、运行资源、密钥与构建产物不在提交范围。发布检查见 [记录](reports/frontend-v1.1/V1_1_RELEASE_CHECK.md)，交接见[工作日志](worklogs/2026/10/2026-10-09-07-v1.1-release.md)。P9-C PARTIAL 与其他未验收项不因 V1.1 发布改变。


## 2026-10-10 监控输入源与事件告警详情优化

输入源切换清空地址，USB 输入限制非负整数。USB 实际通过服务端 `cv2.VideoCapture(index)` 读取摄像头，并非固定 HP；自动后端编号与 Windows 名称缺少可靠映射，暂不显示猜测的设备名称。事件详情与处理响应附带当前会话近期事件的真实通道投递回执（控制台/网页/语音、成功/失败/跳过、时间、原因代码），不返回可能含敏感信息的异常文本。历史 SQLite 未存回执，明确显示未知，不修改数据库 Schema。

验证：前端 35 PASS；独立 API 3 PASS；生产构建 PASS（既有包体警告）；compileall 与 diff --check PASS。浏览器输入源清空及详情区域可见。自动审批拒绝停止/重启 8775 进程，运行后端尚未加载新增回执字段，前端明确提示需更新后端；真实通道详情浏览器联调 NOT_EXECUTED。P9-C 与 G-CFR-01/RISK-030 及 V1.2 发布 BLOCKED 状态保持。无 commit/push/tag。见 [交接](worklogs/2026/10/2026-10-10-02-monitor-input-alerts.md)。


## 2026-10-10 语音运行环境与告警详情卡片

API 挂载冻结运行环境时显式追加已安装 PyWin32 模块路径及 DLL 搜索目录，修复 `pywintypes` 无法加载；不安装依赖、不修改冻结环境。详情回执改为可换行卡片，展示中文原因与完整代码。前端 35 PASS，API 3 PASS，构建/compileall/diff 检查 PASS。独立 API 解释器真实语音引擎初始化和工作线程 speak 返回 PASS，实际可听性待人工确认。浏览器真实三通道回执卡片宽度/contentWidth 均 386px，无横向溢出；历史语音失败回执保留。运行 8775 尚需人工重启加载本次语音修复，因前次自动审批拒绝重启，本次不绕过。P9-C/G-CFR 及发布状态不变，无 commit/push/tag。


## 2026-10-10 MP4 语音非阻塞与会话隔离

API 语音改为有界队列（32）及固定 COM 工作线程；Windows 原生 SAPI 同步播音只在该线程执行，避免 pyttsx3 循环复用异常与检测线程等待。入队不计投递成功，详情显示等待播报并轮询真实完成结果；指标只统计完成投递。冷却/去重记录按监控会话隔离，保留会话内原30秒规则，避免复用 Track ID 被上一段视频抑制。检测/跟踪/合规/SQLite Schema 与冻结配置不变。

验证：后端语音/告警/API20 PASS，前端35 PASS（详情补充复验1 PASS，非新增独立数量），build/compileall/diff PASS。指定真实MP4两次均completed/570帧/2事件/6通道投递，4条语音最终均delivered，SAPI调用各持续约5–6秒；独立验证目录不写正式数据库。诊断轮确认跨会话TTS_COOLDOWN，保留诊断证据。证据：docs/reports/v1.2/TTS_TWO_MP4_VALIDATION.json；TTS_TWO_MP4_COOLDOWN_DIAGNOSIS.json。实际声音可听性及浏览器主观流畅度仍待人工确认；不能将570帧完整处理宣称为浏览器30FPS。正式8775实例尚需重启加载；此前自动审批阻止重启，本次未绕过。既有P9-C/G-CFR风险保持，未commit/push/tag。


## 2026-10-10 固定事件类型短音频播报

语音只播报事件类型中文短句，去除Track ID/置信度。选择启动时SAPI预生成三种固定WAV、运行时winsound直接播放，保留独立工作线程/有界队列/会话内冷却/真实完成回执。不引入外部音频或依赖；缓存由TemporaryDirectory管理，关闭线程时清理。真实准备0.555秒；三条音频时长2.537/2.611/2.620秒，播放进程CPU时间0.015625/0.015625/0秒（单次观察，非视频帧率/长期保证）。20项语音/告警/API测试PASS，compileall/diff PASS。运行8775自动重启被审批策略阻止，代码待人工重启加载，现有数据保持。P9-C/G-CFR风险及发布门禁不变。


## 2026-10-10 安全助手持久事件只读增强

API Agent 会话显式复用当前dashboard查询实例，避免另建默认数据库运行时；增加事件类型/处理状态/非负Track ID过滤与事件明细快捷问题，沿原AgentApplicationService/四个冻结只读工具/候选参数及引用校验执行。已保存事件、统计、处理状态和证据引用可作为回答依据；不开放写入、删除、任意SQL/文件访问。额外请求字段拒绝，显式修改命令在API拒绝；模型仍只能规划白名单查询和选择已验证事实，不自由生成不受校验的业务结论。前端增加只读筛选及说明，旧后端不支持时明确错误。

验证：API/配置助手/Agent Web边界/工具注册/API契约/LLM候选联合61 PASS；前端35 PASS/build PASS；compileall/diff PASS。补充保存事件读取、类型/日期/轨迹筛选、空结果、修改/删除/SQL拒绝及数据库状态不变测试。此前release检查的空状态失败源于测试中助手未共享隔离数据库；修复绑定，并用明确已保存fixture验证非空/空范围，原空结果断言保留。真实Provider新增查询与浏览器联调未执行；自动审批拒绝8775停止/重启，运行实例未加载本次API。现有CFR/P9-C及V1.2发布门禁不因本次测试关闭；未commit/push/tag。


## 2026-10-10 安全助手输出与受控解读优化

事件明细改为中文字段卡片，展示时间/类型/状态/轨迹/置信度及事件和证据入口，去除重复原始总数字段；明确本条回答的明细展示数量并提示完整记录前往事件中心。证据引用折叠为可放大缩略图，经现有受限图片 API 读取，不将引用存在视为完整性校验通过。新增模型可选择的上下文复核建议、待处理/Track ID/置信度解释；仍使用既有 statement ID 校验、只读白名单及失败降级，不开放自由事实编造或任何修改权限。

验证：相关后端25 PASS、前端37 PASS、生产构建PASS；最初Python测试收集因先导入业务模块缺少冻结运行库失败，按已有API环境引导顺序重新执行通过。真实Provider新解读、浏览器新布局联调及本次后端重启未执行，需人工在启动终端重启并刷新验证。P9-C/CFR及V1.2发布门禁保持，未commit/push/tag。


## 2026-10-10 V1.2 发布授权与补充验收

用户明确授权暂时接受 G-CFR-01/RISK-030 与 P9-C 未决风险，完成版本及真实联调后提交、推送并发布 V1.2；ADR-029记录例外，不改原风险状态与验收标准。前端package/lock、Python包metadata与API统一1.2.0。实时/离线并行未实现。

前端37 PASS/build PASS；独立API/业务联合134 PASS；真实缓存音频两次指定MP4均570帧、2事件、语音全部成功，播报期间帧数继续推进。真实Provider筛选返回与SQLite事件/图片对应，助手保持只读；浏览器1366/1920无横向溢出，事件卡片及证据放大通过，error日志为空。冻结全量回归最终结果见发布检查报告。仍不宣称长期稳定、全分辨率覆盖或人耳可听性已验收。详细证据与发布说明：docs/reports/v1.2/V12_RELEASE_CHECK.md、V12_RELEASE_NOTES.md。

最终冻结业务回归：820 PASS/13独立API文件SKIP（422.17秒，exit0，无deselect），跳过不计为通过；独立API/业务134 PASS。按ADR-029准予已授权V1.2发布，CFR/P9-C状态及原验收标准不变。
