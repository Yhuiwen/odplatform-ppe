# Phase 09 — Integration & Delivery

## V1.2-G 集成验收（2026-10-10）

G授权确认F已审核。本轮显示优化、八种真实图片输入、47/570真模型链、混合FIFO/排队取消、同Worker三视频、API安全与四尺寸浏览器检查已执行。最终Vue34 PASS/build PASS、独立API109 PASS、真实8用例分轮有通过证据、冻结819 PASS/12独立API文件跳过。首轮570帧在推理前仍出现CFR间隔拒绝，后续十次严格探测和三任务通过未解释失败：G-CFR-01/RISK-030为发布阻塞。G结论BLOCKED / HUMAN REVIEW PENDING；P9-C PARTIAL/FROZEN、Global Phase9不关闭，未提交/推送/Tag。[G报告](../reports/v1.2/V12_G_FINAL_ACCEPTANCE_REPORT.md)。

## V1.2-F 离线工作台（2026-10-09）

F授权确认E审核通过。Vue离线三个Tab、上传/进度/取消/历史、图片对比、H.264/时间轴/只读证据与真实manifest下载已实现；受限原图/HEAD与Range验证缓存补充通过。前端31 PASS/build PASS，独立API106非模型+5真实资源PASS，冻结819 PASS/11独立API文件跳过。四种桌面尺寸和原七页无横向溢出，真实图片/47/570链路和下载/取消通过。F门禁PASS / HUMAN REVIEW PENDING；Global Phase9、P9-C不变，不进入G或发布。[F报告](../reports/v1.2/V12_F_FRONTEND_REPORT.md)。

## 1. 阶段目标

【LOCKED】全链路测试、性能分析、文档、Demo、答辩交付。

## 2. 进入条件

- Phase 8 Gate 全部 PASS。
- 功能范围冻结，已知缺陷完成分级。

## 3. 当前子任务

Current update (2026-10-08): user-authorized V1.1 Vue/FastAPI frontend migration is implemented for all seven formal pages and pending human review. The independent API runtime reuses the frozen business services; an isolated real 47-frame MP4 run completed with processed MJPEG preview. Frontend build, two API tests, 810 V1 regression tests (one intentional API test skip in the frozen environment), and seven-page browser checks at 1366×768 and 1920×1080 passed. Physical USB/RTSP, live Provider and P9-C long stability remain unverified; no existing Phase 9 gate or Charter status is promoted. See `docs/reports/frontend-v1.1/V1_1_FRONTEND_MIGRATION_REPORT.md`.

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


## FE-8 响应式布局优化（2026-10-09）

固定导航/顶栏、主内容与数据区域滚动、七页响应式及图表容器监听已实现。49次真实浏览器尺寸测量无主内容横向溢出；前端4测试、API2测试、真实MP4验证通过。实际125%浏览器缩放未执行，现场助手Provider请求超时；不提升V1/P9-C完成状态。详见 [FE8报告](../reports/frontend-v1.1/FE8_RESPONSIVE_LAYOUT_REPORT.md)。HUMAN REVIEW PENDING；未commit/push/tag。


## 2026-10-09 鼠标演示与交互修复

用户指定MP4真实鼠标启动/停止/完成验证：完整570帧、1777检测观测、2事件、4通道告警；事件处理与恢复持久化、证据校验/放大/复制、跨页详情和统计筛选通过。修复跨页选择、AI等待与日期范围、四个受控快捷问题及中文展示。真实Provider报告Grounding valid、助手统计与本地今日5条查询通过；前端8测试与API2测试通过。未知英文句型保留原文，P9-C风险保留。详见 [演示修复报告](../reports/frontend-v1.1/FUNCTION_DEMO_FIX_REPORT.md)。HUMAN REVIEW PENDING；未commit/push/tag。


## 2026-10-09 相对时间查询与报告中文展示优化

- API 仅对完整匹配的安全事件问题适配最近分钟/小时/天查询（最长 7 天）；继续经过原只读 Agent。手动日期优先，追加删除指令不会被改写。
- 前端展示本地时间范围与无事件状态；补齐截图中的报告中文句式，未适配原文保留在明确标记的展开区域。
- 验证：前端 9 项通过；独立 API 环境 2 项通过（包括空范围、超限、危险追加指令）；生产构建通过；diff --check 通过。
- 运行实例重启被自动审批拒绝，因此当前 8765 后端尚未加载适配；实时端到端查询待手动重启验证。P9-C 原有风险保留。没有 commit/push/tag。

## 2026-10-09 报告证据图片与导航状态

报告引用已关联同范围已持久化事件，只向前端提供服务端完整性验证通过的事件证据 ID；报告直接显示缩略图并可放大。路由组件及主内容滚动位置在模块切换时保留，监控页离开时暂停轮询/预览。前端 10 项、API 2 项测试及构建通过；真实 Provider 报告 Grounding valid，24 条引用对应 24 张可用图片；浏览器验证报告、日期、助手草稿在导航往返后保留。详见 [专项记录](../reports/frontend-v1.1/REPORT_EVIDENCE_NAV_STATE.md)。P9-C 风险保持，V1.1 仍待人工审核。

