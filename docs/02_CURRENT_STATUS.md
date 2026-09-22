# Current Status

## Current Phase

P2-7 Training Result Freeze

## EXP-001 Training

COMPLETED

## GitHub Release Strategy

当前项目采用 Phase Milestone Release：

Phase 完成 → Gate PASS → Commit → Tag → Push

## Overall Status

Phase 2 的 EXP-001 baseline training 已完成并由
`docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md` 归档。本次训练依据明确
人工授权执行，95/100 epochs 后由 `patience: 20` 提前停止，最佳 epoch 为 75。
验证结果为 precision `0.899`、recall `0.649`、mAP50 `0.767`、
mAP50-95 `0.480`；权重、日志、resolved args、epoch metrics 和 run record
均已生成。`best.pt` SHA256 为 `1c144eef...871f61`。M-004 已满足并标记
`已经实现`。M-005 仍未实现，Phase 3 独立评估尚未开始。

Phase 1 仍记为 `实现中`，但 P1A 至 P1E 的数据工程子阶段已经完成。P1A
已通过；P1B 已完成并冻结 `CSS-PPE-10-V1`。P1C-0、
P1C-1 和 P1C-2 已完成，Strategy C 的 7 类 training mapping 已冻结并生成
7 类 processed dataset。P1D-0 已完成 observation-only quality validation
设计与离线框架；P1D-1 已完成真实数据集质量验证并通过 G1D1-1 至
G1D1-10。质量扫描记录了 perceptual split-leakage candidates、small-object
risk、class imbalance 和 empty-label observations，但未修改数据。P1E-0
已完成 dataset release 与 training preparation 设计，包括 release
contract、experiment structure、配置模板和 G1E0-1 至 G1E0-7。随后已完成
P1E-1 Baseline Training Preparation Review：数据契约、实验
配置、环境、复现性清单和 EXP-001 runbook 均已审计，P1E1-G1 至 P1E1-G7
全部 PASS。M-001 保持 `待实现`，因为数据治理层仍有需要独立确认的五类/
场景上下文边界和 perceptual split-leakage candidate 风险。

Phase 2 的 P2-0 Training Environment Preparation 与 Dependency
Boundary Review 已完成：当前 Windows 主机没有 NVIDIA GPU，PyTorch 和
Ultralytics 均未安装，训练环境仍为 `NOT READY FOR TRAINING`。P2-0 仅记录
dependency strategy、version matrix 和 readiness boundary，未安装依赖、
未下载权重、未修改 dataset、未启动训练。

P2-1 已完成环境架构决策和设置方案：选择 `D. Controlled Cloud GPU`，记录
Python 3.11.16、PyTorch 2.11.0+cu128、CUDA 12.8、torchvision 0.26.0、
Ultralytics 8.4.158 等 `PLANNED VERSION`，并定义安装顺序、验证、回滚和
environment freeze 方案。P2-1 完成时仍未 provision cloud GPU、未安装依赖、
未下载权重、未执行训练；当时 `Dependency Freeze` 为 `PENDING`。

P2-2 已完成训练执行授权审查：dependency freeze 仍为 `PENDING`；EXP-001
数据集、mapping、模型、class count、输出、logging 和 metrics 已复核。
P2-3 已完成 cloud provider selection 与 cost review：推荐 AutoDL 作为
成本受控方案，设计目标为 RTX 4090 24GB，并比较阿里云、腾讯云和其他方案。
P2-4-G3 随后在用户提供的 AutoDL RTX 4090 实例上完成隔离环境 provisioning：
创建 `ppe-exp001`，安装 Python 3.10.21、PyTorch 2.5.1+cu124、torchvision
0.20.1+cu124、Ultralytics 8.4.157、OpenCV 5.0.0.93 和 NumPy 2.2.6，并确认
`cuda_available: True`。P2-1 计划中的 Ultralytics 8.4.158 未在配置 index
发布，实际安装记录为 8.4.157。P2-4-G4 随后将冻结的
`CSS-PPE-10-V1` 传输到 AutoDL，并完成 5,604 个文件、2,799 张图片、
2,799 个 label、7 类 mapping 和完整 SHA256 manifest 验证。P2-4 final
provisioning gate 已完成：Environment READY，Dataset READY，Training
PENDING AUTHORIZATION。该阶段完成时训练授权保持 `NOT GRANTED`。

