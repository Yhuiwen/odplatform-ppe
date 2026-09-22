# Phase 01 — Data

## 1. 阶段目标

【LOCKED】数据获取、格式统一、质量检查、数据报告。

## 2. 进入条件

- Phase 0 Gate 全部 PASS。
- 用户批准开始数据工程和相应的数据下载/许可范围。

## 3. 当前子任务

| Subphase | Scope | Status | Evidence |
| --- | --- | --- | --- |
| P1A | Source & License Gate | 已经实现 | G1A-1 至 G1A-11 PASS；来源、许可、版本、类别、split 和下载机制已记录 |
| P1B | Download & Raw Snapshot | 已经实现 / FROZEN | Roboflow API v27 导出已完整复制为 2,799 图 / 5,601 文件不可变快照，并冻结为 `CSS-PPE-10-V1` |
| P1B.1 | Dataset Freeze Correction | 已经实现 | ADR-010 已定义 artifact fingerprint；历史 CSS-V1 保留为 rejected / blocked 记录 |
| P1B.2 | Dataset Candidate Decision Gate | 已经实现 | `docs/11_DATASET_CANDIDATE_EVALUATION.md` 对比 CSS-V1 与 CSS-V1.1；ADR-011 定义 V1 选择标准 |
| P1B.3 | Final Dataset Freeze Decision | 已经实现 / FROZEN | `docs/12_DATASET_FREEZE_DECISION.md` 选择并冻结 `CSS-PPE-10-V1`；ADR-012 固化 artifact fingerprint identity |
| P1C-0 | Class Mapping Design Gate | 已经实现 | `docs/13_CLASS_MAPPING_DESIGN.md` 分析 A/B/C；ADR-013 要求 conversion 前冻结 mapping |
| P1C-1 | Class Mapping Decision Gate | 已经实现 / FROZEN | `docs/14_CLASS_MAPPING_DECISION.md` 选择 Strategy C；ADR-014 固化 7 类 mapping |
| P1C-2 | Dataset Conversion Implementation | 已经实现 / PASS | frozen contract + deterministic service 生成 7 类 processed dataset；P1C-2 已生成未跟踪的 processed dataset |
| P1C | Class Mapping & Conversion | 已经实现 | Strategy C mapping 已转换；7 类输出、图片 SHA-256 与原样复制已验证 |
| P1D-0 | Dataset Quality Validation Design | 已经实现 / DESIGN FROZEN | `docs/16_DATASET_QUALITY_PLAN.md`、read-only validator、deterministic metrics 和 offline tests；真实 dataset 尚未执行 |
| P1D-1 | Real Dataset Quality Validation | 已经实现 / PASS | payload-only 前后 hash 一致；structure PASS；30,375 boxes；0 invalid bbox；5 dHash candidate pairs；2 perceptual cross-split candidate groups |
| P1D | Deduplication & Quality Validation | 已经实现 / QUALITY ASSESSED | 精确重复、近重复、坏样本、坐标与 split 泄漏检查已完成；风险已记录，未修改数据 |
| P1E-0 | Dataset Release & Training Preparation Design | 已经实现 / DESIGN FROZEN | release contract、experiments 结构、EXP-001 模板、config schema、training strategy 和 G1E0-1 至 G1E0-7；未训练 |
| P1E-1 | Baseline Training Preparation Review | 已经实现 / REVIEW PASS | contract/config/environment audit、reproducibility checklist 和 runbook；环境为 `NOT READY FOR TRAINING`；未训练 |
| P1E | Dataset Freeze & Report | 待实现 | P1E-0/P1E-1 review 已完成；最终 release 与训练执行准备尚未启动 |

## 4. 实现设计

使用可审计脚本完成源数据登记、类别映射、确定性划分、格式转换、精确和近
重复检测，并生成机器可读与 Markdown 报告。不得覆盖原始数据。

## 5. 测试要求

