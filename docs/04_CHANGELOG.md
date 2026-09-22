# Changelog

All notable project changes are recorded here. This project follows a
phase-based log rather than claiming semantic-release completeness.

## 2026-09-22

### P2-0 Training Environment Preparation & Dependency Boundary Review

- Added `docs/reports/P2-0_DEPENDENCY_STRATEGY.md` comparing a Windows NVIDIA
  GPU environment, WSL2 with CUDA, a controlled cloud GPU, and CPU fallback.
- Added `docs/reports/P2-0_VERSION_MATRIX.md` for Python, PyTorch, CUDA,
  Ultralytics, and YOLO11 version decisions. Exact versions and the model
  weight source remain pending and no installation was performed.
- Added `docs/reports/P2-0_TRAINING_READINESS.md` with Dataset `PASS`,
  Experiment `PASS`, Environment `NOT READY`, GPU `PENDING`, Dependencies
  `PENDING`, and recorded P2-0-G1 through P2-0-G6 as PASS.
- Re-audited the live environment: Windows 11 `10.0.22631`, Python `3.13.6`,
  pip `25.3`, PyTorch not installed, Ultralytics not installed, CUDA
  unavailable, no NVIDIA GPU detected, Intel Iris Xe only, approximately
  `31.65 GiB` visible RAM, and Intel Core i5-1340P with 16 logical processors.
- Re-verified all three frozen dataset fingerprints against the training
  contract and confirmed the processed seven-class order without modifying
  the dataset.
- Updated the Phase 2 status record to mark P2-0 complete for review and P2-1
  environment setup as the next allowed step.
- No dependency, driver, dataset, or model weight was downloaded or installed;
  no training or evaluation was executed; no frozen EXP-001 field was changed.
- Validation: pytest `173 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-1 Training Environment Setup

- Selected `D. Controlled Cloud GPU` as the EXP-001 environment architecture
  because the current host has no NVIDIA GPU or CUDA support.
- Added `docs/reports/P2-1_ENVIRONMENT_DECISION.md` with the selected option,
  rejected alternatives, cost/risk controls, and the impact on EXP-001.
- Added `docs/reports/P2-1_DEPENDENCY_SPECIFICATION.md` with planned versions
  for Python `3.11.16`, PyTorch `2.11.0+cu128`, CUDA `12.8`, torchvision
  `0.26.0+cu128`, Ultralytics `8.4.158`, NumPy `2.2.6`, and key supporting
  packages.
- Added `docs/reports/P2-1_SETUP_PLAN.md` with provisioning, installation,
  non-training verification, rollback, and runtime-freeze procedures.
- Updated the P2-0 readiness record with `Environment Decision: SELECTED`,
  `Provisioning: NOT STARTED`, and `Dependency Freeze: PENDING`.
- No cloud instance was provisioned; no dependency or model weight was
  downloaded; no training, evaluation, dataset mutation, or class mapping
  change was performed.
- Validation: pytest `173 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-2 Training Execution Authorization Review

- Added `docs/reports/P2-2_CLOUD_ENVIRONMENT_REVIEW.md`. Provider, region,
  GPU, VRAM, CUDA capability, OS image, storage, cost estimate, and retention
  policy are explicitly `PENDING_SELECTION`.
- Added `docs/reports/P2-2_DEPENDENCY_FREEZE.md`. Python, PyTorch, CUDA,
  torchvision, Ultralytics, and NumPy remain planned and uninstalled, so the
  dependency freeze remains `PENDING`.
- Added `docs/reports/P2-2_EXP001_EXECUTION_REVIEW.md`. Verified the canonical
  EXP-001 dataset, model, seven-class output, paths, logging settings, and
  eight required metrics without modifying the configuration.
- Added `docs/reports/P2-2_TRAINING_AUTHORIZATION.md`. Dataset, mapping, and
  experiment review pass; environment, dependencies, and GPU remain pending;
  authorization is `NOT GRANTED`.