P2-5 已完成 EXP-001 training execution authorization review，当时结果因
训练参数、权重二进制、完整环境 freeze 和人工授权未完成而记录为 `BLOCKED`。
P2-5.1 随后完成 EXP-001 configuration freeze：模型实现版本、数据身份、
class count、`imgsz`、epochs、batch、optimizer、LR strategy、seed、device、
workers 和全部输出路径均已冻结并有 SHA256 记录。`execution_enabled` 仍为
`false`，训练授权仍为 `NOT GRANTED`；本次冻结未下载权重或修改 dataset。

P2-5.2 随后完成 EXP-001 weight registration：从 Ultralytics 官方 assets
`v8.3.0` release 获取 `yolo11n.pt`，保存到 Git-ignored
`models/pretrained/yolo11n.pt`，核对 HTTP content length，计算 SHA256 和
MD5，并创建 `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml`。该权重仅作为训练
初始化权重；未启动训练，未修改 dataset、mapping 或 EXP-001 配置。

P2-5.3 随后完成 EXP-001 dependency freeze：导出 `ppe-exp001` 的完整
conda environment、conda explicit URLs 和 `pip freeze --all` lock，并记录
RTX 4090 UUID、NVIDIA driver `560.35.03`、CUDA driver API `12.6`、PyTorch
CUDA runtime `12.4`、Python `3.10.21`、PyTorch `2.5.1+cu124` 和
Ultralytics `8.4.157`。导出结果与远端环境逐行匹配，`pip check` PASS；
未训练、未安装新依赖、未修改 dataset、mapping 或 canonical config。

P2-5.4 随后完成 EXP-001 remote weight transfer verification：将官方
`yolo11n.pt` 初始化权重传输到 AutoDL
`/root/autodl-tmp/models/pretrained/yolo11n.pt`，远端文件存在且大小为
`5,613,764` bytes，远端 SHA256 与本地
`0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`
一致。该阶段完成时未启动训练、未执行模型、未修改 dataset、mapping 或
EXP-001 configuration；随后用户明确授权 EXP-001 单次训练，授权记录现已
标记为 `CONSUMED`。

## Current Subphase

P2-7 — EXP-001 Training Result Freeze

实现状态：COMPLETED / TRAINING RESULT FROZEN

Freeze report：`docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md`

Best model manifest：`docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml`

本次仅冻结已有训练结果，未重新训练、未执行 evaluation、未进入 Phase 3。

Experiment：`EXP-001`

Authorization：GRANTED AND CONSUMED

Run status：COMPLETED

Epochs completed：`95` with early stopping; best epoch `75`

Overall validation：precision `0.899`, recall `0.649`, mAP50 `0.767`,
mAP50-95 `0.480`

Best checkpoint：`models/checkpoints/EXP-001/best.pt`

Best checkpoint SHA256：
`1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`

Execution report：`docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`

数据修改：NONE

M-004：已经实现

M-005：待实现

Phase 3：NOT STARTED

## Previous Subphases

P2-5.5 — EXP-001 Baseline Training Execution

实现状态：COMPLETED / TRAINING EXECUTED；95 epochs，best epoch 75。

P2-5.4 — EXP-001 Remote Weight Transfer Verification

实现状态：COMPLETED / REMOTE WEIGHT VERIFIED

Local path：`models/pretrained/yolo11n.pt`

Remote path：`/root/autodl-tmp/models/pretrained/yolo11n.pt`

Local SHA256：`0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`

Remote SHA256：`0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`

Match result：PASS

P2-5.3 — EXP-001 Dependency Freeze

实现状态：COMPLETED / DEPENDENCY FROZEN

Dependency locks：

- `locks/EXP-001/conda-environment.yml`
- `locks/EXP-001/conda-explicit.lock`
- `locks/EXP-001/pip-freeze-all.txt`

Runtime fingerprint：`locks/EXP-001/runtime-fingerprint.yaml`

P2-5.2 — EXP-001 Weight Registration

实现状态：COMPLETED / WEIGHT REGISTERED

