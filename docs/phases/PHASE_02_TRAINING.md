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
- EXP-001 的 hyperparameters、seed、device strategy 和权重仍为
  `PENDING_DESIGN_REVIEW`，不得在本阶段自行决定。
- P2-1 记录 controlled cloud GPU architecture；P2-3 选择 AutoDL +
  RTX 4090 24GB，P2-4-G3 已在实例 `bcb849a74f-38320766` 上创建
  `ppe-exp001` 并完成 dependency verification；P2-4 final gate 已 PASS，
  Environment 和 Dataset 为 READY。live price、storage 和 retention 继续
  作为 provider risk 管理。
- P2-1 dependency specification 中的 version 是 `PLANNED VERSION`；
  P2-4-G3 实际安装 Ultralytics `8.4.157`，因为 planned `8.4.158` 未在配置
  index 发布。P2-4 已记录 resolved runtime 和 dependency fingerprint；训练
  授权仍需独立审批。
- Cloud GPU 设置将涉及数据上传、凭据、网络、存储保留和成本风险；这些必须
  在 P2-2 中审核，凭据不得进入 Git。
- P2-2 cloud environment review 的 `PENDING_SELECTION` 是历史状态；P2-4
  已记录当前 AutoDL instance 的 provider、region、GPU、VRAM、OS、driver
  和 runtime fingerprint。storage、cost 和 retention 继续按 provider risk
  管理。
- P2-2 dependency freeze review 记录的是安装前历史状态；P2-4-G3 已安装并
  验证实际依赖，P2-4-G2 已记录 runtime fingerprint。
- P2-2 EXP-001 execution review 已通过 dataset、mapping、模型、class count、
  output/logging paths 和 metrics 检查，但 seed、weights、hyperparameters、
  device 和 runtime 仍未冻结；`execution_enabled` 继续为 `false`。
- 训练授权为 `NOT GRANTED`；下一允许步骤是
  `WAIT FOR TRAINING AUTHORIZATION`。
- P2-3 已选择 AutoDL 作为推荐云 GPU 方案；P2-4-G3 已在用户提供的
  RTX 4090 24GB 实例完成 isolated dependency provisioning，P2-4-G4
  已完成 dataset transfer 和 integrity verification；P2-4 final gate 已
  PASS，training authorization 仍需单独完成。
- P2-3 成本数字是规划上限，不是实时报价；若 RTX 4090 现价超过
  `CNY 3/hour`，必须重新申请预算批准。

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
