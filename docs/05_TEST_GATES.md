# Test Gates

## Gate Rules

- A Gate is PASS only when its stated evidence exists and was executed.
- A phase remains `实现中` while any required Gate fails.
- No later phase may hide or waive an earlier Gate.
- Results below are evidence summaries, not substitutes for reproducible
  commands.

## Phase 0 Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| G0-1 | 项目目录完整 | `test_structure.py`: all required directories and entry points present | PASS |
| G0-2 | Python package 可导入 | `test_imports.py`: 39 package/module imports passed | PASS |
| G0-3 | YAML 配置全部可解析 | `test_config_loader.py`: all six UTF-8 YAML mappings passed | PASS |
| G0-4 | paths 工具工作正常 | `test_paths.py`: root discovery and explicit creation passed | PASS |
| G0-5 | 日志初始化工作正常 | `test_logging_utils.py`: console/file write passed | PASS |
| G0-6 | system info 能正常获取 | `test_system_utils.py`: passed without torch/CUDA installed | PASS |
| G0-7 | pytest 基础测试通过 | `python -m pytest`: 92 passed | PASS |
| G0-8 | README 快速开始与实际一致 | README commands and Phase 0 dependency scope verified | PASS |
| G0-9 | Markdown 没有明显断链/缺失 | Governance inventory and local Markdown link test passed | PASS |
| G0-10 | git diff --check PASS | Intent-to-add whitespace check exited 0 with no output | PASS |
| G0-11 | 未下载完整训练数据 | Asset directory test found only `.gitkeep`; data card marked NOT DOWNLOADED | PASS |
| G0-12 | 未进入 Phase 1+ | Future business calls assert explicit `NotImplementedError` | PASS |
| G0-13 | Charter 锁定内容未发生非授权修改 | Locked markers, 26 MUST, 12 Extension, and pending statuses asserted | PASS |

## Future Phase Gate Index

Detailed gates are defined in each phase document. A later phase cannot begin
until every gate in its immediate predecessor is PASS.

## Phase 1A Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| G1A-1 | CSS 至少有一个可验证权威/可信来源 | Original Roboflow Universe project selected; Kaggle retained as secondary mirror evidence | PASS |
| G1A-2 | 数据集许可证有直接证据 | Roboflow Construction Site Safety project page directly states `License: CC BY 4.0`; CC legal terms are recorded separately | PASS |
| G1A-3 | 原始类别定义有直接证据 | Roboflow version 27 records 25 original class names and per-class box counts | PASS |
| G1A-4 | 标注格式已确认 | Source annotation task is bounding-box object detection; selected export is Ultralytics YOLO / `yolov8`; target framework is YOLO11 | PASS |
| G1A-5 | 数据规模有来源证据 | Version 27: 2,801 images; 2,605/114/82 split; 25 classes; total annotation count `UNVERIFIED / NOT FROZEN` | PASS |
| G1A-6 | 下载方式已确认 | Roboflow Universe ZIP or Python SDK/REST; workspace, project, version, and format frozen | PASS |
| G1A-7 | 重分发/引用义务已记录 | CC BY 4.0 share/adapt terms, attribution, license link, change notice, and no-endorsement rule recorded | PASS |
| G1A-8 | 来源冲突已解析或明确标为 blocker | Version drift and mirror mismatch documented; V1 frozen to Roboflow version 27; mirror-correspondence remains explicitly unresolved but excluded | PASS |
| G1A-9 | 未下载完整数据集 | No dataset archive, images, labels, or generated export retrieved | PASS |
| G1A-10 | PROJECT_CHARTER 无修改 | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |
| G1A-11 | 未进入 Phase 1B | Dataset Card and Phase 1 document keep download status `NOT DOWNLOADED`; no processing artifacts | PASS |

Phase 1A result: PASS at its closure. Phase 1 overall remains `实现中`; P1B was
subsequently started under the Phase 1B gate below.

## Phase 1B Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| G1B-1 | 下载来源严格为 Roboflow CSS version 27 | `source.json` records workspace `roboflow-universe-projects`, project `construction-site-safety`, version `27`, format `yolov8`, and Roboflow API download | PASS |
| G1B-2 | Export format 严格为 `yolov8` | `source.json`, `data.yaml` URL, and snapshot record identify the `yolov8` export | PASS |
| G1B-3 | Archive/source snapshot SHA-256 已记录 | API returned an extracted directory, so archive hash is explicitly unavailable; source manifest SHA-256 is `ea0de4b0...f98d795` | PASS |
| G1B-4 | `source/` 未被本项目修改 | Full read-only comparison of the downloaded directory and `source/` matched for all 5,601 files | PASS |
| G1B-5 | 实际图片数 2605 / 114 / 82 / 2801 | Expected metadata is 2,605 / 114 / 82 / 2,801; observed artifact is 2,603 / 114 / 82 / 2,799, so train and total are each two below expectation | FAIL |
| G1B-6 | Image-label pairing 已检查 | Real source: zero missing labels, zero orphan labels, zero zero-byte images; 23 empty label files reported without deletion | PASS |
| G1B-7 | `data.yaml` 原件存在且未修改 | Source and snapshot `data.yaml` both hash to `5c393e74...b3d21b34`; file retains relative train/val/test paths | PASS |
| G1B-8 | 实际原始类别已从 `data.yaml` 读取并记录 | Actual `nc: 10`; all ten names and the mismatch against the P1A-reported 25 classes are recorded | PASS |
| G1B-9 | 五个目标语义类别存在于 source `data.yaml` | `Person`, `Hardhat`, `NO-Hardhat`, `Safety Vest`, and `NO-Safety Vest` are present | PASS |
| G1B-10 | 完整 Manifest 已生成 | 5,601-file manifest generated and verified; file SHA-256 `ea0de4b0...f98d795` | PASS |
| G1B-11 | Dataset snapshot summary 已生成 | `docs/dataset_snapshots/CSS_V27_YOLOV8.md` records source, counts, classes, integrity, hashes, and failure status | PASS |
| G1B-12 | 无机器绝对路径写入可提交文件 | Manifest paths are source-relative; governance tests reject machine absolute paths in evidence and snapshot documents | PASS |
| G1B-13 | 无 API Key / token 写入仓库 | `source.json` records `secret_saved: NO`; no credential value is present | PASS |
| G1B-14 | 完整 dataset 未进入 Git | `data/external/` remains ignored; only synthetic fixture files are intended for tracking | PASS |
| G1B-15 | PROJECT_CHARTER 无修改 | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |
| G1B-16 | 未开始 P1C | No conversion, remapping, cleaning, or source mutation was added | PASS |

Phase 1B result: `BLOCKED / NEEDS FREEZE CORRECTION`. The immutable snapshot and
tooling are present, but G1B-5 fails and the actual 10-class export differs from
the P1A-reported 25-class metadata. ADR-010 now requires a complete export
artifact fingerprint; `CSS-V1.1 Candidate` is recorded but not frozen. P1B
remains `实现中`; P1C must not start until the freeze correction is resolved.

P1B.1 freeze-correction gates:

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P1B.1-G1 | Historical mismatch preserved without deleting evidence | Dataset Card retains expected 25-class/2,801-image metadata and observed 10-class/2,799-image artifact | PASS |
| P1B.1-G2 | Artifact fingerprint model defined | ADR-010 lists workspace, project, version, export format, data.yaml SHA256, class list, manifest SHA256, and actual split counts | PASS |
| P1B.1-G3 | Candidate is not mistaken for a freeze | `CSS-V1.1 Candidate` is marked `Candidate, not frozen` | PASS |
| P1B.1-G4 | Dataset and P1C remain untouched | No dataset file changed and P1C remains `待实现` | PASS |

