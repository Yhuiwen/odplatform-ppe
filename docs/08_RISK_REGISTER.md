# Risk Register

Status values: `OPEN`, `MITIGATED`, `MONITORING`, `CLOSED`.

| ID | Risk | Probability | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| RISK-001 | 两周周期紧张 | High | High | 严格按 Phase Gate 推进；优先保障 MUST；提前记录阻塞；避免跨阶段开发 | OPEN |
| RISK-002 | 数据集类别不完全一致 | High | High | 已冻结 Roboflow CSS v27；其 25 个源类别包含 Person、Hardhat、NO-Hardhat、Safety Vest、NO-Safety Vest，其余类别必须在 Phase 1C 显式映射、丢弃并统计 | OPEN |
| RISK-003 | 多源数据潜在重复 | Medium | High | MD5 精确去重 + perceptual hash 近重复检查 + 人工抽样复核 | OPEN |
| RISK-004 | PPE 遮挡导致漏检 | High | High | 数据增强、困难样本分析、置信度与未关联分类处理；报告限制 | OPEN |
| RISK-005 | Person-PPE Association 错配 | High | High | P5-2 已实现 containment/IoU/confidence、ambiguity margin 和显式 `unknown`，禁止 nearest-distance forced assignment；仍需 P5-3 使用真实检测/跟踪输出覆盖小目标、重叠和遮挡边界测试 | OPEN |
| RISK-006 | 视频单帧检测抖动导致假告警 | High | High | Phase 6 已实现连续 5 帧 + 1.0 秒确认、恢复、冷却和事件去重；P7-5 已通过短 MP4 runtime smoke path 验证链路，但只有一个 `PPE_UNKNOWN` 事件，仍缺真实多场景、长期运行和调参前证据 | OPEN |
| RISK-007 | GPU/显存不足 | Medium | High | 自适应 batch、冻结/较小模型、CPU 小样本验证；集中记录环境 | OPEN |
| RISK-008 | RTSP 不稳定 | High | Medium | P7-4 已实现 RTSP adapter、URI 脱敏、timeout 设置和连接失败状态；P7-5 未打开真实 RTSP endpoint，重连策略和断流恢复仍未验证 | OPEN |
| RISK-009 | LLM API 不可用 | Medium | Medium | 本地模板降级、超时和错误状态；报告明确数据来源 | OPEN |
| RISK-010 | 开源许可证误用 | Medium | High | 逐版本检查 LICENSE；默认不复制；复用前记录来源并复核义务 | OPEN |
| RISK-011 | Teacher checkpoint class semantics are not fully verified | Medium | High | 不直接将 head 等同于 no_hardhat；不直接将 ordinary_clothes 等同于 no_vest；获取老师数据说明或通过受控实验验证；保持本项目五类定义不变 | OPEN |
| RISK-012 | Teacher reference package contains credentials or non-project artifacts | Confirmed / High | High | teacher zip 不进入 Git；best.pt 不进入 Git；history.db 不进入 Git；API key 不复制；.env / secret management 后续独立实现；如发现真实有效 Key，视为已暴露，不使用 | OPEN |
| RISK-013 | Dataset license/source provenance ambiguity | Medium | High | 仅使用 Roboflow 原始项目冻结的 v27 作为 V1 源；Kaggle 镜像不做基线；保留许可、署名和修改说明；原始数据不提交 Git；公开再分发前复核底层图像权利与隐私边界 | MONITORING |
| RISK-014 | Generated augmentation may appear as perceptual near-duplicates | High | Medium | exact hash duplicates 单独统计；perceptual duplicates 仅报告；不自动删除 Roboflow 合法增强样本；删除数据必须在 P1D 有明确规则和证据 | OPEN |
| RISK-015 | Roboflow version metadata differs from materialized export artifact | High | High | 保留 API 导出原样和双份观测记录；按 ADR-010 绑定 workspace、project、version、export format、`data.yaml` SHA256、class list、manifest SHA256 和实际 split counts；在 P1C 前完成冻结修正；不得编辑 source、标签或 `data.yaml` 来强行匹配 | OPEN |
| RISK-016 | Incorrect class mapping reduces PPE compliance detection quality | Medium | High | evaluate mapping before conversion；freeze mapping decision；Mapping frozen before conversion.；keep original snapshot immutable；对每个原始类别记录 retained/discarded disposition；转换前建立可测试的 source-to-output mapping contract；ADR-014 固化 Strategy C | OPEN |
| RISK-017 | Dataset quality issues may affect model performance | Medium | High | evaluate before training；record risks；do not silently modify data；执行 P1D structure、class distribution、bbox、small-object、duplicate、leakage 和 label-consistency 检查；任何修复必须生成新 dataset version | OPEN |
| RISK-018 | Training experiments may become irreproducible without configuration tracking | Medium | High | experiment config；fixed dataset id；recorded metrics；ADR-016 要求所有实验由 immutable configuration 定义并保留 dataset fingerprint、环境、硬件、checkpoint 和 notes；禁止 command-line-only run 作为可复现记录 | OPEN |
| RISK-019 | Cloud GPU provider, image, price, and retention drift may invalidate the training environment | Medium | High | freeze provider/GPU design; require live-price check, image ID/driver/runtime fingerprint, budget ceiling, dataset transfer hash verification, external artifact backup, and remote-data cleanup before instance release | OPEN |
| RISK-020 | SQLite schema or migration drift makes event history unreadable | Medium | High | 使用 versioned migrations、`schema_migrations`、checksum、foreign keys、pre-migration backup 和 additive upgrades；P7-1 已实现 empty-database migration/checksum tests；P7 release 前仍需验证 deployed previous-version upgrade | OPEN |
| RISK-021 | Streamlit rerun/session behavior couples UI lifecycle to long-running inference | High | High | P7-3 已实现只读 dashboard query/service boundary 和 session-scoped read runtime，页面不拥有 inference/source loop；P7-5 已执行全部四个 Streamlit 页面和本地 server health/root check；长期 session lifecycle 和 monitoring integration 仍需验证 | OPEN |
| RISK-022 | USB Camera or RTSP source stalls, disconnects or returns stale frames | High | High | P7-4 已将 MP4/USB/RTSP 隐藏在 `VideoSource` 后，实现 observable state、timeout、credential redaction、connection failure 和 release cleanup；P7-5 已验证真实 USB open/read/close 和 injected disconnect，但真实 RTSP、bounded reconnect 与 stale-frame detection 仍待验证 | OPEN |
| RISK-023 | Evidence snapshots consume unbounded disk or lose their database reference | Medium | High | P7-2 已实现 date-partitioned relative paths、atomic write、SHA256/尺寸验证、event snapshot association、identical retry 去重和 conflict rejection；P7-5 已验证一个真实 runtime snapshot 的落盘和 integrity；database/file reconciliation、disk monitoring 和 documented retention/archive policy 仍待实现 | OPEN |
| RISK-024 | Web, Console or TTS delivery failure blocks or corrupts the event main path | Medium | High | persistence-first；P7-3 已实现 Console/Web adapter failure isolation、ordered fan-out 和 idempotency by `event_id`；P7-5 已验证两个 adapter 的实际 delivery path，TTS cooldown/failure isolation 仍未实现和验证 | OPEN |
| RISK-025 | Phase 6 event identity is lost or remapped inconsistently at the Phase 7 boundary | Medium | High | persist in-memory `event_id` at ingestion；`event_id` 作为 SQLite primary key 和 alert idempotency key；P7-3 duplicate delivery returns `skipped`；不改 frozen JSONL wire contract | OPEN |
| RISK-026 | Dashboard statistics diverge from event history | Medium | Medium | `events` 作为 source of truth；P7-3 直接从同一过滤条件聚合，不依赖 stale cache；P7-5 已用单事件 SQLite runtime 执行四页和统计查询，较大历史规模及长期一致性仍需验证 | OPEN |
