# V1.2-F 离线智能检测工作台实施报告

日期：2026-10-09。实现门禁 PASS / HUMAN REVIEW PENDING。F授权明确确认E审核通过；不进入G，不提交/推送/创建Tag。

## Git与范围

Branch main；Base/Current HEAD：`1d283dcbe37d853dab3240ebe4cc6084c7be9e42`。保留B/C/D/E未提交成果。F没有修改模型、推理阈值、跟踪/关联/合规规则、实时事件Schema、Agent或训练资产。无新依赖、无模型/数据下载。

## 页面与组件

新增 `/offline`，菜单“离线检测”位于实时监控之后。沿用MainLayout、Vue Router、Axios、Pinia、Element Plus、主题和FE-8固定shell；不建立第二套布局或HTTP Client。

新增 `front/src/api/offline.js`、`stores/offline.js`、`utils/offline.js`、`views/OfflineDetectionView.vue`。六个组件：OfflineUploader、OfflineTaskProgress、ImageDetectionPanel、VideoDetectionPanel、OfflineTaskHistory、OfflineArtifactDownloads。视频面板合并播放器、只读事件、时间轴和证据；没有空壳组件。新增store/component测试，扩展原路由测试。

扩展既有Axios错误拦截，兼容字符串detail、离线{code,message}及校验数组，保留安全错误码/HTTP状态；不显示Python堆栈。普通查询15秒、上传300秒、原AI180秒。

## API映射

统一 `/api/v1/offline`：

| 交互 | 接口与字段 |
| --- | --- |
| 上传限制/可用能力 | GET /capabilities |
| 上传 | POST /jobs；multipart file、audio_discard_confirmed |
| 状态恢复/取消 | GET /jobs/{job_id}；POST /jobs/{job_id}/cancel |
| 历史分页/过滤 | GET /jobs；limit/offset/status/media_type/start_at/end_at；total_count |
| 清单/摘要/播放/下载 | GET /jobs/{job_id}/artifacts；GET/HEAD /artifacts/{key} |
| 图片原图 | GET /jobs/{job_id}/input-image（F新增） |
| 事件/时间轴 | GET /jobs/{job_id}/events；total（区别于历史total_count） |
| 证据详情/双图 | GET /jobs/{job_id}/evidence/{evidence_id}；同路径/image?variant=original或annotated |

实际任务字段：original_filename、input_width/input_height/input_fps/input_duration_seconds、processed_frames/total_frames/progress_percent、artifact_keys。完整统计读取已验证summary产物，无任务Schema变更。历史视频本页已完成任务读取摘要显示确认事件；D的null/NOT_IMPLEMENTED显示“未执行事件分析”，未完成/失败不伪造0。

## 上传、状态和恢复

Element Plus上传支持选择/拖拽，JPG/JPEG/PNG和MP4；大小按capabilities真实字节限制，不压缩/缩放。浏览器不能可靠判断音轨，因此每次MP4都明确确认移除音轨，同意后才传true，拒绝不提交。服务端最终校验，登记后展示可靠视频规格/实际音轨；逐帧CFR与输出完整性由Worker验证。

Axios loaded/total为上传进度，未知总量不伪造百分比；上传100%仍需后台处理。9个真实任务状态分别呈现，ENCODING包含编码验证和发布，只有COMPLETED启用结果和下载。取消以服务端为准。

轮询采用1.5秒递归timeout，请求结束后安排下一次；终态停止。切换Tab不取消Worker，离开页面暂停查询，卸载清理请求。generation/AbortController阻止旧请求覆盖新任务；上传中防重复提交。离开页面后上传完成仅记住任务，不重新启动轮询。sessionStorage只保存job_id；重开从服务端恢复，不保存媒体/路径/状态快照。

## 图片、视频、事件与证据

