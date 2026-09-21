# Risk Register

Status values: `OPEN`, `MITIGATED`, `MONITORING`, `CLOSED`.

| ID | Risk | Probability | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| RISK-001 | 两周周期紧张 | High | High | 严格按 Phase Gate 推进；优先保障 MUST；提前记录阻塞；避免跨阶段开发 | OPEN |
| RISK-002 | 数据集类别不完全一致 | High | High | 已冻结 Roboflow CSS v27；其 25 个源类别包含 Person、Hardhat、NO-Hardhat、Safety Vest、NO-Safety Vest，其余类别必须在 Phase 1C 显式映射、丢弃并统计 | OPEN |
| RISK-003 | 多源数据潜在重复 | Medium | High | MD5 精确去重 + perceptual hash 近重复检查 + 人工抽样复核 | OPEN |
| RISK-004 | PPE 遮挡导致漏检 | High | High | 数据增强、困难样本分析、置信度与未关联分类处理；报告限制 | OPEN |
| RISK-005 | Person-PPE Association 错配 | High | High | 使用 IoU/包含关系/人体区域约束；小目标边界测试；输出未关联结果 | OPEN |
| RISK-006 | 视频单帧检测抖动导致假告警 | High | High | 连续帧/持续时间确认、恢复规则、冷却和事件去重 | OPEN |
| RISK-007 | GPU/显存不足 | Medium | High | 自适应 batch、冻结/较小模型、CPU 小样本验证；集中记录环境 | OPEN |
| RISK-008 | RTSP 不稳定 | High | Medium | 超时、重连、帧丢弃策略和可观察状态；不得伪造正常流 | OPEN |
| RISK-009 | LLM API 不可用 | Medium | Medium | 本地模板降级、超时和错误状态；报告明确数据来源 | OPEN |
| RISK-010 | 开源许可证误用 | Medium | High | 逐版本检查 LICENSE；默认不复制；复用前记录来源并复核义务 | OPEN |
| RISK-011 | Teacher checkpoint class semantics are not fully verified | Medium | High | 不直接将 head 等同于 no_hardhat；不直接将 ordinary_clothes 等同于 no_vest；获取老师数据说明或通过受控实验验证；保持本项目五类定义不变 | OPEN |
| RISK-012 | Teacher reference package contains credentials or non-project artifacts | Confirmed / High | High | teacher zip 不进入 Git；best.pt 不进入 Git；history.db 不进入 Git；API key 不复制；.env / secret management 后续独立实现；如发现真实有效 Key，视为已暴露，不使用 | OPEN |
| RISK-013 | Dataset license/source provenance ambiguity | Medium | High | 仅使用 Roboflow 原始项目冻结的 v27 作为 V1 源；Kaggle 镜像不做基线；保留许可、署名和修改说明；原始数据不提交 Git；公开再分发前复核底层图像权利与隐私边界 | MONITORING |