- 类别映射、坐标转换、缺失标签和坏样本边界测试。
- 重复检测、split 泄漏和确定性随机种子测试。
- 数据报告数字与处理后清单一致性测试。

## 6. Gate

| Gate | Requirement |
| --- | --- |
| P1A-G1 | CSS 来源、许可证、版本、类别、split 和下载机制证据齐全 |
| P1A-G2 | 未下载完整数据集，未进入 Phase 1B |
| P1B-G1 | Roboflow CSS v27 YOLOv8 API 导出快照、SHA-256 和来源记录齐全；无 ZIP 时明确记录 |
| P1B-G2 | Expected 2605/114/82/2801 与实际 artifact identity 核验通过 |
| P1B-G3 | 完整 Manifest 和精简 snapshot summary 已生成且不含机器绝对路径 |
| P1B-G4 | `data/external/` 仍被 Git ignore，未进入 P1C |
| P1B.1-G1 | 历史 expected/observed 差异保留且不修改 dataset |
| P1B.1-G2 | workspace、project、version、export format、data.yaml SHA256、class list、manifest SHA256、split counts 全部指纹化 |
| P1B.1-G3 | CSS-V1 freeze 在 expected != observed 时保持 blocked |
| P1B.1-G4 | P1C 保持未开始，M-001 保持待实现 |
| P1B.2-G1 | CSS-V1 与 CSS-V1.1 的来源、artifact fingerprint、数量、类别、PPE 相关性、优缺点和适用性均被记录 |
| P1B.2-G2 | V1 选择标准由 ADR-011 固化，不以最大类别数作为唯一依据 |
| P1B.2-G3 | CSS-V1 继续 blocked，CSS-V1.1 继续是未冻结 candidate，P1C 与 M-001 不变 |
| P1B-F1 | Dataset identity 已冻结为 `CSS-PPE-10-V1` |
| P1B-F2 | Artifact fingerprint 已完整记录 |
| P1B-F3 | 10 类导出类别列表已冻结 |
| P1B-F4 | Train/Valid/Test 实际 split counts 已冻结 |
| P1B-F5 | P1C 使用不可变 snapshot，未进入 P1C |
| P1C-0-G1 | Frozen dataset identity 与 fingerprint 保持不变 |
| P1C-0-G2 | 10 类原始数据、实例分布和 A/B/C 候选均被记录 |
| P1C-0-G3 | 每个原始类别的保留或丢弃 disposition 可审计 |
| P1C-0-G4 | Mask、scene classes、YOLO11 训练影响和后续系统影响均有分析 |
| P1C-0-G5 | 不写最终映射选择，不执行 conversion，不生成 processed dataset |
| P1C-0-G6 | ADR-013 与 RISK-016 已记录，Charter 和 M-001 状态不变 |
| P1C-1-G1 | Strategy C 被选择并记录完整 source-to-training mapping |
| P1C-1-G2 | 新 class IDs 唯一，前五类保持 ADR-003 顺序 |
| P1C-1-G3 | Mask、NO-Mask、Safety Cone 的 discard policy 明确 |
| P1C-1-G4 | source fingerprint 未修改，未生成 processed dataset |
| P1C-1-G5 | ADR-014 固化 mapping，RISK-016 记录 conversion 前冻结要求 |
| G1C2-1 | Conversion mapping contract 存在且由 `PPE-MAPPING-V1` 冻结 |
| G1C2-2 | Source `data.yaml` 与 manifest fingerprint 在转换前后保持不变 |
| G1C2-3 | Processed dataset、metadata 和 YOLO `data.yaml` 已生成 |
| G1C2-4 | Source/processed train、valid、test 图片数量一致 |
| G1C2-5 | Processed 图片逐文件 SHA-256 与 source 一致 |
| G1C2-6 | Label class ID 按冻结 mapping 正确转换，bbox 数值不变 |
| G1C2-7 | 每个 discarded class 的 box 数量已记录，不能静默丢失 |
| G1C2-8 | Processed `data.yaml` 为 7 类且不引用 external |
| G1C2-9 | Unknown class ID 被拒绝并记录为空 |
| G1C2-10 | 重复转换输出确定一致，metadata 不含时间戳或机器绝对路径 |
| G1C2-11 | 未开始训练、未下载权重、未进入 P2 |
| G1C2-12 | Charter 未修改，M-001 保持 `待实现` |
| P1D-0-G1 | Quality plan 存在并覆盖 Q1-Q9 与报告格式 |
| P1D-0-G2 | small/medium/large 阈值、small-object 风险阈值和 perceptual duplicate threshold 全部显式冻结 |
| P1D-0-G3 | Validator 只读，不提供自动修复或写回 API |
| P1D-0-G4 | 结构、类别分布、empty label、bbox、small object、exact duplicate、leakage 和 label consistency 指标可确定性计算 |
| P1D-0-G5 | 未对真实 processed dataset 执行 validator，未生成真实 quality report |
| P1D-0-G6 | Synthetic offline tests 全部通过且验证前后 dataset hash 不变 |
| P1D-0-G7 | ADR-015、RISK-017、P1D 未开始和 M-001 待实现状态已记录 |
| G1D1-1 | Payload scope 固定为 `data.yaml`、train/valid/test images 和 labels，排除 metadata/report |
| G1D1-2 | payload hash 在验证前后一致 |
| G1D1-3 | structure、目录、图片/标签数量和配对全部有效 |
| G1D1-4 | 每个 split 的 image、box、class 统计和 PPE 比例已生成 |
| G1D1-5 | 全部 label bbox 已完成 class、坐标和格式验证 |
| G1D1-6 | exact duplicate 和 perceptual dHash duplicate 分析完成 |
| G1D1-7 | exact 和 perceptual split leakage 分析完成 |
| G1D1-8 | Markdown 与机器可读 quality report 已生成 |
| G1D1-9 | 未修改 processed dataset payload |
| G1D1-10 | Charter 未修改，M-001 保持 `待实现` |
| G1E0-1 | Training release contract 存在并绑定 frozen dataset、mapping、classes、fingerprints 和 quality report |
| G1E0-2 | `experiments/` structure、baseline/augmentation templates 和 run/report retention files 存在 |
| G1E0-3 | Training config schema 存在：required fields、`EXP-\d{3}` ID 规则和非执行边界明确 |
| G1E0-4 | Required metrics 定义完整：mAP50、mAP50-95、precision、recall、per-class AP、confusion matrix、inference speed、model size |
| G1E0-5 | Dataset fingerprint 与 materialized source/processed artifact 一致，且未修改 dataset |
| G1E0-6 | 未执行训练、未下载权重、未生成 run output 或 checkpoint |
| G1E0-7 | Charter 未修改，M-001 保持 `待实现` |
| P1E1-G1 | Training contract、dataset id、processed path、mapping、class order/count、quality report、immutable boundary 和 fingerprints verified |
| P1E1-G2 | Experiment config 可解析，canonical ID 唯一，model/dataset/output/seed/device/hyperparameter state 已审计 |
| P1E1-G3 | Python、PyTorch、Ultralytics、CUDA、GPU、memory 和 readiness 已审计，未安装依赖 |
| P1E1-G4 | Reproducibility checklist 覆盖 dataset、experiment、runtime、artifacts 和复现步骤 |
| P1E1-G5 | `docs/reports/EXP-001_TRAINING_RUNBOOK.md` 已建立且明确 `DESIGN ONLY / TRAINING EXECUTION: NOT STARTED` |
| P1E1-G6 | 未执行训练、未下载权重、未生成 checkpoint 或 run output |
| P1E1-G7 | Charter 未修改，M-001 保持 `待实现` |
| P1-G1 | CSS 来源、许可证、版本和校验证据齐全 |
| P1-G2 | 五类映射严格匹配 Charter 顺序 |
| P1-G3 | Train/Val/Test 清单可复现且无交叉泄漏 |
| P1-G4 | 完整性、坐标、类别和重复检查测试通过 |
| P1-G5 | 数据质量报告可重复生成并通过人工复核 |

