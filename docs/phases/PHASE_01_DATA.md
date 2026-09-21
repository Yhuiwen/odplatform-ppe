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
| P1B | Download & Raw Snapshot | 待实现 | 必须按 ADR-009 下载 Roboflow CSS v27，记录哈希与来源 |
| P1C | Class Mapping & Conversion | 待实现 | 仅按 Charter 锁定五类映射并显式处理其余类别 |
| P1D | Deduplication & Quality Validation | 待实现 | 精确重复、近重复、坏样本、坐标与 split 泄漏检查 |
| P1E | Dataset Freeze & Report | 待实现 | 生成冻结清单、机器可读报告和 Markdown 数据质量报告 |

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
| P1-G1 | CSS 来源、许可证、版本和校验证据齐全 |
| P1-G2 | 五类映射严格匹配 Charter 顺序 |
| P1-G3 | Train/Val/Test 清单可复现且无交叉泄漏 |
| P1-G4 | 完整性、坐标、类别和重复检查测试通过 |
| P1-G5 | 数据质量报告可重复生成并通过人工复核 |

## 7. 已知问题

- CSS V1 已冻结为 Roboflow v27；Kaggle 镜像与 Roboflow 版本号不可混用。
- v27 含增强配置，Phase 1D 必须执行重复和近重复审计。
- CC BY 4.0 明确许可条件，但底层图像隐私/来源仍由 RISK-013 监控。
- 尚未下载、转换或生成任何 processed dataset。

## 8. 开发记录

- 2026-09-21: 计划建立，未开始实现。
- 2026-09-21: P1A 完成来源与许可 Gate；选择 Roboflow CSS v27，
  `yolov8` 导出机制；未下载数据，未进入 P1B。
