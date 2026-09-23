# Changelog

## 2026-09-23 — Phase 4 Scope Adjustment and Offline Inference Release

- Added ADR-018 to re-scope Phase 4 as `Offline Inference`: structured image
  inference, sequential local MP4 inference, frozen runtime/checkpoint, and
  real validation evidence.
- Deferred Camera, RTSP, real-time/network behavior, M-008 and annotated video
  rendering as Extension work; Charter M-008 remains `待实现`.
- Updated the Phase 4 milestone name to
  `phase-4-offline-inference-complete`; the original
  `phase-4-inference-complete` name is explicitly not used.
- Updated README, Master Plan, current status, Phase 4 document and test-gate
  records to report `Phase 4: Offline Inference COMPLETE`,
  `Camera/RTSP: Deferred Extension`, and `Phase 5: WAITING`.
- No detector or tracker behavior was changed, no model or dataset was
  modified, and Phase 5 was not started.

## 2026-09-23 — Phase 4C-2 Real MP4 Inference Validation

- 新增 `configs/video_validation.yaml` 和
  `scripts/run_video_validation.py`；validation-only 配置显式启用执行，
  frozen `configs/inference.yaml` 保持 `execution_enabled: false`。
- 使用 `INF-RUNTIME-001` 加载 frozen
  `models/checkpoints/EXP-001/best.pt`，checkpoint SHA256 保持
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`。
- 顺序处理 external public-domain MP4 的全部 47/47 帧，未跳帧、未 batch、
  未 async、未迁移 CUDA；检测 77 项（person 76、no_vest 1），端到端耗时
  15.1920268 s，处理速率 3.0937281 FPS。
- 新增 Git-ignored `artifacts/validation/P4C-2/video_validation.json`、
  `frame_summary.json` 和 schema-backed `validation_report.json`。
- 新增 `tests/test_video_validation_config.py`，验证 validation-only 配置、
  frozen inference contract 和 Git-ignore 边界。
- Phase 4C-2 COMPLETE，Phase 5 WAITING。未执行 RTSP、Camera、tracking、
  association、compliance、events、alerts、Web 或 LLM；未修改 dataset、
  mapping、training config 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4C-1 Real Image Inference Validation

- 新增 `configs/validation.yaml` 和 `scripts/run_image_validation.py`；validation
  配置单独启用执行，frozen `configs/inference.yaml` 保持
  `execution_enabled: false`。
- 增加显式 `execution_enabled` 调用级 override，并修正 Torch runtime
  fingerprint 读取为 `torch.__version__`，从而严格匹配冻结的
  `2.5.1+cpu` 而不是 wheel metadata 的 `2.5.1`。
- 在 `INF-RUNTIME-001` 中使用 frozen `models/checkpoints/EXP-001/best.pt`
  完成一次外部 public-domain construction image 的真实推理；checkpoint
  SHA256 保持
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`。
- Hot inference 返回 5 个 `DetectionResult`：person 2、hardhat 1、
  no_hardhat 1、no_vest 1；cold start 为 14.237 s，warm inference 为
  176.386 ms。
- 新增 Git-ignored `artifacts/validation/P4C-1/image_validation.json` 和
  `validation_report.json`，并通过既有 validation schemas 重新构造验证。
- Phase 4C-1 image validation COMPLETE；video、tracking、association、
  compliance、events 和 alerts 未执行。未修改 dataset、mapping、training
  config 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4C-0 Real Inference Validation Design

- 新增 `docs/phases/PHASE_04C_VALIDATION_DESIGN.md`，定义真实 checkpoint +
  external image / short MP4 验证流程、证据字段、Git-ignored `artifacts/`
  输出政策和 fail-closed 错误边界。
- 新增 `core/schemas/validation.py`，定义 model-independent
  `ImageValidationRecord`、`VideoValidationRecord` 和
  `InferenceValidationReport`；记录 detection statistics、confidence、
  latency、processing time 和 processing FPS。
