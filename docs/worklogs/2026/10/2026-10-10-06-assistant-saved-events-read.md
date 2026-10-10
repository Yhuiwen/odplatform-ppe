# 安全助手保存事件只读查询增强

Changed: api/main.py、front/src/views/AIAssistantView.vue、tests/integration/test_frontend_api.py、阶段/状态/变更/门禁。
Reason: 复用当前API真实事件库，增加显式类型/状态/Track筛选和事件明细快捷操作，确保模型查询受控且无修改权限。
Validation: .venv-frontend-api/Scripts/python.exe -m pytest tests/integration/test_frontend_api.py tests/integration/test_configured_assistant.py tests/test_agent_web_boundary.py tests/test_agent_tool_registry.py tests/test_agent_api.py tests/test_llm_planner_adapter.py -q：61 PASS；前端35 PASS/build PASS；compileall/diff PASS。测试保存EVT fixture，确认读取和空范围分别成功/empty；拒绝状态修改、删除、SQL及未知payload字段，repo前后相同。原release检查失败已通过真实query实例绑定修复，不删除空结果断言。
Evidence: tests/integration/test_frontend_api.py；tests/integration/test_configured_assistant.py；既有Agent边界/注册/API/候选测试。
Risk: 读取对象为当前事件中心已持久化事件，通过现有EventQueryService和Agent Application执行；不将查看写成已读标记，不增加SQLite列，不改冻结工具白名单或权限策略。SYSTEM是既有服务身份，客户端不能选择身份/能力；四工具没有修改功能。模型组织输出继续受既有事实选择/引用验证约束。API中文修改意图保护可能保守拒绝歧义问题，可改用明确读取问法。
Not Verified: 真实Provider新增查询和浏览器筛选联调；自动审批拒绝停止/重启8775，仅说明策略阻止，旧运行实例未加载新API。新界面遇到旧后端筛选能力缺失明确提示。
Next Step: 重启8775并刷新后按事件类型/状态/轨迹询问已保存数据，人工复验。CFR/P9-C及发布阻塞保持；未commit/push/tag。
