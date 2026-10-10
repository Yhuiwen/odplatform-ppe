# V1.2-D 原分辨率逐帧检测与 H.264 导出报告

日期：2026-10-09。分支 `main`；Base/Current HEAD 均为 `1d283dcbe37d853dab3240ebe4cc6084c7be9e42`。B/C 未提交改动完整保留。提交、推送、Tag 均未执行；**HUMAN REVIEW PENDING**。

## 审计与授权边界

核对 AGENTS、Charter、计划、状态、ADR、Changelog、门禁、风险、参考资产、数据卡、Phase 9 和 B/C 报告。仓库没有独立 V1.2-A 报告文件，未虚构该文件；以已提供的 D 任务、现行 B/C 报告及实际资源检查作为本阶段依据。

原 `VideoReader` 顺序解码为 `FrameData`，能检查声明帧数与实际解码数。`VideoInferenceService` 和旧 `AnnotatedVideoService` 聚合帧记录，不用于本阶段长视频缓存。原 M-007 Writer/Service、YOLO、ByteTrack、PPE 关联、合规规则及事件库 Schema 都未修改。B 的任务库、进程锁、准入锁、Publisher 和 C 的冻结推理/渲染实例继续复用。

## 实现

- `offline/video_processor.py`：原尺寸顺序解码，每帧一次 `InferenceService.infer_frame`，现有 `AnnotatedFrameRenderer` 绘制，再逐帧提交 FFmpeg。只保存当前帧、当前检测及计数；`frames.jsonl` 每帧立即写入，包含 frame_id、timestamp、detection_count、detections、原尺寸坐标。
- `offline/video_encoder.py`：明确 BGR24 原尺寸输入、精确 Fraction FPS；libx264 / CRF18 / medium / yuv420p / faststart / 无音轨。单帧有界队列、16×1024 字节 stderr 环形缓存、独立排空线程、30 秒写入/收尾监督；取消或超时 kill/wait 并 join 线程、关闭管道。不回退 mp4v。
- `offline/video_probe.py`：容器/元数据检查后，单线程 ffprobe 解码逐帧时间戳至临时文件，校验严格递增、时间基允许的帧间隔、累计 CFR 时间和帧数。保留精确有理帧率。VFR、无效时间戳、旋转、奇数宽高、超过限制的规格明确拒绝。探测有超时及输出限制，不构建帧列表。
- Worker 的 `PROCESSING→ENCODING→COMPLETED` 覆盖实际编码收尾、完整输出解码、ZIP 验证和发布；视频进度在完成之前封顶 99%。HTTP 返回真实 elapsed_seconds；视频结果登记实际检测数及总处理耗时，candidate_count 保持 null。任务库继续使用 B/C 的版本 2，未改事件库。
- 图片与视频共用一个持久 Worker/模型实例。支持媒体间 FIFO；同秒上传用 SQLite 插入顺序打破时间戳并列，避免 UUID 排序造成插队。长视频占用 Worker 时，图片排队等待，不抢占视频。刷新/查询不创建新 Worker 或推理任务。
- 实时监控与离线任务使用同一个进程内准入锁，同一任务根目录使用 OS 文件锁；禁止多 Uvicorn Worker。不同根目录/不同服务进程不具有全局 CPU 准入保证。
- 启动 capabilities 前执行真实小尺寸 libx264 自检。主开发前另完成 128×72、30FPS、3 帧 H.264/MP4 小规模编码，FFmpeg 8.1.2 正常退出。

## 冻结指纹

| 资产 | 重新核验 SHA256 |
| --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |

冻结模型大小 5,479,891 字节；640/conf0.25/IoU0.45/五类 filter 不变。仍通过 C 的显式应用层执行授权，不修改被冻结 YAML 的 execution_enabled。machinery/vehicle 标记 NOT_EVALUATED，未将未评估类别写成零检测。继续禁止 Ultralytics AutoInstall；独立 API 环境确认没有 pi-heif。没有新增 Python/npm 依赖，没有训练或下载。

## 产物及完整性

任务输出：`annotated.mp4`、`frames.jsonl`、`summary.json`、`video_verification.json`、`results.zip`。ZIP 的 MP4 使用 ZIP_STORED，其余文件可压缩；分块打包、检查磁盘/取消，校验精确成员名单、CRC、逐成员 SHA256。摘要/验证 JSON 与生成字节比较，JSONL 比较流式生成指纹、顺序和数量；输出 MP4 完整解码检查尺寸、实际帧数、H.264、yuv420p、FPS 和无音轨。API 下载再次核验数据库登记清单的 SHA256/大小。