- 新增 `tests/test_validation_schema.py`，只验证 schema creation、计数一致性
  和 JSON serialization，不加载模型或访问真实输入。
- Phase 4C-0 COMPLETE，Phase 4C-1 WAITING。未加载 `best.pt`、未执行真实
  inference，未修改模型、dataset 或 training assets，未 commit/push/tag。

## 2026-09-23 — Phase 4B-2b MP4 Video Inference Implementation

- 新增 `core/video/reader.py`，实现 lazy OpenCV、本地 MP4 顺序读取、
  metadata extraction、timestamp generation 和结构化 reader errors。
- 新增 `services/video_inference_service.py`，串联 `VideoReader`、
  `InferenceService`、`FrameInferenceResult` 和 `VideoInferenceResult`；
  不复制 detector 参数、checkpoint 校验或结果解析逻辑。
- 为 `YOLODetector` 和 `InferenceService` 增加共享 frame-level entry
  point，使图片与视频使用同一冻结 CPU/checkpoint/class-filter 策略。
- 新增 `scripts/run_video_inference.py`，支持
  `python scripts/run_video_inference.py xxx.mp4` 并输出结构化 JSON；
  missing、invalid format、empty、decode 和 disabled execution 都有稳定
  error code。
- 新增 `tests/test_video_inference.py`，默认使用 fake capture 和 fake
  inference service，覆盖顺序、frame count、metadata、serialization、
  disabled execution 和错误处理，不加载 `best.pt`。
- Phase 4B-2b COMPLETE，Phase 4B-3 WAITING。未执行真实大规模视频测试，
  未修改 dataset、mapping、training config 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4B-2a Video Inference Architecture Design

- 新增 `docs/phases/PHASE_04B2_VIDEO_DESIGN.md` 和
  `PHASE_04B2_VIDEO_DESIGN_REPORT.md`，定义本地 MP4 顺序推理、
  `VideoReader -> FrameProcessor -> InferenceService -> Result Writer`
  流水线、runtime policy、错误处理和非目标。
- 新增 `core/schemas/video.py`，只定义 `FrameData`、`VideoMetadata`、
  `FrameInferenceResult` 和 JSON-serializable `VideoInferenceResult`，
  不包含 OpenCV/Torch/Ultralytics 依赖或视频读取实现。
- 新增 `tests/test_video_schema.py`，验证 schema creation、字段完整性和
  serialization。
- Phase 4B-2a COMPLETE，Phase 4B-2b WAITING。未修改 detector/service，
  未加载模型、未执行真实视频推理，未修改 dataset、mapping、training
  assets 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4B-1 Single Image Inference

- 新增 `core/inference/detector.py` 与 `core/inference/__init__.py`，实现
  lazy-loading `YOLODetector`、frozen checkpoint size/SHA256 检查、CPU-only
  device policy、固定 `imgsz/conf/iou/max_det/classes` 和
  `DetectionResult` 转换。
- 实现 `services/inference_service.py` 的单图路径检查、格式验证和 detector
  委托；video 与 Camera/RTSP 仍为明确的 future-phase placeholder。
- 新增 `scripts/run_image_inference.py`，支持
  `python scripts/run_image_inference.py image.jpg` 并输出 JSON；默认
  `execution_enabled: false` 时返回明确的 `execution_disabled`。
- 新增 `tests/test_image_inference.py`，默认使用 fake model/image loader，
  不加载真实 `best.pt`；覆盖 invalid input、disabled execution、lazy load、
  schema output、checkpoint tamper 和 CLI error output。
- Phase 4B-1 COMPLETE，Phase 4B-2 WAITING。未执行真实推理，未修改 dataset、
mapping、training artifact 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4B-0 Inference Runtime Freeze

- 新增 `docs/phases/PHASE_04B_RUNTIME_FREEZE.md`，冻结 release checkpoint
  `models/checkpoints/EXP-001/best.pt` 及 SHA256
  `1c144eef...871f61`。
