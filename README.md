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

- 当前 Phase：Phase 0 — Foundation
- Phase 状态：已经实现（G0-1 至 G0-13 全部 PASS）
- 当前成果：工程骨架、配置体系、文档治理、日志/路径/系统信息基础能力与测试
- 尚未完成：YOLO 模型训练、PPE 检测、跟踪关联、合规判断、事件告警、
  Web 业务页面、LLM 报告和 Agent

当前没有训练 YOLO 模型，也没有可用的 PPE 检测业务功能。任何未来阶段占位
接口都会明确抛出 `NotImplementedError`，不会返回伪造业务结果。

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

## 环境要求

- Python 3.10 或更高版本
- Git
- Phase 0 基础测试仅需要 `pytest` 和 `PyYAML`
- 完整 GPU/PyTorch/Ultralytics 环境是后续阶段的计划依赖，Phase 0 不要求
  安装，也不要求 CUDA 可用

## Phase 0 安装方式

`requirements.txt` 记录后续完整运行计划依赖，并不表示当前都必须安装。
Phase 0 只需要：

```powershell
python -m pip install pytest PyYAML
```

这项安装不会下载数据集或模型权重。`pyproject.toml` 只保存项目元数据和
测试配置，不声明第二套运行时依赖来源。

## Phase 0 测试方法

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
- `docs/06_DATASET_CARD.md`：数据集计划，Phase 0 不下载
- `docs/07_OPEN_SOURCE_USAGE.md`：开源依赖、参考和许可证记录
- `docs/08_RISK_REGISTER.md`：风险登记册
- `docs/phases/`：每个阶段的独立文档

## 开源使用原则

依赖优先通过包管理器使用；算法性项目以阅读设计和自主实现为主。禁止复制
未知许可证代码或整份业务架构。所有计划依赖、参考与潜在选择性复用都记录
在 `docs/07_OPEN_SOURCE_USAGE.md`。

## 下一阶段

只有 Phase 0 Gate 全部通过后才能进入：

```text
Phase 1 — Data Engineering
```

Phase 1 的计划数据源是 Construction Site Safety (CSS)，不会在 Phase 0
提前下载。