- No cloud instance was provisioned; no dependency, wheel, or model weight was
  downloaded; no training or dataset mutation occurred.
- Validation: pytest `173 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-3 Cloud Provider Selection & Cost Review

- Added `docs/reports/P2-3_CLOUD_PROVIDER_SELECTION.md` comparing AutoDL,
  Alibaba Cloud GPU ECS, Tencent Cloud GPU, and RunPod/Vast.ai-style
  alternatives.
- Selected AutoDL with an RTX 4090 24GB design target; RTX 3090 24GB is
  recorded only as a contingency and is not treated as the same runtime.
- Recorded a 40 GPU-hour planning limit and CNY 150 compute/storage ceiling
  for the AutoDL path. The estimates are not provider quotations.
- Recorded data-upload, credential, retention, image-identity, and cleanup
  requirements for the future isolated environment.
- Updated the P2-2 authorization checklist so Environment and GPU read
  `DESIGN SELECTED / NOT PROVISIONED`; Authorization remains `NOT GRANTED`.
- No cloud instance was provisioned; no dependency, dataset, or model weight
  was uploaded or downloaded; no training was executed.
- Validation: pytest `174 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

## 2026-09-21

### Phase 0 Foundation initialized

- Created the complete engineering directory and Python package skeleton.
- Added six YAML configuration files with future-phase status markers.
- Added path, YAML loading, logging, timing, system information, and detection
  schema foundations.
- Added explicit `NotImplementedError` boundaries for Phase 1 through Phase 9
  business modules.
- Added the locked project charter, master plan, ten phase documents, ADR log,
  dataset card, open-source usage record, risk register, and test gate system.
- Added Phase 0 unit tests and repository retention files.
- Initialized the Git repository without committing or pushing.

### Phase 0 Gate verified

- `python -m pytest`: 92 passed.
- `python -m compileall .`: passed.
- `git diff --check`: passed with all project files in intent-to-add state,
  then the intent-to-add index state was removed.
- G0-1 through G0-13: PASS.
- Phase status updated to `已经实现`; all MUST and Extension business statuses
  remain `待实现`.

### Pre-Phase 1 Reference Intake

- Added `docs/09_REFERENCE_ASSETS.md`.
- Added ADR-007 and ADR-008.
- Added RISK-011 and RISK-012.
- Updated AGENTS mandatory reading order.
- No business implementation.
- No teacher asset copied.
- Validation: pytest 99 passed; compileall passed.

### Phase 1A Dataset Source & License Gate

- Added `docs/10_DATA_SOURCE_EVIDENCE.md`.
- Verified the original Roboflow Universe Construction Site Safety project,
  CC BY 4.0 license, source class names, version 27 counts, split, and download
  mechanism.
- Added ADR-009 to freeze Roboflow CSS version 27 with the `yolov8` export.
- Updated the dataset card to `SOURCE VERIFIED / NOT DOWNLOADED`.
- Marked P1A `已经实现`; P1B through P1E remain `待实现`.
- M-001 remains `待实现`.
- No dataset, model weight, conversion, commit, or push.
- Validation: pytest 110 passed; compileall passed; `git diff --check` passed;
  charter diff empty.

### Phase 1B Download & Raw Snapshot Tooling

- Replaced the dataset placeholder with P1B-only snapshot, inspection, file
  counting, deterministic manifest, archive verification, and image-label pair
  validation capabilities.
- Added `inspect`, `snapshot`, and `verify` commands to
  `scripts/prepare_dataset.py`; conversion, remapping, cleaning, and
  deduplication remain intentionally unimplemented.
- Added a synthetic fixture and offline tests so default pytest never requires
  the real CSS download.
- User downloaded workspace `roboflow-universe-projects`, project
  `construction-site-safety`, version `27`, format `yolov8` through the
  Roboflow API with their own account.
- Copied the extracted directory without modification to the Git-ignored
  external snapshot and generated `source.json`, `counts.json`,
  `checksums.sha256`, and a concise Markdown snapshot summary.
