# ODPlatform-PPE Master Plan

> Governance: final goals are locked in `docs/00_PROJECT_CHARTER.md`.
> Phase goals below are LOCKED. Internal modules, implementation routes, and
> test methods may be adjusted within a phase.

## 1. 阶段总览

| Phase | 名称 | 锁定阶段目标 | 状态 |
| --- | --- | --- | --- |
| P0 | Foundation | 工程、文档、环境、配置体系建立 | 已经实现 |
| P1 | Data | 数据获取、格式统一、质量检查、数据报告 | 实现中 |
| P2 | Training | YOLO11 baseline 训练与实验归档 | 已经实现 |
| P3 | Evaluation | 模型评估、对照实验、模型选择 | 已经实现 |
| P4 | Offline Inference | 本地图片与 MP4 视频结构化推理流水线；Camera/RTSP 延期实施，仍保留 V1 MUST 归属 | 已经实现（Offline Inference COMPLETE；ADR-018） |
| P5 | Tracking & Association | ByteTrack + Person-PPE Association | 已经实现（COMPLETE / RELEASED；tag `phase-5-tracking-association-complete`；P5-3-G5 historical `BLOCKED / NOT RUN` followed by explicit release authorization） |
| P6 | Compliance & Events | PPE 合规规则、时序判断、Event Engine | 已经实现（COMPLETE / RELEASED；tag `phase-6-compliance-event-engine-complete`） |
| P7 | Web & Alerts | SQLite + Snapshot + TTS + Streamlit | 实现中（7-0 至 7-5 PASS；7-Release audit complete for review；publication WAITING） |
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
| P4 | 本地图片结构化检测、MP4 顺序推理与真实验证 | M-006/M-007 的离线推理证据；M-008 deferred MUST implementation |
| P5 | ByteTrack 人员跟踪、Person-PPE 关联 | M-009、M-010 |
| P6 | Helmet/Vest 规则、多帧确认、事件去重 | M-011、M-012、M-013、M-014 |
| P7 | SQLite、截图、TTS、Streamlit 查询与大屏 | M-015、M-016、M-017、M-018、M-019、M-020 |
| P8 | LLM 报告、本地降级、平台数据 Agent | M-021、M-022、M-023 |
| P9 | 全链路测试、部署文档、Demo、答辩证据 | M-024、M-025、M-026 |

重复的 MUST 只表示工作覆盖关系，不代表在其他阶段提前完成。

### Phase 4 deferred MUST ownership (ADR-019)

M-007 annotated video rendering and M-008 Camera/RTSP remain V1 MUST work.
Phase 7 owns implementation and page/service integration; Phase 9 owns final
Charter acceptance. They are not Extensions. Existing phase statuses remain
unchanged. For Phase 4 to Phase 5, the predecessor gate rule refers to the
Offline Inference Gates, plus explicit deferred ownership and no frozen asset
conflict; separate Phase 5 authorization remains required.

### Phase 7 subphases (7-0 through 7-Release)

Phase 7 remains locked to the goal `SQLite + Snapshot + TTS + Streamlit`.
The following internal subphase order is frozen by ADR-022:

| Subphase | Scope | Status |
| --- | --- | --- |
| 7-0 | Architecture Freeze: audit, target architecture, contracts, technology decision and risk review | COMPLETE / HUMAN REVIEW PASS |
| 7-1 | Event Storage: SQLite schema, migrations, repository, event ingestion and query tests | COMPLETE / HUMAN REVIEW PASS |
| 7-2 | Evidence Snapshot: atomic file write, relative path policy, integrity and event association | COMPLETE / HUMAN REVIEW PASS |
| 7-3 | Dashboard and Alerts: Streamlit pages plus Console and Web alert adapters | COMPLETE / HUMAN REVIEW PASS |
| 7-4 | Camera/RTSP: unified `VideoSource` input adapters and observable source lifecycle | COMPLETE / HUMAN REVIEW PASS |
| 7-4b | Real-time monitoring integration and annotated video rendering for M-007/M-008 | WAITING |
| 7-5 | Runtime Validation: integrated source-to-event-to-dashboard/alert evidence | COMPLETE / HUMAN REVIEW PASS |
| 7-Release | Phase 7 release audit, tag and remote publication only after all gates pass | AUDIT COMPLETE FOR HUMAN REVIEW / NOT PUBLISHED |

Console and Web alerts are the first implementation priority in 7-3, but TTS
remains a required V1 adapter under M-017. Email, WeChat and SMS are future
Extension adapters, not V1 acceptance dependencies.

Phase 7-0 is design-only, Phase 7-1 implements SQLite event storage, Phase 7-2
implements evidence-file persistence and metadata association, Phase 7-3
implements the read-only dashboard query path plus Console/Web alert adapters,
and Phase 7-4 implements the unified MP4/USB Camera/RTSP input adapters.
Phase 7-5 validates one integrated MP4 runtime path through the frozen
checkpoint, tracking, association, compliance/events, JSONL, SQLite, evidence
snapshot, dashboard and Console/Web alert boundaries. It also validates a real
USB Camera lifecycle and the four Streamlit pages. Real RTSP,
reconnect/backoff, stale-frame detection, monitoring integration, annotation
rendering, reconciliation automation, retention cleanup and TTS remain
pending. These slices do not change the locked phase goal, camera deferral,
M-007/M-008 ownership, M-015 through M-020 definitions, or any frozen
model/data/training asset.

Phase 7 Release Preparation Audit verifies the uncommitted release change set,
ignored generated-artifact boundaries, absence of credential/model/media
artifacts, documentation consistency for 7-0 through 7-5, and the complete
repository test baseline. It does not authorize publication: commit, push and
tag remain pending explicit human review, and the remaining V1 limitations
are not converted into completion claims.

## 4. 状态规则

- `待实现`：尚未满足验收标准。
- `实现中`：已经开始实现，但 Gate 或验收标准尚未全部满足。
- `已经实现`：真实代码存在、对应测试通过、验收标准满足。
- 阶段目标不得由后续开发自行修改。
- 代码、Charter、Master Plan 冲突时必须停止相关工作并报告。
