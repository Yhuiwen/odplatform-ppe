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

## ADR-009

- Date: 2026-09-21
- Status: Accepted
- Title: CSS is the V1 primary dataset source
- Decision: V1 使用 Roboflow Universe 原始公开项目
  `roboflow-universe-projects/construction-site-safety` 的冻结版本 `27`
  作为 CSS 主数据源，下载格式确定为 `yolov8`。
- Dataset license evidence:
  https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety
  directly states `License: CC BY 4.0` for the dataset.
- License legal terms: https://creativecommons.org/licenses/by/4.0/
- Context: Construction Site Safety 项目页直接标记
  `License: CC BY 4.0`；Creative Commons 页面仅作为该许可证法律条款证据。
  原始项目元数据另外提供目标类别语义、2,801 张图像、2,605/114/82
  split、25 个源类别和 YOLO 导出能力；可复现下载可通过 Roboflow Universe
  UI 或 Python SDK/REST 机制完成。
- Annotation scope: 源标注任务是 bounding-box object detection；Phase 1B
  选择 `yolov8` 作为导出格式，目标训练框架为 YOLO11。不得把 YOLO11
  写成数据集原始类标注格式。
- Annotation total: 源元数据提供逐类别框数，但未发现可直接冻结的单一
  总标注数字段；Phase 1B 下载前总标注数保持
  `UNVERIFIED / NOT FROZEN`。
- Why not the mirror: Kaggle 镜像只作为次级证据。其版本号来自 Kaggle，
  不证明与任何 Roboflow 版本逐位对应，且其公开元数据报告十类，而 Roboflow
  版本 27 报告 25 个源类别，因此镜像不进入 V1 下载基线。
- License basis: 原始项目公开记录为 `CC BY 4.0`；允许分享、改编及商业使用，
  但必须适当署名、链接许可证、说明修改，并不得暗示许可方背书。底层图像
  的隐私/肖像来源限制仍由 RISK-013 监控。
- Usage boundary: 原始数据集保留在仓库外；`ROBOFLOW_API_KEY` 只能来自本地
  环境变量；不得将下载档案、图像或标签提交 Git；公开分发或再许可前复核
  署名、修改说明和底层内容权利。
- Phase 1B rule: 只允许按以下冻结标识下载：
  `workspace=roboflow-universe-projects`,
  `project=construction-site-safety`, `version=27`, `format=yolov8`。
- Consequences: Phase 1B 必须记录实际下载档案哈希与来源；Phase 1C 只按
  Charter 锁定五类做显式映射，不修改本 ADR 锁定的源版本。

## ADR-010

- Date: 2026-09-21
- Status: Accepted
- Title: Dataset freeze requires export artifact fingerprint
- Decision: Roboflow version number alone cannot uniquely identify a training
  artifact. A dataset identity must include:
  - workspace
  - project
  - version
  - export format
  - `data.yaml` SHA256
  - class list
  - manifest SHA256
  - actual split counts
- Context: The frozen v27 metadata recorded 25 classes and 2,801 images, while
  the materialized `yolov8` export records 10 classes and 2,799 images. Both
  artifacts identify the same workspace and project and both contain version
  `27`, so the version number alone cannot distinguish the metadata identity
  from the exported training artifact.
- Consequences: CSS-V1 remains blocked for freeze correction. The 10-class,
  2,799-image artifact is recorded as `CSS-V1.1 Candidate`, not as a frozen
  replacement. Any future freeze must bind the complete artifact fingerprint
  above and must not treat a version number, class count, or image count in
  isolation as sufficient identity.

## ADR-011

- Date: 2026-09-21
- Status: Accepted
- Title: V1 dataset selection criteria
- Decision: V1 dataset selection prioritizes:
  1. reproducibility
  2. verified artifact identity
  3. PPE task relevance
  4. license clarity
  5. training feasibility
  Maximum class count is not a selection criterion by itself.
- Context: CSS-V1 has a broader 25-class metadata record but no matching
  materialized artifact fingerprint. CSS-V1.1 is a materialized 10-class,
  2,799-image export with a complete fingerprint, but it remains an unfrozen
  candidate. Selecting the larger metadata record without a reproducible
  artifact would make the eventual training data ambiguous.
