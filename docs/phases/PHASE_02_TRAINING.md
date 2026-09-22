# Phase 02 — Training

## 1. 阶段目标

【LOCKED】YOLO11 baseline 训练与实验归档。

## 2. 进入条件

- Phase 1 Gate 全部 PASS。
- 训练数据、环境、显存策略和许可边界已确认。

## 3. 当前子任务

| Subphase | Scope | Status | Evidence |
| --- | --- | --- | --- |
| P2-0 | Training Environment Preparation & Dependency Boundary Review | 已经实现 / REVIEW PASS | environment baseline、dependency strategy、version matrix 和 readiness checklist 已生成；六个 P2-0 gates PASS；未安装依赖、未训练 |
| P2-1 | Training Environment Setup | 已经实现 / DESIGN COMPLETE | 选择 controlled cloud GPU；dependency specification、setup plan、rollback 和 freeze requirements 已记录；未 provision、未安装、未训练 |
| P2-2 | Training Execution Authorization Review | 已经实现 / REVIEW COMPLETE | cloud provider/GPU/image、dependency freeze、EXP-001 和 authorization checklist 已复核；environment/dependencies/GPU 为 PENDING，authorization `NOT GRANTED` |
| P2-3 | Cloud Provider Selection & Cost Review | 已经实现 / DESIGN SELECTION COMPLETE | 选择 AutoDL + RTX 4090 24GB，比较阿里云、腾讯云和其他方案，记录成本、上传和 retention 边界；未 provision、未安装、未训练 |
| P2-4 | AutoDL Training Environment Provisioning | 已经实现 / FINAL GATE PASS | AutoDL RTX 4090 instance、`ppe-exp001` runtime、dependency fingerprint、dataset transfer 和 full manifest integrity 均验证；Environment/Dataset READY；training 仍待授权 |
| P2-4-G3 | AutoDL Dependencies Provisioning | 已经实现 / G3 PASS | 在 AutoDL RTX 4090 实例创建 `ppe-exp001`，安装并验证 Python 3.10.21、PyTorch 2.5.1+cu124、Ultralytics 8.4.157、OpenCV 和 CUDA；训练授权仍独立管理 |
| P2-4-G4 | Dataset Transfer & Integrity Verification | 已经实现 / G4 PASS | 将 `CSS-PPE-10-V1` 原样传输至 AutoDL，验证 5,604 个文件、2,799 张图片、2,799 个 label、7 类 mapping、processed/source fingerprints 和 full manifest；未训练 |
| P2-5 | EXP-001 Training Execution Authorization Review | 已经实现 / REVIEW RESULT BLOCKED | 授权报告复核配置、输出、环境 fingerprint 和 reproducibility；当时参数、权重二进制、完整 freeze 与授权缺失，因此禁止训练 |
| P2-5.1 | EXP-001 Configuration Freeze Review | 已经实现 / CONFIGURATION FREEZE COMPLETE | 冻结 EXP-001 模型、数据、class count、训练参数、augmentation、device、workers 和输出路径；记录配置 SHA256；`execution_enabled: false` 保持不变 |
| P2-5.2 | EXP-001 Weight Registration | 已经实现 / WEIGHT REGISTERED | 登记官方 Ultralytics `yolo11n.pt` 初始化权重，记录来源、5,613,764 bytes、SHA256、MD5、checkpoint 结构和 manifest；权重保持 Git-ignored，未训练、未修改 dataset/mapping/config |
| P2-5.3 | EXP-001 Dependency Freeze | 已经实现 / DEPENDENCY FROZEN | 导出 conda environment、conda explicit URLs 和 pip freeze lock；记录 RTX 4090、driver、CUDA API/runtime、cuDNN 和 runtime fingerprint；lock 与远端逐行匹配，`pip check` PASS；未训练或修改 dataset/mapping/config |
| P2-5.4 | EXP-001 Remote Weight Transfer Verification | 已经实现 / REMOTE WEIGHT VERIFIED | 将 `yolo11n.pt` 传输到 AutoDL，验证远端存在、5,613,764 bytes 和 SHA256 与本地一致；未训练、未执行模型、未修改 dataset/mapping/config |
| P2-5.5 | EXP-001 Baseline Training Execution | 已经实现 / TRAINING COMPLETED | 使用显式一次性授权完成 95/100 epochs 训练，best epoch 75；产出 best/last checkpoints、日志、args、results.csv、confusion matrix、run record 和 frozen config snapshot；validation mAP50 `0.767`、mAP50-95 `0.480` |
| P2-7 | EXP-001 Training Result Freeze | 已经实现 / RESULT FROZEN | 冻结报告与最佳模型 manifest 记录 29 项产物 SHA256、最终训练验证指标、best epoch 75、runtime 和时长；未进入 Phase 3 |

