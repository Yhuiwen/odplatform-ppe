# Phase 06 — Compliance & Events

## 1. 阶段目标

【LOCKED】PPE 合规规则、时序判断、Event Engine。

Phase 6 建立保守、可审计的离线合规事件链：

```text
AssociationResult
-> AssociationAdapter
-> ComplianceInput
-> ComplianceEngine
-> ComplianceResult
-> TemporalViolationFilter
-> EventEngine
-> ComplianceEvent
-> JSONEventStore
```

阶段输出只依赖项目自有 schema，不返回 YOLO、Ultralytics、ByteTrack 或视频
框架对象。

## 2. 进入条件

- Phase 5 Gate 全部 PASS。
- 关联结果具备人员 track、PPE 类别、帧与时间信息。

当前已满足：

- Phase 5 `COMPLETE / RELEASED`，tag 为
  `phase-5-tracking-association-complete`。
- `AssociationResult` 包含 `frame_id`、`timestamp`、`source`、
  person-only `tracks` 及 associated/unknown `associations`。
- `best.pt`、dataset、mapping、training config 和 Phase 5 tracking 实现保持
  冻结；Phase 6 不加载模型。

## 3. 当前子任务

Phase 6 实现范围：

- `core/schemas/compliance.py`：冻结 `ComplianceInput`、
  `ComplianceFinding`、`ComplianceResult`、`ComplianceEvent` 和事件类型。
- `core/adapters/association_adapter.py`：把 Phase 5 `AssociationResult`
  无损转换为 `ComplianceInput`。
- `core/rules/compliance_engine.py`：评估 `NO_HELMET`、`NO_VEST` 和
  `PPE_UNKNOWN`。
- `core/rules/temporal_filter.py`：连续 N 帧及最短持续时间确认，单帧不得
  触发。
- `core/events/event_engine.py`：创建事件、同一 track/type 去重、恢复和
  冷却后再次触发。
- `infra/storage/json_event_store.py`：追加保存
  `outputs/events.jsonl`。
- `services/compliance_service.py` 与 `services/event_service.py`：只做编排，
  不复制规则逻辑。
- `examples/phase6_demo.py` 与 JSON fixture：离线演示，不使用 GPU、YOLO、
  camera 或 RTSP。

## 4. 实现设计

### Data contract

`ComplianceInput`:

```text
frame_id
timestamp
tracks
associations
```

`ComplianceFinding` 记录逐 track/type 的 `compliant`、`violation` 或
`unknown` 状态。`ComplianceResult` 是该帧全部 findings 的不可变集合。

`ComplianceEvent`:

```text
event_id
track_id
event_type
confidence
timestamp
evidence
```

JSONL wire record 只包含：

```text
type
track_id
confidence
timestamp
```

### Conservative rules

- `no_hardhat` associated 且无冲突/不确定证据：`NO_HELMET` violation。
- `no_vest` associated 且无冲突/不确定证据：`NO_VEST` violation。
- 对应 PPE 缺失、只有 unknown association、或同时出现 positive/violation
  证据：`PPE_UNKNOWN`，不得伪造合规或违规结论。
- 未被关联的 unknown PPE 没有 person track，禁止强制归属，因此不直接生成
  针对某个 track 的事件。

### Temporal and event policy

- 默认必须连续 `5` 帧且持续至少 `1.0` 秒。
- 候选达到阈值后，TemporalFilter 只在本次连续候选周期内确认一次。
- EventEngine 以 `(track_id, event_type)` 隔离并进行活动周期去重。
- 连续 `5` 个 compliant frames 后恢复；恢复后 `30` 秒冷却期内不重复生成
  同一 track/type 的新事件。
- 新增事件使用新的 `event_id`；同一活动周期只输出一次。

## 5. 测试要求

- Helmet/Vest 合规、违规和缺失证据测试。
- 单帧抖动、满足阈值、恢复和再次违规测试。
- 同一事件去重、冷却和不同人员隔离测试。
- Adapter 必须保持 frame context，且不得修改 Phase 5 输入。
- JSONL 必须使用 `type` wire 字段，并保持可重新读取。
- 离线 demo 必须可在无 Torch、无 YOLO、无 GPU、无 camera 的环境运行。

## 6. Gate

| Gate | Requirement |
| --- | --- |
| P6-G1 | Helmet/Vest 规则满足验收和边界测试 |
| P6-G2 | 多帧确认可抑制短暂误报 |
| P6-G3 | 事件去重、恢复和冷却可复现 |

Phase 6 release gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P6-F1 | Association adapter contract is frozen and tested | PASS |
| P6-F2 | Conservative Helmet/Vest/Unknown rules are implemented | PASS |
| P6-F3 | Single-frame events are impossible under frozen config | PASS |
| P6-F4 | Event deduplication and lifecycle state are tested | PASS |
| P6-F5 | JSONL storage uses the frozen wire contract | PASS |
| P6-F6 | Offline demo does not load a model or use GPU/camera | PASS |
| P6-F7 | Dataset, mapping, training assets and Phase 5 tracking stay frozen | PASS |
| P6-F8 | Full test, compile and diff checks pass | PASS |

## 7. 已知问题

遮挡和关联缺失会造成“无证据”，需要与明确违规区分。

Phase 6 采用保守策略：缺失或冲突证据输出 `PPE_UNKNOWN`，不会为了减少事件数
而推断人员合规。真实 detector/tracker runtime evidence 仍受 Phase 5
P5-3-G5 的 `BLOCKED / NOT RUN` 历史限制；Phase 6 的 fixture、rules 和事件
行为可用离线确定性证据验证。

## 8. 开发记录

- 2026-09-23: Phase 6 architecture frozen and implemented under the existing
  `core/`, `services/`, `infra/` and `utils/` boundaries. Added deterministic
  rule/temporal/event tests and an offline fixture/demo. No model, dataset,
  training configuration, evaluation artifact or Phase 5 tracking code was
  modified.
- 2026-09-21: 计划建立，未开始实现。
