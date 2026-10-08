# Phase 09 — Integration & Delivery

## 1. 阶段目标

【LOCKED】全链路测试、性能分析、文档、Demo、答辩交付。

## 2. 进入条件

- Phase 8 Gate 全部 PASS。
- 功能范围冻结，已知缺陷完成分级。

## 3. 当前子任务

Current update (2026-10-07): P9-D Overview and event presentation refinement
is implemented. Event IDs are hidden from visible tables, event time ordering
is selectable and applied before database pagination, source labels and
filters show only `mp4` / `usb{id}` / `rtsp`, and the Overview emphasizes
pending work, evidence-based KPIs, trends and source distribution. Full
regression: 786 passed. Manual responsive review remains open. See
`docs/reports/phase-09/P9D_OVERVIEW_SOURCE_SORT_REPORT.md`.

Current update (2026-10-07): P9-D operator flow refinements are implemented.
Monitoring start/stop controls rerun after one click; the alert KPI now names
channel deliveries. Event rows have Chinese status/actions, persist `OPEN` or
`RESOLVED` through a dedicated write service, and open the selected event in
Evidence Viewer. The lower detail panel and read-only tables' English native
menus were removed. Focused UI/service tests and the full 783-test suite pass.
Physical USB and manual responsive browser review remain open. See
`docs/reports/phase-09/P9D_EVENT_OPERATOR_FLOW_REPORT.md`.

Current update (2026-10-07): the user-authorized realtime CPU profile in
ADR-025 reaches the targeted **24 processed FPS MP4 gate** on the supplied
570-frame video. Two warm production-path runs measured 28.836 and 29.414
FPS and each retained one `NO_HELMET` and one `NO_VEST` event. The unchanged
offline profile remains 640 pixels; monitoring selects a verified 416-pixel
OpenVINO export. A third run with the actual Console/Web/TTS adapters reached
26.000 FPS with six delivered alerts and zero failures. Full regression: 780
passed. This is a bounded local-video result; camera/RTSP throughput, browser display
cadence, broad-scene accuracy and long-run resource stability remain open.
P9-C overall remains PARTIAL. See
`docs/reports/phase-09/P9_CPU_24FPS_REPORT.md`.

Current update (2026-10-07): authorized P9-C.3i inference worker/session
lifecycle isolation **PASS as attribution; P9-C overall PARTIAL**.
Five fresh 20-minute, same-47-frame controls measured RSS
+0.00144/+0.00231/+0.10446/+0.10432/+0.00331 MiB/cycle for
T0 direct inference, T1 persistent worker, T2 fresh inference worker
per cycle, T3 formal H0, and T4 formal H0 with a diagnostic
persistent inference bridge. T2/T3 matched growth while T4 collapsed
toward T1 despite continued H0 session churn. Real inference × fresh
worker-thread lifecycle is strongly supported as the observed
20-minute growth mechanism; a material MonitoringService-specific
increment is not supported. All semantic/exit gates, 762 tests,
compileall, preflight, demo/pip/diff checks and frozen identity passed.
The retained native owner and indefinite production leak remain
unconfirmed. No production architecture change was made. P9-C.4 and
P9-D/E/F are unauthorized. See
`docs/reports/phase-09/P9C3I_INFERENCE_WORKER_LIFECYCLE_REPORT.md`.

Current update (2026-10-07): authorized P9-C.3h real-inference
downstream boundary isolation **PASS as attribution**. H0/H1/H2
fresh 10-minute cached-frame screens completed 72/68/69 cycles with
RSS +0.10190/+0.10508/+0.10653 MiB/cycle. H0 used real inference,
precomputed Track and formal MonitoringService session but no real
Association/Compliance/Event/SQLite/Snapshot/Alert. A fresh 20-minute
H0/RP pair completed 142/150 cycles with +0.10318/+0.10255
MiB/cycle and positive 10–20-minute slopes. **FIRST MATERIAL
DOWNSTREAM DIVERGENCE: NONE; H0 already at RP scale.** P9-C.3g's
coarse real-inference association remains valid, but its suggested
requirement for formal business downstream is superseded by this
narrower result. Production retained owner and indefinite leak remain
unconfirmed. Full regression 755 PASS; frozen identities unchanged.
**P9-C overall PARTIAL; P9-C.4 and P9-D/E/F unauthorized.** See
`docs/reports/phase-09/P9C3H_INFERENCE_DOWNSTREAM_BOUNDARY_REPORT.md`.