- Actual snapshot: 2,799 images and labels, 5,601 manifest files, zero missing
  labels, zero orphan labels, 23 empty label files, zero zero-byte images, and
  22 exact SHA-256 duplicate files retained without deletion.
- Actual `data.yaml`: 10 classes; all five target semantics are present, but the
  count and class metadata conflict with the P1A-frozen 2,801-image, 25-class
  source record.
- P1B remains `实现中 / VALIDATION FAILED`; P1C has not started; M-001 remains
  `待实现`. No source data was edited to resolve the mismatch.
- Validation: pytest 125 passed; compileall, `git diff --check`, and Charter
  diff are recorded in the final Phase 1B validation report for this working
  tree.

### P1B.1 Dataset Freeze Correction

- Added ADR-010: dataset freeze requires a complete export artifact
  fingerprint because a Roboflow version number alone is not a training
  artifact identity.
- Recorded `RISK-015`: version metadata differs from the materialized export
  artifact.
- Preserved the historical CSS-V1 record and marked it
  `BLOCKED / NEEDS FREEZE CORRECTION`.
- Added `CSS-V1.1 Candidate` with the observed YOLOv8 artifact fingerprint:
  10 classes, 2,799 images, train/valid/test 2,603/114/82, `data.yaml`
  SHA256 `5c393e74...d21b34`, and manifest SHA256 `ea0de4b0...f98d795`.
- The candidate remains explicitly `Candidate, not frozen`.
- No dataset file was modified, downloaded, remapped, or deleted.
- P1C remains not started and M-001 remains `待实现`.

### P1B.2 Dataset Candidate Decision Gate

- Added `docs/11_DATASET_CANDIDATE_EVALUATION.md` comparing CSS-V1 and
  CSS-V1.1 by source identity, artifact fingerprint, counts, classes, PPE
  relevance, advantages, risks, and V1 suitability.
- Added ADR-011: V1 dataset selection prioritizes reproducibility, verified
  artifact identity, PPE task relevance, license clarity, and training
  feasibility rather than maximum class count.
- CSS-V1 remains `BLOCKED / NEEDS FREEZE CORRECTION`; CSS-V1.1 remains
  `Candidate, not frozen`.
- No dataset was downloaded or modified, no class conversion was performed,
  and no model was trained.
- P1C remains not started and M-001 remains `待实现`.

### P1B.3 Final Dataset Freeze Decision

- Added `docs/12_DATASET_FREEZE_DECISION.md`.
- Rejected CSS-V1 because its metadata identity cannot be bound to a
  materialized artifact.
- Promoted `CSS-V1.1 Candidate` to the frozen dataset ID `CSS-PPE-10-V1`.
- Froze the 10-class list, `data.yaml` SHA256, manifest SHA256, 2,799 images,
  and train/valid/test `2,603/114/82`.
- Added ADR-012: V1 dataset identity is defined by artifact fingerprint, not
  only by a Roboflow version number.
- Added P1B-F1 through P1B-F5 freeze gates.
- No dataset was downloaded or modified, no class conversion was performed,
  and no model was trained.
- P1C remains not started and M-001 remains `待实现`.

### P1C-0 Class Mapping Design Gate

- Added `docs/13_CLASS_MAPPING_DESIGN.md` with the frozen dataset identity,
  ten-class source distribution, and candidate mappings A, B, and C.
- Documented training, inference, rule-engine, tracker, association, event, and
  LLM-report implications without making a final mapping selection.
- Added ADR-013: class mapping must be frozen before label conversion,
  processed dataset generation, or training.
- Added RISK-016 for incorrect class mapping reducing compliance detection
  quality.
- Added P1C-0 design gates and offline tests.
- No source data, labels, `data.yaml`, or frozen fingerprint was modified.
- P1C conversion remains not started and M-001 remains `待实现`.

### P1C-1 Class Mapping Decision Gate