## 7. 已知问题

- CSS V1 的历史 metadata 记录保留为 rejected / `BLOCKED`；最终 V1 训练
  数据是 `CSS-PPE-10-V1`。
- v27 含增强配置，Phase 1D 必须执行重复和近重复审计。
- CC BY 4.0 明确许可条件，但底层图像隐私/来源仍由 RISK-013 监控。
- P1C-2 已生成 Git-ignored `data/processed/css-ppe-10-v1/`，但尚未通过
  P1D/P1E 最终质量与冻结审核。
- 实际快照为 train `2,603`、valid `114`、test `82`、total `2,799`，与
  P1A 冻结的 `2,605/114/82/2,801` 不一致；ADR-012 通过 artifact
  fingerprint 冻结实际导出，历史差异不得通过修改快照掩盖。
- 实际 `data.yaml` 为 10 类，而 P1A 记录的版本元数据为 25 类；五个目标
  语义均存在，冲突已作为 CSS-V1 历史记录保留，不再阻塞 P1C-2。
- `CSS-V1.1 Candidate` 已通过 P1B.3 和 ADR-012 冻结为 `CSS-PPE-10-V1`；
  P1C 可以使用该冻结输入，但不得修改 source snapshot。
- P1C-2 已实现 `PPE-MAPPING-V1` conversion；source fingerprint 保持不变，
  processed images 与原图片逐文件 SHA-256 一致。P1D/P1E 完成前不得训练。
