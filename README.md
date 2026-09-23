# ODPlatform-PPE

基于 YOLO11 的智慧工地 PPE 违规检测与智能告警平台。

## 项目简介

项目最终目标是在智慧工地场景中形成完整工程闭环：

```text
数据 -> 训练 -> 评估 -> 推理 -> 人员关联 -> 规则判断
     -> 事件管理 -> 告警 -> 留证 -> 查询 -> 分析
```

最终能力包括 YOLO11 模型训练与评估、图片/视频/实时流推理、ByteTrack
人员跟踪、Person-PPE 关联、Helmet/Vest 合规分析、多帧违规确认、SQLite
事件持久化、截图留证、TTS 告警、Streamlit Web 平台、历史查询、数据大屏、
LLM 安全分析报告和基础 Agent。

## 当前开发状态

- 当前 Phase：Phase 7 — Web & Alert Platform
- 当前 Subphase：Phase 7-Release — Release Preparation Audit
- Phase 状态：RELEASE AUDIT COMPLETE FOR HUMAN REVIEW / PUBLICATION WAITING
- Phase 7 implementation：7-0、7-1、7-2、7-3、7-4、7-5 PASS；7-Release AUDIT COMPLETE FOR HUMAN REVIEW
- Phase 6 — PPE Compliance Event Engine：COMPLETE / RELEASED
- Phase 4 — Offline Inference：COMPLETE / Camera-RTSP Deferred MUST
- EXP-001 Training：COMPLETED / M-004 已经实现
- Phase 3 Evaluation：PASS / M-005 已经实现
- Release model：`models/checkpoints/EXP-001/best.pt`
- Dataset：READY
- Environment：READY
- EXP-001 Configuration：FROZEN / P2-5.1 COMPLETE
- YOLO11n Initialization Weight：REGISTERED / P2-5.2 COMPLETE
- Dependency Lock：FROZEN / P2-5.3 COMPLETE
- Remote Weight Copy：VERIFIED / P2-5.4 COMPLETE
- Training：COMPLETED / P2-5.5
- Inference Runtime：FROZEN / `INF-RUNTIME-001`
- Single Image Inference：VALIDATED / FROZEN CHECKPOINT
- Video：VALIDATED / FROZEN CHECKPOINT
- Camera / RTSP：Deferred MUST / Input Adapters IMPLEMENTED / USB Runtime PASS / RTSP Pending / M-008 PENDING
- M-009 Tracking：IMPLEMENTED / Phase 7-5 Runtime Evidence Recorded / Charter Acceptance Pending
- M-010 Association：IMPLEMENTED / Phase 7-5 Runtime Evidence Recorded / Charter Acceptance Pending
- M-011 Helmet Rule：IMPLEMENTED / Offline Validated
- M-012 Vest Rule：IMPLEMENTED / Offline Validated
- M-013 Temporal Confirmation：IMPLEMENTED / Offline Validated
- M-014 Event Deduplication：IMPLEMENTED / Offline Validated
- Phase 7 architecture：FROZEN
- 已完成准备：Phase 0 工程基线、Phase 1 数据工程，以及 P2-4 AutoDL
  runtime、依赖和数据集完整性验证

## Completed Capabilities

- YOLO11 training
- Evaluation and model selection
- Frozen release checkpoint
- Single-image inference
- Sequential MP4 inference
- Real image validation
- Real MP4 validation
- Person-only ByteTrack adapter implementation with a fail-closed boundary
- Conservative Person-PPE association implementation with explicit unknown
  outcomes
- Conservative Helmet/Vest/Unknown compliance rules
- Five-frame and one-second temporal confirmation
- Active-cycle event deduplication with recovery and cooldown
- Append-only JSONL compliance event storage
- Versioned SQLite event storage with migration checksums, restart-persistent
  history queries, event status updates and idempotent event ingestion
- Atomic JPEG evidence storage with UTC date partitions, relative POSIX paths,
  SHA256/dimension verification and idempotent event snapshot association
- Read-only Streamlit dashboard source for Overview, Event Explorer, Evidence
  Viewer and Statistics
- Dashboard event filtering, source filters, pagination and statistics from
  the SQLite-backed event query service
- Console and in-process Web alert adapters behind one idempotent
  `AlertAdapter` contract
- Unified `VideoSource` lifecycle for MP4, USB Camera and RTSP
- MP4, USB Camera and RTSP adapters with source metadata, observable status,
  credential-redacted RTSP identity, connection failure handling and release
  cleanup
