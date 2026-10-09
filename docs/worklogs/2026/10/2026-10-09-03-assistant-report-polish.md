# 助手与报告展示优化


## 2026-10-09 相对时间查询与报告中文展示优化

- API 仅对完整匹配的安全事件问题适配最近分钟/小时/天查询（最长 7 天）；继续经过原只读 Agent。手动日期优先，追加删除指令不会被改写。
- 前端展示本地时间范围与无事件状态；补齐截图中的报告中文句式，未适配原文保留在明确标记的展开区域。
- 验证：前端 9 项通过；独立 API 环境 2 项通过（包括空范围、超限、危险追加指令）；生产构建通过；diff --check 通过。
- 运行实例重启被自动审批拒绝，因此当前 8765 后端尚未加载适配；实时端到端查询待手动重启验证。P9-C 原有风险保留。没有 commit/push/tag。

Changed: api/main.py、agentDisplay.js、AIAssistantView.vue、AIReportView.vue 及测试
Reason: 用户截图中的相对时间误拒绝和中英混排
Validation: 9 frontend + 2 API PASS
Evidence: tests/integration/test_frontend_api.py；front/src/utils/agentDisplay.test.js
Risk: 未适配 Provider 原文仍需展开阅读；P9-C 保留
Not Verified: 当前运行后端新适配（重启被策略拒绝）
Next Step: 手动重启并验收最近5分钟查询