- Added `docs/14_CLASS_MAPPING_DECISION.md`.
- Selected Strategy C and froze the seven-class training mapping while
  preserving the five ADR-003 compliance classes at IDs 0 through 4.
- Added `machinery` and `vehicle` as scene-context classes.
- Explicitly discarded `Mask`, `NO-Mask`, and `Safety Cone` with reasons and
  future-extension rules.
- Added ADR-014 and strengthened RISK-016 with the pre-conversion mapping
  freeze requirement.
- Added P1C-1 gates and offline mapping-identity tests.
- No source data, labels, `data.yaml`, or frozen fingerprint was modified.
- P1C conversion remains not started and M-001 remains `待实现`.

### P1C-2 Dataset Conversion Implementation

- Added `docs/dataset_contracts/CSS-PPE-10-V1-MAPPING.yaml` as the frozen
  `PPE-MAPPING-V1` source-to-training contract.
- Added `services/dataset_conversion_service.py` with deterministic
  image/label conversion, source fingerprint verification, per-image SHA-256
  checks, class mapping, discard accounting, metadata generation, and safe
  output replacement.
- Added `convert` to `scripts/prepare_dataset.py`; the default source is
  `CSS-PPE-10-V1` and the default mapping is `PPE-MAPPING-V1`.
- Generated the Git-ignored `data/processed/css-ppe-10-v1/` artifact:
  train/valid/test `2,603/114/82`, total `2,799` images and labels, seven
  target classes, `30,375` retained boxes, and `8,460` discarded boxes.
- Discarded boxes: `Mask` `1,792`, `NO-Mask` `3,362`, and `Safety Cone`
  `3,306`; unknown source class IDs: `[]`.
- Added fake-free offline tests for deterministic mapping, unknown IDs,
  discard statistics, coordinate preservation, image hash preservation,
  output YAML, source immutability, and repeatability.
- Added `docs/15_DATASET_CONVERSION_REPORT.md` and P1C-2 gates.
- M-001 remains `待实现`; P1D, training, commit, and push were not started.

### P1D-0 Dataset Quality Validation Design Gate

- Added `docs/16_DATASET_QUALITY_PLAN.md` with frozen observation-only
  principles and explicit Q1 through Q9 quality dimensions.
- Froze normalized bbox thresholds: small `< 0.01`, medium `< 0.09`, and
  large `>= 0.09`; small-object risk is `LOW < 20%`,
  `MEDIUM 20% to < 40%`, and `HIGH >= 40%`.
- Froze the planned perceptual duplicate algorithm and threshold as 64-bit
  dHash with Hamming distance `<= 5`, while leaving real-data execution to
  P1D-1.
- Added `utils/quality_metrics.py` for deterministic bbox validation, size
  buckets, class distribution, exact duplicate grouping, and cross-split
  leakage grouping.
- Added `services/dataset_quality_service.py` as a read-only validator
  architecture. It records dataset manifest hashes before and after analysis
  and exposes no repair or write operation.
- Added offline tests for plan structure, immutability, invalid bbox
  detection, deterministic class distribution, deterministic duplicate
  detection, leakage observation, and unchanged dataset hashes.
- Added ADR-015 and RISK-017. No real dataset quality report was generated,
  no dataset was modified, and no model was trained.
- P1C-2 conversion implementation is recorded as manually reviewed PASS;
  P1D-0 is completed for review; P1D real execution is not started; M-001
  remains `待实现`; no commit or push was performed.

### P1D-1 Real Dataset Quality Validation

- Executed the observation-only validator against the real
  `data/processed/css-ppe-10-v1/` payload.
- Fixed the hash scope to `data.yaml`, train/valid/test images, and labels;
  metadata and report files are excluded from the payload fingerprint.
- Verified payload hash
  `bc762204e2305164cfdbc492d15269b84c4ce4ff3cfdcdc805baf84c5616237b`
  before and after validation, covering 5,599 payload files.