Current update (2026-10-04): authorized P9-C.3g unified lean
inference × tracker matrix **PASS as an attribution increment**.
Four fresh 20-minute cached-frame full-downstream controls completed
PP/PR/RP/RR at 150/150/149/148 full cycles, with 597 matching
SQLite events/verified snapshots, 1,194 delivered alerts and zero
failures. All four one-cycle business signatures matched. Their
2–20-minute RSS slopes were +0.01245/+0.00156/+0.10231/+0.10512
MiB/cycle respectively. Real inference has a strong positive effect
with either tracker; real ByteTrack adds no comparable effect.
Inference × downstream interaction is supported, tracker × downstream
is not supported as a material positive effect here, and the
inference × tracker term is weak. Cached RP/RR growth means fresh
source/decode is not required over this 20-minute control. No
production retained owner or unbounded leak is confirmed. Full
regression 742 PASS; package/frozen identity unchanged. **P9-C
overall remains PARTIAL; P9-C.4 and P9-D/E/F are not authorized.**
See `docs/reports/phase-09/P9C3G_LEAN_INTERACTION_MATRIX_REPORT.md`.

Current update (2026-09-27): authorized P9-C.3f final lean real full-graph
confirmation is **PARTIAL / SUSPICIOUS_CONTINUED_GROWTH**. A fresh
production-like MonitoringService graph processed the frozen real MP4 for
3602.625 seconds without heavy observation: 692 complete 47-frame cycles,
32,524 frames, 692 unique SQLite events and verified snapshots, 1,384
Console/Web deliveries, zero failures, and clean final worker/source
lifecycle. Four Dashboard pages passed post-run. External RSS warm-window
means continued rising 469.88 → 483.40 → 496.78 → 510.16 → 521.17 MiB;
the 30–60-minute slope remained +1.2200 MiB/min. This reproduces
resource growth under lean real full-graph observation, without proving
an unbounded production memory leak or a retained owner. Full regression
731 PASS; frozen identities and package inventory unchanged. **P9-C
overall remains PARTIAL; P9-D/E/F and P9-C.4 are not authorized.**
See `docs/reports/phase-09/P9C3F_FINAL_LEAN_FULL_GRAPH_STABILITY_REPORT.md`.

Current update (2026-09-27): P9-C.3e N-harness bridge attribution
**PASS / DIAGNOSTIC HARNESS CONTRIBUTION SUPPORTED**. A one-cycle
S4/H semantic comparison matched 47 frames, 77 detections, 66 tracks,
compliance and event at frame 24, SQLite data, snapshot SHA256 and
two alert statuses. H reused historical N diagnostic wiring and ran
150 cycles/events over 20 minutes: RSS +0.03127 MiB/cycle and
+0.22384 MiB/min in the 10–20-minute window, reproducing N's
direction/order of magnitude (+0.0238 MiB/cycle). A matched lean S4
J ran the same 150 cycles/events for 20 minutes at only +0.00408
MiB/cycle and +0.02986 MiB/min in the late window. H/J supports
an observation/harness contribution without identifying one faulty
wrapper or a production downstream leak. Historical N remains valid
as an instrumented observation; at this P9-C.3e checkpoint P9-C
overall was PARTIAL because lean real full-graph boundedness was
untested. P9-C.3f was the next separately authorized action at that
time; its completed result is recorded above. P9-C.4 and P9-D/E/F
remain unauthorized. See
`docs/reports/phase-09/P9C3E_N_HARNESS_BRIDGE_REPORT.md`.