## 4. 实现设计

固定数据版本、配置、随机种子、依赖版本与设备策略；训练日志和配置快照保存
至 `artifacts/runs/`，模型产物保存至受忽略的 `models/`。

## 5. 测试要求

- 配置解析、种子固定和训练命令测试。
- 至少完成一轮训练并验证权重、日志、配置和指标文件存在。
- 从记录信息可重建相同实验入口。

## 6. Gate

### P2-0 Preparation Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-0-G1 | 当前训练环境已完成只读审计 | PASS |
| P2-0-G2 | Windows/NVIDIA、WSL2/CUDA、Cloud GPU、CPU fallback 方案已比较 | PASS |
| P2-0-G3 | Python、PyTorch、CUDA、Ultralytics、YOLO11 版本兼容矩阵已记录 | PASS |
| P2-0-G4 | Dataset、Experiment、Environment、GPU、Dependencies readiness 已记录 | PASS |
| P2-0-G5 | 未安装依赖、未下载权重、未执行训练或修改 dataset | PASS |
| P2-0-G6 | Charter、MUST、Phase Goal 和 EXP-001 冻结字段未修改 | PASS |

### P2-1 Environment Setup Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-1-G1 | Environment decision documented | PASS |
| P2-1-G2 | Dependency specification documented | PASS |
| P2-1-G3 | Setup plan documented | PASS |
| P2-1-G4 | No training executed | PASS |
| P2-1-G5 | Charter unchanged | PASS |

### P2-2 Training Authorization Review Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-2-G1 | Cloud environment reviewed | PASS |
| P2-2-G2 | Dependencies reviewed | PASS |
| P2-2-G3 | EXP-001 reviewed | PASS |
| P2-2-G4 | Authorization checklist created | PASS |
| P2-2-G5 | No training executed | PASS |
| P2-2-G6 | Charter unchanged | PASS |

### P2-3 Cloud Provider Selection Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-3-G1 | Candidate providers compared | PASS |
| P2-3-G2 | Recommended provider and GPU selected | PASS |
| P2-3-G3 | Cost, upload, and retention risks reviewed | PASS |
| P2-3-G4 | Authorization remains NOT GRANTED | PASS |
| P2-3-G5 | No instance, dependency, weight, or training was created | PASS |
| P2-3-G6 | Charter unchanged | PASS |

### P2-4-G3 Dependency Provisioning Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-4-G3-G1 | AutoDL instance identity recorded | PASS |
| P2-4-G3-G2 | Isolated `ppe-exp001` environment created | PASS |
| P2-4-G3-G3 | PyTorch CUDA stack installed | PASS |
| P2-4-G3-G4 | Ultralytics and runtime dependencies installed | PASS |
| P2-4-G3-G5 | PyTorch CUDA and Ultralytics imports verified | PASS |
| P2-4-G3-G6 | No dataset, weight, training, or frozen identity change | PASS |
| P2-4-G3-G7 | Charter unchanged | PASS |

### P2-4-G4 Dataset Transfer Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-4-G4-G1 | Remote dataset directory created | PASS |
| P2-4-G4-G2 | Frozen dataset transferred unchanged | PASS |
| P2-4-G4-G3 | File, image, and label counts verified | PASS |
| P2-4-G4-G4 | `data.yaml` and class mapping verified | PASS |
| P2-4-G4-G5 | Source and processed fingerprints verified | PASS |
| P2-4-G4-G6 | Full remote manifest verification passed | PASS |
| P2-4-G4-G7 | No training, weights, or frozen identity change | PASS |
| P2-4-G4-G8 | Charter unchanged | PASS |

### P2-4 Final Provisioning Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-4-G1 | Instance created | PASS |
| P2-4-G2 | Runtime fingerprint recorded | PASS |
| P2-4-G3 | Dependencies installed and verified | PASS |
| P2-4-G4 | Dataset transferred and verified | PASS |
| P2-4-G5 | Training not executed | PASS |
| P2-4-G6 | Charter unchanged | PASS |

