# V1.1 前端测试记录

日期：2026-10-08。API 独立运行环境 `.venv-frontend-api`；V1 冻结环境 `.venv-final-demo` 已恢复原 Starlette 1.7.0，`scripts/preflight.py` 再次 PASS。

| 检查 | 结果 |
| --- | --- |
| `npm install`, `npm run build` | PASS；Vite 构建七页。ECharts/Element Plus 包产生体积警告，不影响构建 |
| `npm run test` | PASS，3 个路由/API 契约测试 |
| `python -m compileall api services web` | PASS |
| `.venv-frontend-api` 的 `tests/integration/test_frontend_api.py` | PASS，2 个测试；SQLite 统计、分页筛选、状态持久化、损坏证据拒绝、报告本地模板降级、只读助手查询 |
| `.venv-final-demo` 全量旧回归首次运行 | 809 PASS、1 FAIL；文档链接测试误扫 `front/node_modules` |
| 排除生成的 `node_modules` 后全量复测 | 810 PASS、1 SKIP（API 测试在独立环境执行）；冻结环境预检 PASS |
| 真实已核验 MP4 经 API 单例监控 | PASS；47 帧、74 检测观测、1 条 PPE_UNKNOWN 事件、2 次通道告警、预览可用、正常 completed。使用隔离临时存储 |
| 1366×768 与 1920×1080 七页浏览器导航 | PASS；14 个组合无页面级横向溢出，无新 JS 错误；侧栏点击成功进入事件页，主题切换有效；截图在 `screenshots/` |
| USB 摄像头、RTSP 实源 | NOT_EXECUTED；本轮没有占用或配置设备/流 |
| 真实外部 AI Provider | NOT_EXECUTED；未发起外部模型请求。模板降级已测试 |

监控 P9-C 长时间资源生命周期风险仍 PARTIAL。本次 47 帧完成不等于长时稳定性验证。
