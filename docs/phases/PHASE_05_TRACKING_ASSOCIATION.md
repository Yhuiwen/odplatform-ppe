# Phase 05 — Tracking & Association

## 1. 阶段目标

【LOCKED】ByteTrack + Person-PPE Association。

## 2. 进入条件

- Phase 4 Offline Inference Gates PASS（Phase 4 文档与 TEST_GATES 的离线门禁）。
- Deferred requirements ownership clarified：M-007 标注视频、M-008 Camera/RTSP
  由 Phase 7 实现并集成，Phase 9 按 Charter 最终验收，详见 ADR-019。
- 无冻结资产冲突；开始任务时检查 dataset、mapping、checkpoint、training
  assets 与 inference configuration，不能将本次文档澄清视为资产验证。
- 已获得 2026-09-23 Phase 5 开发授权，开发按 P5-0、P5-1、P5-2、P5-3
  顺序推进；每个子阶段完成后等待人工审核。
- 检测输出包含稳定的人与 PPE 类别及置信度。

## 3. 当前子任务

Phase 5-0 — Tracking & Association Interface Freeze 已人工审核 PASS。
Phase 5-1 — Person-only ByteTrack Adapter 已人工审核 PASS。
Phase 5-2 — Person-PPE Association 已人工审核 PASS。
Phase 5-3 — Synthetic pipeline validation 已完成；真实 runtime validation
已准备并完成静态 preflight，但当前主机缺少 `torch` / `ultralytics`，因此
`BLOCKED / NOT RUN`。该门禁记录保留为历史事实。接口、输出 schema、
tracker 配置和 association
阈值继续保持冻结。

Phase 5 Release Final Audit — Git 边界、冻结资产、测试和其他发布证据已
完成审计。审计当时由于真实 runtime Gate 未通过，文档状态为
`NOT RELEASED`；后续人工明确授权发布，并创建 annotated tag
`phase-5-tracking-association-complete`，指向提交
`6da6213f0cc541765f231c81b4264a98f01d5f4a`。

当前状态：Phase 5 `COMPLETE / RELEASED`。本次文档同步不改变 P5-3-G5 的
历史 `BLOCKED / NOT RUN` 证据。

实现层状态：M-009 和 M-010 为 `IMPLEMENTED / Runtime Evidence Pending`。
Charter 锁定状态仍为 `待实现`，只有真实 checkpoint、inference 和
ByteTrack runtime 验收通过后才能改为 `已经实现`。

下一允许步骤：`WAIT FOR PHASE 5 DOCUMENTATION SYNC REVIEW`。

## 4. 实现设计

ByteTrack 只跟踪 person 目标；关联使用人体框包含/IoU 和可解释约束。无法
可靠归属时输出未关联项，禁止强制分配给最近人员。

冻结链路：

```text
DetectionResult
-> PersonTrackingAdapter
-> TrackResult
-> PPEAssociationAdapter
-> AssociationResult
```

- `core/schemas/tracking.py` 定义只看 person 的 `TrackResult`。
- `core/schemas/association.py` 定义 `associated` / `unknown` 状态、
  containment / IoU 方法和 frame-level `AssociationResult`。
- `core/tracking/bytetrack_adapter.py` 实现 person-only
  `ByteTrackPersonTrackingAdapter`；真实 Ultralytics `BYTETracker` 只能通过
  私有 lazy backend 使用，外部结果统一转换为 `TrackResult`。
- `configs/tracker.yaml` 冻结 Ultralytics `8.4.157` BYTETracker 参数和
  person-only class filter；P5-1 保持原阈值并启用 adapter execution。
- `configs/association.yaml` 冻结 confidence `0.25`、containment `0.50`、
  IoU `0.10`、ambiguity margin `0.10`，并明确禁止 nearest-distance
  assignment。
- `core/association/ppe_person_association.py` 实现
  `PPEPersonAssociationAdapter`；仅已存在的 person `TrackResult` 可作为归属
  目标，PPE 1–4 类通过 containment/IoU/confidence 规则得到
  `associated` 或显式 `unknown`。
- `tests/test_phase5_pipeline_validation.py` 使用 scripted ByteTrack backend
  和真实 `PPEPersonAssociationAdapter` 验证完整合成链路，覆盖单人、多人、
  PPE present/missing 和 ambiguous unknown。
- `configs/p5_3_validation.yaml` 固定真实 validation 的 checkpoint/video
  identity、输出路径和执行门；`scripts/run_tracking_association_validation.py`
  提供只读 preflight 与未来受控执行。当前 config 为
  `execution_enabled: false`，未加载 checkpoint 或执行推理。
- P5-0 只冻结接口和配置；`PersonTrackingAdapter` 与
  `PPEAssociationAdapter` 的实际实现分别由 P5-1 和 P5-2 完成。P5-1 已完成
  adapter 实现，但真实 Ultralytics runtime 尚未执行。

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

P5-0 interface gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P5-0-G1 | Phase 4 和 Phase 5 entry state reviewed | PASS |
| P5-0-G2 | Frozen asset identities rechecked without mutation | PASS |
| P5-0-G3 | Tracking and association schemas frozen | PASS |
| P5-0-G4 | Person-only ByteTrack boundary frozen | PASS |
| P5-0-G5 | Unknown-safe association policy frozen | PASS |
| P5-0-G6 | No runtime tracking/association implementation performed | PASS |

