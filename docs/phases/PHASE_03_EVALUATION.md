# Phase 03 — Evaluation

## 1. 阶段目标

【LOCKED】模型评估、对照实验、模型选择。

## 2. 进入条件

- Phase 2 Gate 全部 PASS。
- 至少存在一个可加载且来源可追踪的训练结果。

## 3. 当前子任务

P3-1 / M-005：EXP-001 best.pt 的独立 test evaluation 已完成，人工审核 PASS。
总体指标、5 类 PPE AP（另含 2 类 context AP）、confusion matrix、error analysis
和原始结果离线复算已实现。测试集 82 images / 561 boxes；评估记录 `EVAL-001`。
P3-G3：CMP-001 已完成 best.pt（epoch 75）与 last.pt（epoch 95）的同条件
checkpoint 对照。P3-G4 已形成 SEL-001 正式选择记录，保留 best.pt（epoch 75），
技术门禁 P3-G1～P3-G4 PASS，人工审核 PASS；Phase 3 已完成。

当前子阶段为 Phase 3 Release Freeze：发布证据已冻结，报告为
`docs/reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md`。Freeze COMPLETED；human review PASS；
M-005 正式状态同步为 `已经实现`。

## 4. 实现设计

使用固定测试集和统一后处理参数计算 Precision、Recall、mAP50、mAP50-95
及五类 AP；记录模型、数据、配置和命令以便复核。

## 5. 测试要求

- 指标结果结构和类别顺序测试。
- 固定结果 fixtures 的关键数值回归测试。
- 对照实验必须使用同一测试集并记录差异原因。

## 6. Gate

| Gate | Requirement |
| --- | --- |
| P3-G1 | 四项总体指标完整且可复核 |
| P3-G2 | 五类 per-class AP 完整且顺序正确 |
| P3-G3 | 对照实验条件一致、结论有证据 |
| P3-G4 | 选定模型有书面选择和限制说明 |

## 7. 已知问题

固定使用 CSS-PPE-10-V1 的 test split；P/R confidence=0.25、match IoU=0.5，
AP confidence floor=0.001、IoU=0.50:0.05:0.95。参数在实测前确定，没有 test tuning。
未设置部署质量通过阈值；本次只验收 M-005 指标完整性与可复核性。
保留 valid/test perceptual near-duplicate candidates、small-object 和不均衡风险。
老师模型类别语义未验证，不能直接当作同条件对照。

## 8. 开发记录

- 2026-09-21: 计划建立，未开始实现。

### P3-1 M-005 Evaluation Evidence

| Gate | Status | Evidence |
| --- | --- | --- |
| P3-G1 | PASS | 四项总体指标保存在报告与 JSON，可从 predictions.json 离线复算 |
| P3-G2 | PASS | person / hardhat / no_hardhat / vest / no_vest AP 顺序完整，另保留 context classes |
| P3-G3 | NOT EXECUTED | 本次只评估预先选定的 EXP-001 best.pt，未开展模型对照 |
| P3-G4 | PENDING REVIEW | best.pt 保持训练验证集选择结果；不宣称最优部署模型 |

- 2026-09-22：完成 M-005 evaluation pipeline 和真实 test evaluation；总体
  precision=0.798669、recall=0.712315、mAP50=0.733203、mAP50-95=0.465122。
- 报告：`PHASE_3_EVALUATION_REPORT.md`；JSON summary：
  `docs/reports/EXP-001_EVALUATION_SUMMARY.json`；raw artifacts：
  `artifacts/reports/EXP-001-evaluation/EVAL-001/`。
- 没有重训、dataset/mapping/weight 修改、新训练实验、Phase 2 release 修改、
  commit 或 push。M-005 技术证据等待人工审核；Phase 3 保持实现中。

### P3-G3 Checkpoint Comparison Evidence

- 2026-09-22：CMP-001 比较冻结的 EXP-001 best.pt 与 last.pt；两者重新使用同一
  ValService、test split、参数、代码和 runtime。原 EVAL-001 保留且 best 指标完全复现。
- P3-G3：PASS / AWAITING HUMAN REVIEW。报告：`P3_MODEL_COMPARISON_REPORT.md`；
  机器可读结果：`docs/reports/P3_MODEL_COMPARISON_SUMMARY.json`。
- last 的 mAP50-95 为 0.472776，best 为 0.465122；但 no_hardhat recall
  从 0.609756 降至 0.585366，Precision 从 0.798669 降至 0.781081。
  不将单项 mAP 增加解释为全面更优。
- 这是同一次训练的 checkpoint 对照，不是独立模型/架构实验；Teacher Baseline
  类别语义仍未验证，未进入本次定量对照。P3-G4 保持待审核，不改变原 best 选择。
- 测试与完整性检查见比较报告；未重训、未改变 Phase 2 产物，未 commit/push。

### P3-G4 Final Comparative Model Selection

- 2026-09-22：SEL-001 选择 `models/checkpoints/EXP-001/best.pt`（epoch 75），
  SHA256 `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`。
- 主要依据：保留原验证集选择；已有对照显示 PPE 相关指标存在取舍，没有充分
  证据支持替换。报告完整披露 last 的 AP、no_vest recall 和小目标 recall 优势。
- 选择报告：`P3_MODEL_SELECTION_REPORT.md`；机器可读记录：
  `EXP-001_RELEASE_MODEL.yaml`。仅新增选择记录，没有调整评估/训练参数或权重。
- P3-G4：PASS / AWAITING HUMAN REVIEW；P3-G1～G4 技术证据齐备。
  人工验收、Phase 3 发布及 Phase 4 授权仍未完成。
- 全量测试 213 passed / 1 skipped；清单身份与证据 SHA256 校验通过。

### Phase 3 Final Release Freeze

- 2026-09-22：冻结 EVAL-001、CMP-001、SEL-001 的报告、配置、实现、测试和
  运行产物哈希引用；选定模型保持 best.pt（epoch 75）。
- 最终报告：`docs/reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md`。P3-G1～P3-G4 技术 PASS；
  freeze COMPLETED / AWAITING HUMAN REVIEW，未执行 GitHub 发布。
- M-005 技术证据完整；Charter 正式状态未改写，等待人工验收。
- Phase 4 需完成 Phase 3 人工审核、确认选定模型及推理配置，并取得明确开始指令。
  当前只冻结评估配置，不把它视为已批准的生产推理配置。
- 无训练、新模型评估、dataset/mapping/weights 修改或 Phase 4 开发；未 commit/push。