- End-to-end MP4 smoke validation through inference, tracking, association,
  compliance, JSONL, SQLite, snapshot evidence, dashboard queries and
  Console/Web alert delivery
- Real USB Camera open/read/close validation and Streamlit runtime page
  validation for Overview, Event Explorer, Evidence Viewer and Statistics

## Current Runtime

- Runtime ID：`INF-RUNTIME-001`
- Python：3.10.4
- PyTorch：2.5.1+cpu
- torchvision：0.20.1
- Ultralytics：8.4.157
- Device policy：CPU only
- Frozen checkpoint：`models/checkpoints/EXP-001/best.pt`
- Frozen inference configuration：`configs/inference.yaml`

## Validation Evidence

- Image：PASS
- Video：PASS
- Phase 7-5 integrated MP4 pipeline：PASS
- Phase 7-5 dashboard runtime：PASS
- Phase 7-5 USB Camera lifecycle：PASS
- Phase 7-5 RTSP runtime：NOT RUN
- Phase 7-5 Console/Web alerts：PASS
- Phase 7-5 TTS：NOT IMPLEMENTED

The Phase 7-5 validation runtime used Python `3.12.1`, PyTorch `2.5.1+cpu`,
Ultralytics `8.4.157` and Streamlit `1.64.0` in an isolated CPU-only
environment. Python 3.12.1 differs from the frozen `INF-RUNTIME-001` Python
3.10.4 baseline; this is recorded as a release limitation, not a runtime
re-freeze.

Phase 4 的完成声明仅覆盖 structured offline inference。Camera/RTSP、
real-time source behavior、M-008、tracking、association、compliance、
events、alerts、Web、LLM 和 annotated video rendering 不在本次 release
scope 内。

P5-0 已人工审核 PASS，并冻结 `DetectionResult -> TrackResult ->
AssociationResult` 接口、person-only ByteTrack 边界和
containment/IoU/confidence association policy。P5-1 已实现 person-only
`ByteTrackPersonTrackingAdapter`：真实 Ultralytics backend 保持 lazy/private，
只接收 class `0` / `person`，输出项目自有 `TrackResult`。当前环境未安装
Ultralytics/Torch 是 P5-1 review 时的历史限制；Phase 7-5 后续已在隔离
环境中执行一次真实 ByteTrack/MP4 runtime path，但没有单独证明长期 track
ID 连续性，Charter 验收仍未完成。
P5-2 已实现 `PPEPersonAssociationAdapter`：仅关联已有 person track，使用
containment `0.50`、IoU `0.10`、confidence `0.25` 和 ambiguity margin
`0.10`，无法确定时输出 `unknown`，不存在 nearest-distance 强制归属。
P5-3 已用 synthetic pipeline 验证完整的
`DetectionResult -> TrackResult -> AssociationResult` adapter 组合；真实
checkpoint/MP4 validation 在 P5-3 review 时因缺少 Torch 和 Ultralytics
返回 `BLOCKED_RUNTIME_DEPENDENCIES`。Phase 7-5 后续用隔离 runtime 完成
一次真实 detector、tracker、association 和视频端到端运行。因此 M-009
和 M-010 当前记录为 `IMPLEMENTED / Phase 7-5 Runtime Evidence Recorded /
Charter Acceptance Pending`；Charter 锁定状态仍保持 `待实现`，完整验收
通过前不得改写为 `已经实现`。

EXP-001 已完成一轮授权 YOLO11n baseline 训练：95/100 epochs，
best epoch 75，validation precision `0.899`、recall `0.649`、mAP50
`0.767`、mAP50-95 `0.480`。`best.pt` 和 `last.pt` 为 `5,479,891`
bytes；最佳 checkpoint SHA256 为
`1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`。
完整训练证据见 `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`。

Phase 6 已实现离线
`AssociationResult -> ComplianceInput -> ComplianceResult ->
ComplianceEvent -> events.jsonl` 链路，包含保守的 Helmet/Vest/Unknown
规则、多帧确认、事件去重、恢复和冷却。该链路使用确定性 JSON fixture 验证，
不需要 Torch、YOLO、GPU、Camera 或 RTSP。