图片原图/标注切换、Element Plus放大、原/输出尺寸、检测框、候选项、非零类别数、类别统计、候选坐标和耗时均来自API；不创建Track ID或确认事件。原图接口限定已完成图片任务、固定安全source扩展名、输入SHA256/大小和归属/路径检查，不接受任意路径。

HTML5 video直接使用同源受限产物URL，不用大Blob或canvas编码；保持原比例，支持播放、暂停、进度拖动、全屏和MP4下载。累计检测框、任务内轨迹ID、时序确认事件、PPE_UNKNOWN事件、unknown_associations观测和证据文件数分开；机械/车辆未评估。

事件表格只读、类型筛选/分页。时间轴逐页加载轻量元数据，以video_timestamp_seconds/播放器duration定位；点击设currentTime、高亮事件、查询对应证据。空任务无虚构节点。证据原图/标注图contain、可放大，显示事件/轨迹/帧/视频时间/SHA256/服务端校验状态；异常保留事件信息，显示错误，不替换证据或误报已验证。

## Range与下载

安装的Starlette FileResponse已原生支持Range、206/416、Content-Range及video/mp4，直接复用。F增加HEAD和64项有界进程内校验缓存：每次校验任务/manifest/受限路径，比较dev/inode/size/mtime_ns/ctime_ns；首次或变化时完整SHA256，并核对哈希前后stat一致。应用完成产物只发布一次、之后不写。文件变化/缺失拒绝409；连续3次Range只哈希一次、同尺寸修改拒绝的测试通过。

此策略针对可信本地应用的写一次产物，不防御本机恶意进程伪造时间或验证后并发篡改；不宣称传输是文件系统事务。首次大文件仍完整哈希，后续Range避免反复扫描。

下载项来自真实manifest，内部SQLite隐藏；支持图片四项及视频帧JSONL、验证、事件JSON/CSV、证据索引、MP4/ZIP。HEAD失败提示错误，成功后浏览器直接流式GET到磁盘、保留服务端安全filename；不显示未经下载确认的成功通知。后续传输失败由浏览器下载状态反馈，不用JS缓存大文件。

## 真实浏览器联调

用户8768未重启或中断，其旧离线路径返回SPA，未把health200当作E启用证明。独立API环境127.0.0.1:8774，一个Worker，capabilities image/video/event_analysis均true。测试root与正式历史隔离，当前保存在仓库外 `C:/Users/慧文/AppData/Local/Temp/odplatform-v12f-jobs-20261009`；测试实例供本地审核，不污染正式任务。

| 资源/job_id | 实际结果 |
| --- | --- |
| JPG fbbdc45f6a594e4684bac5c620bd1292 | 1024×766，5框/2候选，原图/标注/ZIP |
| PNG cabe150dec90468ab0e6c63c9fac5f2e | 同一公开素材无损转换的测试PNG，1024×766，5框/2候选 |
| 47帧 2d78f3efb91f417586cd57f7617c40df | 47/47，77框，1 PPE_UNKNOWN/2证据；1280×720、24000/1001FPS |
| 570帧 4b92b42a2fd44341ba837474168013f3 | 570/570，1829框，2事件/4证据，7轨迹ID/46未知关联；1280×720、30FPS |
| 取消 aa95a962123c4c768809a0b6fbbe8b4c | 22帧后CANCELLING→CANCELLED，无可下载输出 |

浏览器时间轴定位47事件1.000999秒/frame24；570事件4.2/14.766666秒/frame126/443。两视频readyState4、实际1280×720，真实播放控制可用。双图原尺寸读取及原图放大通过；未戴安全帽筛选返回1条；刷新/导航恢复同一job，没有新建任务。无关键JS错误。图片/47/570三个实际ZIP下载SHA256/CRC通过；实际570标注MP4下载SHA256通过。`artifacts/validation/v12f/browser_chain.json`为忽略的联调记录。

## 响应式截图与原V1.1回归

