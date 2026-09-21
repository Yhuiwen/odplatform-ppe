# Phase 00 — Foundation

## 1. 阶段目标

【LOCKED】工程、文档、环境、配置体系建立。

## 2. 进入条件

- 用户批准 Phase 0 范围。
- 当前目录不存在冲突规则、项目或锁定文档。

## 3. 当前子任务

- 建立最终工程目录与 Python package 边界。
- 建立配置、路径、日志、系统信息和计时基础。
- 建立 Charter、Master Plan、State、ADR、Gate、Dataset、License、Risk 和
  十个 Phase 文档。
- 建立真实 Phase 0 测试并执行 G0-1 至 G0-13。

## 4. 实现设计

- 真实基础能力仅位于 `utils/` 和 `core/detection/schemas.py`。
- 所有未来业务入口只保留接口/占位，调用时抛出带目标 Phase 的
  `NotImplementedError`。
- `requirements.txt` 记录完整计划依赖，Phase 0 只要求 pytest、PyYAML。
- 数据、权重和运行产物不进入版本控制，仅保留目录标记。

## 5. 测试要求

- 导入、配置、paths、logging、system info 和 schema 单元测试。
- Charter、Master Plan、十份 Phase、五类映射、开源记录和风险记录的治理测试。
- 业务占位必须明确失败，不得返回假结果。
- 执行 pytest、compileall、git diff whitespace check 和状态检查。

## 6. Gate

G0-1 至 G0-13 的完整定义与证据见 `docs/05_TEST_GATES.md`。只有全部 PASS，
本阶段状态才可更新为 `已经实现`。

## 7. 已知问题

- PyTorch 未安装；Phase 0 不依赖它，Phase 2 前需完成环境评估。
- `ppe_compliance_detection` 没有发现许可证文件，禁止复用其代码。
- Ultralytics 使用 AGPL-3.0，交付前需完成义务评估。

## 8. 开发记录

- 2026-09-21: Phase 0 工程与文档骨架建立。
- 2026-09-21: pytest 92 项通过，compileall 通过，git diff --check 通过，
  G0-1 至 G0-13 全部 PASS；阶段状态更新为 `已经实现`。