Current update (2026-09-27): P9-C.3d Monitoring lifecycle and
downstream interaction isolation **PASS as an attribution increment**.
Formal S0 completed 150 repeated MonitoringService sessions/7050 cached
real frames in 20 minutes with balanced worker/source lifecycle and
+0.000344 MiB/cycle warm RSS, far below historical N +0.0238. S1–S4
each completed 75 cycles in separate processes, with warm RSS slopes
−0.00302, +0.000827, +0.00197 and +0.00464 MiB/cycle. S4 persisted
75 events, made 75 real snapshots and delivered 150 alerts, but did
not reproduce N's sustained magnitude. No material first downstream
divergence was found, so conditional stage and tracker pairs were not
triggered. N's observer/recorder/JSONL/rolling-log harness differs
from the lean staged control; the N residual and tracker/downstream
interaction remain unresolved. **P9-C overall PARTIAL; full production
graph boundedness and an unbounded leak are both unproven.** P9-C.4
and P9-D/E/F remain unauthorized. See
`docs/reports/phase-09/P9C3D_DOWNSTREAM_INTERACTION_ATTRIBUTION_REPORT.md`.

Current update (2026-09-27): P9-C.3c tracker native lifecycle attribution
**PASS / NEITHER CLEARLY**. P, Q and R each completed 149 paced tracker-only
cycles over 20 minutes. Persistent update P RSS was +0.00155 MiB/cycle;
construct/reset-only Q +0.00080; combined real tracker-only R +0.00168,
all far below the directional L−N +0.0192 MiB/cycle difference. Their
10–20-minute windows approached a stable plateau, so no tracker-only
path met the trigger for a 60-minute extension. The L/N full-downstream
difference remains real, but standalone update or reset/reconstruct is
not established as its owner. Tracker × downstream interaction or
cross-component allocator behavior remains possible. Full graph
boundedness remains unproven; P9-C overall PARTIAL, with P9-C.4 and
P9-D/E/F unauthorized. See
`docs/reports/phase-09/P9C3C_TRACKER_NATIVE_ATTRIBUTION_REPORT.md`.

Current update (2026-09-26): P9-C.3b inference/tracker isolation **PASS**.
Real variable-frame inference alone (M) ran 125 cycles/20.125 minutes with
+0.00736 MiB/cycle warm RSS, weak as a standalone explanation of K−L.
Verified real precomputed Track output preserved one-cycle L/N semantics.
N completed 150 paced cycles/events in 20 minutes; RSS fell from L's
+0.0430 to +0.0238 MiB/cycle, supporting a ByteTrack update/reset
contribution while leaving non-tracker residual growth. No unbounded
full-graph leak or eventual plateau is proven. P9-C overall remains
PARTIAL; P9-C.4 and P9-D/E/F are unauthorized. See
`docs/reports/phase-09/P9C3B_INFERENCE_TRACKER_ISOLATION_REPORT.md`.

Current update (2026-09-26): P9-C.3a precomputed-detection downstream
isolation **PASS**. A real 47-frame/77-detection fixture and independent
model recheck passed; one-cycle K/L business semantics matched. The paced
20-minute L control completed 148 cycles/events versus K's 150, with RSS
slopes +0.3211 versus +0.9737 MiB/min and nearly equal Python-traced
slopes. This supports a **MULTI-CONTRIBUTOR PATTERN**, not a proven YOLO
leak or bounded full graph. P9-C overall remains PARTIAL; P9-C.4 and
P9-D/E/F are unauthorized. Full regression: 693 PASS. See
`docs/reports/phase-09/P9C3A_PRECOMPUTED_DETECTION_CONTROL_REPORT.md`.

Current update (2026-09-26): P9-C.3 is PARTIAL / ATTRIBUTION INCONCLUSIVE. A 30-minute
full-chain control reproduced MP4 RSS growth; the 60-minute source-only
control approached a late plateau. Python-traced and alert retained memory
do not explain the full-chain trend. A predecoded-frame full-chain control
still rose +0.9737 MiB/min, so repeated source decoding is not the sole
owner. Exact full-chain allocation ownership is unproven. P9-C remains
PARTIAL; P9-D/E/F are not
authorized. See `docs/reports/phase-09/P9C3_RESOURCE_GROWTH_ATTRIBUTION_REPORT.md`.

