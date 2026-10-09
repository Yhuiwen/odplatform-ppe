# V1.1 API 契约

前缀 `/api/v1`，仅供本机 Vue 前端调用。API 不接受任意路径证据读取、SQL、训练或 Python 调用。错误返回简洁 `detail`，不输出堆栈、密钥或 RTSP 地址。

| 方法 | 路径 | 现有服务 |
| --- | --- | --- |
| GET | `/health`, `/capabilities` | API 运行状态与配置能力 |
| GET | `/overview`, `/statistics` | `EventQueryService.statistics/query_events` |
| GET | `/events`, `/events/{id}` | `EventQueryService` |
| PATCH | `/events/{id}/handling` | `EventStatusService.set_handled`；请求 `{ "handled": true/false }` |
| GET | `/evidence`, `/evidence/{id}`, `/evidence/{id}/image` | `EventQueryService.evidence`、服务端完整性验证；图片仅对已验证事件返回 |
| GET | `/monitor/status`, `/monitor/preview` | 生命周期内单例 `MonitoringService`、MJPEG `PreviewChannel` |
| POST | `/monitor/start`, `/monitor/stop` | 原监控服务；启动请求 `{ "source_type": "mp4|usb_camera|rtsp", "location": ... }` |
| POST | `/reports/generate` | 原 `AgentApplicationService` 报告操作及 Grounding/模板降级 |
| POST | `/assistant/ask` | 原只读 Agent facade 和受控工具 |

事件参数包括 `start_at/end_at`、`event_type`、`status`、`source_group`、`track_id`、`limit`、`offset`。时间可用 `YYYY-MM-DD` 或带时区 ISO 时间。来源只向浏览器投影 `mp4`、`rtsp`、`usb{id}` 或 `其他来源`，不发送原路径/连接地址。监控 `status` 不返回原始 `source_id`；`tracks` 是累计轨迹观测数，`alerts_delivered` 是通道级计数。

服务端单路监控锁处理并发启动/停止。刷新页面只查询状态。预览流不携带摄像头 URL。当前本地演示尚无生产认证，必须持续绑定回环地址；部署到非本机需要单独完成认证与授权设计。

`GET /monitor/status` 的 `preview_fps` 是最近 3 秒内实际发布到 MJPEG 通道的帧率，`preview_age_ms` 是最新发布帧距本次状态查询的毫秒数（画面更新延迟）。二者在未运行、无新帧或帧过旧时为 `null`。该延迟不包含网络传输、浏览器解码和显示时间，不能解释为完整端到端延迟。原有 `fps` 仍是输入视频的标称帧率。

报告响应新增 `evidence_images: [{"event_id": "EVT-..."}]`。API 只从报告的受控引用中选取同一报告时间范围内的持久化事件，并调用 `EventQueryService.evidence` 校验图片。前端用事件 ID 调用既有 `/evidence/{id}/image`；相对证据路径不作为图片 URL 返回。
