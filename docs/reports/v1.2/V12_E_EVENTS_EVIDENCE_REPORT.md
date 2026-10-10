# V1.2-E 离线事件与关键证据实施报告

日期：2026-10-09。Git：main，Base/Current HEAD 均为 1d283dcbe37d853dab3240ebe4cc6084c7be9e42。B/C/D 未提交成果完整保留；本次用户附件明确 D 已通过阶段审核，授权 E，不授权 F 或发布。本文为本次 E 验证记录，不改写 B/C/D 历史报告。

## 架构和单次推理

新增 offline/event_collector.py、offline/evidence_store.py；扩展 offline/video_processor.py、worker.py、jobs.py、media.py、image_processor.py、api/main.py、api/offline.py；新增 E 单元/接口/真实测试并扩展原视频恢复测试。没有修改 core、services、infra 的冻结业务实现；video_encoder.py 未修改；video_probe.py 仅增加安全的帧号/tick/FPS诊断，CFR 判定与编码方案未修改。没有新依赖、模型或数据下载。

VideoProcessor 保留既有两参数 frame_observer 的标注前调用；新增可选 collector_factory(context)，每 Job 创建一个 Collector，标注后接收同一个 FrameData、同一批 DetectionResult 和当前原尺寸标注 ndarray。每帧唯一 infer_frame 调用先完成，再由两条消费路径使用；真实测试记录源 Job 的每一次调用帧号，必须精确等于 range(47)/range(570)。证据不会调用 YOLO，也不二次分析视频。未启用 Collector 时 D 的五产物、NOT_IMPLEMENTED/null 状态和测试保持兼容。应用默认启用 E；ODPLATFORM_OFFLINE_EVENT_EXECUTION=0 后重启可回退到 D，保留已有结果。

Collector 复用 ByteTrackPersonTrackingAdapter → PPEPersonAssociationAdapter → ComplianceService → EventEngine。显式只传 person 给跟踪器，其余四类 PPE 给关联器。空检测帧照常调用跟踪/关联/规则/事件引擎。没有调整算法参数、时序确认、恢复、冷却或 vest 原有窗口。测试按真实视频秒数组织确定性序列；5 帧和 1 秒条件与 vest 1.5 秒窗口照常生效。事件用 EventEngine 直接返回，避免 EventService 默认 JSONEventStore 写入实时路径。

每任务持有新 Tracker、关联器、合规服务和 EventEngine；finally 关闭任务 SQLite 并 reset Tracker/EventEngine。连续任务仅共享原冻结检测模型，不共享轨迹、时序候选或去重状态。unique_track_ids 是任务内轨迹 ID 数，不是独立人员数。active_tracks 明确标记 current_frame_returned_observations，是当前返回的有效轨迹观测数，不包含后台保留的 lost tracks。

## SQLite、事务及隔离

JobEventDatabase 继承既有 Database，运行原 events/workers/snapshots 迁移；EventRepository/EventIngestService 保持原契约。唯一增加的 offline_evidence 表只存在任务库，用 event_id 外键、一对一 evidence_id 和 job_id 保存双图证据关系。一个任务仅持有一个连接，事件发生时增量持久化，不逐帧新建连接。事件 ID 重复会拒绝并使任务失败；只有事件/证据交叉校验通过才允许完成。

数据库先写 staging/events.sqlite3，最后 checkpoint WAL、切换 DELETE 并关闭；确认 WAL/SHM 已消失后按 manifest 发布到 output/events.sqlite3。采用 B 受限的平面文件存储，以免放宽其任意路径访问边界；SQLite 是内部受验证产物，不对外下载、不进入 ZIP。API 使用 manifest 定位并重新核验数据库 SHA256，随后 mode=ro 连接查询，不写数据库。

occurred_at/created_at 由原 IngestService 使用当前 UTC 持久化时间；source_timestamp 对外为 video_timestamp_seconds，frame_id 为源视频从零开始的帧号。不会将相对视频秒数当成现实日期。source 固定为 offline:video:<job_id>，不包含原上传绝对路径、RTSP 密码或个人身份。

Collector 没有 AlertService、Web/TTS 适配器；测试把 AlertService 两个派发入口替换为调用即失败，并验证两任务处理后实时事件数量、实时 MonitoringService 对象及其状态均不变。真实视频及重复上传另行验证实时事件总数不变。任务事件只属于自身 Job，不覆盖实时快照。

