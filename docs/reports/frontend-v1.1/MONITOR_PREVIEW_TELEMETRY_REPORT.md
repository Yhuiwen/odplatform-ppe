# 监控预览指标与镜像优化（2026-10-09）

## 改动

- 视频右上角以小字显示实际 MJPEG 发布帧率和最新帧更新延迟；未运行、视频完成或帧过旧显示“—”。不把视频源标称 `fps` 当实时处理帧率，也不宣称测得浏览器端到端延迟。
- 新增镜像开关，仅用 CSS 翻转预览图像；视频输入、检测、跟踪、事件与证据流水线未变。镜像时已绘制在图像上的检测标签也会随图像一起翻转。
- 移除视频下方的实现说明文字。服务端 `PreviewTelemetry` 包装已有 `PreviewChannel.publish`，记录成功发布帧的单调时钟时间。

## 验证

- `pytest tests/unit/test_preview_telemetry.py tests/integration/test_frontend_api.py -q`：4 PASS。
- `npm test`：11 PASS；`npm run build`：PASS；`python -m compileall -q api`、`git diff --check`：PASS。
- 真实浏览器在 `127.0.0.1:8768/monitoring` 用用户指定 MP4 启动并完成监控：570 帧；运行时 API 返回 `preview_fps=20.2`、`preview_age_ms=15`，页面曾显示 `34.0 FPS / 0 ms`（不同采样时刻）；完成后两项为“—”。镜像按钮选中后画面水平翻转。启动初期曾有一次状态请求超时，服务继续运行且后续状态恢复。
- [真实页面截图](screenshots/monitor-preview-telemetry-mirror.png)。截图拍于视频完成且镜像开启时。

## 状态

本增量不改变 P9-C PARTIAL 资源生命周期风险或 V1.1 HUMAN REVIEW PENDING。未 commit、push、tag。