### P2-5 Training Authorization Review Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-5-G1 | Authorization report exists | PASS |
| P2-5-G2 | Configuration completeness reviewed | PASS |
| P2-5-G3 | Output paths reviewed | PASS |
| P2-5-G4 | Runtime fingerprint reviewed | PASS |
| P2-5-G5 | Reproducibility requirements reviewed | PASS |
| P2-5-G6 | Protected state preserved | PASS |

### P2-5.1 Configuration Freeze Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-5.1-G1 | Canonical configuration frozen | PASS |
| P2-5.1-G2 | Augmentation frozen | PASS |
| P2-5.1-G3 | Schema aligned | PASS |
| P2-5.1-G4 | Freeze record created | PASS |
| P2-5.1-G5 | Final report created | PASS |
| P2-5.1-G6 | Execution remains disabled | PASS |
| P2-5.1-G7 | No protected-state mutation | PASS |
| P2-5.1-G8 | Charter unchanged | PASS |

### P2-5.2 Weight Registration Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-5.2-G1 | Official initialization checkpoint acquired | PASS |
| P2-5.2-G2 | Binary size, MD5, and SHA256 verified | PASS |
| P2-5.2-G3 | PyTorch checkpoint structure verified | PASS |
| P2-5.2-G4 | Weight manifest created | PASS |
| P2-5.2-G5 | Binary remains Git-ignored | PASS |
| P2-5.2-G6 | Authorization checklist updated | PASS |
| P2-5.2-G7 | No training, dataset, mapping, or EXP-001 config mutation | PASS |
| P2-5.2-G8 | Execution remains disabled and unauthorized | PASS |
| P2-5.2-G9 | Charter unchanged | PASS |

### P2-5.3 Dependency Freeze Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-5.3-G1 | Conda environment lock exported | PASS |
| P2-5.3-G2 | Pip freeze lock exported | PASS |
| P2-5.3-G3 | Conda explicit URL lock exported | PASS |
| P2-5.3-G4 | GPU/CUDA/driver/runtime fingerprint recorded | PASS |
| P2-5.3-G5 | Exported locks match remote environment | PASS |
| P2-5.3-G6 | Runtime dependency consistency verified | PASS |
| P2-5.3-G7 | Authorization checklist updated | PASS |
| P2-5.3-G8 | No training or protected-state mutation | PASS |
| P2-5.3-G9 | Execution remains disabled and unauthorized | PASS |
| P2-5.3-G10 | Charter unchanged | PASS |

### P2-5.4 Remote Weight Transfer Verification Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-5.4-G1 | Remote destination checked before transfer | PASS |
| P2-5.4-G2 | Registered weight transferred to AutoDL | PASS |
| P2-5.4-G3 | Remote file exists | PASS |
| P2-5.4-G4 | Local and remote file sizes match | PASS |
| P2-5.4-G5 | Local and remote SHA256 match | PASS |
| P2-5.4-G6 | Weight manifest records verified remote copy | PASS |
| P2-5.4-G7 | Authorization checklist records verified remote copy | PASS |
| P2-5.4-G8 | No training or protected-state mutation | PASS |
| P2-5.4-G9 | Execution remains disabled and unauthorized | PASS |
| P2-5.4-G10 | Charter unchanged | PASS |

### P2-5.5 EXP-001 Training Execution Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-5.5-G1 | Explicit one-run authorization recorded | PASS |
| P2-5.5-G2 | Frozen config, dataset, class order, and weight hashes verified before execution | PASS |
| P2-5.5-G3 | At least one training epoch completed | PASS |
| P2-5.5-G4 | Best and last checkpoints produced | PASS |
| P2-5.5-G5 | Training log, resolved args, epoch metrics, plots, and run record produced | PASS |
| P2-5.5-G6 | Frozen configuration snapshot retained | PASS |
| P2-5.5-G7 | Dataset, mapping, and canonical config were not modified | PASS |
| P2-5.5-G8 | Another training run is not authorized | PASS |
| P2-5.5-G9 | M-004 marked implemented and M-005 remains pending | PASS |

P2-5.5 result: `COMPLETED`. The training ran for 95 epochs, stopped early
after epoch 75 as the best epoch, and produced a complete experiment archive.
The metrics are training validation results; they do not replace the
independent Phase 3 evaluation required by M-005.

### Phase Gates

| Gate | Requirement |
| --- | --- |
| P2-G1 | YOLO11n 至少完成一轮可复现训练 |
| P2-G2 | 数据、配置、代码状态、依赖和种子证据齐全 |
| P2-G3 | 权重、日志、配置快照和运行报告可定位 |