Current update (2026-09-25): P9-A PASS, P9-B PASS and P9-C.1 PASS remain
accepted. Authorized P9-C.2 long runs completed: USB 60 minutes plus restart
had a warm RSS plateau and intact correctness; MP4 completed 675 full cycles
with intact correctness but sustained unexplained warm RSS growth. **P9-C.2
PARTIAL / P9-C.3 RESOURCE LEAK ATTRIBUTION REQUIRED. P9-D/E/F NOT
AUTHORIZED.** Phase 9 final delivery Gate remains pending. Details:
`docs/reports/phase-09/P9C2_LONG_RUN_STABILITY_REPORT.md`.

P9-A Final Audit & Runtime Freeze：PASS（2026-09-25）；
FINAL-DEMO-RUNTIME-001 FROZEN / VALIDATED。Phase 9 交付 Gate 尚未验收；
P9-B subsequently authorized; 2026-09-25 real MP4 smoke chain is PARTIAL.
One PPE_UNKNOWN event reached SQLite, snapshot and alerts, but the demo venv
drifted when Ultralytics automatically installed unpinned `lap==0.5.13`.
Violation scenes and Camera OR RTSP full-chain acceptance remain pending.
P9-C NOT READY. 审计及冻结记录见
`docs/reports/phase-09/P9A_FINAL_AUDIT_REPORT.md` 和
`docs/reports/phase-09/P9A_FINAL_DEMO_RUNTIME_FREEZE_REPORT.md`；P9-B 记录见
`docs/reports/phase-09/P9B_FULL_CHAIN_VALIDATION_REPORT.md`。

P9-B.1 follow-up (2026-09-25): the unpublished final-demo lock was corrected
to pin `lap==0.5.13`; independent clean install and real ByteTrack MP4 run
had identical before/after package sets. USB Camera processed 143 real frames
and produced NO_HELMET/NO_VEST events, but live-page visual review and
short cold-start stop reliability remain open. P9-B remains PARTIAL and
P9-C remains NOT READY. See `P9B_RUNTIME_DRIFT_REPAIR_REPORT.md` and
`P9B_USB_FULL_CHAIN_REPORT.md` in the Phase 9 reports directory.

P9-B.2 follow-up (2026-09-25): live browser USB read/detect/display, event
evidence, Stop/restart and five real processed-frame lifecycle rounds passed.
The worker now checks Stop after camera read. A cold inference already in
progress may still exceed the five-second Stop join. Per-frame real USB
tracking/association trace is recorded, but controlled crossing, occlusion,
re-entry and ambiguous multi-person scenes were unavailable. G8 and G10 stay
PARTIAL; P9-B stays PARTIAL and P9-C NOT READY. See the P9-B.2 stop lifecycle,
tracking and M-008 assessment reports. Phase 9 final Charter acceptance is
pending.

P9-B.3 Charter re-adjudication (2026-09-25): the existing real-scene
ByteTrack/association evidence meets locked M-009/M-010 and G8; the real
Camera read/detect/display and observable zero-frame failure meet locked
M-008 and G10. Complex crossing/occlusion/re-entry and a five-second cold
Stop bound are recorded limitations, not Charter MUST clauses. G1–G13 meet
their technical criteria, with 684 tests PASS. P9-B is READY FOR HUMAN
VISUAL SIGN-OFF; final P9-B PASS and Charter status updates await the user's
confirmation. P9-C remains unauthorized. See
`P9B3_CHARTER_GATE_READJUDICATION_REPORT.md`.

P9-B.3 human closure (2026-09-25): the user replied `pass` to the USB Camera
Realtime Monitoring visual checklist. HUMAN VISUAL REVIEW PASS. G1–G13 are
PASS and P9-B RESULT: PASS. Charter M-008/M-009/M-010 acceptance is recorded
without changing their locked descriptions or criteria. P9-C remains NOT
AUTHORIZED; Phase 9 final delivery Gate is still pending.


### Deferred MUST final acceptance ownership (ADR-019)

Phase 9 owns final Charter acceptance of M-007, including annotated video
output, and M-008, including Camera OR RTSP live detection/display and observable
failure behavior. Phase 7 owns implementation and page/service integration.
Phase 4 offline completion is not evidence of full M-007/M-008 acceptance.
Missing evidence blocks final V1 delivery; these requirements cannot be waived
or treated as Extensions. The locked phase goal is unchanged.

## 4. 实现设计