- Consequences: The P1B.2 evaluation compares candidates against these
  criteria and records both current statuses without freezing either one.
  A future freeze still requires an explicit route decision and the complete
  artifact fingerprint required by ADR-010. P1C and training remain blocked
  until that decision is recorded.

## ADR-012

- Date: 2026-09-21
- Status: Accepted
- Title: V1 dataset is frozen by artifact fingerprint
- Decision: V1 dataset identity is defined by the complete artifact
  fingerprint, not only by a Roboflow version number. The frozen V1 dataset is
  `CSS-PPE-10-V1`, promoted from `CSS-V1.1 Candidate`, with:
  - workspace `roboflow-universe-projects`
  - project `construction-site-safety`
  - version `27`
  - format `yolov8`
  - `data.yaml` SHA256
    `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`
  - ten-class exported class list
  - manifest SHA256
    `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795`
  - actual split counts train `2603` / valid `114` / test `82`
  - total images `2799`
- Context: CSS-V1's 25-class / 2,801-image metadata cannot be tied to the
  materialized 10-class / 2,799-image export. Under ADR-011, reproducibility
  and verified artifact identity take priority over the larger reported class
  count.
- Consequences: `CSS-PPE-10-V1` is the immutable P1C input. CSS-V1 remains
  recorded as rejected and blocked for historical audit but is not the V1
  training dataset. No class conversion, download, training, or P1C work is
  performed by this ADR.

## ADR-013

- Date: 2026-09-21
- Status: Accepted
- Title: Class mapping must be frozen before dataset conversion
- Decision: Original dataset classes and training classes are separate
  concepts. A class mapping must be reviewed and frozen before:
  - label conversion
  - processed dataset generation
  - model training
- Context: The frozen `CSS-PPE-10-V1` export contains ten original classes,
  while the locked V1 output defines five PPE compliance classes. Candidate
  mapping choices can retain, discard, or reorganize classes, so conversion
  must not begin while the mapping remains ambiguous.
- Consequences: P1C remains blocked until a mapping candidate is explicitly
  selected and recorded. The original snapshot and `data.yaml` remain
  immutable. Conversion must emit new files under `data/interim/` or
  `data/processed/` and must prove coverage or disposition for every original
  class.

## ADR-014

- Date: 2026-09-21
- Status: Accepted
- Title: V1 training class mapping decision
- Decision: Training dataset classes are derived from `CSS-PPE-10-V1` through
  the frozen Strategy C mapping:
  - `0 person <- [5]`
  - `1 hardhat <- [0]`
  - `2 no_hardhat <- [2]`
  - `3 vest <- [7]`
  - `4 no_vest <- [4]`
  - `5 machinery <- [8]`
  - `6 vehicle <- [9]`
  Source classes `1 Mask`, `3 NO-Mask`, and `6 Safety Cone` are discarded from
  the V1 training output.
- Context: The original export contains ten classes, while the locked
  compliance surface contains five PPE classes. Strategy C retains the five
  compliance classes in ADR-003 order and adds two scene-context classes for
  future hazard and report capabilities without changing the compliance
  semantics.
- Governance boundary: `machinery` and `vehicle` are not PPE compliance
  classes. They must not trigger helmet or vest violations and must not alter
  the required five-class per-class AP reporting.
- Consequences: Original dataset remains immutable. P1C conversion must use
  this exact seven-class mapping, preserve source data, and report mapped and
  discarded boxes. Conversion and processed dataset generation remain
  unimplemented until the P1C implementation gate is approved.

## ADR-015

- Date: 2026-09-21
- Status: Accepted
- Title: Dataset quality validation is observation-only before training
- Decision: Quality validation may identify risks, report invalid records,
  and recommend a later dataset version, but it must not mutate the frozen
  source or processed datasets. Any data modification requires a new dataset
  version and a new frozen artifact fingerprint.
- Context: P1D must answer whether the YOLO-ready dataset is suitable for
  training without improving metrics by silently deleting, relabeling,
  resizing, remapping, or resplitting data. Roboflow augmentation also means
  that exact and perceptual duplicates require interpretation rather than
  automatic deletion.
