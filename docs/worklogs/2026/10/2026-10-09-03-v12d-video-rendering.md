# V1.2-D 视频渲染交接

Changed: 新增 offline/video_processor.py、video_encoder.py、video_probe.py，扩展现有 worker/jobs、FastAPI 生命周期/capabilities/elapsed、视频统计和恢复；新增28项视频单元测试、真实47/570帧链路及重启API测试。同步报告、README、Phase 9、当前状态、Changelog、门禁与开源记录。B/C全部未提交工作保留。

Reason: 实现授权的原分辨率逐帧 MP4 推理和高质量 H.264 导出，复用冻结模型和现有渲染器，不改事件规则。

Validation: 联合API67 PASS；另一次非模型65 PASS含新恢复用例，68个不同测试有通过证据；视频专项最终28 PASS。冻结全量复验819 PASS/7独立API文件跳过；前端11 PASS/build PASS；文档同步后治理/资产专项52 PASS；compileall/diff/指纹/凭据模式/忽略检查PASS。实际独立Uvicorn健康/能力自检、两段浏览器完整播放通过，临时服务已关闭。

Evidence: [D报告](../../../reports/v1.2/V12_D_VIDEO_RENDERING_REPORT.md)；本地忽略路径 artifacts/validation/v12d/47、570 保存真实MP4/JSONL/摘要/验证/指标，playback.png保存播放截图。额外ZIP保留在仓库旁 odplatform-ppe-v12d-validation/47、570。全部五项产物通过HTTP下载与SHA/CRC校验。

Risk: P9-C保持PARTIAL/FROZEN。父进程RSS采样和570→47顺序任务不证明长期稳定性；同步模型算子只能在检查点取消。不同任务根目录不具有全局资源准入。旧P1资产门禁对仓库ZIP较宽泛，验证ZIP须隔离，未放宽门禁。初轮曾出现时序拒绝，单线程严格探测后真实链路通过，根因未单独证实。

Not Verified: 真实FullHD YOLO、4K/600秒性能、长期资源稳定性。VFR/旋转/奇数尺寸不支持。E事件分析和Vue离线页未实现。

Next Step: HUMAN REVIEW PENDING；用户审核D后另行授权E。本次没有commit/push/tag；模型/配置/检测与合规规则不变。