官方 `yolo11n.pt` 初始化权重已登记，来源、大小和 SHA256 已记录；二进制保持
Git-ignored；该登记阶段完成时远端副本尚未传输，随后由 P2-5.4 验证。

P2-5.1 — EXP-001 Configuration Freeze Review

实现状态：COMPLETED / CONFIGURATION FREEZE COMPLETE

canonical EXP-001 参数、augmentation 和输出路径已冻结；配置 SHA256 已记录，
训练授权保持不变。

P2-5 — EXP-001 Training Execution Authorization Review

实现状态：COMPLETED / REVIEW RESULT BLOCKED

该审查确认 dataset、mapping 和输出路径满足要求，但当时 EXP-001 参数、权重
二进制、完整 dependency freeze 与人工授权尚未完成。该结果作为历史证据保留；
P2-5.1 只解决配置参数冻结。

P2-4 — AutoDL Training Environment Provisioning

实现状态：COMPLETED / FINAL GATE PASS

Environment 和 Dataset 已通过 P2-4 final gate；训练仍待独立授权。

P2-3 — Cloud Provider Selection & Cost Review

实现状态：COMPLETED / DESIGN SELECTION COMPLETE

该阶段记录 AutoDL + RTX 4090 24GB 的 provider selection、cost、upload 和
retention 边界；P2-4-G3 随后在用户选定的实例上完成隔离依赖安装，但该历史
记录中的 `NOT PROVISIONED` 状态仍表示 P2-3 完成时的状态。

P2-2 — Training Execution Authorization Review

实现状态：COMPLETED / REVIEW COMPLETE

该阶段记录 cloud environment、dependency freeze、EXP-001 执行审查和
authorization checklist；provider 选择后续由 P2-3 完成，authorization
仍保持 `NOT GRANTED`。

P2-1 — Training Environment Setup

实现状态：COMPLETED / DESIGN COMPLETE / AWAITING HUMAN REVIEW

该阶段记录 controlled cloud GPU 选择、planned dependency stack、setup、
verification、rollback 和 runtime freeze requirements；未 provision、未安装。

P2-0 — Training Environment Preparation & Dependency Boundary Review

实现状态：COMPLETED / REVIEW PASS

该阶段记录 environment baseline、dependency strategy、version matrix 和
readiness boundary 的历史证据；P2-1 在其上完成方案选择，但未 provisioning。

P1E-1 — Baseline Training Preparation Review

实现状态：COMPLETED / REVIEW PASS

该阶段的历史 contract、config、environment、reproducibility 和 runbook 证据
继续保留；P2-0 只在其上增加 environment preparation boundary。

## Reference Intake

Reference Intake: COMPLETED

- Teacher reference package registered as REF-001.
- Teacher checkpoint registered as REF-002.
- No teacher asset committed or copied into the repository.
- P1A reference-intake prerequisites reviewed.

## Current Environment

- Local OS: Windows NT 10.0.22631.0
- Local Python: 3.13.6
- Local pip: 25.3
- Local Git: 2.51.2.windows.1
- Local PyTorch: not installed
- Local CUDA: unavailable
- Environment decision: D. Controlled Cloud GPU (provisioned)
- Training instance: AutoDL `bcb849a74f-38320766`, region `bjb1`
- Training OS: Ubuntu 20.04.5 LTS
- Training GPU: NVIDIA GeForce RTX 4090, 24,564 MiB
- Training environment: `/root/miniconda3/envs/ppe-exp001`
- Training Python: 3.10.21
- Training PyTorch: `2.5.1+cu124`
- Training CUDA runtime: 12.4; GPU available via `torch.cuda.is_available()`
- Training Ultralytics: `8.4.157`
- Remote dataset: `/root/autodl-tmp/datasets/css-ppe-10-v1/`
- Remote dataset integrity: 5,604 files; processed manifest PASS
- Initialization weight: `models/pretrained/yolo11n.pt`; registered; SHA256
  `0ebbc80d...7644ee1`
- Remote initialization weight:
  `/root/autodl-tmp/models/pretrained/yolo11n.pt`; size and SHA256 verified
