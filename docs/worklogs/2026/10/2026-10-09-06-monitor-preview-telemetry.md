# 2026-10-09 监控预览指标与镜像交接

- 需求：视频右上角显示实时帧率和延迟，镜像翻转，移除下方文字。
- 实现：API 监控生命周期中包装 `PreviewChannel.publish`，只统计成功发布到 MJPEG 的帧；前端角标和预览镜像开关。
- 验证：前端 11 PASS、API 4 PASS、构建/compileall/diff --check PASS；指定 MP4 浏览器运行 570 帧，指标与镜像可见，结束后指标为“—”。截图及详情见 [专项报告](../../../reports/frontend-v1.1/MONITOR_PREVIEW_TELEMETRY_REPORT.md)。
- 注意：更新延迟是服务端最新帧年龄，不是网络和浏览器显示总延迟。镜像也会翻转烧录在画面上的检测标签。P9-C PARTIAL 保留。
- 状态：HUMAN REVIEW PENDING；未 commit、push、tag。
