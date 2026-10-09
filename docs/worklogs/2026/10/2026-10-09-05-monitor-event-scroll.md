# 监控最新事件滚动窗口交接

Changed: `front/src/views/MonitoringView.vue`、`front/src/styles/main.scss`、监控事件测试与相关文档。

Reason: 最新事件卡片随事件数增加而变高，无法稳定显示最新事件。

Validation: 前端 11 测试与构建 PASS；真实浏览器排序和独立滚动 PASS；`git diff --check` PASS。

Evidence: `docs/reports/frontend-v1.1/MONITOR_EVENTS_SCROLL_REPORT.md`、`docs/reports/frontend-v1.1/screenshots/monitor-events-scroll.png`。

Risk: 服务端仍只保留最近 20 条会话事件，完整历史在事件中心；P9-C 长期生命周期风险保留。

Not Verified: 无本次范围内未执行的功能。

Next Step: 人工审核；未 commit、push、打 Tag。