P1B.2 candidate-evaluation gates:

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P1B.2-G1 | Candidate comparison is recorded | `docs/11_DATASET_CANDIDATE_EVALUATION.md` compares source identity, fingerprint, counts, classes, PPE relevance, advantages, risks, and suitability | PASS |
| P1B.2-G2 | V1 selection criteria are frozen in an ADR | ADR-011 prioritizes reproducibility, verified artifact identity, PPE task relevance, license clarity, and training feasibility; class count alone is not decisive | PASS |
| P1B.2-G3 | CSS-V1 remains blocked | CSS-V1 remains `BLOCKED / NEEDS FREEZE CORRECTION` | PASS |
| P1B.2-G4 | CSS-V1.1 remains a candidate | CSS-V1.1 remains `Candidate, not frozen` | PASS |
| P1B.2-G5 | P1C and M-001 remain unchanged | P1C remains `待实现`; M-001 remains `待实现`; no conversion, download, or training was performed | PASS |

P1B.3 final-freeze gates:

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P1B-F1 | Dataset identity frozen | `CSS-PPE-10-V1` is recorded as the frozen V1 dataset in `docs/12_DATASET_FREEZE_DECISION.md`; CSS-V1 is rejected | PASS |
| P1B-F2 | Artifact fingerprint recorded | workspace, project, version, format, `data.yaml` SHA256, manifest SHA256, class list, and actual split counts are bound | PASS |
| P1B-F3 | Class list frozen | ten exported classes are frozen exactly as read from the unmodified `data.yaml` | PASS |
| P1B-F4 | Split counts frozen | train `2603`, valid `114`, test `82`, total `2799` are frozen | PASS |
| P1B-F5 | P1C input immutable | P1C input is the Git-ignored immutable `data/external/css-v27-yolov8/source/` snapshot; no conversion or mutation was performed | PASS |

P1B.3 result: `FROZEN`. The historical G1B-5 failure remains visible because it
measured the mismatch against the rejected CSS-V1 metadata. P1B.3 resolves the
freeze decision by selecting the materialized artifact by fingerprint rather
than rewriting that historical evidence. P1C remains `待实现`.

P1C-0 class-mapping design gates:

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P1C-0-G1 | Frozen dataset identity remains unchanged | `CSS-PPE-10-V1` fingerprint remains bound in the Dataset Card and freeze decision; no source file was modified | PASS |
| P1C-0-G2 | Original classes and distribution are recorded | `docs/13_CLASS_MAPPING_DESIGN.md` records all ten classes and the read-only per-split box counts | PASS |
| P1C-0-G3 | Candidate mappings cover all source classes | A, B, and C each state retained/mapped classes and explicit discard dispositions | PASS |
| P1C-0-G4 | Required design questions are analyzed | Mask, machinery/vehicle, Safety Cone, YOLO11 class effects, and downstream layer impacts are documented | PASS |
| P1C-0-G5 | No mapping is selected and no conversion occurs | The design document says no final selection; P1C remains `待实现` and no processed dataset exists | PASS |
| P1C-0-G6 | Decision protections are recorded | ADR-013 requires a frozen mapping before conversion; RISK-016 records mapping-quality risk; Charter remains unchanged | PASS |

P1C-0 result: `DESIGN RECORDED / AWAITING MAPPING DECISION`. The design work is
complete for review, but no class mapping is frozen and P1C conversion remains
not started.

P1C-1 class-mapping decision gates:

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P1C-1-G1 | Strategy C is frozen | `docs/14_CLASS_MAPPING_DECISION.md` selects Strategy C and records the complete source-to-training map | PASS |
| P1C-1-G2 | Training class IDs are unique and ordered | Seven unique new IDs are recorded; IDs 0 through 4 preserve ADR-003 compliance semantics | PASS |
| P1C-1-G3 | Discard policy is complete | Mask, NO-Mask, and Safety Cone are explicitly discarded with reasons and future handling | PASS |
| P1C-1-G4 | Frozen source remains unchanged | `CSS-PPE-10-V1` `data.yaml` SHA256 remains `5c393e74...d21b34`; no processed dataset exists | PASS |
| P1C-1-G5 | Decision protections are recorded | ADR-014 freezes the mapping; RISK-016 requires the mapping to be frozen before conversion | PASS |

P1C-1 result: `FROZEN`. Strategy C is the approved mapping contract. P1C
conversion remains `待实现` and must not start automatically.

## Phase 1C-2 Conversion Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| G1C2-1 | Mapping contract exists | `docs/dataset_contracts/CSS-PPE-10-V1-MAPPING.yaml` records `CSS-PPE-10-V1`, `PPE-MAPPING-V1`, source classes, target classes, mapping, discard classes, and conversion rules | PASS |
| G1C2-2 | Source immutable | Conversion preflight matched `data.yaml` SHA256 `5c393e74...d21b34` and manifest SHA256 `ea0de4b0...f98d795`; post-conversion hashes are unchanged | PASS |
| G1C2-3 | Output generated | Git-ignored `data/processed/css-ppe-10-v1/` contains train/valid/test images and labels, `data.yaml`, and four metadata files | PASS |
| G1C2-4 | Image count preserved | Source and processed counts are train `2603`, valid `114`, test `82`, total `2799` | PASS |
| G1C2-5 | Image hash preserved | Per-image SHA-256 comparison found zero mismatches | PASS |
| G1C2-6 | Labels converted correctly | Target IDs are `0` through `6`; offline tests verify the frozen mapping and unchanged bounding-box tokens | PASS |
| G1C2-7 | Discard statistics generated | `Mask` `1792`, `NO-Mask` `3362`, `Safety Cone` `3306`; total discarded `8460` | PASS |
| G1C2-8 | Processed `data.yaml` correct | Seven classes in frozen order with train/valid/test paths `../train/images`, `../valid/images`, `../test/images` | PASS |
| G1C2-9 | No unknown classes | Conversion records `unknown_class_ids: []` and tests assert unknown source IDs raise an error | PASS |
| G1C2-10 | Conversion deterministic | Output contains no timestamps or machine paths; offline repeated-conversion tree hashes are identical | PASS |
| G1C2-11 | No training started | No training code, weights, runs, model evaluation, or Phase 2 work was added | PASS |
| G1C2-12 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty; M-001 remains `待实现` | PASS |

P1C-2 result: `COMPLETED / MANUAL REVIEW PASS`. The processed dataset is
Git-ignored. P1D remains `待实现`; M-001 remains `待实现`.

## Phase 1D-0 Quality Validation Design Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P1D-0-G1 | Quality plan exists with all required dimensions | `docs/16_DATASET_QUALITY_PLAN.md` defines Q1 structure, Q2 class distribution, Q3 empty labels, Q4 bboxes, Q5 small objects, Q6 duplicates, Q7 leakage, Q8 label consistency, and the report format | PASS |
| P1D-0-G2 | Quality thresholds are explicit | Small `< 0.01`, medium `< 0.09`, large `>= 0.09`; small-object risk `20%` / `40%`; perceptual dHash distance `<= 5` are frozen in the plan and `QualityThresholds` | PASS |
| P1D-0-G3 | Validation remains observation-only | `DatasetQualityService.analyze()` returns a report object, exposes no repair API, and records source-relative manifest hashes before and after analysis | PASS |
| P1D-0-G4 | Required deterministic metrics are implemented | `utils/quality_metrics.py` covers bbox parsing/issues, size buckets, class distribution, exact duplicate grouping, and cross-split leakage grouping | PASS |
| P1D-0-G5 | Real dataset was not executed | P1D-0 ran only synthetic offline fixtures; no real `CSS-PPE-10-V1` quality report was generated | PASS |
| P1D-0-G6 | Offline validation tests pass | Tests cover plan existence, dataset immutability, invalid bbox detection, deterministic class distribution, deterministic duplicates, leakage observation, and unchanged dataset hashes | PASS |
| P1D-0-G7 | Governance and project status are preserved | ADR-015 and RISK-017 are recorded; P1C-2 is manually reviewed PASS; at P1D-0 close, P1D real execution remained `待实现` (subsequently completed by P1D-1); M-001 remains `待实现`; Charter remains unchanged | PASS |

