# Current Status

## Current Phase

Phase 1 — Data Engineering

## Overall Status

Phase 1 实现中。P1A — Dataset Source & License Gate 已通过；P1B 尚未开始，
M-001 仍为待实现。

## Current Subphase

P1A — Dataset Source & License Gate: COMPLETED

## Reference Intake

Reference Intake: COMPLETED

- Teacher reference package registered as REF-001.
- Teacher checkpoint registered as REF-002.
- No teacher asset committed or copied into the repository.
- P1A reference-intake prerequisites reviewed.

## Current Environment

- OS: Windows NT 10.0.22631.0
- Python: 3.13.6
- pip: 25.3
- Git: 2.51.2.windows.1
- PyTorch: not installed
- CUDA: unavailable

## Completed

- 最终工程目录和 Python package 边界
- 六份 YAML 配置
- 路径、配置加载、日志、计时和系统信息基础工具
- 检测 schema
- 未来阶段服务、业务和基础设施占位边界
- Charter、Master Plan、ADR、Phase、Dataset、Open Source、Risk 文档
- Phase 0 基础测试
- G0-1 至 G0-13 全部 PASS
- pytest 99 项测试通过
- compileall 成功
- git diff --check 成功
- Pre-Phase 1 Reference Intake 文档与治理记录
- Phase 1A 来源证据、许可核验和 RoBoflow CSS v27 冻结决策
- G1A-1 至 G1A-11 全部 PASS
- pytest 110 项测试通过
- compileall 成功
- git diff --check 成功

## In Progress

Phase 1 — Data Engineering。P1A 已完成，P1B 尚未开始。

## Pending

- P1B 下载与原始快照
- P1C 类别映射与转换
- P1D 去重与数据质量验证
- P1E 数据冻结与报告
- 所有 M-001 至 M-026 业务能力
- 所有 E-001 至 E-012 扩展能力

## Known Issues

- PyTorch 尚未安装，Phase 0 不会因此失败；Phase 2 前需完成环境选型。
- `ppe_compliance_detection` 当前默认分支未发现 LICENSE 或 COPYING 文件，
  在任何代码复用前必须单独复核。
- `ultralytics` 当前许可证为 AGPL-3.0；正式交付和分发前必须完成许可义务评估。
- Teacher checkpoint 的五类名称与本项目锁定五类语义不同，映射保持
  `UNVERIFIED`。
- 老师参考包包含 `history.db`，并可能包含凭据；不得复制或提交其中内容。
- CSS 源项目存在版本漂移；V1 固定使用 Roboflow v27，不能使用移动的项目
  级数量或未经证明对应的 Kaggle 镜像替代。
- v27 含增强配置，后续重复检测和 split 泄漏检查不可跳过。

## Blockers

无 P1A 阻塞项。P1B 仍需按 ADR-009 使用本地 `ROBOFLOW_API_KEY` 下载
Roboflow CSS v27，并记录实际档案哈希。

## Next Allowed Step

P1A Gate 已全部 PASS。下一允许步骤是：

```text
P1B — Download & Raw Snapshot
```

本轮不执行 P1B。M-001 保持 `待实现`，因为尚未完成下载、转换和 split 管理。
