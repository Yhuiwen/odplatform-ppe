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
