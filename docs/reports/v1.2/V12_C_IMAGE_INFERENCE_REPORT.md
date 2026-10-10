# V1.2-C 图片推理与原尺寸标注实施报告

日期：2026-10-09。分支 `main`；基线与当前 HEAD 均为 `1d283dcbe37d853dab3240ebe4cc6084c7be9e42`。V1.2-B 未提交工作树已保留，本阶段继续在同一工作树实施。未 commit、push 或打 Tag。

## 实现与文件

- `offline/image_processor.py`：实现 B 阶段 `JobContext`/`ArtifactPublisher` 契约。固定使用现有 `InferenceService` → `YOLODetector` → `DetectionResult` → `AnnotatedFrameRenderer`，不实现第二套模型或检测参数。处理发生在单 Worker，HTTP 上传请求只登记任务。
- `offline/worker.py`：按媒体类型从持久化队列领取任务；生产只接入图片 Processor，MP4 留在 `QUEUED`，不阻塞后续图片。模型对象随单 Worker 复用，检测时的图片数组与文件句柄在任务结束后释放；停止仅在安全检查点生效，不能中断正在执行的 CPU 算子。失败/取消清理该图片任务的暂存和未完成产物。
- `offline/migrations/0002_image_results.sql`、`offline/jobs.py`：增量添加检测框数、疑似违规检测项数、总处理耗时；旧 B 任务与状态原样保留。没有修改 V1.1 事件库。
- `api/main.py`、`api/offline.py`、`configs/offline_jobs.toml`：在同一 FastAPI 生命周期装配图片 Processor，明确 `image_execution_enabled=true` 的应用层授权和冻结配置 SHA256；`capabilities` 分别报告图片和视频处理能力，任务查询返回真实统计和产物可用状态。`ODPLATFORM_OFFLINE_IMAGE_EXECUTION=0` 可关闭图片执行而不改冻结推理配置。API 启动时设置 `YOLO_AUTOINSTALL=False`，禁止模型库运行时自动安装可选包。
- 新增图片 Processor 单元测试、旧 B 库升级/混合队列测试，以及真实模型 HTTP 全链路测试。前端和原检测/跟踪/合规规则未修改。

## 冻结模型与图片策略

冻结权重 `models/checkpoints/EXP-001/best.pt` 的 SHA256 为 `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`；当前获准配置 `configs/inference.yaml` 的 SHA256 为 `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`。这两个值在开发后重新核验。应用层只覆盖 `execution_enabled=True`，并校验配置指纹；冻结配置文件、阈值、IoU、类别过滤和模型文件均未改动。配置保持 640 像素模型输入、`conf=0.25`、`IoU=0.45`。

Pillow 保留原始上传字节，读取编码宽高和 EXIF orientation；将方向标准化后作为检测坐标系。RGBA/透明 PNG 合成在白色背景，灰度转 RGB，然后只做一次 RGB→BGR，向现有检测器与渲染器传递标准化原尺寸 ndarray。输出 `annotated.png` 宽高必须与标准化后的宽高相等；检测框由原 `AnnotatedFrameRenderer` 校验类别并裁剪到图片范围。`summary.json` 同时记录编码尺寸、EXIF 方向、标准化尺寸及输出尺寸。像素限制在解码前后检查。

冻结 `class_filter` 仅包含 `person/hardhat/no_hardhat/vest/no_vest` 五类，尽管模型还列出 `machinery/vehicle`。本阶段没有扩充过滤条件。五类实际检测框有真实计数；另外两类标为 `NOT_EVALUATED`，不能写作零检测。`no_hardhat/no_vest` 只计作单帧**疑似违规检测项**，保留置信度和框坐标；不创建 Track ID、已确认事件或跨帧合规结论。

## 结果、完整性与取消

每个完成图片任务提供 `annotated.png`、`detections.json`、`summary.json`、`results.zip`。JSON 含 job/input/model/config 指纹、原尺寸坐标、类别统计和疑似项。ZIP 只打包前三个产物，不重复上传原图，也没有路径前缀。产物先写入本任务 `staging`，验证文件内容哈希、PNG 解码/尺寸、JSON 计数与 ZIP 条目/CRC，再经 B 阶段 `ArtifactPublisher` 发布。只有四项产物均验证、任务记录写入检测统计后才允许进入 `COMPLETED`。API 下载时重新检查登记的 SHA256 和大小；未完成任务不能下载。

排队取消为 `CANCELLED`；处理中转 `CANCELLING`，在解码、推理前后、写入及发布检查点停止并清理未完成文件。进程重启后，未完成图片任务为 `INTERRUPTED`，清理其暂存/输出但保留原始输入；不从中间步骤冒充成功。MP4 没有处理器，保持排队供 D/E 阶段接入。

## 实测与门禁

使用 Git 忽略的已有真实工地图片 `artifacts/validation/P4C-1/input/construction-workers-public-domain.jpg`，在隔离临时任务根目录执行真实 HTTP 上传→Worker YOLO11 推理→原尺寸标注→四项产物下载。输入/输出均为 1024×766。检测框 5：`person=2, hardhat=1, no_hardhat=1, vest=0, no_vest=1`；疑似检测项 2。四项产物均通过下载 SHA256 复核，ZIP 可解压；与 V1.1 实时事件库的总事件数未发生变化。随后顺序执行两张相同输入，三张任务均完成且复用同一个模型对象。最后一次独立复测：首张任务数据库总处理耗时约 10.359 秒，三张总墙钟约 14.343 秒，50 ms 采样峰值 RSS 449,806,336 字节、结束 RSS 441,741,312 字节；四项产物大小依次为 1,289,123 / 2,073 / 2,020 / 1,286,783 字节。少量图片无法证明长期内存稳定性，P9-C 仍为 PARTIAL。