- Consequences: `DatasetQualityService.analyze()` is read-only and verifies
  the dataset manifest before and after analysis. P1D findings remain evidence.
  Auto-repair APIs are prohibited. P1D-0 defines thresholds and architecture;
  only P1D-1 may execute the framework against the real `CSS-PPE-10-V1`
  processed dataset and generate the real quality report.

## ADR-016

- Date: 2026-09-21
- Status: Accepted
- Title: Training experiments must be configuration-driven
- Decision: All experiments must be defined by immutable configuration files.
  Manual command-line-only experiments are not accepted as reproducible
  records.
- Context: The baseline must be traceable across dataset identity, model
  version, hyperparameters, hardware, metrics, and checkpoint outputs.
  Untracked command lines can produce results that cannot be audited or
  compared, especially after the dataset, dependency, or hardware state
  changes.
- Consequences: Every training run must reference a version-controlled YAML
  configuration, the frozen dataset contract, and recorded environment and
  metric evidence. The canonical EXP-001 template and schema are introduced in
  P1E-0. P1E-0 does not execute training, download weights, or create a model
  checkpoint.

## ADR-017

- Date: 2026-09-22
- Status: Accepted
- Title: GitHub Phase Milestone Release Strategy

## Decision

项目采用“大 Phase 完成后 GitHub 归档”的发布策略。

每完成一个主要 Phase：

1. 完成对应 Gate 验收；
2. 更新阶段状态；
3. 执行测试验证；
4. 创建 Git commit；
5. 创建对应 Git tag；
6. 推送 GitHub。

## Phase Release Mapping

| Phase   | GitHub Action                                |
| ------- | -------------------------------------------- |
| Phase 0 | tag: `phase-0-foundation-complete`           |
| Phase 1 | tag: `phase-1-data-engineering-complete`     |
| Phase 2 | tag: `phase-2-training-complete`             |
| Phase 3 | tag: `phase-3-evaluation-complete`           |
| Phase 4 | tag: `phase-4-inference-complete`            |
| Phase 5 | tag: `phase-5-tracking-association-complete` |
| Phase 6 | tag: `phase-6-compliance-event-engine-complete` |
| Phase 7 | tag: `phase-7-web-alerts-complete`           |
| Phase 8 | tag: `phase-8-llm-agent-complete`            |
| Phase 9 | GitHub Release + final tag                   |

## Release Rules

- 只有 Phase Gate 全部 PASS 后允许发布。
- 未完成 Gate 的阶段禁止创建 complete tag。
- tag 必须对应真实代码状态。
- 不允许使用 tag 掩盖未完成工作。
- 大文件、数据集、模型权重必须遵守 .gitignore 规则。
- Phase 9 使用 GitHub Release 作为最终交付版本。

## ADR-018

- Date: 2026-09-23
- Status: Accepted
- Title: Phase 4 scope adjustment for offline inference release
- Supersedes: the original Phase 4 scope and `phase-4-inference-complete`
  milestone name from ADR-017 are superseded by this ADR.

> Clarification (2026-09-23, ADR-019): the former Extension classification
> is corrected below. The offline release decision, evidence, date and tag
> remain unchanged; no historical ADR is removed.

### Decision

Phase 4 is re-scoped to **Offline Inference**:

- structured single-image inference;
- sequential local MP4 inference;
- frozen checkpoint and CPU runtime identity;
- real image and real MP4 validation evidence.

Phase 4 release tag:

```text
phase-4-offline-inference-complete
```

Camera, RTSP, real-time/network source behavior, M-008, and annotated video
rendering are deferred from Phase 4 scope. M-008 remains a V1 MUST, and
annotated video rendering remains part of M-007 acceptance. Neither is an
Extension or claimed complete by this release. ADR-019 clarifies ownership.

### Original scope

The original Phase 4 target covered Image, Video and Camera/RTSP inference,
with M-006, M-007 and M-008 as Charter delivery mappings. The original
`phase-4-inference-complete` tag name did not distinguish the completed local
offline path from the unimplemented real-time path.

### Completed scope

The completed implementation provides:

- `Image -> InferenceService -> YOLODetector -> DetectionResult`;
- `MP4 -> VideoReader -> VideoInferenceService -> FrameInferenceResult`;
- structured JSON output without returning Ultralytics framework objects;
- frozen `INF-RUNTIME-001` CPU policy and checkpoint fingerprint verification;
- real single-image validation against the frozen release checkpoint;
- real 47/47-frame MP4 validation with no frame skipping, batching, async
  execution or CUDA migration.