- Dependency freeze: P2-5.3 FROZEN; training authorization remains separate
- Dependency locks: `locks/EXP-001/conda-environment.yml`,
  `conda-explicit.lock`, and `pip-freeze-all.txt`
- Runtime fingerprint: `locks/EXP-001/runtime-fingerprint.yaml`
- Training authorization: GRANTED AND CONSUMED for one EXP-001 run
- Training status: COMPLETED on 2026-09-22
- Best checkpoint:
  `models/checkpoints/EXP-001/best.pt`; SHA256
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`
- Execution report: `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`

## Completed

- P2-7 完成 EXP-001 Training Result Freeze：冻结最佳权重身份、最终训练验证指标、
  runtime fingerprint、训练时长和 29 项产物清单；source/processed checksum
  manifest 与冻结身份均已只读校验，dataset、mapping 和 frozen config 未修改。

- 最终工程目录和 Python package 边界
- 六份 YAML 配置
- 路径、配置加载、日志、计时和系统信息基础工具
- 检测 schema
- 未来阶段服务、业务和基础设施占位边界
- Charter、Master Plan、ADR、Phase、Dataset、Open Source、Risk 文档
- Phase 0 基础测试
- G0-1 至 G0-13 全部 PASS
- pytest 99 项测试通过
- compileall 成功
- git diff --check 成功
- Pre-Phase 1 Reference Intake 文档与治理记录
- Phase 1A 来源证据、许可核验和 RoBoflow CSS v27 冻结决策
- G1A-1 至 G1A-11 全部 PASS
- pytest 110 项测试通过
- compileall 成功
- git diff --check 成功
- P1B 离线 `inspect` / `snapshot` / `verify` 工具、Manifest 和
  image-label pairing 校验能力
- P1B 合成 fixture 与离线单元测试；默认 pytest 不依赖真实 CSS 下载
- P1B 真实下载目录已复制到 Git-ignored `data/external/css-v27-yolov8/source/`
  并冻结为不可变快照
- 真实 Manifest、counts、source.json 和精简 snapshot summary 已生成
- 离线测试覆盖 snapshot、manifest、pair validation、verify 和治理文档
- pytest 125 项测试通过
- ADR-010、RISK-015、`CSS-V1.1 Candidate` 和 freeze-correction 治理测试
- P1B.2 candidate comparison、ADR-011 选择标准与候选治理测试
- P1B dataset freeze completed
- ADR-012、`CSS-PPE-10-V1` 冻结决策与 P1B-F1 至 P1B-F5 治理门禁
- P1C-0 class mapping design、ADR-013、RISK-016 和 A/B/C 影响分析
- P1C-1 Strategy C mapping decision、ADR-014 和 7 类 training contract
- P1C-2 frozen mapping contract、deterministic conversion service、离线测试和
  Git-ignored processed dataset
- P1D-0 quality validation plan、observation-only validator、deterministic
  metric helpers、thresholds、offline tests、ADR-015 和 RISK-017
- P1D-1 真实 payload-only validation；structure PASS、2,799 images / 2,799
  labels、30,375 boxes、0 invalid bbox、0 exact image duplicate、5 个 dHash
  candidate pairs、2 个 perceptual cross-split candidate groups
- P1D-1 生成 `docs/17_DATASET_QUALITY_REPORT.md` 和 Git-ignored
  `data/processed/css-ppe-10-v1/metadata/quality_report.json`
- P1E-0 dataset training contract、experiments 目录、EXP-001 baseline 模板、
  augmentation 模板、training config schema、训练策略文档和治理测试
- P1E-0 ADR-016、RISK-018 和 G1E0-1 至 G1E0-7 全部 PASS；未下载权重、
  未执行训练、未修改 dataset
- P1E-1 contract audit、experiment config audit、environment audit、
  reproducibility checklist 和 EXP-001 training runbook
- P1E-1 确认 canonical experiment ID 唯一为 `EXP-001`，训练配置仍为
  `execution_enabled: false`，未冻结参数继续保持 `PENDING_DESIGN_REVIEW`
- P1E-1 环境审计发现 PyTorch/Ultralytics 未安装、CUDA 不可用且未检测到
  NVIDIA GPU；记录为 `NOT READY FOR TRAINING`，未安装依赖或下载权重
- P2-0 环境基线复核、依赖方案比较、版本兼容矩阵和 training readiness
  checklist 已生成；六个 P2-0 gates 全部 PASS
- P2-0 确认当前主机无 NVIDIA GPU、CUDA 不可用，PyTorch/Ultralytics 未安装；
  推荐后续在具备 NVIDIA GPU 的本地/WSL2 环境或受控 cloud GPU 中完成 P2-1
  环境搭建，CPU fallback 仅作为诊断路径
- P2-0 再次验证 source `data.yaml`、source manifest 和 processed manifest
  三个 SHA-256 与 training contract 一致，processed class order 保持不变
- P2-1 选择 `D. Controlled Cloud GPU` 作为 EXP-001 训练环境架构，原因是当前
  主机无法提供 NVIDIA GPU/CUDA；本地 CPU、本机 GPU 升级和 WSL2 CUDA 均不能
  在当前状态直接形成可复现 GPU baseline
- P2-1 生成 environment decision、dependency specification 和 setup plan，
  记录 Python 3.11.16、PyTorch 2.11.0+cu128、CUDA 12.8、torchvision
  0.26.0+cu128、Ultralytics 8.4.158 和 NumPy 2.2.6 等 planned versions
- P2-1 记录安装顺序、non-training verification commands、rollback 与
  environment freeze requirements；没有任何依赖、权重或云实例被创建
- P2-2 完成 cloud environment review，逐项记录 provider、region、GPU、
  VRAM、CUDA capability、OS image、storage、cost 和 retention 均为
  `PENDING_SELECTION`
- P2-2 完成 dependency freeze review，确认 Python/PyTorch/CUDA/torchvision/
  Ultralytics/NumPy planned versions 均未安装，dependency freeze 保持
  `PENDING`
- P2-2 完成 EXP-001 execution review：dataset、model、7-class mapping、
  output/logging paths 和 8 项 metrics 已复核，所有冻结身份未修改；
  seed、hyperparameters、weights、device 和 runtime fingerprint 仍未解决
- P2-2 生成 training authorization checklist；Dataset、Mapping、Experiment
  为 PASS，Environment、Dependencies、GPU 为 PENDING，Authorization 为
  `NOT GRANTED`
- P2-3 比较 AutoDL、阿里云 GPU ECS、腾讯云 GPU 和 RunPod/Vast.ai 等方案，
  记录 GPU、VRAM、CUDA、Ubuntu 镜像、成本规划区间、数据上传方式和风险
- P2-3 选择 AutoDL + RTX 4090 24GB 作为成本受控设计目标，规划上限为
  40 GPU-hours 和 CNY 150；RTX 3090 24GB 只作为 contingency，不得冒充同一
  runtime
- P2-3 确认 Ubuntu 18.04 不满足 planned `manylinux_2_28` wheel 的 glibc
  要求；providers 必须提供 Ubuntu 20.04 或兼容的 glibc 2.31+ Linux
  userland
- P2-3 更新 P2-2 authorization checklist 的 Environment/GPU 状态为
  `DESIGN SELECTED / NOT PROVISIONED`，Authorization 保持 `NOT GRANTED`
- P2-3 未创建云实例、未安装依赖、未下载权重、未上传 dataset、未训练、
  未修改 dataset 或 EXP-001 frozen identity
- P2-3 验证：pytest `174 passed`；compileall 成功；`git diff --check` 成功；
  Charter diff 为空
- P2-4-G3/G4 与 final provisioning gate 完成：AutoDL RTX 4090 runtime、
  `ppe-exp001` dependencies、dataset transfer、7-class mapping 和 full
  manifest integrity 均验证；Environment/Dataset READY
- P2-5 完成 EXP-001 authorization review；结果为 `BLOCKED`，并记录配置参数、
  权重二进制、环境 freeze 和人工授权缺失项
- P2-5.1 完成 EXP-001 configuration freeze：记录 model、dataset、class count、
  `imgsz`、epochs、batch、optimizer、LR strategy、seed、device、workers 和
  output path；配置 SHA256 已记录，`execution_enabled: false` 保持不变
- P2-5.1 未下载权重、未训练、未修改 dataset 或 mapping；weight binary
  SHA256、完整 dependency freeze 和 explicit training authorization 仍待完成
- P2-5.1 验证：pytest `175 passed`；compileall 成功；`git diff --check`
  成功；Charter diff 为空
- P2-5.2 从 Ultralytics assets `v8.3.0` 获取官方 `yolo11n.pt`，验证
  `5,613,764` bytes、MD5 content header、ZIP/PyTorch 结构和 SHA256
  `0ebbc80d...7644ee1`
- P2-5.2 创建 `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` 和
  `P2-5.2_WEIGHT_REGISTRATION_REPORT.md`；二进制保持 Git-ignored，未训练、
  未修改 dataset、mapping 或 EXP-001 配置
- P2-5.3 导出 `ppe-exp001` 的完整 conda environment、conda explicit URLs 和
  pip freeze lock；记录 RTX 4090 UUID、driver、CUDA API/runtime、cuDNN、
  Python、PyTorch 和 Ultralytics fingerprint
- P2-5.3 三个 lock 与远端当前输出逐行匹配，`pip check` 为 PASS；生成
  `P2-5.3_DEPENDENCY_FREEZE_REPORT.md` 和 `locks/EXP-001/runtime-fingerprint.yaml`
- P2-5.4 将登记后的 `yolo11n.pt` 传输到
  `/root/autodl-tmp/models/pretrained/yolo11n.pt`；传输前确认目标不存在，
  未覆盖已有文件
- P2-5.4 远端文件存在、大小为 `5,613,764` bytes，SHA256
  `0ebbc80d...7644ee1` 与本地一致；生成
  `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md`
- P2-5.4 未启动训练、未执行模型、未修改 dataset、mapping 或 EXP-001
  canonical configuration；training authorization 保持 `NOT GRANTED`
- P2-5.4 验证：pytest `179 passed`；compileall 成功；`git diff --check`
  成功；Charter diff 为空
- P2-5.5 在明确人工授权后执行一次 EXP-001 YOLO11n baseline 训练；训练
  于 `2026-09-22T08:00:02Z` 开始，`2026-09-22T08:19:29Z` 完成，95 个 epoch
  后由 `patience: 20` 提前停止，最佳 epoch 为 75
- P2-5.5 产生 `best.pt`、`last.pt`、training log、resolved args、
  `results.csv`、confusion matrix、曲线、run record 和 frozen config
  snapshot；全部运行产物保持 Git-ignored
- P2-5.5 验证结果为 precision `0.899`、recall `0.649`、mAP50 `0.767`、
  mAP50-95 `0.480`；最佳 checkpoint SHA256
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`
- P2-5.5 生成 `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`；M-004
  更新为 `已经实现`，M-005 保持 `待实现`
