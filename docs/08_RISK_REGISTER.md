# Risk Register

Status values: `OPEN`, `MITIGATED`, `MONITORING`, `CLOSED`.

| ID | Risk | Probability | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| RISK-001 | 两周周期紧张 | High | High | 严格按 Phase Gate 推进；优先保障 MUST；提前记录阻塞；避免跨阶段开发 | OPEN |
| RISK-002 | 数据集类别不完全一致 | High | High | 在 Phase 1 建立审计映射表；对未知、冲突和丢弃类别保留统计 | OPEN |
| RISK-003 | 多源数据潜在重复 | Medium | High | MD5 精确去重 + perceptual hash 近重复检查 + 人工抽样复核 | OPEN |
| RISK-004 | PPE 遮挡导致漏检 | High | High | 数据增强、困难样本分析、置信度与未关联分类处理；报告限制 | OPEN |
| RISK-005 | Person-PPE Association 错配 | High | High | 使用 IoU/包含关系/人体区域约束；小目标边界测试；输出未关联结果 | OPEN |
| RISK-006 | 视频单帧检测抖动导致假告警 | High | High | 连续帧/持续时间确认、恢复规则、冷却和事件去重 | OPEN |
| RISK-007 | GPU/显存不足 | Medium | High | 自适应 batch、冻结/较小模型、CPU 小样本验证；集中记录环境 | OPEN |
| RISK-008 | RTSP 不稳定 | High | Medium | 超时、重连、帧丢弃策略和可观察状态；不得伪造正常流 | OPEN |
| RISK-009 | LLM API 不可用 | Medium | Medium | 本地模板降级、超时和错误状态；报告明确数据来源 | OPEN |
| RISK-010 | 开源许可证误用 | Medium | High | 逐版本检查 LICENSE；默认不复制；复用前记录来源并复核义务 | OPEN |
