# 报告证据图片与导航状态交接

Changed: `api/main.py`、`front/src/layouts/MainLayout.vue`、`front/src/views/AIReportView.vue`、`front/src/views/MonitoringView.vue`、前端样式、相关测试与 V1.1 文档。

Reason: 报告引用需要以真实证据图片展示，模块切换不应清空表单与已生成结果。

Validation: 前端 10 测试和构建 PASS；API 2 测试、compileall、diff check PASS；真实 Provider 报告 `grounding=valid`，24 张已验证图片；浏览器缩略图、放大及往返状态 PASS。

Evidence: `docs/reports/frontend-v1.1/REPORT_EVIDENCE_NAV_STATE.md`、`docs/reports/frontend-v1.1/screenshots/report-evidence-gallery.png`、`docs/reports/frontend-v1.1/screenshots/report-evidence-zoom.png`。

Risk: 页面硬刷新会重建局部界面状态；P9-C 长期生命周期风险保留。原 8765 实例仍在运行，新版本在本机 8767 供审核。

Not Verified: 无本次范围内未执行的功能；生产环境长期运行不属于本次增量。

Next Step: 人工审核；未 commit、push、打 Tag。
