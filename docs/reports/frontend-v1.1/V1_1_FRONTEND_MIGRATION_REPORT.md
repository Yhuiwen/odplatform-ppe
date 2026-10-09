# V1.1 前端迁移审核报告

分支 `main`；基线 HEAD `5356e763b1de0cdab74e9ed3233d121e5a2d98b0`。七页和 API 适配已实现，保留 `web/` Streamlit 作为回退。新增前端依赖锁 `front/package-lock.json`，API 独立依赖记录 `locks/frontend-v1.1-api/requirements.txt`。V1 冻结依赖文件未修改。

FE-1：Vue 3、Vite、Router、Pinia、Element Plus、SCSS、ECharts 公共布局与七页。FE-2：FastAPI 生命周期、事件/证据/统计/监控/AI 路由。FE-3：真实 MP4 47 帧完成；USB/RTSP 接口已连接但实源未在本轮执行。FE-4：事件处理/证据完整性闭环经隔离 SQLite 测试。FE-5：总览与四类统计图表使用真实 SQLite。FE-6：报告模板降级与本地只读助手通过测试；真实 Provider 未调用。FE-7：构建、接口、旧回归、双视口浏览器检查；本轮资源生命周期长期验证不在完成证据中。

已知限制：仅本地回环环境且无生产认证；FastAPI 单进程单路监控，不使用多 worker；RTSP 远端稳定性和 USB 物理设备仍缺实测；P9-C 内存风险仍 PARTIAL；部分服务投影/报告来自现有英文契约，界面通过已验证投影的中文映射显示；ECharts 与 Element Plus 首包较大。旧 Streamlit 回退命令和新启动命令见 `FRONTEND_ARCHITECTURE.md`。

提交、推送、Tag 均未执行；等待人工审核。
