# ODPlatform-PPE Master Plan

> Governance: final goals are locked in `docs/00_PROJECT_CHARTER.md`.
> Phase goals below are LOCKED. Internal modules, implementation routes, and
> test methods may be adjusted within a phase.

## 1. 阶段总览

| Phase | 名称 | 锁定阶段目标 | 状态 |
| --- | --- | --- | --- |
| P0 | Foundation | 工程、文档、环境、配置体系建立 | 已经实现 |
| P1 | Data | 数据获取、格式统一、质量检查、数据报告 | 待实现 |
| P2 | Training | YOLO11 baseline 训练与实验归档 | 待实现 |
| P3 | Evaluation | 模型评估、对照实验、模型选择 | 待实现 |
| P4 | Inference | 图片、视频、Camera/RTSP 推理流水线 | 待实现 |
| P5 | Tracking & Association | ByteTrack + Person-PPE Association | 待实现 |
| P6 | Compliance & Events | PPE 合规规则、时序判断、Event Engine | 待实现 |
| P7 | Web & Alerts | SQLite + Snapshot + TTS + Streamlit | 待实现 |
| P8 | LLM & Agent | LLM Report + Fallback + Basic Agent | 待实现 |
| P9 | Integration & Delivery | 全链路测试、性能分析、文档、Demo、答辩交付 | 待实现 |

## 2. 阶段依赖

```text
P0 -> P1 -> P2 -> P3 -> P4 -> P5 -> P6 -> P7 -> P8 -> P9
```

只有在当前阶段 Gate 全部 PASS 后才能进入下一阶段。P0 只有在
`docs/05_TEST_GATES.md` 中 G0-1 至 G0-13 全部 PASS 后才能改为 `已经实现`。

## 3. 交付主线

| 阶段 | 主要交付物 | 对应主要 MUST |
| --- | --- | --- |
| P0 | 工程骨架、配置、路径/日志/系统工具、治理文档、基础测试 | M-024 基础部分，不代表 M-024 完成 |
| P1 | 可复现数据准备、五类映射、质量检查、数据报告 | M-001、M-002、M-003 |
| P2 | 可复现 YOLO11n baseline、实验归档 | M-004 |
| P3 | 完整指标、对照实验、方案选择 | M-005 |
| P4 | 图片、视频、Camera/RTSP 推理 | M-006、M-007、M-008 |
| P5 | ByteTrack 人员跟踪、Person-PPE 关联 | M-009、M-010 |
| P6 | Helmet/Vest 规则、多帧确认、事件去重 | M-011、M-012、M-013、M-014 |
| P7 | SQLite、截图、TTS、Streamlit 查询与大屏 | M-015、M-016、M-017、M-018、M-019、M-020 |
| P8 | LLM 报告、本地降级、平台数据 Agent | M-021、M-022、M-023 |
| P9 | 全链路测试、部署文档、Demo、答辩证据 | M-024、M-025、M-026 |

重复的 MUST 只表示工作覆盖关系，不代表在其他阶段提前完成。

## 4. 状态规则

- `待实现`：尚未满足验收标准。
- `实现中`：已经开始实现，但 Gate 或验收标准尚未全部满足。
- `已经实现`：真实代码存在、对应测试通过、验收标准满足。
- 阶段目标不得由后续开发自行修改。
- 代码、Charter、Master Plan 冲突时必须停止相关工作并报告。