- 冻结 `INF-RUNTIME-001`：Windows x86_64、Python 3.10.4、PyTorch
  2.5.1+cpu、torchvision 0.20.1、Ultralytics 8.4.157、NumPy 2.2.6、
  OpenCV 5.0.0.93；依赖来源固定为 `locks/EVAL-001/requirements.txt`。
- 冻结 CPU-only device policy、`imgsz: 640`、confidence `0.25`、
  NMS IoU `0.45`、五类 output filter、input formats、`DetectionResult`
  output reference 和 fail-closed error handling policy。
- 将 `configs/inference.yaml` 从 planned defaults 更新为只读配置契约；
  `execution_enabled: false`，不包含推理逻辑，不加载模型。
- Phase 4A COMPLETE，Phase 4B-0 COMPLETE，Phase 4B-1 WAITING。
- 未执行模型加载或推理，未修改 dataset 或训练产物，未 commit/push/tag。

## 2026-09-23 — Phase 4A Inference Architecture Design

- 完成 Phase 3 人工审核 PASS 后的状态同步：Phase 3 COMPLETE，M-005
  `已经实现`，Phase 4A 进入 design-only 工作。
- 新增 `PHASE_4A_PRECHECK_REPORT.md`，审计现有 inference 占位接口、
  `configs/inference.yaml`、detection schemas、缺失模块和风险。
- 新增 `docs/phases/PHASE_04_INFERENCE_DESIGN.md`，定义 Input Adapter、
  YOLO11 detector wrapper、统一 `DetectionResult`、未来 P5-P7 集成边界和
  Phase 4A non-goals。
- 新增 `core/schemas/detection.py`，只定义无模型依赖的结果数据结构及
  JSON-serializable `to_dict()`；现有 Detector、Pipeline、Service 和 CLI
  占位实现保持不变。
- 新增 `tests/test_detection_schema.py` 验证结果创建、字段完整性和序列化。
- 未加载 `best.pt`、未启动推理、未实现 ByteTrack/PPE 关联/规则/事件/告警/
  Web/LLM/Agent，未修改 dataset、mapping、weights 或 EXP-001 配置，未 commit
  或 push。

## 2026-09-22 — Phase 3 Final Release Freeze

- 创建 `PHASE_3_FINAL_RELEASE_REPORT.md`，汇总 P3-G1～G4 技术 PASS、M-005
  技术完成/人工验收待定、最终 best.pt 模型、artifact 清单、SHA256 和限制。
- 冻结现有 EVAL-001、CMP-001、SEL-001 证据及实现/配置/测试哈希；不改写既有
  报告或 EXP-001_RELEASE_MODEL.yaml，不新增模型实测或调优。
- 本轮全量测试 213 passed / 1 skipped；离线复算与证据身份核验通过。
- Freeze COMPLETED / AWAITING HUMAN REVIEW；GitHub NOT_RELEASED。
  明确 Phase 4 需人工审核、模型/推理配置确认和开始指令，未进入开发。
- 未训练、未修改 dataset/mapping/weights 或 Phase 2 artifacts；未 commit/push。

## 2026-09-22 — P3-G4 Final Comparative Model Selection

- SEL-001 正式记录选择 EXP-001 best.pt（epoch 75），保留原验证集选择；last.pt
  保留为参考。没有新增模型实测、重新训练、调阈值或修改权重。
- 新增 `P3_MODEL_SELECTION_REPORT.md` 与 `EXP-001_RELEASE_MODEL.yaml`，记录
  候选、既有评估证据、PPE 合规关注点、取舍、SHA256 与限制；人工审核 PENDING。
- 全量测试 213 passed / 1 skipped；compileall、离线复算、清单身份与证据哈希
  校验通过。P3-G4 技术门禁 PASS；Phase 3 尚未发布，未进入 Phase 4。
- 未修改 dataset、mapping、EXP-001 weights、既有评估/比较结果或 Phase 2
  artifacts；未 commit/push。

