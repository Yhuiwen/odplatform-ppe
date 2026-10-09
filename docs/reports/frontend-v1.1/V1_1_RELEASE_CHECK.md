# V1.1 前端发布检查（2026-10-09）

- 范围：七个 Vue 页面、FastAPI 适配、前端/API 独立锁文件、测试、文档与真实页面截图；旧 Streamlit 保留。
- 发布基线：`main` / `5356e763b1de0cdab74e9ed3233d121e5a2d98b0`；`git fetch origin` 后本地与 `origin/main` 的 ahead/behind 为 `0/0`，远端无 `v1.1-frontend-replacement-complete` 标签。
- V1 冻结环境：`python -m pytest -q` 结果 812 PASS、1 SKIP（FastAPI 测试按环境分离）；`scripts/preflight.py` PASS。
- API 独立环境：4 PASS；`python -m compileall -q api services web` PASS。前端：Vitest 11 PASS、Vite build PASS。
- 计划提交的文件不含模型、视频、数据库、训练集、原设计图、`node_modules`、`dist` 或本地依赖环境。暂存差异 `git diff --cached --check` PASS；常见令牌/私钥/含凭据 RTSP 模式扫描无命中。
- 已知限制：本地回环部署无生产身份认证；USB 和远端 RTSP 不在本轮实测；P9-C 资源生命周期仍 PARTIAL；前端大包体积警告；监控启动初期曾有一次请求超时，随后恢复。服务端“更新延迟”不含浏览器网络及渲染时间。
- 发布目标：提交到 `main`，推送 `origin/main`，创建并推送 `v1.1-frontend-replacement-complete` 标签。此发布不宣称 Phase 9 全面验收。
