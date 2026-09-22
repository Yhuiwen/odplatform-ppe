# Current Status

## Current Phase

Phase 1 — Data Engineering / Phase 2 Preparation

## Overall Status

Phase 1 实现中。P1A 已通过；P1B 已完成并冻结 `CSS-PPE-10-V1`。P1C-0、
P1C-1 和 P1C-2 已完成，Strategy C 的 7 类 training mapping 已冻结并生成
7 类 processed dataset。P1D-0 已完成 observation-only quality validation
设计与离线框架；P1D-1 已完成真实数据集质量验证并通过 G1D1-1 至
G1D1-10。质量扫描记录了 perceptual split-leakage candidates、small-object
risk、class imbalance 和 empty-label observations，但未修改数据。P1E-0
已完成 dataset release 与 training preparation 设计，包括 release
contract、experiment structure、配置模板和 G1E0-1 至 G1E0-7。随后已完成
P1E-1 Baseline Training Preparation Review：数据契约、实验
配置、环境、复现性清单和 EXP-001 runbook 均已审计，P1E1-G1 至 P1E1-G7
全部 PASS。当前环境为 `NOT READY FOR TRAINING`，训练尚未开始；M-001
仍为待实现，因为真实训练、权重、日志和可复现实验结果尚未产生。

Phase 2 仍为 `待实现`。P2-0 Training Environment Preparation 与 Dependency
Boundary Review 已完成：当前 Windows 主机没有 NVIDIA GPU，PyTorch 和
Ultralytics 均未安装，训练环境仍为 `NOT READY FOR TRAINING`。P2-0 仅记录
dependency strategy、version matrix 和 readiness boundary，未安装依赖、
未下载权重、未修改 dataset、未启动训练。

P2-1 已完成环境架构决策和设置方案：选择 `D. Controlled Cloud GPU`，记录
Python 3.11.16、PyTorch 2.11.0+cu128、CUDA 12.8、torchvision 0.26.0、
Ultralytics 8.4.158 等 `PLANNED VERSION`，并定义安装顺序、验证、回滚和
environment freeze 方案。当前仍未 provision cloud GPU、未安装依赖、未下载
权重、未执行训练；`Dependency Freeze` 仍为 `PENDING`。

P2-2 已完成训练执行授权审查：dependency freeze 仍为 `PENDING`；EXP-001
数据集、mapping、模型、class count、输出、logging 和 metrics 已复核。
P2-3 已完成 cloud provider selection 与 cost review：推荐 AutoDL 作为
成本受控方案，设计目标为 RTX 4090 24GB，并比较阿里云、腾讯云和其他方案。
该选择尚未 provisioning，region、host、image ID、driver、live price 和
retention policy 仍需人工确认。训练授权保持 `NOT GRANTED`，下一允许步骤是
`WAIT FOR HUMAN TRAINING AUTHORIZATION`。

## Current Subphase

P2-3 — Cloud Provider Selection & Cost Review

实现状态：COMPLETED / DESIGN SELECTION COMPLETE / AWAITING HUMAN REVIEW

数据修改：NONE

训练执行：NONE

环境决策：SELECTED — D. Controlled Cloud GPU

环境选择：SELECTED BY DESIGN — AutoDL / RTX 4090 24GB / NOT PROVISIONED

依赖冻结：PENDING

训练授权：NOT GRANTED

环境状态：NOT PROVISIONED / NOT READY FOR TRAINING

## Previous Subphases

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

- OS: Windows NT 10.0.22631.0
- Python: 3.13.6
- pip: 25.3
- Git: 2.51.2.windows.1
- PyTorch: not installed
- CUDA: unavailable
- Environment decision: D. Controlled Cloud GPU (selected, not provisioned)
- Planned training Python: 3.11.16 (not installed)
- Cloud provider and GPU SKU: AutoDL / RTX 4090 24GB (selected by design,
  not provisioned)
- Dependency freeze: PENDING
- Training authorization: NOT GRANTED

## Completed

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

## In Progress

Phase 1 — Data Engineering。P1A 已完成；P1B 已冻结 `CSS-PPE-10-V1`；
P1C-0、P1C-1 与 P1C-2 已完成。P1C-2 已从不可变 source 生成 7 类 processed
dataset，人工审核结果为 PASS。P1D-0 已完成设计框架；P1D-1 已完成真实质量
扫描并生成报告：payload hash 前后一致，structure PASS，10 个 P1D-1 gates
全部 PASS。P1E-0 已完成设计门禁；P1E-1 已完成训练前审查并通过 G1E1 系列
门禁。当前环境不满足训练执行条件，训练尚未开始。