## 2026-09-22 — P3-G3 Model Comparison

- 完成 CMP-001：EXP-001 best.pt（epoch 75）与 last.pt（epoch 95）的同条件
  checkpoint 对照；两者调用相同 ValService，使用相同 test split、参数、代码与 runtime。
- 新增配置、比较入口、条件一致性验证与离线复算；checkpoint 仅能从 Phase 2
  冻结清单选择。保留 EVAL-001，并精确复现其 best 指标。
- 输出 `P3_MODEL_COMPARISON_REPORT.md` 和机器可读 summary，包含四项总体指标、
  七类 AP、no_hardhat / no_vest / small-object recall 与取舍分析。
- 全量测试 213 passed / 1 skipped；专用环境相关测试 29 passed。P3-G3 PASS，
  等待人工审核；P3-G4 仍未完成，不改变原 best 选择。
- 未训练、未下载模型、未修改 EXP-001 配置/权重、dataset/mapping 或 Phase 2
  artifacts；未 commit/push，未进入 Phase 4。

All notable project changes are recorded here. This project follows a
phase-based log rather than claiming semantic-release completeness.

## 2026-09-22

### GitHub Phase Milestone Release Governance

- Added ADR-017 GitHub Phase Milestone Release Strategy.

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

### P2-4-G3 AutoDL Dependencies Provisioning

- Connected to the user-provided AutoDL instance `bcb849a74f-38320766`
  (RTX 4090 24GB, Ubuntu 20.04.5 LTS) using key authentication.
- Created the isolated conda environment `ppe-exp001` with Python `3.10.21`
  without changing the base environment.
- Installed `torch 2.5.1+cu124`, `torchvision 0.20.1+cu124`,
  `torchaudio 2.5.1+cu124`, `ultralytics 8.4.157`,
  `opencv-python 5.0.0.93`, NumPy `2.2.6`, PyYAML `6.0.3`, tqdm `4.70.1`,
  matplotlib `3.10.9`, and psutil `7.2.2`.
- Verified `torch.cuda.is_available() == True`, RTX 4090 visibility, and
  successful PyTorch, Ultralytics, OpenCV, and NumPy imports.
- Recorded that planned Ultralytics `8.4.158` was not published by the
  configured index and pinned the resolved `8.4.157` instead.
- Added `docs/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md`.
- No dataset transfer, model weight download, training execution, dataset
  mutation, mapping change, experiment change, or source-code change occurred.

### P2-4-G4 Dataset Transfer & Integrity Verification

- Transferred `data/processed/css-ppe-10-v1/` unchanged to
  `/root/autodl-tmp/datasets/css-ppe-10-v1/` using recursive SCP without
  compression or restructuring.
- Verified 5,604 total files, 2,799 images, 2,799 labels, and the frozen split
  counts: train 2,603, valid 114, test 82.
- Verified the processed seven-class order:
  `person, hardhat, no_hardhat, vest, no_vest, machinery, vehicle`.
- Verified the processed `data.yaml` SHA256 as `45cc2717...d2878a`, the
  upstream source `data.yaml` as `5c393e7...d21b34`, the source manifest as
  `ea0de4b0...f98d795`, and the processed manifest file as
  `dbfe43c4...831c2c`.
- Verified all 5,602 entries in `metadata/checksums.sha256` and all 5,604
  entries in the external full dataset manifest.
- Added `docs/P2-4-G4_DATASET_VERIFICATION_REPORT.md`.
- No training, `yolo train`, model weight download, label modification,
  annotation regeneration, class mapping change, or EXP-001 configuration
  change occurred.
- Validation: pytest `174 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-4 Final AutoDL Provisioning Gate

- Added `docs/P2-4_FINAL_PROVISIONING_REPORT.md` consolidating instance,
  runtime, dependency, dataset, safety, and final-gate evidence.
- Marked P2-4-G1 through P2-4-G6 PASS.
- Recorded Environment `READY`, Dataset `READY`, and Training
  `PENDING AUTHORIZATION`.
- Confirmed no training, `yolo train`, `python train.py`, model download,
  benchmark, or evaluation was executed.
- Updated project status and Phase 2 records to mark P2-4 complete without
  marking training, model, or experiment work complete.
- Validation: pytest `174 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5 EXP-001 Training Execution Authorization Review