Phase 5-1 adapter gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P5-1-G1 | Person-only ByteTrack adapter implemented behind the frozen interface | PASS |
| P5-1-G2 | Only class ID `0` / `person` reaches the tracker | PASS |
| P5-1-G3 | `DetectionResult` and core schemas remain runtime-independent | PASS |
| P5-1-G4 | Required adapter boundary tests pass | PASS |
| P5-1-G5 | Frozen checkpoint, dataset, mapping and training config remain unchanged | PASS |
| P5-1-G6 | No model load, inference, association, training or commit/push occurred | PASS |

Phase 5-2 association gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P5-2-G1 | Association adapter implemented behind the frozen protocol | PASS |
| P5-2-G2 | Only existing person tracks are assignment targets | PASS |
| P5-2-G3 | Frozen confidence/containment/IoU thresholds are preserved | PASS |
| P5-2-G4 | Nearest-distance and forced assignment are excluded | PASS |
| P5-2-G5 | Required association boundary tests pass | PASS |
| P5-2-G6 | Frozen checkpoint, dataset, mapping and training config remain unchanged | PASS |
| P5-2-G7 | No model load, inference, training or commit/push occurred | PASS |

Phase 5-3 validation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P5-3-G1 | Integrated synthetic pipeline validation exists | PASS |
| P5-3-G2 | Single-person, multi-person, PPE present/missing and ambiguous cases pass | PASS |
| P5-3-G3 | Frozen schemas and adapter boundaries remain unchanged | PASS |
| P5-3-G4 | Real runtime validation assets and preflight are prepared | PASS |
| P5-3-G5 | Real checkpoint/video runtime validation executed | BLOCKED / NOT RUN |
| P5-3-G6 | Frozen dataset, mapping, training config and checkpoint preserved | PASS |
| P5-3-G7 | No model load, inference, training, commit, push or tag occurred | PASS |

P5-3-G5 remains a historical `BLOCKED / NOT RUN` record. The Phase 5 release
tag was created later under explicit human authorization; it does not rewrite
the missing runtime evidence as PASS.

## 7. 已知问题

遮挡、尺度变化和人员重叠会增加关联难度。

## 8. 开发记录

- 2026-09-23: Phase 5 release documentation synchronized to `COMPLETE /
  RELEASED` with tag `phase-5-tracking-association-complete` at commit
  `6da6213f0cc541765f231c81b4264a98f01d5f4a`. The original P5-3-G5
  `BLOCKED / NOT RUN` history is preserved, and this documentation-only sync
  did not modify code, tests, models or datasets.
- 2026-09-23: Phase 5 release final audit completed for human review. Audited
  Git status, staged/untracked contents, frozen hashes, release-file
  boundaries and the full test suite. M-009 and M-010 are recorded as
  `IMPLEMENTED / Runtime Evidence Pending`; the locked Charter statuses remain
  `待实现`. Phase 5 remains NOT RELEASED until real runtime evidence exists.
  No commit, push or tag occurred.
- 2026-09-23: Phase 5 final release preparation completed for human review.
  Consolidated P5-0 through P5-3 evidence, frozen asset hashes, release gates
  and limitations in `P5_FINAL_RELEASE_REPORT.md`. The phase remains
  `PREPARED / NOT RELEASED` because real checkpoint/inference/ByteTrack
  validation did not run. M-009 and M-010 remain pending. No commit, push or
  tag occurred.
- 2026-09-23: P5-3 synthetic tracking/association validation completed for
  human review. Added an integrated deterministic pipeline suite and a
  validation-only config/script for the frozen checkpoint and validated MP4.
  Static preflight passed asset identity and hash checks but reported
  `BLOCKED_RUNTIME_DEPENDENCIES` because `torch` and `ultralytics` are not
  installed. No model load, inference, ByteTrack execution, training or
  checkpoint mutation occurred. Real runtime validation remains not run.
- 2026-09-23: P5-2 Person-PPE association completed for human review.
  Implemented conservative containment/IoU/confidence association against
  existing person tracks, explicit unknown outcomes and deterministic
  ambiguity handling. Synthetic tests cover single/multiple people, wrong
  candidates, ambiguity, missing PPE and empty input. Real video integration
  remains deferred to P5-3.
- 2026-09-23: P5-1 person-only ByteTrack adapter completed for human review.
  Added a lazy Ultralytics backend boundary, person/confidence filtering,
  project-owned `TrackResult` conversion and focused tests for continuous,
  multi-person, enter/leave, missing-frame and invalid-class behavior. Real
  Ultralytics execution was not available in the current workspace. P5-2
  remains waiting for P5-1 review.
- 2026-09-23: P5-0 interface freeze completed for human review. Added
  model-independent `TrackResult` and `AssociationResult` contracts,
  person-only tracking and association protocols, frozen tracker/association
  configuration, ADR-020, design/report/worklog and focused tests. No model
  loading, ByteTrack execution, association run, dataset mutation, training or
  checkpoint change occurred. P5-1 remains waiting.
- 2026-09-21: 计划建立，未开始实现。
