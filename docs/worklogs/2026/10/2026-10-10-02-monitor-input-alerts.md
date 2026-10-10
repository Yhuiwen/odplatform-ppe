# 监控输入源与事件告警详情

Changed: front/src/views/MonitoringView.vue、EventsView.vue、MonitoringView.test.js；api/main.py；tests/integration/test_frontend_api.py；阶段、状态、变更、门禁记录。
Reason: 避免不同输入源复用错误地址；明确摄像头编号语义；展示真实通道投递结果。
Validation: npm test -- --run 35 PASS；npm run build PASS；.venv-frontend-api/Scripts/python.exe -m pytest tests/integration/test_frontend_api.py -q 3 PASS；compileall api、git diff --check PASS。API 测试覆盖详情/处理回执字段、失败/跳过/成功、敏感异常隐藏、历史记录缺失。浏览器 MP4→USB 旧地址清空，USB 说明与详情区域可见。
Evidence: front/src/views/MonitoringView.test.js；tests/integration/test_frontend_api.py。
Risk: 回执仅来自 MonitoringService 当前会话的 bounded recent_events，重启或记录移出窗口后不可查询；没有持久化告警账本。投递成功不等于用户已确认。USB 数字索引由自动选择的 OpenCV 系统后端决定，不把 Windows 设备列表顺序误当编号；动态名称映射未实现。既有 P9-C/G-CFR 风险保持。
Not Verified: 自动审批拒绝重启运行中的 8775 服务（策略阻止进程停止/重启命令，无更具体理由），因此新版真实告警回执浏览器联调尚未执行；未启动摄像头或新增检测任务。
Next Step: 在监控/离线任务均停止后人工重启 8775 后端，沿用 ODPLATFORM_OFFLINE_ROOT 原路径；刷新页面。下一次监控事件可显示真实通道回执。无 commit/push/tag；人工审核待定。