- P2-5.5 完成且无训练进程、GPU 利用率为 `0 %` 后，已向 AutoDL 实例发出
  shutdown；未删除远端 dataset、权重或训练产物

## In Progress

Phase 1 — Data Engineering。P1A 已完成；P1B 已冻结 `CSS-PPE-10-V1`；
P1C-0、P1C-1 与 P1C-2 已完成。P1C-2 已从不可变 source 生成 7 类 processed
dataset，人工审核结果为 PASS。P1D-0 已完成设计框架；P1D-1 已完成真实质量
扫描并生成报告：payload hash 前后一致，structure PASS，10 个 P1D-1 gates
全部 PASS。P1E-0 已完成设计门禁；P1E-1 已完成训练前审查并通过 G1E1 系列
门禁。当前仍保留 M-001 的数据治理语义项和 P1D-1 perceptual leakage
candidate 风险，因此 Phase 1 继续记为 `实现中`。

Phase 2 已完成 EXP-001 baseline 训练和实验归档。P2-0 至 P2-4 已完成环境
准备与 provisioning；P2-5.1 至 P2-5.4 完成 configuration、dependency、
weight 和 remote-copy freeze/verification；P2-5.5 使用一次性授权完成
训练。授权记录现为 `CONSUMED`，不能用于第二次运行。

