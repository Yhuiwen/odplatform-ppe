# 安全助手输出与受控解读优化

Changed: front/src/views/AIAssistantView.vue、front/src/utils/assistantResult.js 及测试、agentDisplay.js、web/agent_support.py、infra/llm/assistant_client.py、配置助手集成测试与阶段记录。

Reason: 原始英文 key=value 明细和长图片路径难以阅读；用户授权适当扩大解读。

Validation: Python25 PASS、前端37 PASS/build PASS；既有语句选择越权/未知引用/重复字段拒绝测试通过。

Evidence: tests/integration/test_configured_assistant.py; front/src/utils/assistantResult.test.js。

Risk: 模型只能选择上下文解读与复核建议，不自由新增事实。引用不代表图片校验通过；返回明细可能只是回答选取的子集，不代表全部事件。检测/合规/SQLite及只读权限不变。既有CFR/P9-C风险保持。

Not Verified: 真实Provider新增提示、浏览器布局、后端新版加载；运行进程不自动停止（此前重启被自动策略拒绝）。

Next Step: 人工重启当前后端并刷新页面，验证新解读与证据放大；发布仍待门禁及人工审核。