固定演示环境与数据；端到端覆盖输入、检测、跟踪、关联、事件、留证、查询、
报告；所有性能结论引用机器配置、数据规模和命令。

## 5. 测试要求

- 单元、集成、端到端测试套件全部执行。
- 延迟、吞吐、资源和稳定性测试并记录边界。
- 全新环境按 README/部署文档复现。
- Demo 与答辩证据可追溯到真实运行结果。

## 6. Gate

| Gate | Requirement |
| --- | --- |
| P9-G1 | 端到端基本流程通过且证据完整 |
| P9-G2 | 性能结果有环境、数据和命令支撑 |
| P9-G3 | README、部署和故障排查文档可复现 |
| P9-G4 | Demo 与答辩证据覆盖全部 MUST 验收 |

## 7. 已知问题

最终模型、数据集、硬件和演示网络条件尚未确定。

## 8. 开发记录

- 2026-09-21: 计划建立，未开始实现。

### 2026-10-07 实时监控画面刷新优化

已将实时监控 Streamlit fragment 的刷新间隔从 1.0 秒缩短到 0.3 秒，启动和停止后避免额外强制重绘。逐帧推理、跟踪、PPE 关联、事件确认与持久化链路，以及冻结模型与配置均未改动。干净启动的浏览器演示中，47 帧 MP4 的预览与计数同步前进并完成处理。CPU 推理的热态基线约 7.3 FPS，实际推理吞吐没有由本次 UI 改动提高；P9-C 资源增长问题仍为 PARTIAL。详见 [刷新报告](../reports/phase-09/P9D_MONITORING_REFRESH_REPORT.md)。

### 2026-10-07 已处理帧实时回显

监控服务现在复用已有检测标注渲染器，在一帧完成检测、跟踪、关联、事件处理后发布对应标注画面。本地浏览器画面通过独立、会话隔离的 MJPEG 通道接收最新帧，不再受 Streamlit 统计/事件 fragment 的 0.3 秒刷新上限约束。短视频全链路与流协议测试通过；浏览器连续播放的目视检查因控制接口暂不可用而待补。该增量不改变冻结模型、逐帧事件判定和持久化语义；P9-D/P9-C 总体状态未因此关闭。详见 [实时回显报告](../reports/phase-09/P9D_PROCESSED_FRAME_STREAM_REPORT.md)。
# P9-D UI/UX polish checkpoint — 2026-10-07

Authorized P9-D presentation work is **PARTIAL / AWAITING HUMAN UI REVIEW**. Seven formal Streamlit pages are polished; automated suite is `771 passed`. Exact responsive review and completed UI MP4 demo remain open. No backend acceptance or P9-C resource claim changes. See [P9-D report](../reports/phase-09/P9D_UI_UX_POLISH_REPORT.md).
## 2026-10-07 P9-D follow-up — vest confirmation repair

User-authorized ADR-024 changes only `NO_VEST` temporal confirmation to tolerate brief conflicting vest classifications while retaining a five-frame violation run and one-second evidence span. The isolated 570-frame MP4 full-chain run completed with one `NO_VEST` and one `NO_HELMET`, two SQLite rows, verified snapshots, and four delivered alerts. Full pytest: `773 passed`. This focused defect repair is **PASS** on the supplied video; broad-scene false-positive evaluation and the P9-D UI human review remain open. P9-C stays PARTIAL/FROZEN. [Report](../reports/phase-09/P9D_VEST_CONFIRMATION_FIX_REPORT.md).

## 2026-10-07 P9-D follow-up — Agent result pages

AI report and assistant display recognized event statistics in Chinese and retain separate results for report generation and assistant questions. The five-field read-only projection and provider-disabled Web runtime remain unchanged. Focused Web and page tests: 22 passed. Browser result-state visual review remains open after a stale-module service restart. P9-D remains PARTIAL.

## 2026-10-07 P9-D report localization follow-up

The fixed, grounded template report now renders its known summary, type counts, evidence availability, tracker-scope caveat, dominant-type caveat and priority recommendations in Chinese. This changes presentation only; report generation, validation and stored evidence remain unchanged. Focused tests: 23 passed. A fresh browser generation on the ordinary six-event database showed the translated report and three translated recommendations. P9-D overall remains PARTIAL pending full responsive/human review.