- Added `P2-5_TRAINING_AUTHORIZATION_REPORT.md` with a `BLOCKED` result.
- Recorded that the dataset, mapping, fingerprints, output paths, and runtime
  fingerprint were present, while unresolved training parameters, weight
  binary provenance, complete environment freeze, and explicit human
  authorization still prevented execution.
- No training, weight download, dataset modification, mapping modification, or
  configuration modification was performed.

### P2-5.1 EXP-001 Configuration Freeze Review

- Added `docs/reports/P2-5.1_CONFIGURATION_FREEZE.md` and
  `P2-5.1_CONFIGURATION_FREEZE_REPORT.md`.
- Froze model `YOLO11n`, Ultralytics `8.4.157`, starting weight reference
  `yolo11n.pt`, dataset `CSS-PPE-10-V1`, seven classes, `imgsz: 640`,
  `epochs: 100`, `batch: 16`, `optimizer: AdamW`, learning rate `0.001` with
  cosine schedule, `seed: 42`, single-GPU `cuda:0`, `workers: 8`, and the
  canonical output/log/report/checkpoint paths.
- Froze the EXP-001 augmentation configuration and recorded SHA256 hashes for
  the canonical configuration, schema, augmentation file, and alias template.
- Kept `execution_enabled: false` and training authorization `NOT GRANTED`.
- No model weight was downloaded, no training was executed, and no dataset or
  mapping was modified.
- Validation: pytest `175 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5.2 EXP-001 Weight Registration

- Registered the official Ultralytics `yolo11n.pt` initialization checkpoint
  from the `ultralytics/assets` `v8.3.0` release at
  `models/pretrained/yolo11n.pt`.
- Verified the `5,613,764` byte content length, MD5
  `261474e91b15f5ef14a63c21ce6c0cbb`, PyTorch checkpoint ZIP structure, and
  SHA256 `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Added `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` and
  `P2-5.2_WEIGHT_REGISTRATION_REPORT.md`.
- Updated the P2-2 authorization checklist, configuration-freeze record,
  training strategy, README, current-status record, and focused tests to
  distinguish the registered initialization weight from a training result.
- The weight remains Git-ignored and has not been transferred to the remote
  training environment. No training was executed, and no dataset, mapping, or
  EXP-001 configuration was modified.
- Validation: pytest `177 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5.3 EXP-001 Dependency Freeze

- Exported `ppe-exp001` to `locks/EXP-001/conda-environment.yml` with exact
  conda build strings and to `locks/EXP-001/pip-freeze-all.txt` with the
  complete resolved pip package set.
- Added `locks/EXP-001/conda-explicit.lock` and
  `locks/EXP-001/runtime-fingerprint.yaml`.
- Recorded AutoDL instance `bcb849a74f-38320766`, RTX 4090 UUID, `24,564 MiB`
  VRAM, compute capability `8.9`, NVIDIA driver `560.35.03`, CUDA driver API
  `12.6`, PyTorch CUDA runtime `12.4`, cuDNN `90100`, Python `3.10.21`,
  PyTorch `2.5.1+cu124`, and Ultralytics `8.4.157`.
- Verified all exported locks against the current remote output and confirmed
  `python -m pip check` reports no broken requirements.
- Added `docs/reports/P2-5.3_DEPENDENCY_FREEZE.md` and
  `P2-5.3_DEPENDENCY_FREEZE_REPORT.md`; updated the training authorization
  checklist to mark dependencies `FROZEN / VERIFIED`.
- No training was executed; no dependency was installed; no dataset, mapping,
  weight, or EXP-001 canonical configuration was modified.
- Validation: pytest `178 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5.4 EXP-001 Remote Weight Transfer Verification