P1D-0 result: `COMPLETED / DESIGN FROZEN / MANUAL REVIEW PASS`.
The framework is implemented and verified only with synthetic fixtures. P1D-1
is the first step permitted to execute it against the real processed dataset.

## Phase 1D-1 Real Dataset Quality Validation Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| G1D1-1 | Payload scope fixed | Validation covers only `data.yaml`, train/valid/test images, and labels; metadata and report files are excluded | PASS |
| G1D1-2 | Hash unchanged | Payload manifest SHA256 is `bc762204e2305164cfdbc492d15269b84c4ce4ff3cfdcdc805baf84c5616237b` before and after analysis across 5,599 files | PASS |
| G1D1-3 | Structure valid | All six split image/label directories exist; counts match with train `2603`, valid `114`, test `82`, total `2799`; zero missing/orphan labels and zero zero-byte images | PASS |
| G1D1-4 | Class statistics generated | Seven frozen classes, 30,375 boxes, train/valid/test box counts, PPE share, and imbalance ratio are recorded | PASS |
| G1D1-5 | Bbox validation complete | 30,375 valid lines; zero invalid bbox, invalid class ID, invalid coordinate, or malformed line | PASS |
| G1D1-6 | Duplicate analysis complete | Zero exact image duplicate groups; five dHash candidate pairs at Hamming distance `<= 5`, with full counts and deterministic groups | PASS |
| G1D1-7 | Leakage analysis complete | Zero exact cross-split groups; two perceptual cross-split candidate groups across `valid` and `test` are recorded as risk evidence | PASS |
| G1D1-8 | Quality report generated | `docs/17_DATASET_QUALITY_REPORT.md` and Git-ignored `metadata/quality_report.json` contain all required sections and metrics | PASS |
| G1D1-9 | No dataset modification | Payload hashes match; no image, label, `data.yaml`, or payload metadata file was deleted, relabelled, remapped, or rewritten | PASS |
| G1D1-10 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty; M-001 remains `待实现` | PASS |

P1D-1 result: `COMPLETED / PASS`. Four risk flags remain recorded for P1E:
perceptual split-leakage candidates, HIGH small-object risk, class imbalance,
and empty labels. They are observations, not permission to modify the frozen
dataset. P1E remains `待实现`; training remains prohibited.

## Phase 1E-0 Dataset Release & Training Preparation Design Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| G1E0-1 | Dataset release contract exists | `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml` binds `CSS-PPE-10-V1`, `css-ppe-10-v1`, `PPE-MAPPING-V1`, seven ordered classes, source/processed fingerprints, and the quality report | PASS |
| G1E0-2 | Experiment structure exists | `experiments/README.md`, `experiments/configs/baseline.yaml`, `experiments/configs/augmentation.yaml`, `experiments/runs/.gitkeep`, and `experiments/reports/.gitkeep` exist | PASS |
| G1E0-3 | Training config schema exists | `configs/training/schema.yaml` is non-executable, defines required fields, records the `EXP-\d{3}` ID rule, and requires dataset/version/weights/hardware/metrics/checkpoint records | PASS |
| G1E0-4 | Metrics defined | `docs/18_TRAINING_STRATEGY.md`, the schema, and the EXP-001 template require mAP50, mAP50-95, precision, recall, per-class AP, confusion matrix, inference speed, and model size | PASS |
| G1E0-5 | Dataset immutable | Contract fingerprints match the materialized source `data.yaml`, source manifest, and processed manifest; no dataset or label file was modified | PASS |
| G1E0-6 | No training executed | No run/report artifact beyond `.gitkeep`, no training output, and no `.pt`/`.pth`/`.weights` file were created; all configuration templates are marked non-executable | PASS |
| G1E0-7 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty; M-001 remains `待实现` | PASS |

P1E-0 result: `COMPLETED / DESIGN FROZEN`. The release contract and
configuration-driven training preparation framework are recorded, but P1E
itself remains not started and training remains prohibited. The next allowed
step is P1E-1 Baseline Training Preparation Review.

## Phase 1E-1 Baseline Training Preparation Review Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P1E1-G1 | Training contract verified | `docs/reports/P1E-1_TRAINING_CONTRACT_AUDIT.md` confirms dataset ID, processed path, mapping, class order/count, quality report, immutable boundary, and all three materialized fingerprints | PASS |
| P1E1-G2 | Experiment config verified | `docs/reports/P1E-1_EXPERIMENT_CONFIG_AUDIT.md` confirms YAML parsing, canonical `EXP-001` uniqueness, model/dataset references, output paths, seed, device strategy, hyperparameter state, and metrics | PASS |
| P1E1-G3 | Environment audited | `docs/reports/P1E-1_TRAINING_ENVIRONMENT_AUDIT.md` records Python, PyTorch, Ultralytics, CUDA, GPU, memory, and readiness; result is `NOT READY FOR TRAINING` without installing anything | PASS |
| P1E1-G4 | Reproducibility checklist complete | `docs/reports/P1E-1_REPRODUCIBILITY_CHECKLIST.md` covers dataset, experiment, runtime, artifacts, and reproduction sequence | PASS |
| P1E1-G5 | Runbook created | `docs/reports/EXP-001_TRAINING_RUNBOOK.md` records environment requirements, data paths, config/entry points, output directories, logs, reproduction steps, and stop conditions as `DESIGN ONLY` | PASS |
| P1E1-G6 | No training executed | No training run, model weight, checkpoint, run output, or dependency installation was created; `execution_enabled` remains `false` | PASS |
| P1E1-G7 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty; M-001 remains `待实现` | PASS |

P1E-1 result: `COMPLETED / REVIEW PASS`. Environment readiness is
`NOT READY FOR TRAINING`, so the next allowed step is
`P2-TRAINING EXECUTION PREPARATION`; it must not execute training until a new
explicit instruction and Phase 2 entry conditions authorize it.

## Phase 2-0 Preparation Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-0-G1 | Environment audited | `docs/reports/phase-02/P2-0_TRAINING_READINESS.md` records OS, Python, pip, PyTorch, Ultralytics, CUDA, GPU, RAM, and CPU without installation | PASS |
| P2-0-G2 | Dependency strategy documented | `docs/designs/phase-02/P2-0_DEPENDENCY_STRATEGY.md` compares Windows NVIDIA, WSL2 CUDA, cloud GPU, and CPU fallback | PASS |
| P2-0-G3 | Version matrix documented | `docs/designs/phase-02/P2-0_VERSION_MATRIX.md` records compatibility policy and pending states | PASS |
| P2-0-G4 | Training readiness documented | Dataset `PASS`, Experiment `PASS`, Environment `NOT READY`, GPU `PENDING`, Dependencies `PENDING` | PASS |
| P2-0-G5 | No training executed | No dependency, weight, run, evaluation, or dataset mutation was created | PASS |
| P2-0-G6 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |

P2-0 result: `COMPLETED`. Preparation records are complete, but the environment
remains `NOT READY FOR TRAINING`.

## Phase 2-1 Environment Setup Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-1-G1 | Environment decision documented | `docs/designs/phase-02/P2-1_ENVIRONMENT_DECISION.md` selects controlled cloud GPU and records alternatives | PASS |
| P2-1-G2 | Dependency specification documented | `docs/designs/phase-02/P2-1_DEPENDENCY_SPECIFICATION.md` records planned Python, PyTorch, CUDA, torchvision, Ultralytics, NumPy, and key supporting versions as `PLANNED VERSION` | PASS |
| P2-1-G3 | Setup plan documented | `docs/designs/phase-02/P2-1_SETUP_PLAN.md` defines installation order, verification, rollback, and freeze outputs as design only | PASS |
| P2-1-G4 | No training executed | No cloud instance, dependency installation, model weight, run output, evaluation, dataset mutation, or class mapping change was created | PASS |
| P2-1-G5 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty; M-001 and M-004 remain `待实现` | PASS |

P2-1 result: `COMPLETED / DESIGN COMPLETE`. The environment architecture and
planned dependency stack are recorded, but provisioning and dependency freeze
remain pending. The next allowed step is
`P2-2 TRAINING EXECUTION AUTHORIZATION REVIEW`; training remains prohibited.

## Phase 2-2 Training Authorization Review Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-2-G1 | Cloud environment reviewed | `docs/reports/phase-02/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` records provider, region, GPU, VRAM, CUDA capability, image, storage, cost, and retention as `PENDING_SELECTION` | PASS |
| P2-2-G2 | Dependencies reviewed | `docs/reports/phase-02/P2-2_DEPENDENCY_FREEZE.md` records the planned versions, missing installation evidence, missing lock, missing runtime fingerprint, and `Dependency Freeze: PENDING` | PASS |
| P2-2-G3 | EXP-001 reviewed | `docs/reports/phase-02/P2-2_EXP001_EXECUTION_REVIEW.md` verifies dataset, model, class count, seed state, output/logging paths, metrics, and `execution_enabled: false` without changing the config | PASS |
| P2-2-G4 | Authorization checklist created | `docs/reports/phase-02/P2-2_TRAINING_AUTHORIZATION.md` records Dataset/Mapping/Experiment `PASS`, Environment/Dependencies/GPU `PENDING`, and Authorization `NOT GRANTED` | PASS |
| P2-2-G5 | No training executed | No cloud instance, package installation, weight download, training, evaluation, dataset mutation, or class mapping change was created | PASS |
| P2-2-G6 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty; M-001 and M-004 remain `待实现` | PASS |

P2-2 result: `COMPLETED / REVIEW COMPLETE`. Authorization remains
`NOT GRANTED`. The next allowed step is
`WAIT FOR TRAINING AUTHORIZATION`; training remains prohibited.

## Phase 2-3 Cloud Provider Selection Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-3-G1 | Candidate providers compared | `docs/reports/phase-02/P2-3_CLOUD_PROVIDER_SELECTION.md` compares AutoDL, Alibaba Cloud GPU ECS, Tencent Cloud GPU, and other options | PASS |
| P2-3-G2 | Recommended provider and GPU selected | AutoDL is selected as the primary design target with RTX 4090 24GB and a documented RTX 3090 contingency boundary | PASS |
| P2-3-G3 | Cost, upload, and retention risks reviewed | Planning cost envelope, 40 GPU-hour cap, CNY 150 ceiling, dataset upload boundary, and cleanup/retention rules are recorded | PASS |
| P2-3-G4 | Authorization remains NOT GRANTED | `docs/reports/phase-02/P2-2_TRAINING_AUTHORIZATION.md` records Environment/GPU as `DESIGN SELECTED / NOT PROVISIONED` and Authorization as `NOT GRANTED` | PASS |
| P2-3-G5 | No instance, dependency, weight, or training was created | No cloud resource, package installation, dataset upload, model weight, run output, evaluation, or training was created | PASS |
| P2-3-G6 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty; M-001 and M-004 remain `待实现` | PASS |

P2-3 result: `COMPLETED / DESIGN SELECTION COMPLETE`. The provider choice is
selected but not provisioned, dependency freeze remains `PENDING`, and
authorization remains `NOT GRANTED`. The next allowed step is
`WAIT FOR HUMAN TRAINING AUTHORIZATION`.

## Phase 2-4-G3 AutoDL Dependency Provisioning Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-4-G3-G1 | AutoDL instance identity recorded | `docs/reports/phase-02/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` records instance `bcb849a74f-38320766`, RTX 4090 24GB, Ubuntu 20.04.5, and GPU UUID | PASS |
| P2-4-G3-G2 | Isolated `ppe-exp001` environment created | Remote `conda info --envs` lists base and `/root/miniconda3/envs/ppe-exp001`; base dependencies were not modified | PASS |
| P2-4-G3-G3 | PyTorch CUDA stack installed | `torch 2.5.1+cu124`, `torchvision 0.20.1+cu124`, and `torchaudio 2.5.1+cu124` are installed | PASS |
| P2-4-G3-G4 | Ultralytics and runtime dependencies installed | `ultralytics 8.4.157`, `opencv-python 5.0.0.93`, NumPy 2.2.6, PyYAML, tqdm, matplotlib, and psutil are installed | PASS |
| P2-4-G3-G5 | PyTorch CUDA and Ultralytics imports verified | `torch.cuda.is_available()` is true on the RTX 4090 and all required imports succeed | PASS |
| P2-4-G3-G6 | No dataset, weight, training, or frozen identity change | Dataset transfer, weight download, training, source/config/dataset/mapping changes were not performed | PASS |
| P2-4-G3-G7 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |

P2-4-G3 result: `PASS`. The isolated dependency environment is provisioned
and verified. The full environment freeze and training authorization remain
outstanding.

## Phase 2-4-G4 Dataset Transfer & Integrity Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-4-G4-G1 | Remote dataset directory created | `/root/autodl-tmp/datasets/css-ppe-10-v1/` contains the transferred artifact | PASS |
| P2-4-G4-G2 | Frozen dataset transferred unchanged | Recursive SCP copied `data/processed/css-ppe-10-v1/` without restructuring, compression, or mutation | PASS |
| P2-4-G4-G3 | File, image, and label counts verified | 5,604 total files, 2,799 images, and 2,799 labels match locally and remotely | PASS |
| P2-4-G4-G4 | `data.yaml` and class mapping verified | Remote `data.yaml` declares `nc: 7` and the frozen `person, hardhat, no_hardhat, vest, no_vest, machinery, vehicle` order | PASS |
| P2-4-G4-G5 | Source and processed fingerprints verified | Processed `data.yaml` is `45cc2717...`; upstream source `data.yaml` is `5c393e7...`; processed manifest file is `dbfe43c4...` | PASS |
| P2-4-G4-G6 | Full remote manifest verification passed | `metadata/checksums.sha256` verified 5,602 entries; full external manifest verified 5,604 entries | PASS |
| P2-4-G4-G7 | No training, weights, or frozen identity change | No training, `yolo train`, weight download, label edit, annotation regeneration, mapping change, or EXP-001 config change occurred | PASS |
| P2-4-G4-G8 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |

P2-4-G4 result: `PASS`. The remote dataset is transferred and
integrity-verified. Training remains prohibited pending explicit
authorization.

