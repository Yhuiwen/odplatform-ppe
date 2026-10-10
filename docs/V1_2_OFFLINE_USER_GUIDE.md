# V1.2 离线检测部署与使用

本版处于人工审核状态；Git 发布尚未执行。V1.1 的实时监控、事件、证据、统计和 AI 页面保留，旧 Streamlit 可回退。离线任务与实时事件库隔离，离线事件不投递实时 Web/TTS 告警。

## Windows PowerShell 部署

使用项目已核验的 Python 3.12 业务环境与独立 API 环境。缺少冻结模型时从授权备份恢复，不下载替代权重。离线模型指纹与 `configs/inference.yaml` 必须匹配 C 报告。FFmpeg/FFprobe 必须在 PATH 中，FFmpeg 须支持 libx264。

```powershell
Set-Location 'E:\大四\创业实训\odplatform-ppe'
# 已有核验业务环境 .venv-final-demo；只在独立API环境缺失时创建。
if (-not (Test-Path '.venv-frontend-api\Scripts\python.exe')) { py -3.12 -m venv .venv-frontend-api }
& .\.venv-frontend-api\Scripts\python.exe -m pip install -r locks/frontend-v1.2-api/requirements.txt
Push-Location front
npm ci
npm test
npm run build
Pop-Location
# 先确认目标端口没有已有实例；不要自动关闭正式 8768。
& .\scripts\start_frontend_local.ps1 -ApiPort 8765
# 浏览器打开 http://127.0.0.1:8765/offline
```

一个任务根目录只能有一个 API 进程、一个 Worker。不要启用 Uvicorn 多 Worker 或 reload 处理正式任务。API 的 `/api/v1/health` 返回 `api_version=1.2.0`；随后检查 `/api/v1/offline/capabilities` 的 image/video/event 能力，不能仅凭健康响应判断模型可用。代码版本号不表示已经发布或人工审核通过。

开发时另开 PowerShell，在 `front` 执行 `$env:VITE_API_TARGET='http://127.0.0.1:8765'; npm run dev -- --host 127.0.0.1`。浏览器访问 5173，Vite 代理 `/api`。默认只监听本机，不使用任意跨域白名单。

### 安全停止与升级

1. 停止提交新任务，在任务历史确认排队及执行状态。
2. 如需结束当前处理，点击其“取消任务”，等待 `CANCELLED`；同步推理只能在前后检查点取消。正在编码时也必须等待服务端终态。
3. 在启动 API 的 PowerShell 按 **Ctrl+C**，等待 Uvicorn 退出。关闭窗口或强杀可能导致下次启动记录为 `INTERRUPTED`，不是完成。
4. 确认该实例端口释放，再构建或重启。同一根目录重启保留历史；中断任务不从半个视频续跑，重新上传创建新 Job。

不要按端口自动杀进程，不要删除任务库、原始文件或用户已有输出。本次验收没有重启正式 8768。

## 图片操作

“图片检测”选择 JPG/JPEG/PNG → 开始检测 → 等待完成 → 原图/标注图切换 → 点击放大 → 下载 PNG、检测 JSON、统计 JSON 或 ZIP。

原始上传字节保留。EXIF 方向标准化后的尺寸是检测及输出坐标系；透明图合成白色背景，灰度转 RGB。单帧只显示检测框与疑似违规检测项，不创建 Track ID 或时序确认事件。历史任务“查看”恢复服务端保存结果。

## 视频操作

“视频检测”选择 MP4 → 明确确认输出移除音轨 → 开始检测 → 查看真实处理帧数 → 等待编码、完整解码校验、导出及发布结束 → 播放标注视频。

点击事件时间轴按真实 `video_timestamp_seconds` 定位；事件类型筛选、分页、复制事件 ID、查看同一触发帧的原图/标注证据均为只读操作。证据 PNG 保持原尺寸，服务端校验 SHA256 后提供受限访问。下载 ZIP 包含视频、逐帧 JSONL、摘要、验证信息、事件 JSON/CSV、证据索引及证据 PNG；不暴露内部 SQLite。

服务端每个解码帧推理一次，原尺寸标注、保持支持的播放 FPS，不主动跳帧。CPU 处理 FPS 与输出播放 FPS 是不同指标。输出 H.264/libx264、CRF18、medium、yuv420p、faststart，**有损编码**，不宣称与原视频像素完全相同；无原始音轨。

## 状态、限制与异常

默认限额：图片 20 MiB、视频 512 MiB/600 秒、最多 3840×2160 像素、20 个排队任务、至少 1 GiB 可用磁盘、暂存上限 1 GiB。这些是配置边界，不代表 FullHD/4K 或 600 秒已通过性能验收。当前仅接受可验证 CFR、无旋转、偶数宽高 MP4；VFR/缺失时间戳/旋转/奇数尺寸明确拒绝，不裁剪或缩放迎合。

冻结过滤类别为 person/hardhat/no_hardhat/vest/no_vest；machinery/vehicle 显示 `NOT_EVALUATED`。轨迹编号不是独立人员数；未知关联观测不是 PPE_UNKNOWN 事件。离线与实时推理同实例互斥，不同 root/进程没有全局资源互斥保证。

只在 `COMPLETED` 开放结果；取消、失败、中断任务不显示成功产物。证据损坏、产物缺失、下载 HEAD 校验失败显示明确错误。浏览器直接流式下载，随后网络传输失败需查看浏览器下载状态。首次大文件完整哈希可能有等待；Range 使用有界指纹缓存，可信本地写一次产物边界不防御本机恶意并发篡改。

历史及本次验收发现同一 570 帧素材偶发在推理前触发 CFR 拒绝，根因未确定，不自动重试或放宽校验。P9-C 资源生命周期仍为 PARTIAL/FROZEN。FullHD/4K/长视频真实 YOLO 及长期稳定性未完整验收，详见 [G 验收报告](reports/v1.2/V12_G_FINAL_ACCEPTANCE_REPORT.md)。

## 回退

仅关闭事件分析：`$env:ODPLATFORM_OFFLINE_EVENT_EXECUTION='0'`；仅关闭视频：`ODPLATFORM_OFFLINE_VIDEO_EXECUTION='0'`；关闭共享离线图片/视频执行：`ODPLATFORM_OFFLINE_IMAGE_EXECUTION='0'`。安全退出 API 后重启才生效，保留已有结果。

旧 Streamlit 启动：`& .\.venv-final-demo\Scripts\python.exe -m streamlit run web/Home.py --server.address 127.0.0.1`。模型、业务规则与旧页面未删除。离线数据不用实时 Streamlit 页面混合展示。

验证实例应设置 `ODPLATFORM_OFFLINE_ROOT` 为仓库外专属目录，避免运行 ZIP 混入旧源码资产门禁；不要为此放宽资产扫描。发布前只审核代码、依赖锁和报告截图，排除模型、私人素材、输入输出、SQLite、密钥与构建产物。候选 Tag 为 `v1.2-offline-media-analysis-complete`，须人工审核及另行授权后创建，不得覆盖已有 Tag。