- Transferred the registered `yolo11n.pt` initialization checkpoint to
  `/root/autodl-tmp/models/pretrained/yolo11n.pt` after confirming that the
  remote destination did not already exist.
- Verified the remote file exists and matches the local artifact at
  `5,613,764` bytes and SHA256
  `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Added `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md` with local path, remote
  path, size, SHA256 evidence, match result, and the `READY` decision.
- Updated `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` and the P2-2
  authorization checklist to record the remote copy as `VERIFIED`.
- No training or model execution occurred; no dataset, mapping, fingerprint,
  or EXP-001 canonical configuration was modified; no commit or push was
  performed.
- Validation: pytest `179 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5.5 EXP-001 Baseline Training Execution

- Executed the explicitly authorized YOLO11n baseline on AutoDL instance
  `bcb849a74f-38320766` using the frozen `CSS-PPE-10-V1` dataset, canonical
  EXP-001 configuration, and registered `yolo11n.pt` initialization weight.
- Training ran from `2026-09-22T08:00:02Z` to `2026-09-22T08:19:29Z`,
  completed 95 of 100 epochs, achieved the best validation result at epoch
  75, and stopped early after 20 epochs without improvement.
- Overall validation result: precision `0.899`, recall `0.649`, mAP50
  `0.767`, and mAP50-95 `0.480`; per-class metrics were also produced.
- Produced Git-ignored best and last checkpoints, training log, resolved
  arguments, epoch metrics, confusion matrices, PR/F1 curves, validation
  plots, run record, and frozen configuration snapshot.
- Best checkpoint: `5,479,891` bytes; SHA256
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
- Added `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md` and marked M-004
  `已经实现`. M-005 remains `待实现`; Phase 3 has not started.
- Recorded that Ultralytics downloaded `yolo26n.pt` only for its one-time AMP
  compatibility check. The log states that it was not used for training and
  it did not replace the frozen YOLO11n initialization weight.
- The one-run authorization record is now `CONSUMED`; no dataset, mapping,
  fingerprint, or canonical configuration was modified, and no second run is
  authorized.
- Verified the host was idle and issued an AutoDL shutdown after archiving the
  evidence; no remote dataset, weight, or run artifact was deleted.

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

### P2-7 EXP-001 Training Result Freeze

- Added the result freeze report and machine-readable best-model manifest with
  dataset/config/weight identity, best epoch, final training-validation metrics,
  runtime fingerprint, command/epoch-loop durations and 29 hashed artifacts.
- Verified both dataset manifests and preserved dataset, mapping, frozen config,
  checkpoints, dependency locks and the existing Charter status change.
- Current Phase is `P2-7 Training Result Freeze`; EXP-001 Training is `COMPLETED`.
- No training, evaluation, Phase 3 work, commit or push was performed.

### P3-1 EXP-001 Test Evaluation (Awaiting Human Review)

- Implemented ValService, the evaluation CLI and deterministic replayable metrics;
  added a fixed test protocol and evaluation-only dependency pins under EVAL-001.
- Evaluated the unchanged EXP-001 best.pt on 82 test images / 561 boxes. Seven-class
  P/R/mAP50/mAP50-95: 0.798669 / 0.712315 / 0.733203 / 0.465122.
- Retained all seven per-class AP entries, the five PPE aggregate, confusion matrix,
  per-image predictions/ground truth/errors and small-object recall diagnostics.
- Cross-checked matching/AP against Ultralytics 8.4.157 and replayed retained results.
- Added PHASE_3_EVALUATION_REPORT.md and EXP-001_EVALUATION_SUMMARY.json. M-005
  technical evidence is complete, awaiting human review; comparison/model-selection
  gates remain pending. No Phase 4 entry, training, commit or push.
- Dataset, mapping, weights, training configuration and Phase 2 release artifacts
  were preserved. The CPU evaluation environment is separate from the training lock.
