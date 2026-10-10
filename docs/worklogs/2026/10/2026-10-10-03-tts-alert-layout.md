# 语音依赖加载与告警卡片

Changed: api/runtime_support.py、api/main.py、front/src/views/EventsView.vue、EventsView.test.js 和阶段/状态/变更/门禁。
Reason: API 只追加 site-packages，未处理 PyWin32 子模块与 DLL 目录；窄抽屉表格横向滚动遮挡原因代码。
Validation: 前端35 PASS、独立API3 PASS、build PASS、compileall/diff PASS。真实 Windows 语音引擎初始化 PASS，工作线程中文 speak 返回 PASS。浏览器真实三通道回执卡片 clientWidth/scrollWidth 均386px。
Evidence: docs/reports/v1.2/screenshots/monitor-alert-cards.png；front/src/views/EventsView.test.js。
Risk: 仅加载已有依赖，不修改冻结环境/锁文件/检测规则；DLL 搜索目录句柄保持至进程退出。已有失败回执不能改为成功。P9-C 与 G-CFR 风险保留。
Not Verified: 实际声音可听性需人工确认；运行8775尚未重启加载语音修复，未执行新监控事件语音端到端。前次自动审批已拒绝重启，未绕过策略。
Next Step: 手动重启8775后用新事件验证语音回执；人工审核，未commit/push/tag。