## Phase 2-4 Final Provisioning Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-4-G1 | Instance created | AutoDL instance `bcb849a74f-38320766` is reachable on an RTX 4090 24GB host | PASS |
| P2-4-G2 | Runtime fingerprint recorded | `docs/reports/phase-02/P2-4_FINAL_PROVISIONING_REPORT.md` records OS, Python, conda, PyTorch, CUDA, driver, and GPU identity | PASS |
| P2-4-G3 | Dependencies installed and verified | `ppe-exp001` contains verified PyTorch, torchvision, torchaudio, Ultralytics, OpenCV, NumPy, and supporting runtime packages | PASS |
| P2-4-G4 | Dataset transferred and verified | `CSS-PPE-10-V1` is remote at `/root/autodl-tmp/datasets/css-ppe-10-v1/` with 5,604 files and full manifest PASS | PASS |
| P2-4-G5 | Training not executed | No `yolo train`, `python train.py`, benchmark, evaluation, or experiment run occurred | PASS |
| P2-4-G6 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |

P2-4 final result: `PASS`. Environment and dataset provisioning is complete;
training remains `NOT STARTED` pending explicit authorization.

## Phase 2-5 Training Authorization Review Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-5-G1 | Authorization report exists | `docs/reports/phase-02/P2-5_TRAINING_AUTHORIZATION_REPORT.md` records the review scope and result | PASS |
| P2-5-G2 | Configuration completeness reviewed | Canonical EXP-001 fields and unresolved execution values are listed | PASS |
| P2-5-G3 | Output paths reviewed | Run, log, report, and checkpoint paths match the schema | PASS |
| P2-5-G4 | Runtime fingerprint reviewed | P2-4 AutoDL, GPU, CUDA, Python, PyTorch, and Ultralytics evidence is recorded | PASS |
| P2-5-G5 | Reproducibility requirements reviewed | Dataset, mapping, fingerprints, metrics, and missing execution evidence are recorded | PASS |
| P2-5-G6 | Protected state preserved | No training, weight download, dataset, mapping, or configuration change occurred | PASS |

P2-5 review result: `BLOCKED`. The review itself completed, but training was
not authorized because unresolved parameters, weight-binary provenance,
complete environment freeze, and explicit human authorization remained
outstanding. P2-5.1 addresses only the configuration-parameter blocker.

## Phase 2-5.1 Configuration Freeze Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-5.1-G1 | Canonical configuration frozen | `configs/training/exp001_baseline.yaml` records model, dataset, class count, image size, epochs, batch, optimizer, LR strategy, seed, device, workers, and output paths | PASS |
| P2-5.1-G2 | Augmentation frozen | `experiments/configs/augmentation.yaml` records enabled values and no longer contains pending placeholders | PASS |
| P2-5.1-G3 | Schema aligned | `configs/training/schema.yaml` declares the frozen values and additional execution controls | PASS |
| P2-5.1-G4 | Freeze record created | `docs/reports/P2-5.1_CONFIGURATION_FREEZE.md` records parameters, dataset identity, hashes, and immutability rules | PASS |
| P2-5.1-G5 | Final report created | `P2-5.1_CONFIGURATION_FREEZE_REPORT.md` records required values and safety boundaries | PASS |
| P2-5.1-G6 | Execution remains disabled | Canonical config and schema keep `execution_enabled: false` and authorization `NOT GRANTED` | PASS |
| P2-5.1-G7 | No protected-state mutation | No training, weight download, dataset modification, or mapping modification occurred | PASS |
| P2-5.1-G8 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |

P2-5.1 result: `CONFIGURATION FREEZE COMPLETE`. Training remains
`NOT AUTHORIZED`.

## Phase 2-5.2 Weight Registration Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-5.2-G1 | Official initialization checkpoint acquired | Ultralytics `assets` release `v8.3.0` provides `yolo11n.pt` | PASS |
| P2-5.2-G2 | Binary identity verified | `5,613,764` bytes; SHA256 `0ebbc80d...7644ee1`; response MD5 matches the file | PASS |
| P2-5.2-G3 | Checkpoint structure verified | File is a PyTorch checkpoint ZIP with 507 members and `data.pkl` | PASS |
| P2-5.2-G4 | Weight manifest created | `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` records source, path, size, hashes, and initialization-only role | PASS |
| P2-5.2-G5 | Binary excluded from Git | `.gitignore` rule `*.pt` covers `models/pretrained/yolo11n.pt`; the file is untracked | PASS |
| P2-5.2-G6 | Authorization checklist updated | `docs/reports/phase-02/P2-2_TRAINING_AUTHORIZATION.md` records Weights `REGISTERED`, remote copy `NOT TRANSFERRED`, and Authorization `NOT GRANTED` | PASS |
| P2-5.2-G7 | Protected state preserved | No training, dataset modification, mapping modification, or EXP-001 configuration modification occurred | PASS |
| P2-5.2-G8 | Execution remains disabled | `execution_enabled: false`; training authorization remains `NOT GRANTED` | PASS |
| P2-5.2-G9 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |

P2-5.2 result: `READY` for initialization-weight registration only. The
registered binary does not authorize training and has not been transferred to
the remote training environment.

## Phase 2-5.3 Dependency Freeze Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-5.3-G1 | Conda environment lock exported | `locks/EXP-001/conda-environment.yml` records `ppe-exp001` with exact build strings and no environment prefix | PASS |
| P2-5.3-G2 | Pip freeze lock exported | `locks/EXP-001/pip-freeze-all.txt` contains 53 exact package records | PASS |
| P2-5.3-G3 | Conda explicit URL lock exported | `locks/EXP-001/conda-explicit.lock` contains 32 explicit package URLs | PASS |
| P2-5.3-G4 | Runtime fingerprint recorded | `locks/EXP-001/runtime-fingerprint.yaml` records instance, machine ID, OS, kernel, GPU, driver, CUDA, cuDNN, and runtime versions | PASS |
| P2-5.3-G5 | Exported locks match remote environment | Conda environment, conda explicit, and pip freeze outputs match the live `ppe-exp001` environment line-for-line | PASS |
| P2-5.3-G6 | Runtime dependency consistency verified | `python -m pip check` reports no broken requirements | PASS |
| P2-5.3-G7 | Authorization checklist updated | `docs/reports/phase-02/P2-2_TRAINING_AUTHORIZATION.md` records Dependencies `FROZEN / VERIFIED` and lock paths | PASS |
| P2-5.3-G8 | Protected state preserved | No training, package installation, dataset modification, mapping modification, or canonical configuration modification occurred | PASS |
| P2-5.3-G9 | Execution remains disabled | `execution_enabled: false`; training authorization remains `NOT GRANTED` | PASS |
| P2-5.3-G10 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |

P2-5.3 result: `READY`. The dependency-freeze blocker is resolved. Remote
weight transfer and explicit human training authorization remain outstanding.

## Phase 2-5.4 Remote Weight Transfer Verification Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-5.4-G1 | Remote destination checked before transfer | `/root/autodl-tmp/models/pretrained/yolo11n.pt` was absent; no existing file was overwritten | PASS |
| P2-5.4-G2 | Registered weight transferred | SCP transferred `models/pretrained/yolo11n.pt` to the AutoDL training environment | PASS |
| P2-5.4-G3 | Remote file exists | `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md` records remote existence and resolved path | PASS |
| P2-5.4-G4 | File size matches | Local and remote sizes are both `5,613,764` bytes | PASS |
| P2-5.4-G5 | SHA256 matches | Local and remote SHA256 are both `0ebbc80d...7644ee1` | PASS |
| P2-5.4-G6 | Machine-readable state updated | `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` records `remote_training_copy: VERIFIED` and the remote path/hash | PASS |
| P2-5.4-G7 | Authorization checklist updated | `docs/reports/phase-02/P2-2_TRAINING_AUTHORIZATION.md` records the remote weight copy as `VERIFIED` | PASS |
| P2-5.4-G8 | No protected-state mutation | No training, model execution, dataset modification, mapping modification, or EXP-001 canonical configuration modification occurred | PASS |
| P2-5.4-G9 | Execution remains disabled | `execution_enabled: false`; training authorization remains `NOT GRANTED` | PASS |
| P2-5.4-G10 | Charter unchanged | `git diff charter-v1 -- docs/00_PROJECT_CHARTER.md` is empty | PASS |