- `prepare_dataset.py` 现在支持 `inspect`、`snapshot`、`verify` 和 `convert`；
  更深层的坐标/坏样本/重复质量验证仍保持 P1D 边界。
- P1D-0 已定义只读质量验证框架、阈值和 report 结构，但未执行真实数据集
  validation，也未生成真实 quality report；下一允许步骤是 P1D-1。
- P1D-1 已完成真实 payload 验证：`2,799` images/labels、`30,375` boxes、
  `0` invalid bbox、`0` exact image duplicate。dHash `<=5` 得到 `5` 个
  candidate pairs，其中 `2` 个跨 `valid/test`；仅记录风险，未删除或重划分。
- P1D-1 检出 hardhat、no_hardhat、vest、vehicle 的 HIGH small-object
  risk、约 `6.20` 的类别计数比和 `32` 个空标签。风险作为 P1E 输入。
- P1E-0 已建立 release contract、experiment structure、EXP-001 baseline
  template、augmentation template、training config schema 和训练策略文档；
  image size、batch、epochs、optimizer、learning rate、augmentation 与 seed
  仍是 `PENDING_DESIGN_REVIEW`，不得视为已冻结参数。
- P1E-1 已完成 contract/config/environment audit，并将 canonical experiment
  ID 唯一绑定到 `configs/training/exp001_baseline.yaml`；`experiments/
  configs/baseline.yaml` 仅为 template alias。
- P1E-1 环境审计结果为 `NOT READY FOR TRAINING`：PyTorch 和 Ultralytics
  未安装，CUDA 不可用，未检测到 NVIDIA GPU；本轮未安装依赖或下载权重。

## 8. 开发记录

- 2026-09-21: 计划建立，未开始实现。
- 2026-09-21: P1A 完成来源与许可 Gate；选择 Roboflow CSS v27，
  `yolov8` 导出机制；未下载数据，未进入 P1B。
- 2026-09-21: P1B 实现离线 source inspection、archive snapshot、deterministic
  manifest、file counts、pair validation 和 verify CLI；随后使用用户 Roboflow
  账号下载 v27 `yolov8` API 导出，复制为不可变外部快照。实际计数为
  `2,603/114/82/2,799`，`data.yaml` 为 10 类，和冻结期望不一致，因此
  P1B 保持实现中且验证失败。