## 原始/标注关键证据

SnapshotStorage/EncodedSnapshot/SnapshotReference 的冻结契约仅支持 JPEG，不能作为无损 PNG 的证据 Schema。新增任务 PNG 适配器复用 SnapshotStorage 的路径约束，OpenCV 无损 PNG 编码、独占暂存文件、fsync、原子重命名、SHA256/文件大小/Pillow 完整解码与尺寸验证；原 JPEG 服务及其数据库 Schema 未改。

在 EventEngine 首次确认当前事件时，从未经原地绘制的解码 frame.image 保存 original，直接保存该帧 renderer 的 annotated 数组；两张图都是原视频尺寸。真实测试重新解码输入，仅用于校验，PNG 原始证据必须与触发帧逐像素一致；不会为校验再次推理。元数据交叉核对 job/event/evidence ID、类型、track、confidence、bbox、frame_id、相对秒数和两图 SHA256。已目视检查实际标注证据；原视频黑边保留，标签局部重叠仍属于现有渲染器限制。

staging/output 使用 original_EVT-<uuid>.png、annotated_EVT-<uuid>.png 与 evidence_index.json 平面文件；ZIP 内映射到 evidence/original/<event_id>.png、evidence/annotated/<event_id>.png、evidence/index.json。正式 API 不接受文件路径，只接受任务、事件、证据 UUID 和固定 variant。返回图像元数据不含服务器 filename/zip_path。

## 输出、统计与发布

保留 D 的 annotated.mp4、frames.jsonl、summary.json、video_verification.json、results.zip；增加 events.json、UTF-8 BOM events.csv、证据清单和双图。JSON 为 offline-events-v1/offline-evidence-v1 集合，包含 job_id/items。CSV 包括事件/证据 ID、类型、轨迹、置信度、帧号、视频秒数、真实 created_at、source、双图 SHA256、尺寸和 bbox；公式起始符及前导控制字符会加单引号净化。

流式从 SQLite 导出 JSON/CSV，不积累全视频图像或 DetectionResult；导出写入的预期 UTF-8 摘要与重新读取文件 SHA256 比较，避免坏文本被重新哈希后冒充通过。summary 增加 event_analysis_status、confirmed_events、events_by_type、track_observations、unique_track_ids、active_tracks/scope、unknown_associations、evidence_events、evidence_image_files、event_analysis_frames；总事件数必须等于类型分组之和。evidence_count 为兼容别名，统计事件数，不是图像数。

未知关联数严格使用 AssociationResult.unknown_count：缺少 PPE 不自动增加未知关联观测；PPE_UNKNOWN 由原合规/时序规则确认。machinery/vehicle 仍 NOT_EVALUATED。没有足够证据就不强制归类 NO_HELMET/NO_VEST。

ZIP 流式写入，MP4 ZIP_STORED，其余 DEFLATED，验证唯一固定成员、CRC、逐成员 SHA256；不含原始上传和 SQLite。所有文件暂存、验证，再经 ArtifactPublisher 发布；数据库状态 COMPLETED 是跨文件可见性门禁，不声称多文件 rename 是一个文件系统事务。部分发布后取消/失败仍不可读，并清理本任务已知生成文件，保留原输入。启动修复 INTERRUPTED/FAILED/CANCELLED 的生成文件，不从中间帧恢复时序。

## F 阶段可用的只读 API

统一前缀 /api/v1/offline：

| 方法 | 路径 | 契约 |
| --- | --- | --- |
| GET | /jobs/{job_id}/events | limit 1..100、offset>=0、event_type 三类筛选；job_id/items/total/limit/offset |
| GET | /jobs/{job_id}/events/{event_id} | 单条事件与双图元数据 |
| GET | /jobs/{job_id}/evidence | 同一确认事件证据集合及分页筛选 |
| GET | /jobs/{job_id}/evidence/{evidence_id} | 当前验证过的证据元数据 |
| GET | /jobs/{job_id}/evidence/{evidence_id}/image | variant=original/annotated，PNG，no-store |

未完成任务/不存在/跨任务记录返回 404；无效筛选/variant 返回 422；哈希、图片或关系损坏返回安全 409。接口只读，无离线 handled 修改。events_db 从任务公开 artifact_keys/列表排除，通用下载也拒绝它。旧 completed D 任务没有 E 数据，事件接口不会编造零事件。capabilities 增加 event_analysis_available。前端 F 尚未实现，本阶段没有修改 Vue。

