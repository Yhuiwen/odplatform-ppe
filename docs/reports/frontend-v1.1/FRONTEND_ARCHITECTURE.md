# V1.1 前端架构与现状审计

## 审计

- 基线：`main`，`5356e763b1de0cdab74e9ed3233d121e5a2d98b0`；与 `origin/main` 同步。修改前唯一未跟踪内容是 `front/source/statices/picture/1.png` 至 `8.png`，已保留并加入忽略规则。
- 现有七个正式 Streamlit 页面、SQLite 事件查询与状态更新、证据 SHA256 校验、MP4/USB/RTSP 单路监控、AnnotatedFrameRenderer、Grounding Validator、模板报告及只读 Agent 均已具备。缺少 Vue 工程和 HTTP 适配。
- 设计图 1–5、8 与映射一致；6、7 均为报告，采用 7 的双栏结构。图中管理员身份、模拟数值、区域/风险等级、多帧证据及与 PPE 无关内容没有业务依据，未实现。
- P9-C 推理 worker 生命周期增长归因仍为 PARTIAL；本次未修改核心时序或宣称风险修复。

## 结构

- `front/src/layouts/MainLayout.vue` 统一导航、连接状态、主题与刷新；七个 `views/` 为真实 API 页面。图表使用 ECharts；状态请求使用 Axios。
- `api/main.py` 在应用 lifespan 中构建一个 `MonitoringService`，FastAPI 接口只做参数验证、服务编排和安全投影。MJPEG 使用同一进程 `PreviewChannel`，不因浏览器重开重建监控任务。
- FastAPI 从独立 `.venv-frontend-api` 启动，再在其包路径之后追加冻结 V1 演示环境的业务依赖路径；FastAPI 所需 Starlette 与 V1 锁环境隔离。若演示环境位置不同，可设置 `ODPLATFORM_RUNTIME_SITE_PACKAGES`。
- API 默认仅由命令绑定 `127.0.0.1`。本机 Windows 将 TCP 7932–8031 保留，8000 无法绑定，因此本机脚本默认 8765。Vite 代理 `/api` 至 8765。
- `front/source/statices/picture/` 只用于设计参考，不参与构建或提交。旧 `web/` 保留为回退入口。

## 安装与启动

```powershell
py -3.12 -m venv .venv-frontend-api
& .\.venv-frontend-api\Scripts\python.exe -m pip install -r locks/frontend-v1.1-api/requirements.txt
cd front
npm ci
npm run build
cd ..
& .\scripts\start_frontend_local.ps1
```

访问 `http://127.0.0.1:8765/`。开发模式运行 `& .\scripts\start_frontend_dev.ps1`，访问 `http://127.0.0.1:5173/`。监控前先按 V1 指南核验模型与素材。停止监控后以 Ctrl+C 结束服务。

旧版回退：`& .\.venv-final-demo\Scripts\python.exe -m streamlit run web/Home.py --server.port 8502 --server.address 127.0.0.1 --server.headless true`。