Phase 7-0、Phase 7-1、Phase 7-2、Phase 7-3、Phase 7-4 和 Phase 7-5 已通过
人工审核。
Phase 7-2 实现了
证据截图文件保存与事件关联：atomic JPEG write、UTC 日期分区、relative
POSIX path、SHA256/尺寸验证、重复证据幂等和 conflict rejection。
`PersistedEvent.snapshot` 现在可以指向真实、已验证的 evidence file。
Phase 7-3 增加了只读 dashboard query service、四个 Streamlit 页面、SQLite
统计查询、证据完整性查看，以及 Console/Web alert adapter 和事件身份幂等
分发。Phase 7-3 review 时触发主机未安装 Streamlit，因此当时只完成页面
源码、服务边界和 schema 测试；Phase 7-5 后续已在隔离环境中执行 AppTest
和真实 Streamlit health/root HTTP check。Phase 6 的四字段 JSONL wire
contract 保持不变。Phase 7-4 新增统一 `VideoSource` interface 和 MP4、USB
Camera、RTSP adapters，具备 `idle/opening/live/degraded/ended/failed/closed`
状态、连接失败处理和 release cleanup；RTSP URI 在日志和 status 中去除
credentials/query。Phase 7-4 review 时未打开真实 device/stream；Phase 7-5
后续验证了真实 USB Camera 的 open/read/close，但 RTSP、reconnect loop 和
monitoring service integration 仍未执行。annotation rendering、automatic
reconciliation、retention 和 TTS 仍未实现。Phase 7 锁定目标仍为
`SQLite + Snapshot + TTS + Streamlit`；Email、WeChat 和 SMS 继续属于未来
Extension。

Phase 7-5 已用 frozen checkpoint 和已验证 MP4 完成一次 CPU end-to-end
runtime smoke path：47/47 帧处理，生成 1 个 `PPE_UNKNOWN` 事件，事件经
Phase 6 JSONL、SQLite、snapshot evidence、dashboard query 和 Console/Web
alerts 全部保持原 `event_id`。真实 USB Camera open/read/close PASS；RTSP
未测。Phase 7-5 已通过人工审核，Phase 7 Release Preparation Audit 已完成
但尚未获得 publication authorization；TTS、real RTSP validation、
annotated video rendering 和 M-008 最终验收仍未完成。Phase 5 的历史
P5-3-G5 `BLOCKED / NOT RUN` 与 M-009/M-010 runtime evidence pending 继续
保留；Phase 7-5 没有改写其历史结论。未来阶段占位接口会明确抛出
`NotImplementedError`，不会返回伪造业务结果。Phase 4A 完成推理架构设计、输入/检测器边界和
`DetectionResult` 数据结构；Phase 4B-0 完成 CPU runtime、checkpoint、
device、threshold、input/output 和错误处理边界冻结；Phase 4B-1 已实现单图
`Image -> YOLO11 -> DetectionResult` 链路和 CLI。默认冻结配置仍为
`execution_enabled: false`；真实推理只通过独立 validation-only 配置显式
启用。
Phase 4B-2a 已完成本地 MP4 视频推理架构设计，新增 model-independent
`FrameData`、`VideoMetadata`、`FrameInferenceResult` 和
`VideoInferenceResult` 契约。Phase 4B-2b 已实现顺序 MP4 reader、
`VideoInferenceService` 和结构化 JSON CLI，并复用单图 `InferenceService`
的冻结 detector 策略。默认 `execution_enabled: false`，未加载 `best.pt`
或执行真实大规模视频推理；Camera/RTSP、tracking、association、event 和
alert 仍不属于当前范围。

Phase 4C-0 已完成真实推理验证设计，定义 external image、短 MP4、
checkpoint/runtime 身份、detection statistics、latency、processing FPS、
Git-ignored `artifacts/validation/` 证据政策和 fail-closed 失败处理。新增
model-independent validation schemas。Phase 4C-1 随后按单独授权执行一次
真实图片验证：使用 `INF-RUNTIME-001` 加载冻结 `best.pt`，外部 public-domain
construction image 的 hot inference 返回 5 个 `DetectionResult`，cold
start 为 14.237 s，warm inference 为 176.386 ms。原始 detection JSON 和
schema report 保存在 Git-ignored `artifacts/validation/P4C-1/`。视频推理、
tracking、association、compliance、events 和 alerts 未执行。

Phase 4C-2 随后按单独授权完成真实 MP4 验证：使用同一冻结 `best.pt` 和
`INF-RUNTIME-001`，顺序处理 external public-domain MP4 的全部 47/47 帧，
未跳帧、未批处理、未异步、未迁移 CUDA。该次 CPU end-to-end 运行共返回
77 个检测（person 76、no_vest 1），处理耗时 15.192 s，处理速率
3.094 FPS。原始 video result、frame summary 和 schema report 保存在
Git-ignored `artifacts/validation/P4C-2/`。RTSP、Camera、tracking、
association、compliance、events、alerts、Web 和 LLM 未执行。