### Camera/RTSP deferral reason

Camera/RTSP requires a real live source or test endpoint, timeout and
disconnect behavior, credential/network handling, and observable failure
evidence. None of those conditions has been validated, so substituting local
video or a simulated stream would violate the M-008 acceptance boundary.

### New phase boundary

- Phase 4 release status: `Offline Inference COMPLETE`.
- Camera/RTSP and M-008: `Deferred MUST`, still `待实现` in the Charter.
- Annotated video rendering: deferred from Phase 4 scope, remaining M-007
  acceptance requirement; not claimed complete by this release.
- M-006 and M-007 Charter acceptance remain subject to their own full
  acceptance review; the offline inference evidence is not a silent status
  change for those MUST items.
- Phase 5 remains `WAITING` and requires a separate authorization.
- No detector or tracker behavior is changed by this scope adjustment.


## ADR-019 Phase 4 Deferred Requirement Ownership

- Date: 2026-09-23
- Status: Accepted
- Clarifies: ADR-018 deferred requirement classification and ownership only.
- Authorization: user instruction for Phase 4 Scope Boundary Clarification.

### Context

Phase 4's accepted release scope covers offline inference delivery. Its original
broader plan also included live inputs, as retained in ADR-018's Original scope.
During implementation, image inference, MP4 sequential inference and real
validation completed. Camera/RTSP and annotated video rendering were not
implemented in Phase 4. The offline release does not complete M-007 or M-008.

### Decision

#### Camera / RTSP

M-008 remains a V1 MUST requirement. Phase 4 does not deliver Camera/RTSP.
It is deferred to later integration work, NOT an Extension. It is a deferred
MUST implementation, with the original Charter acceptance criteria unchanged.

#### Annotated Video Rendering

M-007 remains a V1 MUST requirement. Phase 4 delivers structured offline video
inference evidence. Annotated video rendering is deferred from Phase 4 and
remains part of M-007 acceptance. It is NOT an Extension.

#### Deferred requirement ownership

| Requirement | Delivery owner and phase | Final acceptance |
| --- | --- | --- |
| M-007 annotated video rendering | Phase 7 Web & Alerts: video page/service integration, building on Phase 4 structured output | Phase 9 Integration & Delivery checks full M-007 evidence against the unchanged Charter |
| M-008 Camera/RTSP | Phase 7 Web & Alerts: live-input service and real-time monitoring integration | Phase 9 Integration & Delivery checks full M-008 evidence against the unchanged Charter |

Phase 7 must deliver and verify these dependencies before declaring its related
video/real-time monitoring integration accepted. M-008 retains the Charter's
Camera OR RTSP acceptance wording; this allocation does not require both.
Phase 9 is the final acceptance owner, not permission to omit the Phase 7
integration dependencies. Neither requirement may be waived for V1 delivery.

#### Phase 5 Entry Condition

Phase 5 may start only when:

1. Phase 4 Offline Inference Gates PASS: the offline release tables in
   `docs/phases/PHASE_04_INFERENCE.md` and `docs/05_TEST_GATES.md`.
2. Deferred requirements have explicit ownership and a future delivery phase,
   as assigned above and acknowledged in Phase 7 and Phase 9 documents.
3. No frozen asset conflict exists; verify the frozen dataset, mapping,
   checkpoint, training assets and inference configuration at task entry.
4. Existing Phase 5 detection-output prerequisites and separate user
   authorization are satisfied.

P4-G3 remains deferred, not PASS, and is not an offline-release entry gate.
Its M-008 obligation remains assigned above. This clarification does not start
Phase 5 or certify a new frozen-asset verification.

### Consequence

Phase 4 status remains `Offline Inference COMPLETE`. Camera/RTSP implementation
and annotated video rendering remain deferred MUST work. MUST definitions,
acceptance criteria and statuses are unchanged. Phase 5 remains `WAITING`.
No code, tests, configuration, model or dataset changes are authorized here.

## ADR-020

- Date: 2026-09-23
- Status: Accepted
- Title: Phase 5 tracking and association interfaces are frozen before implementation