## 2026-10-09 实时监控近期事件窗口

右侧事件卡片已改为自适应高度的独立滚动窗口，按发生时间倒序并在新事件到来时回到列表顶部。前端 11 项测试及构建通过；真实浏览器验证列表滚动不带动主内容。详见 [专项记录](../reports/frontend-v1.1/MONITOR_EVENTS_SCROLL_REPORT.md)。原服务契约和 P9-C 状态不变。

## 2026-10-09 监控预览指标与镜像

右上角新增实际发布帧率、最新帧更新延迟和预览镜像开关，移除下方说明。指定 MP4 实跑 570 帧并在浏览器验证；前端 11 项、API 4 项测试通过。详见 [专项记录](../reports/frontend-v1.1/MONITOR_PREVIEW_TELEMETRY_REPORT.md)。P9-C 风险与人工审核状态不变。

## 2026-10-09 V1.1 发布门禁

用户授权发布 V1.1 前端版本；工作区范围、远端同步、敏感信息与忽略规则检查通过。冻结环境全量回归 812 PASS / 1 SKIP（API 环境单独 4 PASS），前端 11 PASS 且构建通过；预检、编译与暂存差异检查通过。此版本发布不关闭 Phase 9 或 P9-C；USB/远端 RTSP 及长时资源风险仍按既有记录。详见 [发布检查](../reports/frontend-v1.1/V1_1_RELEASE_CHECK.md)。

## 2026-10-09 V1.2-D 离线原分辨率视频导出

用户授权的 V1.2-D 已实现逐帧冻结 YOLO11 推理、原尺寸标注和受监督 libx264 编码。真实 47/570 帧 MP4 输入、推理、标注、提交及实际输出帧数一致，均为 1280×720，分别保留 24000/1001 与 30 FPS；浏览器完整播放通过。单 Worker 顺序复用模型、取消/重启及受控产物校验有测试。联合 API 测试 67 PASS，补充恢复与非模型集合 65 PASS（合计 68 个不同测试）；冻结环境全量复验 819 PASS / 7 独立 API 文件跳过，前端 11 PASS/build PASS。初轮验证 ZIP 触发旧资产门禁，已仅隔离本阶段生成的 ZIP 后复验；旧门禁未放宽。视频事件分析 NOT_IMPLEMENTED，真实 FullHD YOLO 和长期稳定性未执行；P9-C PARTIAL/FROZEN 与 Phase 9 验收不变。没有进入 E，没有 commit/push/tag。[D 报告](../reports/v1.2/V12_D_VIDEO_RENDERING_REPORT.md)。HUMAN REVIEW PENDING。


### V1.2-C supplemental verification (2026-10-09)

Added inference-call timing, detection context rejection and pre-publication input hash recheck. Separate C/B/API suite 39 PASS; real original-size image chain and three-job model reuse PASS. Existing D preserved, video dispatch disabled only in isolated C test. P9-C unchanged; HUMAN REVIEW PENDING. See [C report](../reports/v1.2/V12_C_IMAGE_INFERENCE_REPORT.md).


### V1.2-E offline events/evidence (2026-10-09)

User authorization confirms D review passed and authorizes E only. Per-job Collector reuses frozen ByteTrack/association/ComplianceService/EventEngine, SQLite repositories and original-resolution dual PNG evidence, with single-pass detections and verified exports/read-only APIs. Final combined API/image/video suite107 PASS, frozen819 PASS/10 separate-API file skips, Vue11 PASS/build PASS. Real47/570 frames retained, events1/2 and evidence2/4; realtime events/alerts/state isolated. Historical intermittent pre-inference CFR failure recorded despite final passing rerun; P9-C remains PARTIAL/FROZEN. E gate PASS / HUMAN REVIEW PENDING, no F or publication. [E report](../reports/v1.2/V12_E_EVENTS_EVIDENCE_REPORT.md).


## 2026-10-10 监控输入源与事件告警详情优化

输入源切换清空地址，USB 输入限制非负整数。USB 实际通过服务端 `cv2.VideoCapture(index)` 读取摄像头，并非固定 HP；自动后端编号与 Windows 名称缺少可靠映射，暂不显示猜测的设备名称。事件详情与处理响应附带当前会话近期事件的真实通道投递回执（控制台/网页/语音、成功/失败/跳过、时间、原因代码），不返回可能含敏感信息的异常文本。历史 SQLite 未存回执，明确显示未知，不修改数据库 Schema。

验证：前端 35 PASS；独立 API 3 PASS；生产构建 PASS（既有包体警告）；compileall 与 diff --check PASS。浏览器输入源清空及详情区域可见。自动审批拒绝停止/重启 8775 进程，运行后端尚未加载新增回执字段，前端明确提示需更新后端；真实通道详情浏览器联调 NOT_EXECUTED。P9-C 与 G-CFR-01/RISK-030 及 V1.2 发布 BLOCKED 状态保持。无 commit/push/tag。见 [交接](../worklogs/2026/10/2026-10-10-02-monitor-input-alerts.md)。


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