Phase 4 scope 已由 ADR-018 正式调整为 `Offline Inference COMPLETE`。
Camera/RTSP、M-008 和 annotated video rendering 保持 `Deferred MUST`；
本 release 不使用 `phase-4-inference-complete`，而使用准确的
`phase-4-offline-inference-complete`。

EXP-001 的一次性 authorization 已 `CONSUMED`。P2-4、P2-5.1 至 P2-5.4
的 preparation/freeze/verification 步骤不能用于授权第二次训练。

## 最终目标

构建面向智慧工地场景的企业级 PPE 违规检测与智能告警平台。项目重视可复现
数据与训练流程、可审计的模型评估、端到端事件闭环，以及真实可演示的交付
证据，而不只追求单一 mAP 指标。

V1 MUST 目标、Extension 范围和明确非目标已锁定在
`docs/00_PROJECT_CHARTER.md`。阶段边界与顺序锁定在
`docs/01_MASTER_PLAN.md`。

## 架构概览

```text
configs/          YAML configuration
scripts/          Future phase entry points
core/             Domain schemas and future detection pipelines
services/         Application service boundaries
infra/            Database, storage, TTS, and LLM adapters
web/              Future Streamlit application
utils/            Phase 0 paths, config, logging, timing, system helpers
data/             Dataset staging and future data artifacts
models/           Local weights and checkpoints, ignored by Git
artifacts/        Runs, reports, event evidence, and logs
tests/            Unit, integration, E2E, regression, and fixtures
docs/             Locked governance and phase documentation
```

依赖方向应保持为 `web/scripts -> services -> core/infra -> utils`。Phase 0
只提供边界与基础工具，不建立真实业务流水线。

## 目录结构

完整目录由 `configs/`、`core/`、`services/`、`infra/`、`web/`、`utils/`、
`data/`、`models/`、`artifacts/`、`tests/` 和 `docs/` 组成。受 Git 忽略的
数据、模型和运行产物目录通过 `.gitkeep` 保留。

## 环境要求与当前 Runtime

### 本地开发与治理

- Python 3.10 或更高版本
- Git
- Phase 0 基础测试仅需要 `pytest` 和 `PyYAML`

### P2-4 Training Preparation

- AutoDL cloud GPU：NVIDIA GeForce RTX 4090 24GB
- Ubuntu 20.04.5 LTS
- Isolated Conda environment：`ppe-exp001`
- Python 3.10.21
- PyTorch 2.5.1+cu124 / torchvision 0.20.1+cu124
- NVIDIA driver 560.35.03 / CUDA driver API 12.6
- PyTorch CUDA runtime 12.4，`torch.cuda.is_available() == True`
- Ultralytics 8.4.157
- Remote dataset：`CSS-PPE-10-V1`
- Verification：5,604 files、2,799 images、2,799 labels、7-class mapping
  和 full manifest PASS
- Initialization weight：`models/pretrained/yolo11n.pt`，5,613,764 bytes，
  SHA256 `0ebbc80d...7644ee1`
- Remote initialization weight：
  `/root/autodl-tmp/models/pretrained/yolo11n.pt`，size 和 SHA256 与本地
  一致
- Dependency locks：`locks/EXP-001/conda-environment.yml`、
  `conda-explicit.lock`、`pip-freeze-all.txt`
- Runtime fingerprint：`locks/EXP-001/runtime-fingerprint.yaml`

Environment READY、Dataset READY、Configuration FROZEN、Dependency FROZEN
和 Weight REGISTERED / REMOTE VERIFIED 只证明 EXP-001 的输入边界；第二次
训练仍需新的 authorization。

### Phase 4B-0 Inference Runtime

- Runtime ID：`INF-RUNTIME-001`
- Python：3.10.4
- PyTorch：2.5.1+cpu
- torchvision：0.20.1
- Ultralytics：8.4.157
- NumPy：2.2.6
- Device policy：CPU only
- Dependency source：`locks/EVAL-001/requirements.txt`
- Release checkpoint：`models/checkpoints/EXP-001/best.pt`
- `configs/inference.yaml`：FROZEN / `execution_enabled: false`

这是后续 Phase 4B 实现的冻结边界，不是安装、推理、GPU 或性能验证授权。

## Phase 0 历史基线：安装方式

`requirements.txt` 记录后续完整运行计划依赖，并不表示当前都必须安装。
Phase 0 只需要：

```powershell
python -m pip install pytest PyYAML
```