只有五项产物均验证并发布后才写 COMPLETED。Manifest 沿用 B 的 SQLite 持久化清单，不增加另一套任务/路径访问接口。取消、失败清理任务自己的已知暂存/未完成输出；输入保留，终态不允许重新领取。重启将 PROCESSING/ENCODING/CANCELLING 修复为 INTERRUPTED、清理已知输出，完整 QUEUED 保留。不从半个视频续跑。

音轨仅在含音轨任务明确提供 `audio_discard_confirmed=true` 时丢弃。摘要记录 source_has_audio/output_has_audio/audio_policy。CRF18 是有损压缩，不能宣称像素无损。

`event_analysis_status=NOT_IMPLEMENTED`、`confirmed_events=null`、`evidence_count=null`；检测框观测不是事件或独立人数。本阶段不调用跟踪/合规/事件服务，真实测试的已有事件总数保持不变。

## 真实视频结果

| 项目 | 已有短视频 | 用户指定视频 |
| --- | --- | --- |
| 输入 | P4C-2 construction-workers-public-domain.mp4 | test/4afa6b121fe5db806c3ff416bafdf571.mp4 |
| 输入编码/音轨 | H.264 / 无 | HEVC / AAC，确认移除 |
| 输入/输出尺寸 | 1280×720 / 1280×720 | 1280×720 / 1280×720 |
| 精确输入/输出 FPS | 24000/1001 | 30/1（有理数规范表示 30） |
| 实际输入/推理/标注/提交/实际输出帧数 | 47 / 47 / 47 / 47 / 47 | 570 / 570 / 570 / 570 / 570 |
| 播放时长 | 1.960292 秒 | 19 秒；输入容器含音轨时长 19.017211 秒 |
| 处理范围耗时（至输出完整验证） | 10.672 秒 | 106.109 秒 |
| 墙钟耗时（含 HTTP、启动、发布） | 11.718 秒 | 107.484 秒 |
| 平均处理 FPS / 播放 FPS | 4.404 / 23.976 | 5.372 / 30 |
| 输出字节 | 451,930 | 3,951,681 |
| 真实检测观测总数 | 77 | 1,829 |
| 采样 API 父进程峰值 RSS | 585,383,936 | 621,641,728 |
| 结束父进程 RSS | 499,728,384 | 524,681,216 |

570 帧五类计数：person607、hardhat487、no_hardhat107、vest499、no_vest129。随后在**同一 Worker** 再处理短视频 47 帧，模型对象相同，准入锁释放；重复任务后 RSS 527,040,512 字节。570+47 的父进程 CPU user/system 35.734375/5.65625 秒。任务结束没有残留 FFmpeg 子进程。RSS 为父进程观测，不包括编码子进程峰值；少量任务无法证明 P9-C 长期资源稳定性。编码与推理通过管道交叠，没有将收尾等待冒充独立 encoding_seconds。

| 文件 | SHA256 |
| --- | --- |
| 47 帧输入 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |
| 47 帧输出 MP4 | `c985a26ab6b7e1f17411ed9f1a33f8bdc6fac4110d84f075d911e3d56cac74f6` |
| 570 帧输入 | `a734a43322442737da15979709f83d06819b9a94f9112cdf3ee0c7a1592d0695` |
| 570 帧输出 MP4 | `c9a9e52644d122711ada73a4aeee68a24ca5fac4f66f26829b5034f5b5510488` |
| 47 帧结果 ZIP | `ce08041c0df636d5a2ffb59abfd87b856d41fb677330ba477ecbebf74f42d766` |
| 570 帧结果 ZIP | `ffbd8738657da00ec46daf2b6516166a9dd64b430a053f6cee7bcb199bd478cb` |

实际 MP4、JSONL、摘要、验证报告、运行指标和播放截图保留在 Git 忽略的 `artifacts/validation/v12d/47/`、`570/`、`playback.png`。额外导出的两个验证 ZIP 保留在仓库旁的 `odplatform-ppe-v12d-validation/47/` 和 `570/`。原任务 ZIP 仍由隔离任务 API 验证下载，未改变正式 Publisher 的输出契约。

Codex 内置浏览器实际播放两段 MP4 到 ended=true，readyState4，无 video.error。570 帧视频宽高 1280×720、currentTime/duration19 秒；短视频 1.960292 秒。目视检测框和类别/置信度标签；源画面的黑边保留，未裁剪/缩放输出。相邻标签的局部重叠沿用原 renderer 限制。临时验证服务器/浏览器已关闭，未重启用户原服务。

## 测试与门禁

