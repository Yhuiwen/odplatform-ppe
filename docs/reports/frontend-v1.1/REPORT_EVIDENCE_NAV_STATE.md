# V1.1 报告证据与导航状态优化

日期：2026-10-09。状态：HUMAN REVIEW PENDING。

## 修改

- 报告 API 在原有只读 Agent 和 Grounding 结果之后，将报告引用与同一报告时间范围内的已持久化事件匹配。仅对 `EventQueryService.evidence` 完整性校验通过的事件返回 `evidence_images: [{event_id}]`。不向浏览器发送本地文件路径，也不新增任意路径读取接口。
- 报告页面直接显示这些证据缩略图，点击后通过原有受限 `/evidence/{id}/image` 接口放大。图片失效时显示不可用提示。
- 主布局缓存七个路由组件，并按模块保留主内容滚动位置。日期、筛选、分页、报告及聊天记录在导航往返时保留。显式刷新仍向服务端查询数据。监控页切出时暂停轮询与 MJPEG 预览，返回时重新查询实际监控状态。

## 验证

- 前端测试 10 PASS；构建 PASS。API 集成测试 2 PASS，涵盖引用匹配、时间范围约束及证据文件损坏情况；Python compileall 和 `git diff --check` PASS。
- 真实 Provider 报告：`success / LLM / not_degraded / grounding=valid`；24 条引用匹配到 24 张服务端已校验证据。
- 浏览器已验证 24 张证据缩略图与点击放大；生成报告后切换到安全助手再返回，原报告、日期、图片保持，助手未发送的输入仍保留。实际运行截图见 `screenshots/report-evidence-gallery.png` 与 `screenshots/report-evidence-zoom.png`。

## 限制

页面状态仅在当前标签页的模块导航期间保留；浏览器强制重新加载会创建新页面实例。P9-C 长期资源生命周期问题仍未解决。原有 8765 服务尚在运行，本次验证新版本在本机 8767 端口。未 commit、push、打 Tag。
