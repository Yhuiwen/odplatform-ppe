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

- 当前 Phase：Phase 2 — Training
- Phase 状态：EXP-001 COMPLETED / M-004 已经实现
- Dataset：READY
- Environment：READY
- EXP-001 Configuration：FROZEN / P2-5.1 COMPLETE
- YOLO11n Initialization Weight：REGISTERED / P2-5.2 COMPLETE
- Dependency Lock：FROZEN / P2-5.3 COMPLETE
- Remote Weight Copy：VERIFIED / P2-5.4 COMPLETE
- Training：COMPLETED / P2-5.5
- Best checkpoint：`models/checkpoints/EXP-001/best.pt`
- 已完成准备：Phase 0 工程基线、Phase 1 数据工程，以及 P2-4 AutoDL
  runtime、依赖和数据集完整性验证

EXP-001 已完成一轮授权 YOLO11n baseline 训练：95/100 epochs，
best epoch 75，validation precision `0.899`、recall `0.649`、mAP50
`0.767`、mAP50-95 `0.480`。`best.pt` 和 `last.pt` 为 `5,479,891`
bytes；最佳 checkpoint SHA256 为
`1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`。
完整训练证据见 `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`。

当前没有 PPE 检测业务能力。图片/视频/RTSP 检测、人员跟踪、Person-PPE
关联、Helmet/Vest 合规判断、事件管理、告警、Web 业务页面、LLM 报告和
Agent 均尚未实现。未来阶段占位接口会明确抛出 `NotImplementedError`，
不会返回伪造业务结果。

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
- `docs/P2-4_FINAL_PROVISIONING_REPORT.md`：P2-4 runtime、依赖和数据集验证
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
WAIT FOR PHASE 3 EVALUATION AUTHORIZATION
```

在明确授权前，不启动 Phase 3、不执行独立评估、不创建第二次训练，也不
修改冻结 dataset、mapping 或 EXP-001 identity。M-005 仍为 `待实现`。
