# V1.2-B 离线任务基础设施实施报告

日期：2026-10-09。基线：`main` / `1d283dcbe37d853dab3240ebe4cc6084c7be9e42`，已有 V1.1 里程碑 Tag。本阶段只实现任务与安全上传基础，不进行真实推理、标注输出或 H.264 编码；提交、推送和 Tag 均未执行。

## 已实现

- 新增 `offline/`：独立 SQLite 任务库、版本 1 SQL 迁移、状态机、每任务隔离目录、媒体校验、产物完整性检查、可注入 Processor 的单 Worker 框架。
- `api/offline.py` 将七个离线接口加入现有 FastAPI：`POST /api/v1/offline/jobs`、`GET /jobs`、`GET /jobs/{id}`、`POST /jobs/{id}/cancel`、`GET /jobs/{id}/artifacts`、`GET /jobs/{id}/artifacts/{key}`、`GET /capabilities`。所有路径均带 `/api/v1/offline` 前缀。上传成功返回 202 和真实 `QUEUED` 任务；生产 capabilities 明确 `processor_available=false`。
- `api/main.py` 的 lifespan 只创建一次任务库、目录、Worker 和资源准入对象。进程级文件锁阻止同一任务库被多个 API 实例调度。生产 Worker 没有 Processor，因此不会生成虚构产物；队列记录在重启后保留。
- 原实时监控启动经过同一资源准入锁；实时监控状态为 `starting/running/stopping` 时，未来离线处理不得占用资源；离线处理占用时监控启动返回资源冲突。未修改检测/跟踪/合规实现。
- `/artifacts/offline/` 已加入 Git 忽略。V1.2 独立 API 锁新增 `python-multipart==0.0.32` 和 `Pillow==12.3.0`；V1/V1.1 锁不变。

## 存储、状态和恢复

任务库默认位于 `artifacts/offline/jobs.sqlite3`，可通过 `ODPLATFORM_OFFLINE_ROOT` 为测试指定独立根目录。任务 ID 为服务端生成的 32 位十六进制 UUID，每任务独立 `input/staging/output/evidence/metadata` 目录。迁移版本记录在 `schema_migrations`；主表存储原文件名、媒体类型、SHA256、大小、宽高、编码、FPS、帧数、时长、音轨确认、状态、进度、UTC 时间、错误码和产物清单。没有改动现有事件库 Schema。

状态转换：`VALIDATING→QUEUED/FAILED`；`QUEUED→PROCESSING/CANCELLED/FAILED`；`PROCESSING→ENCODING/COMPLETED/CANCELLING/FAILED/INTERRUPTED`；`ENCODING→COMPLETED/CANCELLING/FAILED/INTERRUPTED`；`CANCELLING→CANCELLED/FAILED/INTERRUPTED`。终态不可再运行。任务完成要求经过 `ArtifactPublisher` 发布且 SHA256/大小验证的清单。重启后 `VALIDATING` 变 `FAILED` 并清理本任务的上传暂存，`PROCESSING/ENCODING/CANCELLING` 变 `INTERRUPTED`，完整的 `QUEUED` 保留；不从中间帧继续。

## 上传与访问边界

只接受 JPG/JPEG、PNG、MP4。文件名拒绝路径分隔符与控制字符；MIME、扩展名、实际格式同时检查。上传以 1 MiB 块写入暂存并计算 SHA256，写盘同步后检查：图片由 Pillow 校验，视频先检查 MP4 容器，再以 `ffprobe` 读取视频编码、分辨率、FPS、帧数、时长、音轨及旋转元数据。含音轨视频必须提交 `audio_discard_confirmed=true`，说明未来标注视频不保留原音轨；本阶段不会实际编码。原子移动到本任务输入目录后才进入排队。上传失败清理本任务暂存文件。边界拒绝跨站 Origin、非本机 Host；multipart 请求体设 513 MiB 硬上限，缺少 Content-Length 返回 411。部署仍应只监听 `127.0.0.1`。

默认值：图片 20 MiB、视频 512 MiB、最长 600 秒、最多 3840×2160 像素、最多 20 个排队任务、最少 1 GiB 空闲空间、暂存最多 1 GiB、探测超时 15 秒。它们是保守配置，不是性能验收上限。下载只允许 `COMPLETED` 任务中登记的 artifact key，服务端再次核对 SHA256/大小；响应不含任意本地路径。

## 验证与限制

独立 API 环境：新增任务/媒体/接口及原 V1.1 API 共 21 项通过。JPG、PNG、用户提供的实际 HEVC/AAC MP4、空文件、类型不符、无效媒体、路径穿越、超限、中断上传清理、音轨确认、哈希、取消幂等、持久化、重启恢复、无产物下载、假 Processor 完整性、并发单执行、实例锁及实时资源准入均有针对性测试。原 Vue 11 项测试和 `npm run build` 通过。冻结环境全量回归 816 通过、2 项 API 环境隔离跳过；API 测试在冻结环境中按设计跳过，因为 FastAPI 只在独立 API 环境安装。

未执行真实 YOLO、图片/视频结果生成、H.264 编码、音轨保留、实际高负载争用、长时间资源稳定性。P9-C 资源生命周期仍为 PARTIAL。生产队列目前不会被消费；C/D/E 阶段应注入真实 Processor，使用 `JobContext.progress/cancelled/publisher`，并在任务完成前再次验证产物。当前 in-process Worker 适合单实例本地部署，处理器需要合作式取消；未来真实长任务应补充停止超时和资源回收验收。多实例同根目录启动会因进程锁失败，不能用 Uvicorn 多 Worker 模式。前端离线页面属于后续阶段，本阶段仅交付 API。