1920×1080、1600×900、1366×768、1280×720：离线三个Tab和原七页均无document/main横向溢出，表格容器允许内部滚动。41次测量含1次重复总览，40个独立组合；main纵向滚动时document scrollTop=0，header/aside y=0。宽屏双栏、窄屏单栏，媒体contain，导航继承FE-8。

真实截图在相邻 `screenshots/f-image-*.jpg`、`f-video-*.jpg`、`f-history-*.jpg`、`f-evidence-47-zoom.jpg`、`f-evidence-570.jpg`、`f-cancelled-1280.jpg`。记录 `screenshots/F_BROWSER_MEASUREMENTS.json`。未用设计图冒充运行页面。

## 测试与初轮问题

- Vue31 PASS/36.35秒（包含原11项），build PASS/26.77秒，原大chunk提示保留。
- 非模型API/业务联合106 PASS/63.62秒，包含B/C/D/E/F；F4项覆盖Range/HEAD/206/416/权限/损坏/cache/原图。
- 真实图片/D视频/E视频5 PASS/298.84秒；与前项不同集合，共111项，不描述为同轮。
- 冻结Python819 PASS/11个预期独立API文件跳过，311.90秒；独立API集合覆盖这些文件。
- compileall api services web offline、模型/inference/tracker/association/rules指纹、git diff --check通过；文档后置门禁另行追加。

初轮组件测试需等待Element Plus渲染、设置中文locale；API fixture需登记合法图片统计，已修正。新增测试发现视频分页把total混为total_count，已修复真实契约并浏览器确认分页恢复。Python初轮818 PASS/1 FAIL/11 SKIP：本次浏览器任务ZIP位于仓库内触发原P1资产门禁；确认全部结束后仅迁移本次隔离root到仓库外、保留产物，再全量819 PASS。没有删除或放宽测试、没有改算法。

## 运行与回退

确认旧实例无活动任务后手动退出，再启动一个正式root Worker：

```powershell
Set-Location 'E:\大四\创业实训\odplatform-ppe\front'
npm ci
npm test
npm run build
Set-Location ..
& .\scripts\start_frontend_local.ps1 -ApiPort 8768
# http://127.0.0.1:8768/offline
```

独立测试设置ODPLATFORM_OFFLINE_ROOT为仓库外专属目录；`.venv-frontend-api`启动Uvicorn单Worker。Vite已有VITE_API_TARGET可指向实际API（默认8765）；本次8774为同源构建页面。没有新增依赖，npm/API锁不变。README同步。

关闭全部新离线调度设置ODPLATFORM_OFFLINE_IMAGE_EXECUTION=0后重启；仅关闭视频用ODPLATFORM_OFFLINE_VIDEO_EXECUTION=0，仅关闭事件分析用ODPLATFORM_OFFLINE_EVENT_EXECUTION=0；保留既有任务。原七页、Streamlit和B/C/D/E API保留。

## 限制及G门禁

P9-C长期资源风险保持；E历史偶发CFR拒绝根因未证实，本次通过不宣称修复。FullHD/4K、600秒、长期稳定性、其他浏览器编解码、异常网络下载未全面验收。首次大文件哈希有等待；极近时间轴标签可能重叠，可从列表定位。一个root一个API进程，跨root无全局准入锁。G需独立授权，完成整体验收/发布和更广规格/长期风险复核。本次停止F。

Commit: NOT EXECUTED
Push: NOT EXECUTED
Tag: NOT CREATED
Final Status: HUMAN REVIEW PENDING

## 最终复核

文档与资产门禁52 PASS（51.07秒）；最终diff检查、冻结指纹、敏感模式、大文件与忽略规则通过。没有新增未跟踪的超过1MB文件，dist与运行联调记录被忽略。最终浏览器570帧播放到19秒，ended=true、readyState=4、无解码错误；实际MP4下载SHA256通过。补充证据放大截图 `screenshots/f-evidence-570-zoom.jpg`。独立8774审核实例保留，原8768不变；HEAD未变化。
