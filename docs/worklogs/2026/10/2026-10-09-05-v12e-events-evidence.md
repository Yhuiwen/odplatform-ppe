# V1.2-E 离线事件与关键证据交接

Changed: Collector、PNG证据适配；扩展视频observer工厂、任务失败/重启清理、只读API和导出；安全图片ImportError转换；CFR仅增诊断。新增E测试，保留B/C/D改动。

Reason: 在单次视频YOLO推理上实现冻结跟踪/关联/时序事件和任务隔离的双图取证。

Validation: 联合107 PASS/349.91秒；冻结819 PASS/10独立API文件跳过；Vue11 PASS/build PASS；47/570真实链路、SQLite/PNG/CSV/ZIP与告警隔离PASS。实际8773 Uvicorn自检PASS，子进程释放。

Evidence: [E报告](../../../reports/v1.2/V12_E_EVENTS_EVIDENCE_REPORT.md)；忽略目录artifacts/validation/v12e/<47或570>/<job_id>/包含实际视频、PNG、JSON/CSV和runtime_metrics；ZIP在临时测试目录验证。

Risk: 联合测试曾在推理前CFR拒绝570帧，同一上传指纹和五次严格重检、最终联合通过；根因未证实，不宣称修复。P9-C PARTIAL/FROZEN，有限RSS采样和耗时对比不关闭长期风险。同步算子检查点取消，跨任务根目录无全局资源锁，标签局部重叠。

Not Verified: FullHD/4K/600秒长期性能、长期资源稳定性；F前端未实施。用户8768旧服务未重启，需审核后加载新代码。

Next Step: HUMAN REVIEW PENDING。D已由用户本次授权确认审核通过。E停止，不自动进入F；没有commit/push/tag。

Validation 补充: 文档与资产门禁52 PASS（46.47秒）；最终compileall/diff检查通过，冻结指纹一致，生成资源不入Git，HEAD保持不变。