### Decision

Phase 5 uses explicit project-owned contracts:

- `DetectionResult -> PersonTrackingAdapter -> TrackResult`;
- `TrackResult + PPE DetectionResult -> PPEAssociationAdapter ->
  AssociationResult`.

ByteTrack is used through the mature Ultralytics `8.4.157` integration and
tracks person class ID `0` only. The repository does not copy ByteTrack source.

Person-PPE association may use bbox containment, IoU and confidence
thresholds. Nearest-distance or forced assignment is prohibited. If no
candidate satisfies the frozen geometry/confidence rules, or the leading
candidates are ambiguous, the output status is `unknown`.

The tracker and association policy is frozen in `configs/tracker.yaml` and
`configs/association.yaml`; schemas and adapter protocols are frozen under
`core/schemas/` and the `core/tracking` and `core/association` packages.

### Context

Phase 4 returns only structured `DetectionResult` values. Phase 5 must add
stateful tracking and person attribution without returning Ultralytics Results
objects or silently inventing ownership. Overlapping people and PPE occlusion
make nearest-centre matching unsafe, while association errors would corrupt
all downstream compliance and event logic.

### Consequences

Phase 5-1 implements the person-only tracker adapter. Phase 5-2 implements the
association adapter. Phase 5-3 verifies single-person, multi-person, overlap,
missing-PPE and uncertain-association behavior.

Threshold or schema changes require explicit review and updated evidence.
Phase 5-0 does not implement tracking or association, does not load a model,
does not modify the dataset, mapping, training configuration or checkpoint,
and does not change M-009 or M-010 from `待实现`.

## ADR-021

- Date: 2026-09-23
- Status: Accepted
- Title: PPE compliance events are conservatively temporally confirmed

### Decision

Phase 6 consumes immutable Phase 5 `AssociationResult` values through a
dedicated `AssociationAdapter`. The frozen rule path is:

```text
AssociationResult
-> ComplianceInput
-> ComplianceResult
-> temporal confirmation
-> ComplianceEvent
```

`NO_HELMET` and `NO_VEST` are emitted only from associated `no_hardhat` and
`no_vest` evidence. Missing, unassigned-unknown or conflicting evidence is
reported as `PPE_UNKNOWN`; it is never converted into a confident violation or
compliant result.

An event requires at least `5` consecutive candidate frames and `1.0` second
of duration under the frozen configuration. Event identity is isolated by
`(track_id, event_type)`. An active cycle emits one event, recovers after
`5` compliant frames, and applies a `30` second cooldown before another event
for the same key.

The JSONL wire contract is exactly:

```text
type
track_id
confidence
timestamp
```

### Context

Phase 5 deliberately leaves uncertain Person-PPE ownership unassigned.
Forcing those records onto a nearest person would create unsafe alerts.
Likewise, treating an absent or uncertain PPE observation as compliance would
hide missing evidence. Compliance therefore needs an explicit unknown state
and temporal evidence rather than single-frame rule triggers.

### Consequences

The original Phase 5 schemas and tracking implementation remain unchanged.
Phase 6 stores deterministic offline evidence under `outputs/events.jsonl`,
which is Git-ignored. Its rule and event behavior is testable without Torch,
Ultralytics, a checkpoint, a camera or a network stream.

This ADR does not close the historical P5-3-G5 real-runtime block and does not
change M-011 through M-014 from `待实现`; runtime acceptance requires separate
evidence.

## ADR-022

- Date: 2026-09-23
- Status: Accepted
- Title: Phase 7 Web and alert architecture is frozen before implementation

### Decision

Phase 7 uses the locked goal `SQLite + Snapshot + TTS + Streamlit` and the
following frozen boundaries:

- SQLite is the first V1 persistent store for queryable event history,
  status, snapshot metadata and rebuildable statistics.
- The Streamlit UI calls services only. It does not run SQL, inference,
  tracking, association, rules or alert policy directly.
- MP4, USB Camera and RTSP inputs are behind one project-owned `VideoSource`
  contract. Only source adapters may call `cv2.VideoCapture`; business code
  may not.