P2-5.4 result: `READY`. The remote initialization-weight copy is verified.
At that historical point, explicit human training authorization remained the
only outstanding blocker; P2-5.5 subsequently consumed that authorization.

## Phase 2-5.5 EXP-001 Training Execution Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-5.5-G1 | Explicit one-run authorization recorded | The user authorized EXP-001 training, and `configs/training/exp001_authorization.yaml` records the consumed single-run gate | PASS |
| P2-5.5-G2 | Frozen inputs verified before execution | The run recorded canonical config SHA256 `df6c55ae...cacff989`, processed data SHA256 `45cc2717...d2878a`, and weight SHA256 `0ebbc80d...7644ee1` | PASS |
| P2-5.5-G3 | Training completed | 95/100 epochs completed; early stopping selected epoch 75 | PASS |
| P2-5.5-G4 | Checkpoints produced | Best and last checkpoints are `5,479,891` bytes each; best SHA256 is `1c144eef...871f61` | PASS |
| P2-5.5-G5 | Metrics and run record produced | Overall validation: precision `0.899`, recall `0.649`, mAP50 `0.767`, mAP50-95 `0.480`; per-class metrics and speed are recorded | PASS |
| P2-5.5-G6 | Artifacts are locatable and Git-ignored | Run directory, logs, report, args, results, plots, and checkpoints are recorded in `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md` and remain ignored | PASS |
| P2-5.5-G7 | Frozen dataset, mapping, and config unchanged | No dataset, label, mapping, fingerprint, or canonical configuration change occurred | PASS |
| P2-5.5-G8 | M-004 status updated without claiming M-005 | Charter M-004 is `已经实现`; M-005 remains `待实现` and Phase 3 has not started | PASS |
| P2-5.5-G9 | Another run is not authorized | The authorization record is `CONSUMED`; rerunning EXP-001 in populated output paths is rejected | PASS |

P2-5.5 result: `COMPLETED`. The Phase 2 phase goal and P2-G1 through P2-G3
are satisfied by the M-004 experiment archive. Phase 3 evaluation remains
not started and requires a new explicit instruction.

## Phase 2-7 Training Result Freeze Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P2-7-G1 | Result identity frozen | Freeze report and best-model manifest record all required identities, metrics, runtime and duration | PASS |
| P2-7-G2 | Artifacts verified | 29 existing files hashed; execution-report hashes and config snapshot matched; binaries remain ignored | PASS |
| P2-7-G3 | Dataset integrity preserved | Source 5,601 entries and processed 5,602 entries match frozen manifests | PASS |
| P2-7-G4 | Mapping and frozen config preserved | Class order and frozen hashes match; task-entry comparison recorded in freeze report | PASS |
| P2-7-G5 | Phase boundary preserved | No training/evaluation; Phase 3 NOT STARTED; authorization remains CONSUMED | PASS |
| P2-7-G6 | Verification and Charter review | See final verification results in P2-7 freeze report; existing M-004 status-only diff retained | PASS |

## Phase 3-1 EXP-001 Test Evaluation Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P3-G1 | Four overall metrics complete and replayable | PHASE_3_EVALUATION_REPORT.md; metrics.json and offline replay | PASS |
| P3-G2 | Five PPE per-class AP values in frozen order | EXP-001_EVALUATION_SUMMARY.json includes classes 0-4 and separate context classes 5-6 | PASS |
| P3-G3 | Controlled model comparison | CMP-001 best/last checkpoint comparison; see subsequent P3-G3 evidence below | PASS |
| P3-G4 | Written comparative model selection | SEL-001 selection report and EXP-001_RELEASE_MODEL.yaml; human review pending | PASS |
| P3-1-G1 | Frozen checkpoint/data/config verified | Manifest hashes checked before evaluation; full processed tree unchanged afterward | PASS |
| P3-1-G2 | Fixed test protocol and no test-set tuning | 82 test images; thresholds frozen before prediction | PASS |
| P3-1-G3 | Confusion matrix and error analysis saved | Numeric/PNG matrix; 251 diagnostic events (4 class confusions count as FP and FN) | PASS |
| P3-1-G4 | Metric/reference and replay agreement | Ultralytics matching identical; AP delta <= 2.23e-16; replay exact | PASS |
| P3-1-G5 | Meaningful regression and integrity tests | Tests cover AP, matching, absent classes, duplicates, tampering, overwrite refusal and failures | PASS |
| P3-1-G6 | No Phase 2 protected-state mutation or training | Phase 2 artifacts/weights/config/tags preserved; no new training experiment | PASS |

M-005 technical evidence: COMPLETE / AWAITING HUMAN REVIEW. Phase 3 overall
remains AWAITING HUMAN REVIEW; comparison and selection technical evidence are complete.
Final test counts and integrity evidence are recorded in PHASE_3_EVALUATION_REPORT.md.

## P3-G3 Model Comparison Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P3-G3 | 对照实验条件一致、结论有证据 | P3_MODEL_COMPARISON_REPORT.md; CMP-001 same-run best/last checkpoint scope explicit | PASS |
| P3-CMP-1 | Candidates identified before evaluation | Epoch 75 best and epoch 95 last, distinct SHA256 registered in frozen Phase 2 manifest | PASS |
| P3-CMP-2 | Same test split and evaluation pipeline | Identical 82 image/label hashes, GT, full dataset hashes, protocol, implementation and runtime | PASS |
| P3-CMP-3 | Unified metric coverage | Four metrics, seven-class AP, no_hardhat/no_vest/small-object recall in JSON and report | PASS |
| P3-CMP-4 | Results replay and reference agreement | Both runs replay; official AP difference <= 2.23e-16; best metrics exactly match EVAL-001 | PASS |
| P3-CMP-5 | Regression tests | Full suite 213 passed / 1 skipped; isolated runtime 29 passed; mismatch/tamper rejection tested | PASS |
| P3-CMP-6 | Protected state unchanged | Full task-entry SHA256 verification recorded in comparison report; Phase 2/EVAL-001 preserved | PASS |

P3-G3 technical result: PASS / AWAITING HUMAN REVIEW. Its historical closure preceded
SEL-001; the completed P3-G4 selection is recorded below. No Phase 3 release or Phase 4 entry.
No external-model superiority or statistical significance is claimed from same-run checkpoints.

## P3-G4 Final Comparative Model Selection Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P3-G4 | 选定模型有书面选择和限制说明 | P3_MODEL_SELECTION_REPORT.md selects best.pt, records PPE tradeoffs and limitations | PASS |
| P3-SEL-1 | Candidate and selected identity traceable | EXP-001_RELEASE_MODEL.yaml path/epoch/SHA256 match frozen Phase 2 manifest and local bytes | PASS |
| P3-SEL-2 | Decision grounded in existing evidence | EVAL-001/CMP-001 retained; evidence hashes bound in selection YAML; existing comparison replay PASS | PASS |
| P3-SEL-3 | PPE criteria and alternative advantages disclosed | Both violation recalls, precision, per-class AP and small-object recall reviewed; no invented cost ratio or score | PASS |
| P3-SEL-4 | No new test tuning or protected-state mutation | No new model execution/parameter changes; task-entry integrity audit in selection report | PASS |
| P3-SEL-5 | Verification complete | Full suite 213 passed / 1 skipped; compileall and manifest consistency checks PASS | PASS |