## 7. 已知问题

- 当前主机没有 NVIDIA GPU，CUDA 不可用，PyTorch 和 Ultralytics 未安装；
  P2-0 readiness 为 `NOT READY FOR TRAINING`。
- 推荐 P2-1 使用具备 NVIDIA GPU 的本地/WSL2 环境或受控 cloud GPU。
  CPU fallback 只能作为诊断路径，不能替代 M-004 所需的可复现 baseline。
- Python、PyTorch、CUDA、Ultralytics 和 YOLO11 权重来源尚未冻结；禁止把
  `requirements.txt` 的范围约束误当成训练环境版本 lock。
- P1E-1 的 EXP-001 hyperparameters、seed、device strategy 和权重
  `PENDING_DESIGN_REVIEW` 是历史状态；P2-5.1 已冻结 canonical 参数。
- P2-1 记录 controlled cloud GPU architecture；P2-3 选择 AutoDL +
  RTX 4090 24GB，P2-4-G3 已在实例 `bcb849a74f-38320766` 上创建
  `ppe-exp001` 并完成 dependency verification；P2-4 final gate 已 PASS，
  Environment 和 Dataset 为 READY。live price、storage 和 retention 继续
  作为 provider risk 管理。
- P2-1 dependency specification 中的 version 是 `PLANNED VERSION`；
  P2-4-G3 实际安装 Ultralytics `8.4.157`，因为 planned `8.4.158` 未在配置
  index 发布。P2-4 已记录 resolved runtime 和 dependency fingerprint；
  P2-5.5 使用该 resolved runtime 完成 EXP-001。
- Cloud GPU 设置将涉及数据上传、凭据、网络、存储保留和成本风险；这些必须
  在 P2-2 中审核，凭据不得进入 Git。
- P2-2 cloud environment review 的 `PENDING_SELECTION` 是历史状态；P2-4
  已记录当前 AutoDL instance 的 provider、region、GPU、VRAM、OS、driver
  和 runtime fingerprint。storage、cost 和 retention 继续按 provider risk
  管理。
- P2-2 dependency freeze review 记录的是安装前历史状态；P2-4-G3 已安装并
  验证实际依赖，P2-4-G2 已记录 runtime fingerprint。
- P2-2 EXP-001 execution review 已通过 dataset、mapping、模型、class count、
  output/logging paths 和 metrics 检查；其参数与 runtime 未冻结是历史状态，
  现由 P2-5.1 冻结参数，`execution_enabled` 继续为 `false`。
- EXP-001 的训练授权由明确用户指令提供，并以单独的一次性 authorization
  记录执行；该记录现已 `CONSUMED`，不能再次用于训练。
- P2-3 已选择 AutoDL 作为推荐云 GPU 方案；P2-4-G3 已在用户提供的
  RTX 4090 24GB 实例完成 isolated dependency provisioning，P2-4-G4
  已完成 dataset transfer 和 integrity verification；P2-4 final gate 已
  PASS，随后由 P2-5.5 使用一次性授权完成训练。
- P2-3 成本数字是规划上限，不是实时报价；若 RTX 4090 现价超过
  `CNY 3/hour`，必须重新申请预算批准。
- P2-5.1 已将先前 `PENDING_DESIGN_REVIEW` 的 canonical EXP-001 参数冻结为：
  Ultralytics `8.4.157`、`yolo11n.pt`、7 类、`imgsz: 640`、
  `epochs: 100`、`batch: 16`、`AdamW`、`lr: 0.001`、`cosine`、
  `seed: 42`、`cuda:0`、`workers: 8` 和规范化输出路径。
- P2-5.2 已登记官方 `yolo11n.pt` 初始化权重，并记录
  `5,613,764` bytes 和 SHA256 `0ebbc80d...7644ee1`；该二进制仍为
  Git-ignored。P2-5.3 已冻结 conda/pip 依赖和 runtime fingerprint；
  P2-5.4 已将权重传输到远端并验证路径、大小和 SHA256。
- `execution_enabled` 继续为 `false`；configuration freeze 不等于 training
  authorization。
- Ultralytics 8.4.157 的 AMP 自检自动下载 `yolo26n.pt` 仅用于 one-time
  compatibility check，日志已披露，且该文件不是训练初始化权重。
- P2-5.5 的 metrics 是训练期间 validation results；M-005 仍需 Phase 3
  独立 evaluation。

