# Phase 05 — Tracking & Association

## 1. 阶段目标

【LOCKED】ByteTrack + Person-PPE Association。

## 2. 进入条件

- Phase 4 Gate 全部 PASS。
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