这项安装不会下载数据集或模型权重。`pyproject.toml` 只保存项目元数据和
测试配置，不声明第二套运行时依赖来源。

## Phase 0 历史基线：测试方法

在项目根目录执行：

```powershell
python --version
python -m pytest
python -m compileall .
git diff --check
git status --short
```

测试覆盖核心包导入、六份 YAML、治理文件、五个 V1 类别、路径、日志、无 GPU
系统信息，以及未来业务占位接口必须抛出 `NotImplementedError`。

## 开发文档索引

- `docs/00_PROJECT_CHARTER.md`：锁定目标与 MUST/Extension 验收标准
- `docs/01_MASTER_PLAN.md`：锁定的 P0-P9 阶段计划
- `docs/02_CURRENT_STATUS.md`：当前状态和下一步
- `docs/03_TECHNICAL_DECISIONS.md`：追加式 ADR
- `docs/04_CHANGELOG.md`：变更记录
- `docs/05_TEST_GATES.md`：阶段 Gate
- `docs/06_DATASET_CARD.md`：冻结数据集、mapping 与质量证据
- `docs/07_OPEN_SOURCE_USAGE.md`：开源依赖、参考和许可证记录
- `docs/08_RISK_REGISTER.md`：风险登记册
- `docs/designs/phase-07/PHASE_7_TARGET_ARCHITECTURE.md`：Phase 7 目标架构
- `docs/designs/phase-07/PHASE_7_DATA_CONTRACTS.md`：Phase 7 数据契约
- `docs/reports/phase-07/PHASE_7_ARCHITECTURE_FREEZE_REPORT.md`：Phase 7-0 冻结报告
- `docs/reports/phase-07/PHASE_7_1_EVENT_STORAGE_REPORT.md`：Phase 7-1 事件存储报告
- `docs/reports/phase-07/PHASE_7_2_EVIDENCE_SNAPSHOT_REPORT.md`：Phase 7-2 证据截图报告
- `docs/reports/phase-07/PHASE_7_3_DASHBOARD_ALERT_REPORT.md`：Phase 7-3 Dashboard 与 Alert 报告
- `docs/reports/phase-07/PHASE_7_4_CAMERA_RTSP_REPORT.md`：Phase 7-4 Camera / RTSP 输入报告
- `docs/reports/phase-07/PHASE_7_5_RUNTIME_VALIDATION_REPORT.md`：Phase 7-5 Runtime Validation 报告
- `docs/reports/phase-07/PHASE_7_RELEASE_AUDIT_REPORT.md`：Phase 7 Release Preparation Audit 报告
- `docs/reports/phase-02/P2-4_FINAL_PROVISIONING_REPORT.md`：P2-4 runtime、依赖和数据集验证
- `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`：EXP-001 训练结果、
  指标、产物和披露
- `docs/reports/P2-5.1_CONFIGURATION_FREEZE.md`：EXP-001 配置冻结记录
- `P2-5.1_CONFIGURATION_FREEZE_REPORT.md`：P2-5.1 最终配置冻结报告
- `docs/reports/P2-5.3_DEPENDENCY_FREEZE.md`：EXP-001 依赖与 runtime 冻结记录
- `P2-5.3_DEPENDENCY_FREEZE_REPORT.md`：P2-5.3 最终报告
- `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md`：远端初始化权重完整性验证
- `locks/EXP-001/`：conda、pip 和 runtime fingerprint
- `docs/phases/`：每个阶段的独立文档

## 开源使用原则

依赖优先通过包管理器使用；算法性项目以阅读设计和自主实现为主。禁止复制
未知许可证代码或整份业务架构。所有计划依赖、参考与潜在选择性复用都记录
在 `docs/07_OPEN_SOURCE_USAGE.md`。

## 下一阶段

当前下一允许步骤是：

```text
WAIT FOR PHASE 7 RELEASE HUMAN REVIEW
```

Phase 7 Release Preparation Audit 已核对 repository、documentation、
generated-artifact、secret 和 test 边界。审计阶段不授权 commit、push 或 tag；
必须等待人工审核后才能执行 publication。真实 RTSP、TTS、annotated
rendering 和 M-008 acceptance 仍未完成。
Phase 5 的历史 P5-3-G5 `BLOCKED / NOT RUN` 继续保留。M-009/M-010
已增加 Phase 7-5 runtime evidence，但 Charter acceptance 仍未完成；
Phase 7-5 不把历史 Phase 5 block 改写为 PASS，也不修改冻结 dataset、
mapping、训练配置或 EXP-001 release model。