已直接目视检查一张实际输出，并复制到 Git 忽略的 `artifacts/validation/v12c/annotated_sample.png` 供人工复核。框和类别/置信度标签位于原尺寸画面上；右侧相邻目标的多个标签局部重叠，属于现有渲染器的标注布局限制，未为此修改冻结的共享渲染逻辑。

- 独立 API 环境：37 项单元/API/集成测试通过；其中真实模型 HTTP 链路 1 项通过。覆盖 JPG/PNG、EXIF、RGBA、灰度、异常宽高比、较大尺寸、空检测、多类别、坏图、尺寸上限、取消、旧库迁移、MP4 队首跳过、ZIP/哈希等。
- 冻结 V1 环境全量：819 通过，4 项独立 FastAPI 环境测试按设计跳过。
- Vue：11 项通过；`npm run build` 通过。`compileall api services infra offline`、`git diff --check` 通过。冻结模型及配置 SHA256 复核通过。
- 复测曾观察到 Ultralytics 对可选 HEIF 包的自动安装；已在 API 启动边界禁用 AutoInstall，并从独立 API 环境移除该包。未修改冻结运行环境或依赖锁；在可选包缺失状态再次完成 37 项 API 测试和真实图片链路。

## 限制与下一阶段边界

本阶段没有视频 Processor、H.264 编码、音轨处理或 Vue 离线检测页。`summary.json` 的 `processing_seconds` 统计至标注编码阶段，任务记录中的 `processing_seconds` 统计至产物验证与发布；两者范围有明确标注。进程内单 Worker 适合当前本地单实例服务；同步模型算子只能在前后检查点取消。D/E 阶段可按媒体类型注入视频 Processor 并继续使用同一任务、进度、取消和产物契约，但需单独解决视频编码、时序与长时资源验收，不得把本报告当作视频完成证据。


## 2026-10-09 C 补充核验（保留已授权 D 实现）

再次收到 C 要求后，仅修改 image_processor.py 和两份图片测试：新增 inference_seconds（infer_frame 调用耗时，首任务包括模型懒加载）、检测结果所属帧/来源验证，以及发布前原始输入 SHA256 复核。未改模型、配置、规则、Schema、共享渲染器或视频编码。前文“MP4 无处理器”是原 C 阶段历史记录；当前已有 D，本次隔离测试设置 ODPLATFORM_OFFLINE_VIDEO_EXECUTION=0，验证无视频处理器时 MP4 留队且不阻塞图片，没有撤销 D。

专项命令：`.venv-frontend-api/Scripts/python.exe -m pytest tests/unit/test_offline_jobs.py tests/unit/test_offline_image_processor.py tests/integration/test_offline_api.py tests/integration/test_offline_image_real.py tests/integration/test_frontend_api.py -q -s --tb=short`：39 PASS，29.26 秒。图片单元 15 项，包括错帧拒绝和推理期间输入被修改时拒绝发布。真实 HTTP 上传/推理/四产物下载/哈希及 ZIP 校验通过，三个顺序任务复用模型，实时事件总数不变。

本次实测输入/输出 1024×766，5 框（person 2、hardhat 1、no_hardhat 1、vest 0、no_vest 1），2 个疑似检测项；首次 inference_seconds=10.391，摘要 processing_seconds=10.594，三任务墙钟 13.86 秒。父进程采样峰值 RSS 459329536 字节，结束 449540096 字节。产物字节数 PNG/检测 JSON/摘要 JSON/ZIP：1289123/2073/2123/1286827。输入 SHA256：23aba350f9eace6466851d7e4b0178a3bf02ef208b31f20cbf46e71e049b8e42。新实际输出位于忽略目录 artifacts/validation/v12c/revalidation-inference-timing/；已目视查看 PNG，局部标签重叠仍是原渲染器限制。ZIP 下载验证在临时目录完成，未加入仓库。

Vue 11 PASS，build PASS（已有大 chunk 提示）。模型及配置指纹不变；YOLO_AUTOINSTALL=False，可选 pi-heif 未安装，无运行时依赖下载。P9-C PARTIAL/FROZEN 保持，少量图片不能证明长期资源稳定。machinery/vehicle 仍 NOT_EVALUATED，取消仍为同步算子前后检查点。未实现 Vue 离线页，本轮训练/视频编码/commit/push/tag 均未执行。HUMAN REVIEW PENDING。


Final frozen regression: `.venv-final-demo/Scripts/python.exe -m pytest -q --tb=short` — 819 PASS / 7 expected separate-API file skips, 352.66 seconds. `compileall api services web offline`, `git diff --check`, model/config fingerprints and generated-file ignore checks PASS.

Documentation/source-asset gate: 52 PASS in 53.49 seconds; credential-pattern scan found no matches. No commit, push or tag.