Phase 2 仍处于准备状态：P2-0 设计与环境审计已完成，P2-1 环境架构与 setup
方案已记录，P2-2 authorization review 已完成，P2-3 已选择 AutoDL +
RTX 4090 24GB 作为设计目标。实际 provisioning、dependency freeze、runtime
verification 和 training authorization 尚未完成。

## Pending

- P2-3 provider/GPU 设计选择的人工批准，以及 region、host、image ID、
  driver、live price、storage 和 retention policy 的 provisioning 前确认
- 环境 provisioning、dependency installation/freeze、runtime fingerprint 和
  model weight provenance
- 全部 EXP-001 seed、hyperparameter、augmentation、device 和 weight 参数冻结
- P2 训练执行：只有 P2-2 审核通过、环境实际 provision 与验证完成，并取得
  独立执行授权后才允许启动
- 所有 M-001 至 M-026 业务能力
- 所有 E-001 至 E-012 扩展能力

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
- P1E-1 后，model version、weights、image size、batch、epochs、optimizer、
  learning rate、augmentation、seed、device 和 device strategy 仍是
  `PENDING_DESIGN_REVIEW`；不得视为已冻结训练参数。
- 当前环境没有 PyTorch、Ultralytics 或可用 CUDA/NVIDIA GPU，审计状态为
  `NOT READY FOR TRAINING`；本轮未安装依赖。
- P2-0 的版本矩阵仍将 Python、PyTorch、CUDA、Ultralytics 和 YOLO11
  权重来源标记为待验证；仓库中的 `ultralytics>=8.3,<9` 不是训练执行版本
  freeze。
- P2-0 推荐的完整训练路径是具备 NVIDIA GPU 的本地/WSL2 环境或受控 cloud
  GPU；当前主机只有 Intel Iris Xe，CPU fallback 不能视为等价 GPU baseline。
- P2-1 已记录 controlled cloud GPU architecture；P2-3 随后选择 AutoDL 和
  RTX 4090 24GB 设计目标，但 region、host、image ID、driver、live price 和
  retention policy 尚未确认。
- P2-1 dependency specification 是 PLANNED VERSION，不是已解析 lock；
  `Dependency Freeze` 保持 `PENDING`，不得把 planned version 用于训练声明。
- Cloud GPU 将引入成本、数据上传、凭据、网络和实例保留风险；P2-2 必须先
  审核这些边界，且不得把凭据或数据写入 Git。
- P2-3 已选择 AutoDL + RTX 4090 24GB，但 region、host、image ID、driver、
  live price、storage 和 retention policy 仍需在 provisioning 前记录并人工
  批准；provider selection 不等于 instance creation。
- P2-2 dependency freeze review 确认 planned dependency set 尚未安装；
  `Dependency Freeze: PENDING`，不存在 `pip freeze`、wheel installation 或
  runtime fingerprint。
- EXP-001 execution review 仍不 ready：seed、image size、batch、epochs、
  optimizer、learning rate、augmentation、device、device strategy、model
  version 和 weights 均为 `PENDING_DESIGN_REVIEW`。

## Blockers

- P1E-1 review 无 execution blocker；训练执行仍有 environment readiness
  blocker、未决训练参数和未获授权状态。
- P2-0 未解决硬件和依赖 blocker；P2-1 需要先完成环境选型、隔离安装和
  exact dependency verification。
- P2-1 已解决 architecture decision blocker，但实际 provisioning、provider
  选择、依赖安装、runtime fingerprint 和 model weight provenance 仍未完成。
- P2-3 review 无 provider-selection blocker；训练执行仍有 provider human
  approval、environment provisioning、dependency freeze、GPU verification、
  weight provenance、参数冻结和 authorization blockers。
- 历史 CSS-V1 metadata mismatch 继续作为审计记录保留；ADR-012 已选择并以
  artifact fingerprint 冻结 `CSS-PPE-10-V1`，因此不再阻塞 conversion。
- P1D-1 已完成 exact/perceptual duplicate、坏样本、坐标范围和 split 泄漏
  审计；任何修复或重划分必须进入新的 dataset version，不能原地修改。

## Next Allowed Step

下一允许步骤是 `WAIT FOR HUMAN TRAINING AUTHORIZATION`。在用户明确批准
AutoDL provider/GPU 选择、region、image、live price、budget 和 retention
policy，且完成环境 provisioning、dependency freeze、runtime verification、
weight provenance 和全部参数冻结前，不得创建实例、安装依赖、上传 dataset、
下载权重或启动训练。不得把 P2-3 selection design 解释为训练授权，也不得把
perceptual candidate 当作已确认 contamination 自动修复。

M-001 保持 `待实现`，因为可复现训练、权重、日志和验证结果尚未产生。
