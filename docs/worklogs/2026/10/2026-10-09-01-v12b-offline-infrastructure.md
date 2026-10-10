# V1.2-B 离线任务基础设施交接

Changed: 新增 `offline/`、`api/offline.py`、独立 API 依赖锁与配置、测试；修改现有 FastAPI 生命周期和 `.gitignore`。

Reason: 为后续离线图片/视频分析提供安全上传、持久化状态机及受控产物基础。

Validation: 见 [实施报告](../../../reports/v1.2/V12_B_JOB_INFRA_REPORT.md) 和 [测试门禁](../../../05_TEST_GATES.md)。

Evidence: `tests/unit/test_offline_jobs.py`、`tests/integration/test_offline_api.py`、`offline/migrations/0001_jobs.sql`。

Risk: 生产处理器尚未实现；P9-C 资源生命周期仍为 PARTIAL；仅支持单进程本地 API。

Not Verified: 真实推理、H.264 编码、长时高负载、外部多用户访问。

Next Step: 人工审核 V1.2-B；获单独授权后再规划 V1.2-C。