## 测试覆盖和初轮问题

E 单元 29 项：持续违规去重、多人双类型、恢复与冷却后新周期、缺失 PPE/歧义、空帧/丢失、真实 ByteTrack 重置、重复 Track ID 的跨 Job 隔离、错帧拒绝、双图损坏/缺失/关系错误、取消/SQLite/证据写入/重复事件/Observer 异常、导出哈希拒绝、CSV 注入、零事件完整视频、ZIP 和 FFmpeg 异常清理。E API 6 项，视频重启测试增加 SQLite/WAL/SHM/双图的清理核验；B 资源准入测试继续覆盖实时占用。

初轮真实测试最后记录数据库大小误用了公开 Job DTO，已改为内部登记记录；早期 mock 测试误用 1 秒间距而无法满足原 vest 1.5 秒窗口，修正为合法 0.3 秒采样，没有改规则。告警隔离测试改为验证实际 idle 监控对象/状态保持，而不是错误假设对象不存在。

一次 API 联合收集与 Vite 重建并行导致 dist/assets 临时不存在；之后构建与 API 回归顺序执行。真实 ByteTrack 导入 Ultralytics 会修改全局 Pillow.open，坏图片尝试导入缺失的可选 pi-heif；图片上传/处理边界新增 ImportError 安全转换为 INVALID_MEDIA，保持 YOLO_AUTOINSTALL=False，不安装新包。

曾有一轮联合测试 100 PASS / 2 FAIL，其中坏图片边界失败已修复；570 帧 E 任务 FAILED 的原临时记录没有保留具体错误码。后续联合运行 106 PASS / 1 FAIL，已定位为推理前 UNSUPPORTED_TIMING、processed_frames=0。失败上传文件 SHA256 与原输入一致；重新提取 570 个 PTS 的相邻间隔均为 3000 tick，连续五次原严格 probe_cfr 复核通过。增加安全的帧号/tick/FPS 诊断，没有改判定或加入自动重试。独立 D/E 四项真实视频 4 PASS（324.55秒），最终完整联合 107 PASS（349.91秒）。历史偶发异常的根因仍未证实，不能宣称已修复；P9-C 继续 PARTIAL/FROZEN。

## 冻结资产

- 模型 SHA256：1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61
- 推理配置：0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c
- tracker.yaml：42ec753ee1511b9de652a750b2d67a384f4aea95d56b43a98d287c877121f10a
- association.yaml：be32af654ab76e4d1dd7e82c1a3fb0ffbbed2026e9711bea73fcacfc703073a6
- rules.yaml：ecf291090f3bd64cbf755dad2d00f68105d9301ca3ae97c275399c39cd3a623c

以上指纹复核，冻结模型、规则、core/services、训练资产没有本阶段变更。

## 运行、回退及限制

沿用独立 .venv-frontend-api 和一个本地 Uvicorn Worker。共享模型/视频开启时默认 E 开启；设置 ODPLATFORM_OFFLINE_EVENT_EXECUTION=0 再重启，仅新任务回到 D，不删除已有 E 历史和输入。ODPLATFORM_OFFLINE_VIDEO_EXECUTION=0 可停止新视频调度。用户当前 8768 服务未被重启，需要人工审核后重启才加载新代码。独立受控子进程 127.0.0.1:8773 Uvicorn 健康与 image/video/events capabilities 均通过，已释放该子进程和端口。

没有真实 FullHD/4K 或 600 秒资源验收；同步模型仅检查点取消，跨根目录的不同 API 进程不具备全局资源锁。逐任务 Tracker 状态隔离不等于长期第三方内存稳定。P9-C 未关闭。事件数和疑似检测框数不是同一指标；证据图片数为事件数的两倍。F 页面、离线事件处理状态、实时告警均不在 E 范围。

Commit: NOT EXECUTED
Push: NOT EXECUTED
Tag: NOT CREATED
Final Status: HUMAN REVIEW PENDING


## 最终实测与门禁