- 2026-09-21: P1B.1 完成 dataset identity audit 治理修正：新增 ADR-010 与
  RISK-015，记录 expected/observed mismatch、`CSS-V1.1 Candidate` 和
  artifact fingerprint 要求；未修改 dataset，未进入 P1C。
- 2026-09-21: P1B.2 新增候选评估文档与 ADR-011，明确 V1 数据集选择优先
  可复现性、已验证 artifact identity、PPE 任务相关性、许可清晰度和训练
  可行性；CSS-V1 继续 blocked，CSS-V1.1 继续未冻结，未进入 P1C。
- 2026-09-21: P1B.3 完成最终数据集冻结决策：拒绝 CSS-V1，选择
  `CSS-V1.1 Candidate` 并冻结为 `CSS-PPE-10-V1`；新增 ADR-012 和
  P1B-F1 至 P1B-F5；未下载、未修改 dataset、未转换类别、未进入 P1C。
- 2026-09-21: P1C-0 建立 class mapping design gate：新增
  `docs/13_CLASS_MAPPING_DESIGN.md`、ADR-013 和 RISK-016，分析 A/B/C
  及系统影响；未选择 mapping、未转换 label、未生成 processed dataset。
- 2026-09-21: P1C-1 选择 Strategy C 并冻结 7 类 training mapping；前五类
  保持 ADR-003 顺序，新增 machinery/vehicle 作为 scene context；Mask、
  NO-Mask、Safety Cone 明确丢弃；未转换 label、未生成 processed dataset。
- 2026-09-21: P1C-2 新增 frozen mapping contract、deterministic conversion
  service、`convert` CLI 和 offline tests；从不可变 source 生成 7 类
  processed dataset。实际 counts 为 `2603/114/82`，保留 `30375` boxes，
  丢弃 `8460` boxes，unknown class IDs 为空；未训练、未 commit、未 push。
- 2026-09-21: P1D-0 新增 `docs/16_DATASET_QUALITY_PLAN.md`、
  `utils/quality_metrics.py`、`services/dataset_quality_service.py`、
  ADR-015、RISK-017 和 synthetic offline tests；冻结 small/medium/large、
  small-object risk 与 perceptual duplicate thresholds。未执行真实 dataset
  validation、未生成真实 quality report、未修改 dataset、未训练、未 commit、
  未 push。
- 2026-09-21: P1D-1 执行真实 dataset quality validation。Payload scope
  限定为 `data.yaml` 与 train/valid/test images/labels，前后 hash 为
  `bc762204...6237b` 且一致；structure PASS，bbox 全部有效，exact image
  duplicate 为 0，dHash `<=5` 得到 5 个 candidate pairs、2 个跨 split
  candidate groups。生成 `docs/17_DATASET_QUALITY_REPORT.md` 和
  Git-ignored `metadata/quality_report.json`；未修改数据、未训练、未 commit、
  未 push。G1D1-1 至 G1D1-10 全部 PASS；P1E 尚未开始。
- 2026-09-21: P1E-0 完成 Dataset Release & Training Preparation Design：
  新增 `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml`、
  `experiments/` 结构、`configs/training/schema.yaml`、
  `configs/training/exp001_baseline.yaml`、`docs/18_TRAINING_STRATEGY.md`、
  ADR-016、RISK-018 和 focused tests。未下载权重、未执行训练、未修改
  dataset/labels/data.yaml、未 commit、未 push；G1E0-1 至 G1E0-7 PASS。
- 2026-09-22: P1E-1 完成 Baseline Training Preparation Review：新增
  contract audit、experiment config audit、environment audit、
  reproducibility checklist 和 `EXP-001` training runbook；确认 fingerprints
  和 class order 不变，canonical experiment ID 唯一，环境为
  `NOT READY FOR TRAINING`。未安装依赖、未下载权重、未启动训练、未修改数据；
  P1E1-G1 至 P1E1-G7 PASS。下一允许步骤为
  `P2-TRAINING EXECUTION PREPARATION`，仍禁止训练。