## 8. 开发记录

- 2026-09-21: 计划建立，未开始实现。
- 2026-09-22: 完成 P2-0 Training Environment Preparation 与 Dependency
  Boundary Review。复核 Python/pip、PyTorch、Ultralytics、CUDA、GPU、RAM
  和 CPU；生成 dependency strategy、version matrix 与 readiness checklist。
  当前环境仍为 `NOT READY FOR TRAINING`，未安装依赖、未下载权重、未训练、
  未修改 dataset；P2-0-G1 至 P2-0-G6 PASS。下一允许步骤为 P2-1 环境搭建。
- 2026-09-22: 完成 P2-1 Training Environment Setup 的方案阶段。选择
  `D. Controlled Cloud GPU`，记录 planned Python/PyTorch/CUDA/torchvision/
  Ultralytics/NumPy stack、安装顺序、non-training verification、rollback 和
  environment freeze 要求。未 provision cloud instance、未安装依赖、未下载
  权重、未训练、未修改 dataset；P2-1-G1 至 P2-1-G5 PASS。下一允许步骤为
  P2-2 Training Execution Authorization Review。
- 2026-09-22: 完成 P2-2 Training Execution Authorization Review。新增
  cloud environment review、dependency freeze review、EXP-001 execution
  review 和 training authorization checklist；确认 provider/GPU/image/cost/
  retention 为 `PENDING_SELECTION`、dependency freeze 为 `PENDING`、
  authorization 为 `NOT GRANTED`。未 provision、未安装、未下载权重、未训练、
  未修改 dataset/config；P2-2-G1 至 P2-2-G6 PASS。下一允许步骤为
  `WAIT FOR TRAINING AUTHORIZATION`。
- 2026-09-22: 完成 P2-3 Cloud Provider Selection & Cost Review。比较
  AutoDL、阿里云 GPU ECS、腾讯云 GPU 和 RunPod/Vast.ai 等备选；推荐
  AutoDL + RTX 4090 24GB 作为成本受控设计目标，记录 40 GPU-hour 与
  CNY 150 预算上限、数据集上传规则和 retention/cleanup 要求。P2-2
  authorization 保持 `NOT GRANTED`；未创建实例、未安装依赖、未下载权重、
  未训练、未修改 dataset/config；P2-3-G1 至 P2-3-G6 PASS。下一允许步骤为
  `WAIT FOR HUMAN TRAINING AUTHORIZATION`。
- 2026-09-22: 完成 P2-4-G3 AutoDL Dependencies Provisioning。连接用户提供
  的 AutoDL 实例 `bcb849a74f-38320766`，创建 `ppe-exp001`，安装并验证
  Python 3.10.21、PyTorch 2.5.1+cu124、torchvision 0.20.1+cu124、
  Ultralytics 8.4.157、OpenCV 5.0.0.93 和 NumPy 2.2.6。
  `torch.cuda.is_available()` 为 `True`，GPU 为 NVIDIA GeForce RTX 4090。
  未上传 dataset、未下载权重、未执行训练、未修改 source code、dataset、
  mapping 或 EXP-001 frozen identity；P2-4-G3-G1 至 P2-4-G3-G7 PASS。
  P2-4 final gate 随后确认 runtime fingerprint。
- 2026-09-22: 完成 P2-4-G4 Dataset Transfer & Integrity Verification。使用
  recursive SCP 将 `data/processed/css-ppe-10-v1/` 原样传输到
  `/root/autodl-tmp/datasets/css-ppe-10-v1/`。远端验证 5,604 个文件、
  2,799 张图片、2,799 个 label；processed `data.yaml` SHA256 为
  `45cc2717...`，source `data.yaml` 仍为 `5c393e7...`，processed manifest
  为 `dbfe43c4...`。5,602-entry metadata manifest 和 5,604-entry full
  manifest 均 PASS。未修改 dataset、labels、annotation、mapping 或
  EXP-001 configuration，未下载权重、未执行训练；P2-4-G4-G1 至
  P2-4-G4-G8 PASS；P2-4 final gate 随后确认 Environment 与 Dataset READY。
- 2026-09-22: 完成 P2-4 Final Gate。复核 instance、runtime fingerprint、
  isolated dependency stack、dataset transfer 和 full manifest integrity；
  P2-4-G1 至 P2-4-G6 PASS。Environment 与 Dataset 为 READY，Training 仍为
  `NOT STARTED`，等待独立 training authorization。未执行 `yolo train`、
  `python train.py`、model download、benchmark 或 evaluation。