| 项目 | 47 帧 | 570 帧 |
| --- | --- | --- |
| 输入/推理/标注/提交/输出帧 | 47/47/47/47/47 | 570/570/570/570/570 |
| 检测框 | 77 | 1829 |
| 确认事件 | 1 | 2 |
| 事件类型 | {'PPE_UNKNOWN': 1} | {'NO_HELMET': 1, 'NO_VEST': 1} |
| 轨迹观测 | 66 | 580 |
| 不同 Track ID | 2 | 7 |
| 未知关联 | 1 | 46 |
| 证据图像数 | 2 | 4 |
| 原分辨率 | 1280×720 | 1280×720 |
| 播放 FPS | 24000/1001 | 30 |
| 摘要处理秒数 | 12.25 | 118.46900000004098 |
| 平均处理 FPS | 3.836734693877551 | 4.811385256900985 |
| 任务总处理秒数（含验证/ZIP/发布） | 13.141000000061467 | 120.21900000004098 |
| 父进程峰值 RSS bytes | 581545984 | 642809856 |
| 任务后 RSS bytes | 503115776 | 543027200 |
| FFmpeg 峰值 RSS bytes | 311144448 | 419557376 |
| SQLite bytes | 106496 | 106496 |
| 双图总 bytes | 1866318 | 1521723 |

570 帧输出 H.264/yuv420p、30 FPS、19秒、无音轨；47 帧 24000/1001 FPS。检测数77/1829与D一致，输出 MP4 SHA256 也与D一致。事件触发关系和双图 SHA256 完整保存在对应 events.json/evidence_index.json。真实输入证据逐像素一致、原尺寸PNG、ZIP成员SHA/CRC、CSV BOM/字段映射均验证通过。

- 47 帧实际证据与指标：`artifacts/validation/v12e/47/de9f5dc52a154e2b90fda15895242295/`。SQLite内部文件不额外导出；ZIP只在隔离临时测试目录下载验证，不加入源码仓库。
- 570 帧实际证据与指标：`artifacts/validation/v12e/570/3a7c583ee6c642039e4acdb231ec0fc9/`。SQLite内部文件不额外导出；ZIP只在隔离临时测试目录下载验证，不加入源码仓库。

当前同轮 D 摘要耗时 102.203 秒，E 118.469 秒；此前D阶段基线106.109秒/5.372FPS。E增加关联、事件、证据和导出；有限本地多轮测试存在CPU/热态/采样差异，未进行受控逐模块profiling，不能把耗时差全部归因于单一模块。没有全量帧或检测列表缓存，任务后无FFmpeg进程，准入释放且随后47帧复用模型/独立跟踪。没有据此关闭长期内存风险。

- 最终独立 API 联合：107 PASS，349.91秒；没有跳过真实资源测试。非模型专项102 PASS，48.95秒；E单元29、E接口6均通过。真实图片与D兼容任务也包含在联合集合。
- 冻结 V1 完整回归：819 PASS / 10 个预期独立FastAPI文件跳过，497.73秒；这些文件由独立API环境覆盖。
- Vue：11 PASS，build PASS（已有大chunk提示）；未修改前端。
- 实际单实例Uvicorn 127.0.0.1:8773 健康、图片/视频/事件能力为true，验证子进程已关闭；用户原服务未重启。
- compileall api services web infra offline、git diff --check、冻结指纹、源码范围、敏感模式和大文件检查通过；文档更新后门禁另行追加。

最终命令：

```powershell
& .\.venv-frontend-api\Scripts\python.exe -m pytest tests/unit/test_offline_jobs.py tests/unit/test_offline_image_processor.py tests/unit/test_offline_video_processor.py tests/unit/test_offline_event_collector.py tests/integration/test_frontend_api.py tests/integration/test_offline_api.py tests/integration/test_offline_video_recovery.py tests/integration/test_offline_events_api.py tests/integration/test_offline_image_real.py tests/integration/test_offline_video_real.py tests/integration/test_offline_events_real.py -q --tb=short
& .\.venv-final-demo\Scripts\python.exe -m pytest -q --tb=short
& .\.venv-frontend-api\Scripts\python.exe -m compileall api services web infra offline
cd front
npm test
npm run build
cd ..
git diff --check
```

E implementation gate: PASS / HUMAN REVIEW PENDING. Global Phase 9 acceptance and P9-C unchanged. No F, commit, push or tag.

文档更新后复核：冻结环境 documentation_governance + data_source_evidence 共52 PASS，46.47秒。compileall 与 git diff --check 再次通过；模型与四项冻结配置指纹一致。新增未跟踪文件没有超过1MB的文件，运行验证目录与front/dist均被忽略。工作区保留B/C/D/E未提交改动，HEAD未变化。