## Pending

- Phase 3 模型评估、对照实验和 M-005 独立验收
- M-001 的数据治理语义确认，以及 P1D-1 perceptual split-leakage
  candidates 的解释或后续 dataset version 决策
- 尚未实现的 MUST：M-001 至 M-003 的最终验收，以及 M-005 至 M-026
- 所有 E-001 至 E-012 扩展能力
- 任何新的训练运行；`EXP-001` 的一次性授权已经消费，第二次运行必须使用
  新 experiment ID、新 authorization 和新的空输出目录

## Known Issues

- PyTorch 尚未安装，Phase 0 不会因此失败；Phase 2 前需完成环境选型。
- `ppe_compliance_detection` 当前默认分支未发现 LICENSE 或 COPYING 文件，
  在任何代码复用前必须单独复核。
- `ultralytics` 当前许可证为 AGPL-3.0；正式交付和分发前必须完成许可义务评估。
- Teacher checkpoint 的五类名称与本项目锁定五类语义不同，映射保持
  `UNVERIFIED`。
- 老师参考包包含 `history.db`，并可能包含凭据；不得复制或提交其中内容。
- CSS 源项目存在版本漂移；V1 固定使用 Roboflow v27，不能使用移动的项目
  级数量或未经证明对应的 Kaggle 镜像替代。