- Confirmed events are persisted before alert delivery. Evidence snapshots
  use the relative path
  `artifacts/events/snapshots/YYYYMMDD/event_<event-id>.jpg`, with integrity
  metadata stored in SQLite.
- Console, Web and TTS are V1 alert adapters. Console and Web are the first
  implementation priority, but TTS remains required by M-017 and cannot be
  removed from Phase 7 acceptance.
- Email, WeChat and SMS remain future Extension adapters.
- Phase 7 adds a separate persisted-event DTO. It maps the in-memory Phase 6
  `ComplianceEvent` and preserves the frozen four-field JSONL wire contract
  exactly.
- The Phase 7 subphase order is `7-0` Architecture Freeze, `7-1` Event
  Storage, `7-2` Evidence Snapshot, `7-3` Dashboard and Alerts, `7-4`
  Camera/RTSP, `7-5` Runtime Validation and `7-Release`.

### Context

Phase 6 ends at a model-independent `ComplianceEvent` and append-only JSONL
wire record. Phase 7 must add persistence, evidence, query, live-source and
alert behavior without changing the released detector, tracker, association,
rule engine or event identity. Streamlit reruns also make it unsafe for the
UI to own a long-running source loop.

### Consequences

The architecture remains under the existing `core/`, `services/`, `infra/`,
`web/` and `utils/` boundaries; no `src/` tree is introduced. Phase 7 must
implement migrations and query tests before dashboard work, evidence write
and reconciliation before alert integration, and real runtime validation
before release. This ADR does not implement SQLite, snapshots, Streamlit,
Camera/RTSP, annotated video rendering or alerts, and it does not change any
MUST status.

## ADR-023

- Date: 2026-09-24
- Status: Accepted
- Title: Phase 8 Safety Intelligence Agent boundary and grounding contract

### Decision

Phase 8 remains strictly downstream of the deterministic PPE pipeline:

```text
Video
-> Detection
-> Tracking
-> PPE Association
-> Compliance Engine
-> Event Store
-> Safety Analytics / Agent
```

The Phase 8 read boundary is the existing `EventQueryService`. The agent and
analytics layers must not execute direct SQL, mutate events or import
inference/tracking/association/compliance implementation to reinterpret a
decision.

The architecture is:

```text
SafetyAnalyticsService
-> SafetyContextBuilder
-> SafetyLLMClient
-> StructuredSafetyReport
```

`SafetyAnalyticsService` is deterministic and provider-independent.
`SafetyAnalysisContext` is versioned as `phase8-context-v1` and separates
`observed_facts`, `calculated_metrics`, `metadata` and
`unavailable_fields`. A tracker-scoped `track_id` is not stable person
identity. Unsupported duration, identity and alert-delivery metrics are marked
unavailable rather than inferred.

`SafetyLLMClient` is a provider-independent protocol:

```text
generate_report(context) -> StructuredSafetyReport
```

`StructuredSafetyReport` is versioned as `phase8-report-v1`. Factual claims
must reference valid context facts or metrics; recommendations remain
advisory and separately identified; event IDs, track IDs and numbers are
validated; raw evidence bytes and absolute paths are excluded by default.
Invalid or ungrounded provider output is rejected. Provider failure triggers a
deterministic `TEMPLATE_FALLBACK` result and never affects the monitoring
pipeline.

The Basic Agent may call only allowlisted read-only tools implemented by the
existing service layer. Arbitrary SQL, shell, filesystem, network side effects,
external actions, autonomous loops, LangChain, LlamaIndex and other Agent
frameworks are out of scope.

### Context

Phase 7 exposes persisted events, lifecycle status and verified snapshot
metadata, but it does not expose stable person identity, violation duration or
alert-delivery telemetry. Treating those values as available would create
unsupported safety conclusions. The existing LLM and Agent classes are
placeholders and must not become an implicit provider or tool framework.

### Consequences

P8-0 is design-only. It does not implement an LLM provider, call an external
API, install a dependency or modify Phase 0 through Phase 7. After human
review, P8-1 implemented deterministic analytics, canonical context
serialization and context-schema validation. Report-level grounding validation
remains with P8-2 because the `phase8-report-v1` contract is not implemented in
P8-1. Provider selection and Agent planning remain later decisions. M-021,
M-022 and M-023 remain `待实现`, and Phase 9 is not started.