- Structure result: PASS for 2,799 images, 2,799 labels, and seven classes
  across train `2603` / valid `114` / test `82`.
- Class distribution: 30,375 valid boxes, 23,421 PPE five-class boxes, and a
  maximum-to-minimum class ratio of approximately `6.20`.
- Empty labels: 32 (`1.14%`), classified as image-without-object and retained.
- Bounding boxes: 30,375 valid lines, zero invalid bbox, invalid class,
  invalid coordinate, or malformed line.
- Duplicate analysis: zero exact image duplicate groups and five dHash
  candidate pairs at Hamming distance `<= 5`.
- Leakage analysis: zero exact cross-split groups; two perceptual cross-split
  candidate groups across `valid` and `test`, retained as risk evidence only.
- Recorded HIGH small-object risk for `hardhat`, `no_hardhat`, `vest`, and
  `vehicle`, plus MEDIUM risk for `person` and `no_vest`.
- Generated `docs/17_DATASET_QUALITY_REPORT.md` and Git-ignored
  `data/processed/css-ppe-10-v1/metadata/quality_report.json`.
- Added G1D1-1 through G1D1-10, all PASS. No data was modified, no model
  was trained, and no commit or push was performed.
- P1D-1 is completed/PASS; P1E is not started; M-001 remains `待实现`.

### P1E-0 Dataset Release & Training Preparation Design Gate

- Added `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml`, binding the
  processed dataset, `PPE-MAPPING-V1` class order, source/processed
  fingerprints, quality report, and immutable training-release boundary.
- Added the `experiments/` structure with README, baseline and augmentation
  design templates, and dedicated `runs/` and `reports/` retention
  directories.
- Added `configs/training/schema.yaml` and
  `configs/training/exp001_baseline.yaml` as non-executable configuration
  contracts. Unresolved values remain explicit `PENDING_DESIGN_REVIEW`
  placeholders.
- Added `docs/18_TRAINING_STRATEGY.md` comparing YOLO11n and YOLO11s,
  defining the EXP-001 baseline, recording the required experiment fields, and
  freezing the required metric list.
- Added ADR-016: all experiments must be configuration-driven and manual
  command-line-only experiments are not accepted as reproducible records.
- Added RISK-018 for experiment reproducibility risk.
- Added G1E0-1 through G1E0-7 and focused tests for the contract, schema,
  experiment ID format, no training execution, dataset fingerprints, and
  Charter integrity.
- No model weight was downloaded, no training was executed, no dataset or
  label was modified, and no commit or push was performed.
- P1E-0 is completed for review; P1E itself remains not started; M-001 remains
  `待实现`.

### P1E-1 Baseline Training Preparation Review

- Added the P1E-1 training contract audit, experiment configuration audit,
  training environment audit, reproducibility checklist, and EXP-001
  training runbook under `docs/reports/`.
- Verified the frozen training contract against all three materialized SHA-256
  fingerprints and confirmed the seven-class `PPE-MAPPING-V1` order.
- Made the canonical EXP-001 configuration authoritative and converted
  `experiments/configs/baseline.yaml` into an explicit template alias. The
  canonical experiment ID is unique and matches `EXP-\d{3}`.
- Added explicit dataset-contract, processed-dataset, model, output, log,
  report, checkpoint, device, and hyperparameter-status fields to the
  training schema and EXP-001 template.
- Environment audit: Python `3.13.6`; PyTorch `NOT INSTALLED`;
  Ultralytics `NOT INSTALLED`; CUDA unavailable; no NVIDIA GPU detected.
  Result: `NOT READY FOR TRAINING`.
- No dependency was installed, no model weight was downloaded, no training was
  executed, and no dataset was modified.
- P1E-1 is completed with `P1E1-G1` through `P1E1-G7` PASS. The next allowed
  step is P2 Training Execution Preparation; training remains prohibited
  pending a new instruction.
- M-001 remains `待实现`.