- v27 含增强配置，后续重复检测和 split 泄漏检查不可跳过。
- P1C-2 输出位于 Git-ignored `data/processed/css-ppe-10-v1/`，只能提交代码、
  契约、metadata 生成逻辑、文档和测试；不得提交 2,799 张 processed 图片。
- Processed `checksums.sha256` 采用常见的“不含自身”约定；它记录其余
  5,602 个输出文件。
- P1D-1 检出 2 个跨 split 的 dHash candidate groups；它们只是风险证据，
  不代表已确认污染，也不得自动删除或重划分数据。
- P1D-1 检出 hardhat、no_hardhat、vest、vehicle 的 HIGH small-object
  risk，以及最大/最小类别计数比约 `6.20`；后续训练评估必须保留 per-class
  metrics 和小目标关注。
- P1D-1 检出 32 个空标签，按 image-without-object 保留，未删除。
- P1E-1 的 `PENDING_DESIGN_REVIEW` 状态已由 P2-5.1 configuration freeze
  取代；canonical EXP-001 参数现已冻结。该 canonical 文件保持
  `execution_enabled: false`，本次运行使用一次性 external authorization。
- 本地 Windows 主机没有 PyTorch、Ultralytics 或可用 CUDA/NVIDIA GPU；
  AutoDL `ppe-exp001` 已具备 CUDA 12.4 和 RTX 4090，dataset 已传输并通过
  integrity verification；P2-4 final gate 为 PASS。配置参数已由 P2-5.1
  冻结；依赖已由 P2-5.3 锁定；远端权重副本已由 P2-5.4 验证；P2-5.5 已
  完成一次授权训练。
- P2-0 的版本矩阵仍将 Python、PyTorch、CUDA、Ultralytics 和 YOLO11
  权重来源标记为待验证；仓库中的 `ultralytics>=8.3,<9` 不是训练执行版本
  freeze。
- P2-0 推荐的完整训练路径是具备 NVIDIA GPU 的本地/WSL2 环境或受控 cloud
  GPU；当前主机只有 Intel Iris Xe，CPU fallback 不能视为等价 GPU baseline。
- P2-1 已记录 controlled cloud GPU architecture；P2-3 选择 AutoDL 和
  RTX 4090 24GB，P2-4-G3 已在实例 `bcb849a74f-38320766` 上安装验证
  `ppe-exp001`。P2-4 runtime、依赖和 dataset fingerprint 已验证；live
  price、storage 和 retention 继续按 provider risk 管理。
- P2-1 dependency specification 仍是 PLANNED VERSION；P2-4-G3 的实际
  Ultralytics 版本为 `8.4.157`，因此不能把 planned `8.4.158` 写成已安装
  版本。P2-4 已记录并验证 resolved dependency fingerprint；EXP-001
  执行时使用该 resolved runtime。
- Cloud GPU 将引入成本、数据上传、凭据、网络和实例保留风险；P2-2 必须先
  审核这些边界，且不得把凭据或数据写入 Git。