P3-G1 through P3-G4: technical PASS. Human review: PENDING. Phase 3 release:
NOT_RELEASED. The selected artifact is best.pt; this is not a production-safety
acceptance or permission to begin Phase 4. No commit/push performed.

## Phase 3 Final Release Freeze Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P3-FR-1 | P3-G1 through P3-G4 evidence complete | docs/reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md binds EVAL-001, CMP-001 and SEL-001 | PASS |
| P3-FR-2 | Selected release model identity fixed | best.pt epoch 75 matches EXP-001_RELEASE_MODEL.yaml and Phase 2 SHA256 | PASS |
| P3-FR-3 | Artifact inventory and hash references | Final report inventories documents, implementation/config/tests and ignored runtime outputs | PASS |
| P3-FR-4 | Existing results verifiable | EVAL-001 and CMP-001 offline replay; selection evidence hashes verified in freeze task | PASS |
| P3-FR-5 | Verification and immutable boundaries | 213 passed / 1 skipped; compileall, diff and task-entry SHA256 checks in final report | PASS |
| P3-FR-6 | Limitations and Phase 4 conditions explicit | Human review pending; inference config confirmation and explicit start required; no Phase 4 development | PASS |

Freeze: COMPLETED / AWAITING HUMAN REVIEW. P3-G1～G4: technical PASS.
M-005: technical COMPLETE, formal human acceptance PENDING; Charter status retained.
GitHub release: NOT_RELEASED. No training, new model evaluation, dataset/mapping/weight
mutation, commit/tag/push or Phase 4 development in the freeze task.

## Phase 4C-2 Real MP4 Validation Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P4C2-G1 | Frozen checkpoint identity verified | `best.pt` size and SHA256 matched the Phase 4B-0 freeze before model construction | PASS |
| P4C2-G2 | Frozen CPU sequential runtime used | `INF-RUNTIME-001`; CPU-only, no CUDA migration, batch or async processing | PASS |
| P4C2-G3 | External MP4 excluded from Git | `git check-ignore` confirms the MP4 under `artifacts/validation/` is ignored | PASS |
| P4C2-G4 | All source frames processed in order | 47/47 frames, contiguous IDs, monotonic timestamps, no frame skipping | PASS |
| P4C2-G5 | Structured evidence retained | Git-ignored raw JSON, frame summary and schema-backed validation report contain 77 detections across 47 frames | PASS |
| P4C2-G6 | Downstream scope excluded | No RTSP, Camera, tracking, association, compliance, event, alert, Web or LLM execution | PASS |
| P4C2-G7 | Protected assets preserved | Dataset, mapping, training configuration and frozen checkpoint were not modified | PASS |

Phase 4C-2 result: `COMPLETE`. The frozen model loaded successfully and the
external MP4 was processed sequentially through the implemented video path.
Phase 5 remains `WAITING`; no commit, push or tag was performed.

## Phase 4 Scope Adjustment and Offline Release Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P4-OFF-G1 | Scope adjustment recorded | ADR-018 re-scopes Phase 4 to structured local image/MP4 offline inference | PASS |
| P4-OFF-G2 | Image inference evidence complete | Architecture, implementation, frozen runtime/checkpoint, and real image validation are recorded | PASS |
| P4-OFF-G3 | MP4 inference evidence complete | Sequential implementation processed 47/47 external frames and emitted structured evidence | PASS |
| P4-OFF-G4 | Real validation evidence recorded | Image and MP4 validation both PASS against checkpoint SHA256 `1c144eef...871f61` | PASS |
| P4-OFF-G5 | Deferred scope explicit | Camera/RTSP, real-time behavior, M-008 and annotated rendering are deferred MUST work under ADR-019, not release claims | PASS |
| P4-OFF-G6 | Charter status preserved | M-008 remains `待实现`; no locked MUST status was silently changed | PASS |
| P4-OFF-G7 | Release identity accurate | Milestone tag is `phase-4-offline-inference-complete`, not the original broad Phase 4 tag | PASS |
| P4-OFF-G8 | Phase boundary preserved | Phase 5 remains `WAITING`; detector and tracker behavior were not changed by scope adjustment | PASS |

Phase 4 Offline Inference result: `COMPLETE`. This release covers only the
structured local image and sequential MP4 inference paths. Camera/RTSP and the
remaining downstream capabilities remain deferred or unimplemented.

## Phase 5-0 Tracking & Association Interface Freeze Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P5-0-G1 | Phase 4 and Phase 5 entry state reviewed | Phase 4 Offline Inference is COMPLETE; explicit Phase 5 authorization is recorded in Current Status and the P5-0 worklog | PASS |
| P5-0-G2 | Frozen assets verified without mutation | `best.pt` SHA256 `1c144eef...871f61`; canonical config SHA256 `df6c55ae...cacff989`; processed `data.yaml` SHA256 `45cc2717...d2878a`; source `data.yaml` SHA256 `5c393e74...d21b34` | PASS |
| P5-0-G3 | Tracking and association contracts frozen | `TrackResult`, `AssociationResult`, person-only adapter and association adapter protocols exist and are tested without model runtime dependencies | PASS |
| P5-0-G4 | Person-only ByteTrack policy frozen | `configs/tracker.yaml` freezes Ultralytics `8.4.157` BYTETracker parameters and class `0 person` only | PASS |
| P5-0-G5 | Unknown-safe association policy frozen | `configs/association.yaml` freezes confidence `0.25`, containment `0.50`, IoU `0.10`, ambiguity margin `0.10`; nearest-distance assignment is prohibited and uncertainty maps to `unknown` | PASS |
| P5-0-G6 | No runtime implementation or protected mutation | No ByteTrack execution, association execution, model loading, inference, dataset mutation, training or checkpoint change occurred | PASS |

P5-0 result: `COMPLETE FOR HUMAN REVIEW`. Phase 5 remains `实现中`; M-009 and
M-010 remain `待实现`; Phase 5-1 is waiting for review.

## Phase 5-1 ByteTrack Adapter Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P5-1-G1 | Person-only adapter implemented behind the frozen interface | `ByteTrackPersonTrackingAdapter` implements `PersonTrackingAdapter` and returns project-owned `TrackResult` values | PASS |
| P5-1-G2 | Only class `0` / `person` reaches the tracker | Invalid class input is rejected before backend update; low-confidence person detections are filtered at `0.25` | PASS |
| P5-1-G3 | Schema/runtime boundary preserved | `DetectionResult` is unchanged; core schemas have no Ultralytics dependency; tracker rows and Ultralytics objects remain behind the private backend | PASS |
| P5-1-G4 | Required adapter tests pass | Focused tests cover continuous, multiple, enter/leave, missing-frame and invalid-class scenarios; focused suite `36 passed` | PASS |
| P5-1-G5 | Frozen assets remain unchanged | Checkpoint SHA256 `1c144eef...871f61`; training config SHA256 `df6c55ae...cacff989`; processed `data.yaml` SHA256 `45cc2717...d2878a`; source `data.yaml` SHA256 `5c393e74...d21b34` | PASS |
| P5-1-G6 | Prohibited execution and release actions excluded | No model load, inference, real ByteTrack run, association, training, commit, push or tag occurred | PASS |
| P5-1-G7 | Full repository verification | `python -m pytest`: `286 passed, 1 skipped`; `python -m compileall .`: PASS; `git diff --check`: PASS | PASS |

