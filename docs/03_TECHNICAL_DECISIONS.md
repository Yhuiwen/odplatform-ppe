# Technical Decisions

This file is an append-only ADR log. Historical entries must not be deleted.

## ADR-001

- Date: 2026-09-21
- Status: Accepted
- Decision: 项目采用 Python + YOLO11 + ODPlatform 分层架构。
- Context: 项目需要覆盖数据处理、训练、评估、推理、事件服务和 Web，
  同时保持各阶段可测试、可替换。
- Consequences: Phase 0 建立 `core`、`services`、`infra`、`web` 和 `utils`
  边界；业务依赖方向为 `web/scripts -> services -> core/infra -> utils`。

## ADR-002

- Date: 2026-09-21
- Status: Accepted
- Decision: V1 主数据集选择 Construction Site Safety (CSS)。
- Context: CSS 是第一阶段统一训练与评估的主数据源。
- Consequences: Phase 1 负责下载、许可核验、类别转换、划分和质量报告；
  Phase 0 只记录计划，不下载数据。

## ADR-003

- Date: 2026-09-21
- Status: Accepted
- Decision: V1 类别锁定为 `person`、`hardhat`、`no_hardhat`、`vest`、
  `no_vest`，对应类别索引 0 至 4。
- Context: 需要统一不同数据源的类别语义，避免训练和规则判断不一致。
- Consequences: 后续所有数据映射、模型配置、评估和业务规则必须使用该顺序；
  修改需要用户批准并新增 ADR。

## ADR-004

- Date: 2026-09-21
- Status: Accepted
- Decision: 人员跟踪使用 ByteTrack，但优先通过成熟依赖的集成能力封装使用，
  不复制 ByteTrack 算法源码。
- Context: 跟踪是 MUST 能力，但直接维护上游算法会增加合规和工程成本。
- Consequences: Phase 5 必须固定依赖版本、配置和测试；不得以简化跟踪替代
  ByteTrack 验收。

## ADR-005

- Date: 2026-09-21
- Status: Accepted
- Decision: Safety Harness 不属于 V1 MUST。
- Context: 当前阶段没有可靠主数据源，且该能力已被列为 Extension。
- Consequences: 没有用户明确批准时，不得将其升级为 V1 MUST，也不得占用
  V1 主数据类别的五类位置。

## ADR-006

- Date: 2026-09-21
- Status: Accepted
- Decision: 项目采用“最终目标锁定、阶段目标锁定、阶段内部实现可调整”的
  治理模式。
- Context: 既要防止降低最终目标，也要允许阶段内根据实验调整实现路线。
- Consequences: 修改 Charter 锁定内容或阶段目标必须取得明确批准并新增 ADR；
  阶段内设计、测试方式和子任务可直接更新对应 Phase 文档。

## ADR-007

- Date: 2026-09-21
- Status: Accepted
- Title: Teacher project is reference-only
- Decision: 老师提供的 `yolo_web_v3.zip` 仅作为课程参考实现，不替代
  ODPlatform-PPE 既有分层架构。
- Context: 参考资料包含 Web、数据库、报告等实现思路，但来源为非开源课程
  资产，且可能包含凭据和非项目产物。
- Consequences: 允许借鉴 UI、SQLite、LLM 报告和 Web 流程等设计思想；
  禁止整仓复制、提交资产或直接采用老师 Web 架构替代本项目。

## ADR-008

- Date: 2026-09-21
- Status: Accepted
- Title: Teacher PPE checkpoint is an external baseline
- Decision: 老师提供的 YOLO11n PPE checkpoint 仅作为外部 baseline/reference。
- Context: checkpoint 保存的历史指标可用于未来对照，但不等于本项目实测或
  复现结果，且其训练数据类别语义尚未验证。
- Consequences: M-004 仍必须完成本项目自主可复现 YOLO11 训练；模型对比和
  报告中必须明确区分 `Teacher Baseline` 与 `Project-trained Model`。