- P2-3 已选择 AutoDL + RTX 4090 24GB；P2-4-G3 已在用户提供的实例上完成
  isolated dependency provisioning 和 CUDA 验证。live price、storage 和
  retention 继续按 provider risk 管理；实例保留、停止或销毁需要人工决定。
- P2-4-G4 已将 `data/processed/css-ppe-10-v1/` 原样传输到
  `/root/autodl-tmp/datasets/css-ppe-10-v1/`，未修改 labels、`data.yaml`、
  annotation、class mapping 或 EXP-001 configuration；远端 metadata manifest
  5,602 项和 full 5,604 项 checksum 均 PASS。
- P2-2 dependency freeze review 记录的是历史 `PENDING` 状态；P2-4-G3 已
  安装并验证实际依赖，P2-4-G2 已记录 runtime fingerprint，P2-4 final gate
  为 PASS。
- P2-5.1 已冻结 EXP-001 的 model、dataset、class count、image size、batch、
  epochs、optimizer、learning rate/LR strategy、augmentation、seed、device、
  workers 和 output paths；`execution_enabled` 仍为 `false`。
- P2-5.2 已登记官方 Ultralytics `yolo11n.pt` 初始化权重，记录
  `5,613,764` bytes、MD5 和 SHA256 `0ebbc80d...7644ee1`；二进制保持
  Git-ignored。
- P2-5.3 已冻结 conda/pip 依赖和 runtime fingerprint；`pip check` PASS，
  lock 与远端环境逐行匹配。AutoDL 未通过实例接口暴露 immutable image
  digest；raw pip lock 保留 pip 自身镜像构建机 origin，portable pip pin
  以 conda lock 的 `pip=26.2.1` 为准。
- P2-5.4 已将 `yolo11n.pt` 传输到
  `/root/autodl-tmp/models/pretrained/yolo11n.pt`，远端存在性、文件大小和
  SHA256 均与本地一致；远端校验报告为
  `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md`。
- P2-5.5 的训练日志披露 Ultralytics AMP 自检自动获取了 `yolo26n.pt`；日志
  明确标记该文件仅用于 one-time AMP check，不是训练初始化权重，也未替代
  冻结的 `yolo11n.pt`。
- EXP-001 的 validation metrics 来自训练运行，可作为 M-004 实验归档证据，
  但不能替代 Phase 3 的独立 M-005 evaluation。
- Fast training produced a best epoch at 75 with overall recall `0.649` and
  `no_hardhat` mAP50-95 `0.327`; Phase 3 must retain per-class analysis and
  the P1D-1 small-object and perceptual-leakage risks.

## Blockers

- P1E-1 review 无 execution blocker；P2-5.1 已解除配置参数未决 blocker，
  P2-5.3 已解除 dependency-freeze blocker，P2-5.4 已解除 remote weight
  transfer blocker；P2-5.5 已完成一次授权训练。
- P2-0 未解决的本地硬件和依赖 blocker 已由受控 AutoDL 路径规避；P2-4-G3
  已完成实际依赖安装和 CUDA verification。
- P2-1/P2-3 的 architecture/provider selection blocker 已解除；P2-4
  environment 和 dataset blockers 已解除；P2-5.1 已解除参数冻结 blocker。
  P2-5.2 已解除本地 weight binary provenance/hash blocker；P2-5.4 已解除
  远端权重副本 blocker；P2-5.5 已消费单次 authorization。
- 历史 CSS-V1 metadata mismatch 继续作为审计记录保留；ADR-012 已选择并以
  artifact fingerprint 冻结 `CSS-PPE-10-V1`，因此不再阻塞 conversion。
- P1D-1 已完成 exact/perceptual duplicate、坏样本、坐标范围和 split 泄漏
  审计；任何修复或重划分必须进入新的 dataset version，不能原地修改。

## Next Allowed Step

当前停留在 P2-7 Training Result Freeze，结果冻结已完成，等待新的用户指令。
本任务不授权进入 Phase 3、evaluation、第二次训练、dataset/mapping 修改或新 experiment。

M-004 已由 `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md` 的证据满足并
标记为 `已经实现`。M-005 保持 `待实现`；M-001 也保持 `待实现`，因为其
最终治理边界仍需独立处理。