- 联合 B/C/D/原 API：67 PASS（含真实图片、47 帧、570 帧及顺序重复视频）。另一次非真实模型集合 65 PASS（包括新增视频重启 API 测试）；合计 68 项不同测试有 PASS 证据。最终视频专项 28 PASS。
- Vue Vitest 11 PASS；`npm run build` PASS，保留已有大 bundle 警告。本阶段不增加 Vue 离线页。
- 文档同步后，documentation_governance/data_source_evidence 专项 **52 PASS**；最终未跟踪文件检查无大文件、模型/视频/ZIP等二进制资产或行尾空白。临时 8771/8772 验证端口已释放。
- 冻结 Python 全量复验：**819 PASS / 7 SKIP，356.51 秒**。7 个文件按独立 FastAPI 环境隔离策略跳过，均有独立 API 环境验证。初轮 818 PASS / 1 FAIL / 7 SKIP；唯一失败为额外验证 ZIP 被旧 P1 资产扫描视为未登记。仅移动本阶段自己生成的两份 ZIP，保留内容；测试下载 ZIP 改为隔离临时目录，未修改或放宽旧门禁。复验没有失败。
- compileall api/services/web/infra/offline、diff --check、冻结指纹、凭据模式与忽略规则检查 PASS；模型、原 M-007、core 和冻结规则无差异。
- 实际启动独立 Uvicorn 单实例 `127.0.0.1:8771`，health 和 offline capabilities 返回正常，真实 libx264 自检通过；随后关闭该临时实例。普通部署继续使用 8765。
- 空/损坏媒体、错误扩展/MIME由 B 和 Reader 测试覆盖；D 覆盖中间帧失败、编码器不可用/异常退出/管道写失败及超时、输出哈希/JSON损坏、帧数/尺寸/编码/FPS/音轨异常、空检测、非标准偶数尺寸、分数 FPS、VFR拒绝、FullHD三帧编解码/顺序、音轨未确认、处理/编码/关闭取消、重启、磁盘限制、FIFO、重复领取及实时资源冲突。

测试命令：

```powershell
& .\.venv-frontend-api\Scripts\python.exe -m pytest tests/unit/test_offline_jobs.py tests/unit/test_offline_image_processor.py tests/unit/test_offline_video_processor.py tests/integration/test_offline_api.py tests/integration/test_offline_image_real.py tests/integration/test_offline_video_real.py tests/integration/test_frontend_api.py -q
& .\.venv-frontend-api\Scripts\python.exe -m pytest tests/integration/test_offline_video_recovery.py -q
& .\.venv-final-demo\Scripts\python.exe -m pytest -q
& .\.venv-final-demo\Scripts\python.exe -m compileall api services web offline
cd front
npm test
npm run build
cd ..
git diff --check
```

## 初轮问题、限制及 E 阶段边界

初轮测试保存下载文件误用了未公开的 filename 字段，已改为固定受控 artifact-key映射；未更改 API 路径访问边界。另发现终态与 finally 资源释放的短暂异步间隔，测试以有界等待核验释放，不把瞬时状态误认为泄漏；正常关闭取消已修复为 CANCELLED。初轮曾观察到旧探测路径对真实视频的时序拒绝，根因未单独证实；随后使用单线程 ffprobe 和严格间隔验证的两轮真实任务通过，未放宽 CFR 判定。

旧 P1 源码资产扫描不识别运行时生成 ZIP。验证 ZIP 已隔离；在包含实际业务 ZIP 的工作目录执行该历史资产门禁仍可能报未登记资产，应区分源码资产审计与任务 manifest 校验。本阶段未扩大训练资产白名单。

无已验证的真实 1920×1080 视频，因此真实 FullHD YOLO链路 NOT_EXECUTED；确定性三帧 FullHD 测试只是编解码/尺寸/顺序证据。600 秒/4K 视频上限没有性能验收；逐帧探测有超时，超时任务明确失败。VFR、旋转、奇数尺寸不支持。同步 CPU 模型内部不能立即取消；30秒管道监督和算子后检查点不是硬实时保证。程序级内存有界不等于第三方运行时不增长，P9-C 保持 PARTIAL/FROZEN。

E 扩展点为 `VideoProcessor(frame_observer=...)`，在每帧推理之后同步获得原尺寸 FrameData 和同一批 DetectionResult。当前无 observer，不新增事件或跟踪；未来 E 必须消费该批结果，不重跑 YOLO。本阶段结束，不自动进入 E。

Changed: 新增三个视频模块、视频单元/真实链路/恢复测试；扩展 worker/jobs、API装配/能力/elapsed、原 API 测试隔离及 C 实测断言；同步 README、状态、Changelog、门禁、Phase 9、开源记录和交接。

回退：`ODPLATFORM_OFFLINE_VIDEO_EXECUTION=0` 后重启单实例，只关闭视频处理；`ODPLATFORM_OFFLINE_IMAGE_EXECUTION=0` 关闭共享离线检测执行。保留独立任务库及输入，不删除运行资产。原 Streamlit 与 M-007 工具保留。

Commit: NOT EXECUTED

Push: NOT EXECUTED

Tag: NOT CREATED

Final Status: HUMAN REVIEW PENDING