- 2026-09-22: 完成 P2-5 EXP-001 Training Execution Authorization Review。
  生成 `P2-5_TRAINING_AUTHORIZATION_REPORT.md`，结果为 `BLOCKED`；记录配置
  参数、权重二进制、完整环境 freeze 和人工授权缺失项。未训练、未下载权重、
  未修改 dataset/mapping/configuration。
- 2026-09-22: 完成 P2-5.1 EXP-001 Configuration Freeze Review。冻结 canonical
  EXP-001 训练参数、augmentation、路径和 SHA256；生成
  `docs/reports/P2-5.1_CONFIGURATION_FREEZE.md` 与
  `P2-5.1_CONFIGURATION_FREEZE_REPORT.md`。P2-5.1-G1 至 P2-5.1-G8 PASS；
  `execution_enabled` 保持 `false`，训练授权保持 `NOT GRANTED`，未下载权重、
  未训练、未修改 dataset 或 mapping。
- 2026-09-22: 完成 P2-5.2 EXP-001 Weight Registration。从官方 Ultralytics
  assets `v8.3.0` release 登记 `yolo11n.pt` 到 Git-ignored
  `models/pretrained/yolo11n.pt`，验证 `5,613,764` bytes、MD5、PyTorch
  checkpoint ZIP 结构和 SHA256 `0ebbc80d...7644ee1`；创建
  `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` 和
  `P2-5.2_WEIGHT_REGISTRATION_REPORT.md`，并更新 authorization checklist。
  P2-5.2-G1 至 P2-5.2-G9 PASS；未训练、未修改 dataset、mapping 或 EXP-001
  configuration，权重未传输到远端，训练授权保持 `NOT GRANTED`。
- 2026-09-22: 完成 P2-5.3 EXP-001 Dependency Freeze。导出 `ppe-exp001`
  的 conda environment、conda explicit URLs 和 pip freeze lock，记录 RTX
  4090 UUID、driver `560.35.03`、CUDA driver API `12.6`、PyTorch CUDA
  runtime `12.4`、cuDNN `90100`、Python `3.10.21`、PyTorch `2.5.1+cu124`
  和 Ultralytics `8.4.157`；lock 与远端逐行匹配，`pip check` PASS。
  P2-5.3-G1 至 P2-5.3-G10 PASS；未训练、未安装新依赖、未修改 dataset、
  mapping 或 EXP-001 configuration，远端权重副本和 training authorization
  仍待完成。
- 2026-09-22: 完成 P2-5.4 EXP-001 Remote Weight Transfer Verification。
  在远端目标不存在的前提下，将 `yolo11n.pt` 初始化权重传输到
  `/root/autodl-tmp/models/pretrained/yolo11n.pt`。远端文件存在且大小为
  `5,613,764` bytes，SHA256
  `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`
  与本地一致；生成 `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md`，并更新
  weight manifest 与 authorization checklist。P2-5.4-G1 至 P2-5.4-G10
  PASS；未训练、未执行模型、未修改 dataset、mapping 或 EXP-001
  configuration，training authorization 仍为 `NOT GRANTED`。
- 2026-09-22: 完成 P2-5.5 EXP-001 Baseline Training Execution。在明确授权
  后运行冻结配置；训练从 `08:00:02Z` 至 `08:19:29Z`，完成 95/100 epochs，
  在第 75 epoch 取得最佳结果并由 `patience: 20` 提前停止。总体 validation
  指标为 precision `0.899`、recall `0.649`、mAP50 `0.767`、mAP50-95
  `0.480`。生成 best/last checkpoints、training log、resolved args、
  `results.csv`、confusion matrix、曲线、run record 和 frozen config
  snapshot；生成 `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`。
  M-004 标记 `已经实现`，M-005 保持 `待实现`；授权记录标记为 `CONSUMED`，
  Phase 3 未启动。

### P2-7 Training Result Freeze

- 2026-09-22: 冻结 `EXP-001` 已完成训练的结果；报告位于
  `docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md`，机器清单位于
  `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml`。
- source 5,601 项与 processed 5,602 项 checksum manifest 全部匹配；
  config、initial weight、best/last checkpoint 和 dependency locks 哈希匹配。
- 本次仅归档已有结果；未训练、未 evaluation、未进入 Phase 3，M-005 保持待实现。
