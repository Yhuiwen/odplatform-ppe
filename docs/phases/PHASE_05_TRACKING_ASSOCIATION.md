# Phase 05 — Tracking & Association

## 1. 阶段目标

【LOCKED】ByteTrack + Person-PPE Association。

## 2. 进入条件

- Phase 4 Offline Inference Gates PASS（Phase 4 文档与 TEST_GATES 的离线门禁）。
- Deferred requirements ownership clarified：M-007 标注视频、M-008 Camera/RTSP
  由 Phase 7 实现并集成，Phase 9 按 Charter 最终验收，详见 ADR-019。
- 无冻结资产冲突；开始任务时检查 dataset、mapping、checkpoint、training
  assets 与 inference configuration，不能将本次文档澄清视为资产验证。
- 已获得独立 Phase 5 开发授权；本次任务不启动 Phase 5。
- 检测输出包含稳定的人与 PPE 类别及置信度。

## 3. 当前子任务

未开始。计划通过成熟依赖使用 ByteTrack，并实现人员-PPE 关联。

## 4. 实现设计

ByteTrack 只跟踪 person 目标；关联使用人体框包含/IoU 和可解释约束。无法
可靠归属时输出未关联项，禁止强制分配给最近人员。

## 5. 测试要求

- 轨迹 ID 连续性和重置测试。
- 单人/多人、嵌套框、重叠框和缺失 PPE 关联测试。
- 未关联结果与错误归属回归测试。

## 6. Gate

| Gate | Requirement |
| --- | --- |
| P5-G1 | ByteTrack track ID 稳定且配置/版本可追踪 |
| P5-G2 | Person-PPE 关联满足核心边界测试 |
| P5-G3 | 不确定关联不会产生错误归属 |

## 7. 已知问题

遮挡、尺度变化和人员重叠会增加关联难度。

## 8. 开发记录

- 2026-09-21: 计划建立，未开始实现。