P5-1 result: `COMPLETE FOR HUMAN REVIEW`. The adapter contract is implemented
and tested with an injected backend. Real Ultralytics ByteTrack execution was
not available in the current workspace, so real track-ID continuity remains
unverified. Phase 5-2 is waiting for P5-1 human review.

## Phase 5-2 Person-PPE Association Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P5-2-G1 | Association adapter implemented behind the frozen protocol | `PPEPersonAssociationAdapter` implements `PPEAssociationAdapter` and returns project-owned `AssociationResult` values | PASS |
| P5-2-G2 | Only existing person tracks are assignment targets | Candidates come only from input `TrackResult` values; associated records must reference one of those result tracks | PASS |
| P5-2-G3 | Frozen thresholds are preserved | Confidence `0.25`, containment `0.50`, IoU `0.10`, ambiguity margin `0.10`; containment priority before IoU | PASS |
| P5-2-G4 | Unsafe assignment paths are excluded | Nearest-distance is rejected by configuration; no candidate or an ambiguity gap below `0.10` produces `unknown` | PASS |
| P5-2-G5 | Required association tests pass | Focused tests cover helmet, vest, multiple people, wrong candidate, ambiguity, missing PPE, empty input, IoU-only, confidence, invalid class and context | PASS |
| P5-2-G6 | Frozen assets remain unchanged | Checkpoint SHA256 `1c144eef...871f61`; training config SHA256 `df6c55ae...cacff989`; processed `data.yaml` SHA256 `45cc2717...d2878a`; source `data.yaml` SHA256 `5c393e74...d21b34` | PASS |
| P5-2-G7 | Prohibited execution and release actions excluded | No model load, inference, real ByteTrack run, training, commit, push or tag occurred | PASS |
| P5-2-G8 | Full repository verification | `python -m pytest`: `300 passed, 1 skipped`; `python -m compileall .`: PASS; `git diff --check`: PASS | PASS |

P5-2 result: `COMPLETE FOR HUMAN REVIEW`. Association behavior is verified
with deterministic project schemas and synthetic geometry. Real detector,
tracker and video integration remain unverified until Phase 5-3. M-009 and
M-010 remain `待实现`.

## Phase 5-3 Tracking & Association Validation Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P5-3-G1 | Integrated synthetic pipeline validation exists | `tests/test_phase5_pipeline_validation.py` runs the frozen adapter composition with a deterministic tracking backend and the real association adapter | PASS |
| P5-3-G2 | Required synthetic scenarios pass | Single-person, multi-person, PPE-present, missing-PPE and ambiguous-association cases are covered | PASS |
| P5-3-G3 | Frozen schemas and adapter boundaries remain unchanged | Synthetic outputs are project-owned `TrackResult` and `AssociationResult` values; no runtime object crosses the boundary | PASS |
| P5-3-G4 | Real-runtime validation is prepared | `configs/p5_3_validation.yaml` and `scripts/run_tracking_association_validation.py` freeze checkpoint/video identity, outputs and preflight checks | PASS |
| P5-3-G5 | Real checkpoint/video runtime validation executed | Preflight returns `BLOCKED_RUNTIME_DEPENDENCIES`; `torch`, `torchvision` and `ultralytics` are not installed | BLOCKED / NOT RUN |
| P5-3-G6 | Frozen assets remain unchanged | Checkpoint SHA256 `1c144eef...871f61`; training config SHA256 `df6c55ae...cacff989`; processed `data.yaml` SHA256 `45cc2717...d2878a`; source `data.yaml` SHA256 `5c393e74...d21b34` | PASS |
| P5-3-G7 | Prohibited execution and release actions excluded | No model load, real inference, ByteTrack execution, training, commit, push or tag occurred | PASS |
| P5-3-G8 | Full repository verification | `python -m pytest`: `307 passed, 1 skipped`; `python -m compileall .`: PASS; `git diff --check`: PASS; Charter diff empty | PASS |

P5-3 result: `COMPLETE FOR HUMAN REVIEW`. Synthetic tracking/association
integration passes. Real runtime validation is prepared but not executed
because the current host lacks the frozen Torch/Ultralytics runtime. M-009 and
M-010 remain `待实现`.

## Phase 5 Final Release Preparation Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P5-FR-1 | P5-0 through P5-3 synthetic evidence is complete | Interface freeze, adapter, association and synthetic pipeline reports are present and consistent | PASS |
| P5-FR-2 | Release artifacts are traceable | Frozen schemas, tracker/association configs, validation config/script and reports identify the implemented scope | PASS |
| P5-FR-3 | Final release report records completed scope and limitations | `docs/reports/phase-05/P5_FINAL_RELEASE_REPORT.md` explicitly separates completed work from missing runtime evidence | PASS |
| P5-FR-4 | Real runtime validation is complete | No `best.pt` load, YOLO11 inference or real ByteTrack execution; P5-3 preflight returned `BLOCKED_RUNTIME_DEPENDENCIES` | BLOCKED / NOT RUN |
| P5-FR-5 | Frozen model, dataset and training assets are preserved | Checkpoint SHA256 `1c144eef...871f61`; training config SHA256 `df6c55ae...cacff989`; processed `data.yaml` SHA256 `45cc2717...d2878a`; source `data.yaml` SHA256 `5c393e74...d21b34` | PASS |
| P5-FR-6 | Full repository verification | `python -m pytest`: `307 passed, 1 skipped`; `python -m compileall .`: PASS; `git diff --check`: PASS; Charter diff empty | PASS |
| P5-FR-7 | Phase release gate | Real runtime validation is blocked, so the Phase 5 completion tag is not created | BLOCKED / NOT RELEASED |

Phase 5 final release result: `PREPARED FOR HUMAN REVIEW / NOT RELEASED`.
M-009 and M-010 remain `待实现`. The release package is ready for review, but
full Phase 5 release requires real runtime validation and a later explicit
release authorization.

## Phase 5 Release Final Audit Gates

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| P5-AUDIT-G1 | Git status, diff, staged and untracked files audited | Staged area is empty; all Phase 5 changes remain uncommitted; `git diff --check` passes | PASS |
| P5-AUDIT-G2 | No forbidden release artifacts | No model, dataset, video, database or credential path appears in the release change set | PASS |
| P5-AUDIT-G3 | Implementation status corrected without changing the Charter | M-009 and M-010 are `IMPLEMENTED / Runtime Evidence Pending`; locked Charter statuses remain `待实现` | PASS |
| P5-AUDIT-G4 | Frozen assets remain unchanged | Checkpoint `1c144eef...871f61`; training config `df6c55ae...cacff989`; processed `data.yaml` `45cc2717...d2878a`; source `data.yaml` `5c393e74...d21b34`; video `b630d851...b852` | PASS |
| P5-AUDIT-G5 | Full repository verification | `python -m pytest`: `307 passed, 1 skipped`; `python -m compileall .`: PASS; `git diff --check`: PASS | PASS |
| P5-AUDIT-G6 | Release actions remain unauthorized | No commit, push or Phase 5 completion tag occurred | PASS |

Phase 5 final audit result: `FINAL AUDIT COMPLETE FOR HUMAN REVIEW /
NOT RELEASED`. Real checkpoint, YOLO11 inference and ByteTrack runtime
evidence remains `BLOCKED / NOT RUN`.
