# V1.2-C 图片推理与原尺寸标注交接

Changed: 新增 `offline/image_processor.py`、图片统计数据库迁移与测试；扩展离线 Worker、API 能力状态及离线应用配置。

Reason: 让已验证图片任务通过同一 Worker 完成真实冻结 YOLO11 推理、原尺寸标注、统计及受控下载。

Validation: 独立 API 环境 37 通过；真实图片 HTTP 全链路通过；冻结环境 819 通过/4 项环境隔离跳过；前端 11 通过且构建通过。见 [实施报告](../../../reports/v1.2/V12_C_IMAGE_INFERENCE_REPORT.md)。

Evidence: `tests/unit/test_offline_image_processor.py`、`tests/integration/test_offline_image_real.py`、`offline/migrations/0002_image_results.sql`。

Risk: 冻结推理过滤条件为五类，模型另两类未评估；P9-C 长期资源问题仍未解决；同步推理只能在安全检查点取消。

Not Verified: 视频处理、H.264、长期多图资源稳定性、Vue 离线页面。

Next Step: 人工审核 V1.2-C；V1.2-D 须另行授权。