## 2026-10-07 API text language follow-up

Generated alert messages exposed by Console JSON and Web alert history use English for all three event types. The TTS adapter derives the existing Chinese spoken warning from the event type, keeping the locked Chinese voice requirement independent of the API message. Agent API field names, errors, and fixed responses were already English; Chinese query matching and Streamlit localization remain in their respective input/presentation layers. Focused tests: 23 passed; full regression: 790 passed. No field names, enum values, event persistence, or alert delivery semantics changed. See [report](../reports/phase-09/P9D_API_ENGLISH_TEXT_REPORT.md).

## 2026-10-07 English URL paths for three pages

The existing monitoring, AI report, and AI assistant `st.Page` entries now declare `Monitoring`, `AI_Report`, and `AI_Assistant` as URL paths. Chinese navigation titles and page scripts stay unchanged; `st.switch_page` continues to target the script path. Focused page/navigation/Web boundary tests: 21 passed. Local HTTP requests to the three paths returned 200, although Streamlit's HTML shell response alone does not prove client-side page rendering. Existing Chinese-path bookmarks should use the new paths. See [report](../reports/phase-09/P9D_ENGLISH_PAGE_PATHS_REPORT.md).

## 2026-10-08 Chinese Streamlit shell presentation

The project-owned shell translator localizes the native toolbar, main menu and deployment chooser using `st.html` with static repository JavaScript. It updates only known text nodes and accessibility labels inside these controls, leaving DOM elements and click handlers intact. A single MutationObserver handles newly opened controls and subsequent reruns. Browser inspection verified the Chinese menu, version footer, all deployment descriptions and action labels, plus rerun and dialog close behavior. Focused tests: 19 passed. Overall Phase 9 gates are unchanged. See [report](../reports/phase-09/P9D_CHINESE_SHELL_REPORT.md).

## 2026-10-08 Configured DeepSeek report application

ADR-026 adds optional server-configured provider composition for explicit report operations. The ordinary ASK application, deterministic planner, role policy and five-field UI projection remain unchanged. Missing configuration and provider failure retain the validated local fallback. Tests: 81 passed across configured application, Web boundary/pages, transport, provider fallback and grounding. The running app was restarted. Real DeepSeek validation is pending local credential entry. [Report](../reports/phase-09/P9D_DEEPSEEK_REPORT_INTEGRATION.md).

## 2026-10-08 Configured DeepSeek safety assistant

ADR-027 activates bounded provider planning and selection of verified Chinese statements for ASK. Existing static tools, validation and local fallback remain authoritative. Direct typed question submission is enabled. Targeted integration, Web, planner and transport checks: 90 passed. This increment does not close Phase 9. See [report](../reports/phase-09/P9D_DEEPSEEK_ASSISTANT_INTEGRATION.md).

## 2026-10-08 Project-local LLM credential

Explicit user authorization adds an ignored project-local credential file, resolved by the server composition before process/user settings. Tracked YAML policy and provider schema remain unchanged. 35 targeted tests passed. Git ignore/untracked checks and credential scan of tracked files passed. No remote push performed.

## 2026-10-08 Assistant configuration refresh repair

The session runtime now fingerprints resolved provider settings and rebuilds on change, invalidating old adapter results. Unchanged configuration retains refresh deduplication. Real configured DeepSeek probe returned HTTP 200; a full assistant flow over a temporary one-event fixture returned success / assistant_llm. 37 targeted tests passed. No Phase 9 closure claimed.

## 2026-10-08 V1 completion scope

User-authorized V1 audit items are implemented, excluding RTSP and long stability: session regression/test isolation, split R2 integrity repair and 80-image evaluation, quality charts, real grounded DeepSeek report plus fallback, deployment/recovery and demo/defense index. Preflight/pip check/compileall and delivery checker pass. Historical frozen artifacts and Charter wording/statuses remain unchanged. Detailed validation and current regression record: [V1 completion report](../reports/phase-09/V1_COMPLETION_REPORT.md). This scoped readiness does not close the historical long-stability gate or imply public production acceptance.
