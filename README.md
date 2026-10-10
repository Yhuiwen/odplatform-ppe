# 智慧工地 PPE 安全运营平台

## V1.2 发布（2026-10-10）

Vue 与锁文件、API 版本统一为 **1.2.0**。包含离线图片/视频检测工作台、逐帧视频导出、事件及关键证据、非阻塞缓存语音告警、增强只读安全助手及中文事件卡片/证据放大。实时和离线执行仍互斥，本版未实现并行运行。

用户明确接受本版暂缓 G-CFR-01/RISK-030 与 P9-C 发布阻塞，相关风险保持 OPEN/PARTIAL，不宣称修复或生产级稳定。已补做两次真实570帧MP4缓存音频联调、真实Provider引用核验及1366/1920助手浏览器检查。最终验证、已知限制及发布说明见 [V1.2发布检查](docs/reports/v1.2/V12_RELEASE_CHECK.md)。下文为历史阶段记录，其待审核状态保留原始日期。

本地启动（不依赖PowerShell脚本执行策略）：

```powershell
cd "E:\大四\创业实训\odplatform-ppe\front"
npm ci
npm run build
cd ..
.\.venv-frontend-api\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8775 --workers 1
```

原Streamlit入口保留，可通过冻结演示环境执行 `web/Home.py` 回退。完整环境安装及任务存储配置见 [用户指南](docs/V1_2_OFFLINE_USER_GUIDE.md)。

## V1.2-G 验收结果（2026-10-10，待人工审核）

图片/视频离线工作台及真实模型链路已完成本轮检查：原尺寸标注、完整逐帧H.264、时序事件/双证据、队列/取消/历史、四种桌面尺寸与下载。Vue34、API109、冻结Python819项通过；真实媒体8个用例分轮有通过证据。首轮核验570帧素材再次出现推理前CFR拒绝，根因未确定，**G BLOCKED / HUMAN REVIEW PENDING**；后续通过未覆盖该失败，P9-C仍PARTIAL/FROZEN，FullHD/4K/长视频/长稳不宣称通过。

完整PowerShell部署、启动/停止、操作及回退见[离线用户指南](docs/V1_2_OFFLINE_USER_GUIDE.md)；证据/限制见[G最终验收报告](docs/reports/v1.2/V12_G_FINAL_ACCEPTANCE_REPORT.md)。API health现有api_version=1.2.0；正式8768未重启，本轮独立审核实例为127.0.0.1:8775。B–G尚未提交，没有push或v1.2 Tag；下方各阶段段落保留实施历史。

## V1.2-F 离线智能检测工作台（待人工审核）

菜单“离线检测”位于实时监控之后，路由 `/offline`。图片/视频/任务历史三个Tab支持真实JPG/JPEG/PNG/MP4上传、明确音轨确认、上传/处理进度、取消/恢复、原图/标注放大、H.264播放、只读事件时间轴、双图证据和JSON/CSV/ZIP下载。历史D任务显示“未执行事件分析”，不把null显示成0。[F实施、测试、截图与限制](docs/reports/v1.2/V12_F_FRONTEND_REPORT.md)。

```powershell
Set-Location 'E:\大四\创业实训\odplatform-ppe\front'
npm ci
npm test
npm run build
Set-Location ..
# 先确认旧实例没有活动监控/离线任务，再退出旧实例
& .\scripts\start_frontend_local.ps1 -ApiPort 8768
# 浏览器访问 http://127.0.0.1:8768/offline
```

正式服务只运行一个Worker，沿用独立API环境及已有锁文件。开发Vite代理可用 `VITE_API_TARGET` 指向实际API。本次联调实例为127.0.0.1:8774，使用仓库外隔离任务root，正式8768未被重启；审核时可查看8774的真实测试结果。测试ZIP保持仓库外，避免触发冻结资产门禁。F完成后停止，不自动进入G；P9-C及长期资源风险仍保留。无新增依赖，无提交/推送/Tag。

## V1.2-E 离线视频事件与关键证据（F授权已确认审核通过）

MP4 现在在同一次逐帧推理上复用冻结 ByteTrack、PPE关联、ComplianceService 和 EventEngine，生成任务专属确认事件及原始/标注双 PNG 证据。结果新增 events.json、UTF-8 BOM events.csv、证据清单和图片，ZIP包含完整结果。离线事件不进入实时总览、不发Web/TTS告警；数据库只供内部查询，不提供下载。[E架构、API、实测与限制](docs/reports/v1.2/V12_E_EVENTS_EVIDENCE_REPORT.md)。

真实47/570帧验证通过，原1280×720与FPS/H.264保持；实际确认事件1/2、证据图片2/4。最终联合107项通过；P9-C长期风险仍未关闭，历史偶发CFR拒绝已记录。未进入F，没有Vue离线页面。更新代码后重启一个本地API实例才加载新功能；当前既有服务未自动重启。

GET `/api/v1/offline/jobs/{job_id}/events`、`/evidence` 支持 `limit`、`offset`、`event_type`；详情为 `/events/{event_id}`、`/evidence/{evidence_id}`；PNG为 `/evidence/{evidence_id}/image?variant=original` 或 `annotated`。只有COMPLETED可查询，损坏证据明确报错。`ODPLATFORM_OFFLINE_EVENT_EXECUTION=0` 后重启可让新视频任务回退到D，仅关闭事件分析，保留既有结果和输入。

## V1.2-D 原分辨率 MP4 检测与导出（已审核；阶段历史）

离线 MP4 现在由 B/C 的同一个单 Worker 顺序处理，逐帧调用冻结 YOLO11，在原尺寸画面上标注，并输出 H.264 MP4、frames.jsonl、summary.json、video_verification.json 和 results.zip。真实 47/570 帧、1280×720 视频保留全部帧和精确播放帧率，浏览器播放与下载校验通过。D阶段自身没有事件分析，当前事件能力以上方E为准；关闭E时 confirmed_events/evidence_count 为 null。只支持可靠 CFR、无旋转、偶数宽高；含音轨必须明确确认输出不保留音轨。CRF18 是有损编码。[实施/验证/限制报告](docs/reports/v1.2/V12_D_VIDEO_RENDERING_REPORT.md)。

保持已有冻结业务环境、V1.2 独立 API 依赖与本机 FFmpeg/libx264，不安装替代权重。更新后重启**一个**本地 API 实例；不要使用多 Worker 或开发 reload 调度实际离线任务：

```powershell
& .\.venv-frontend-api\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8765 --workers 1
# 另一个 PowerShell 窗口：上传有音轨的视频并明确确认移除
curl.exe -F "file=@artifacts/validation/test/4afa6b121fe5db806c3ff416bafdf571.mp4;type=video/mp4" -F "audio_discard_confirmed=true" http://127.0.0.1:8765/api/v1/offline/jobs
```

保存返回的 job_id，GET `/api/v1/offline/jobs/{job_id}` 查询状态，POST 同路径 `/cancel` 取消。只有 COMPLETED 后 GET `/artifacts` 和 `/artifacts/{key}` 可下载校验产物；key 为 annotated、frames、summary、video_verification、results。长视频处理时图片按 FIFO 等待；实时监控与离线处理互斥。模型算子只能在安全检查点取消。

`ODPLATFORM_OFFLINE_VIDEO_EXECUTION=0` 后重启可关闭视频调度；共享离线模型执行仍遵循 C 的 `image_execution_enabled` 配置，`ODPLATFORM_OFFLINE_IMAGE_EXECUTION=0` 会关闭共享离线检测。旧 Streamlit 和原 M-007 工具保留。D阶段自身不实现E统计；当前E以上方记录为准。D阶段自身不提供Vue离线页；当前工作台以上方F为准，不关闭P9-C。

测试使用独立临时任务根目录；运行 ZIP 通过任务 manifest 校验。旧 P1 源码资产扫描会将仓库中的未登记 ZIP 报为资产问题，额外验证 ZIP 应保留在仓库外；不因此放宽冻结训练资产门禁。

## V1.2-C 离线图片检测（待人工审核）

在 V1.2-B 任务接口上，JPG/JPEG/PNG 已可由单 Worker 调用冻结 YOLO11 模型并下载原尺寸标注 PNG、检测 JSON、统计 JSON 和结果 ZIP。图片输出只统计单帧疑似检测项，不创建已确认违规事件。C 阶段仅实现图片，当前视频能力以上方 D 阶段为准。启动命令沿用下方 V1.2-B 独立 API 环境；需要已核验的 `models/checkpoints/EXP-001/best.pt`。详见 [V1.2-C 实施报告](docs/reports/v1.2/V12_C_IMAGE_INFERENCE_REPORT.md)。

## V1.2-B 离线任务基础设施（待人工审核）

现有 FastAPI 已新增 `/api/v1/offline`：JPG/PNG/MP4 安全上传、独立 SQLite 任务持久化、状态/取消/历史查询和受控产物边界。**B 阶段自身没有生产推理处理器**；当前处理器已由 C/D 装配。详情、限制和历史测试证据见 [V1.2-B 实施报告](docs/reports/v1.2/V12_B_JOB_INFRA_REPORT.md)。在已有 `.venv-frontend-api` 环境中升级独立依赖，再按现有脚本启动单实例本地 API：

```powershell
& .\.venv-frontend-api\Scripts\python.exe -m pip install -r locks/frontend-v1.2-api/requirements.txt
& .\scripts\start_frontend_local.ps1
```

保留 `127.0.0.1` 监听和单个 Uvicorn Worker；不要用多 Worker 模式运行离线调度器。

## V1.1 Vue 本地界面

七个正式页面现已由 Vue 3、Element Plus、ECharts 和 FastAPI 适配现有 Python 服务实现。V1.1 发布门禁结果见[发布检查](docs/reports/frontend-v1.1/V1_1_RELEASE_CHECK.md)；旧 Streamlit 入口完整保留。安装、PowerShell 开发/部署启动命令、API 契约、验证证据与回退方式见 [V1.1 前端架构](docs/reports/frontend-v1.1/FRONTEND_ARCHITECTURE.md)、[API 契约](docs/reports/frontend-v1.1/API_CONTRACT.md)和[迁移报告](docs/reports/frontend-v1.1/V1_1_FRONTEND_MIGRATION_REPORT.md)。新 API 默认只监听 `127.0.0.1:8765`；本机 Windows 保留了 8000 端口，因此选用 8765。

```powershell
py -3.12 -m venv .venv-frontend-api
& .\.venv-frontend-api\Scripts\python.exe -m pip install -r locks/frontend-v1.1-api/requirements.txt
cd front
npm ci
npm run build
cd ..
& .\scripts\start_frontend_local.ps1
```

访问 `http://127.0.0.1:8765/`。开发模式执行 `& .\scripts\start_frontend_dev.ps1` 并访问 `http://127.0.0.1:5173/`。API 环境使用原冻结 V1 环境的业务依赖，但 FastAPI/Starlette 在独立环境中隔离；先按下方 V1 步骤核验模型和演示资产。USB/RTSP 实源及真实外部 AI Provider 仍需人工复核。

AI 报告的数据依据现在直接显示已校验的事件证据缩略图，点击可放大。七个模块在同一浏览器标签页内切换时保留当前表单、筛选和报告状态；完整重新加载页面会重建界面状态。详见 [报告证据与导航状态记录](docs/reports/frontend-v1.1/REPORT_EVIDENCE_NAV_STATE.md)。

**ODPlatform-PPE — Construction PPE Safety Operations Platform**

平台面向工地人员的安全帽、反光衣穿戴监测，结合目标检测、人员跟踪、规则判断、事件持久化、证据留存和智能分析，实现从视频监控到安全事件处理的闭环。当前交付范围是 **Windows 本地 V1 演示**；[当前状态](docs/02_CURRENT_STATUS.md)与[限制](#运行状态与限制)按各自证据单独披露。

## 项目展示

下图是仓库中已有的真实安全助手界面截图，展示了中文导航与本地查询结果。图中的接口超时提示也是该次运行的真实状态；它不代表提供方始终可用。

![安全助手真实运行界面](docs/reports/phase-09/P9D_DEEPSEEK_ASSISTANT_STATUS.png)

监控画面、事件与证据的完整人工演示步骤见[演示与答辩索引](docs/V1_DEMO_AND_DEFENSE.md)。当前仓库尚无适合公开展示的监控全链路截图。

## 主要功能

| 能力 | 当前实现与证据边界 |
| --- | --- |
| YOLO11 PPE 检测 | 项目训练的 YOLO11n 检测 person、安全帽/未戴安全帽、反光衣/未穿反光衣，并保留 machinery、vehicle 两类场景目标；支持图片与按序 MP4 推理。[训练与评估](docs/reports/phase-09/V1_COMPLETION_REPORT.md) |
| 人员跟踪与 PPE 关联 | 通过 Ultralytics 集成的 ByteTrack 跟踪 person，关联 PPE 候选；有歧义时保留 unknown，不强行归属。[P9-B 验收](docs/reports/phase-09/P9B3_CHARTER_GATE_READJUDICATION_REPORT.md) |
| 多帧规则与事件 | Helmet/Vest 规则经时序确认后创建违规事件；活动周期内去重，并支持恢复与冷却。反光衣短暂冲突证据处理遵循 [ADR-024](docs/03_TECHNICAL_DECISIONS.md)。 |
| 记录、留证与告警 | SQLite 持久化事件和处理状态，JPEG 快照带完整性校验；Console/Web/TTS 告警失败与事件主流程隔离。告警数统计的是通道投递次数，可能大于事件数。 |
| 本地监控与管理 | Streamlit 提供安全总览、事件中心、实时监控、证据中心、统计分析、AI 报告和安全助手；MP4 与 USB 摄像头有实际运行证据，RTSP 有受控本地流验证。[P9-D 记录](docs/reports/phase-09/P9D_UI_UX_POLISH_REPORT.md) |
| 可选 DeepSeek 分析 | 报告基于已持久化数据并经结构和依据校验；失败时标记本地模板降级。安全助手只调用受控只读工具，可选用模型规划及选择已验证陈述。[V1 报告](docs/reports/phase-09/V1_COMPLETION_REPORT.md) |

## 系统架构

```mermaid
flowchart LR
  subgraph Training["训练与评估（独立阶段）"]
    DATA["CSS v27 / 质量检查"] --> TRAIN["YOLO11n 训练"]
    TRAIN --> EVAL["原始评估 + R2 补充测试"]
  end
  subgraph Runtime["本地运行"]
    INPUT["MP4 / USB 摄像头 / RTSP 适配器"] --> DET["YOLO11 推理 / CPU OpenVINO"]
    DET --> TRACK["ByteTrack 人员跟踪"]
    TRACK --> ASSOC["Person-PPE 关联"]
    ASSOC --> RULE["Helmet / Vest 合规与多帧确认"]
    RULE --> EVENT["事件去重与持久化"]
    EVENT --> DB["SQLite"]
    EVENT --> SNAP["证据快照"]
    EVENT --> ALERT["Console / Web / TTS 告警"]
    DB --> UI["Streamlit 查询与可视化"]
    SNAP --> UI
    DB --> ANALYTICS["只读统计分析"]
    ANALYTICS --> AI["可选 LLM 报告 / 安全助手"]
  end
  TRAIN -. "经授权恢复的 checkpoint / 本地导出" .-> DET
```

训练和评估不在网页监控进程中执行。LLM/Agent 位于已确认事件的只读下游，不能决定或修改检测、关联及 PPE 合规结果。

## 技术栈

本地演示基线是 Windows、Python **3.12.1**、CPU。完整依赖以 [FINAL-DEMO-RUNTIME-001 锁文件](locks/FINAL-DEMO-RUNTIME-001/requirements.txt)为准；其中 PyTorch **2.5.1+cpu**、Ultralytics **8.4.157**、OpenCV **5.0.0.93**、Streamlit **1.64.0**、NumPy **2.2.6**、`lap` **0.5.13**。实时 CPU 配置额外使用 OpenVINO **2025.2.0**；ByteTrack 通过 Ultralytics 集成，SQLite 用于事件存储，DeepSeek 是可选的服务端提供方。

历史训练环境与本地演示环境不同；训练用 CUDA 配置不是运行网页所需条件。项目包的 `pyproject.toml` 不自动安装完整演示依赖。

## 快速开始（Windows PowerShell）

在项目根目录运行。最终演示预检要求 **Python 3.12.1**；`py -3.12` 只选择 3.12 系列，不保证一定是 3.12.1。先确认版本输出，再创建虚拟环境。其余命令始终使用该虚拟环境的 Python：

```powershell
py -3.12 --version
py -3.12 -m venv .venv-final-demo
& '.\.venv-final-demo\Scripts\python.exe' -m pip install -r locks/FINAL-DEMO-RUNTIME-001/requirements.txt
& '.\.venv-final-demo\Scripts\python.exe' -m pip install openvino==2025.2.0
& '.\.venv-final-demo\Scripts\python.exe' -m pip install --no-deps .
& '.\.venv-final-demo\Scripts\python.exe' scripts/preflight.py
& '.\.venv-final-demo\Scripts\python.exe' -m streamlit run web/Home.py --server.port 8502 --server.address 127.0.0.1 --server.headless true
```

浏览器访问 `http://localhost:8502/`。以 `--server.headless true` 启动时，无需在终端处理首次使用的邮箱提示；手动打开地址即可。先在监控页停止检测，再用 Ctrl+C 关闭服务。

**克隆仓库后不能直接完整演示。** 模型 checkpoint、416 像素 OpenVINO 导出、数据集和演示视频等大文件未随 Git 分发。请从经授权的项目资产备份恢复 `models/checkpoints/EXP-001/best.pt` 和 `models/exports/best_cpu_416_openvino_model/`，以及所需演示素材；缺失或哈希不符时以预检结果为准，不下载替代权重。持有已核验 checkpoint 的维护者可按 [CPU 性能报告](docs/reports/phase-09/P9_CPU_24FPS_REPORT.md)中的流程重新导出，但导出脚本会写入配置哈希，不能用未审核导出结果冒充冻结资产。

DeepSeek API Key **可选**；未配置时仍可使用经标记的本地报告降级和受控查询。仅按[本地部署指南](docs/V1_DEPLOYMENT_GUIDE.md#private-deepseek-configuration)配置 Git 忽略的服务端文件，不要把凭据写入 README、提交记录或截图。安装、备份、故障恢复及端口问题也见该指南。

## 数据集与训练

数据来自 [Roboflow Construction Site Safety v27](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety/dataset/27)，直接导出的冻结快照共 **2,799** 张图（train/valid/test：**2603/114/82**）。项目将源数据映射为七个训练类别，其中前五类为 person、hardhat、no_hardhat、vest、no_vest；原始数据与生成数据均不提交 Git。[Dataset Card](docs/06_DATASET_CARD.md)记录了导出元数据与实际文件的差异。

对两组已复核的 valid/test 同场景邻近帧，独立 **R2 划分**将两个 test 样本移入 valid，得到 **2603/116/80**。训练集每个文件与原版相同，EXP-001 checkpoint 未重训；R2 仅用于补充测试。R2 的精确哈希及 dHash 距离 ≤5 的跨划分候选为零，这不证明不存在其他语义或场景相似性。[R2 质量记录](docs/reports/phase-09/V1_SPLIT_R2_QUALITY.md)。

该数据集标注为 **CC BY 4.0**；署名、许可链接及再分发前复核事项见[Dataset Card](docs/06_DATASET_CARD.md)。

## 模型与处理速度

以下指标属于不同数据划分，不能直接当作同一测试集上的前后提升：

| 评估 | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| EXP-001 原始训练验证，历史指标 | 0.899 | 0.649 | 0.767 | 0.480 |
| 未重训 checkpoint 的 R2 测试集，80 张图 / 七类 | 0.795859 | 0.709828 | 0.729892 | 0.462068 |

原始指标来源见[训练记录](docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md)，R2 原始数值与逐类 AP 见[补充评估 JSON](docs/reports/phase-09/V1_SPLIT_R2_EVALUATION.json)。

在 **Intel Core i5-1340P、Windows、CPU-only、OpenVINO 2025.2.0、416 像素配置**下，指定 **570 帧 / 1280×720 / 30 FPS MP4** 的两次热态完整处理实验为 **28.836**、**29.414 processed FPS**；实际 Console/Web/TTS 告警适配器开启的另一轮为 **26.000 processed FPS**。指标是处理帧数除以墙钟时间，包含解码、推理、跟踪、关联、事件与快照等，不是视频源帧率或浏览器显示帧率。[方法和原始结果](docs/reports/phase-09/P9_CPU_24FPS_REPORT.md)。这些实验不保证所有 USB/RTSP 来源达到 24 FPS，也不证明广泛场景识别准确率。

## 项目结构

```text
core/       检测、输入源、跟踪、关联、规则、事件与 Agent 的核心契约和逻辑
services/   数据处理、训练评估、监控、事件、报告与 Agent 的服务编排
infra/      SQLite、证据存储、告警/TTS 与 LLM 通信适配
web/        Streamlit 页面及受控 Web 边界
configs/    推理、训练、评估等配置；本地密钥文件被 Git 忽略
scripts/    预检、数据准备、训练评估、推理和交付命令
tests/      单元、集成与端到端测试
docs/       治理、设计、验证报告及交接
data/       外部快照、中间数据、处理数据与样例；数据载荷不入 Git
models/     预训练权重、项目 checkpoint 与导出模型；二进制资产不入 Git
locks/      训练、评估与最终演示环境的冻结依赖
artifacts/  本地事件、快照、日志、推理及验证产物；运行数据不入 Git
```

诊断运行器位于 `diagnostics/`；最小用法示例位于 `examples/`。仓库目录说明与历史文档地图见[文档索引](docs/README.md)。

## 运行状态与限制

- 本地 V1 演示在 **远端 RTSP 和长期稳定性明确排除的范围内**准备就绪；这不代表项目章程的完整验收，也不代表云端或生产部署已验收。P9-D 页面优化仍需人工检查响应式布局并完成演示复核。
- **第四阶段的离线推理已完成**（Phase 4 — Offline Inference）。摄像头和 RTSP 是延期至后续阶段实现的 V1 必需项（Camera / RTSP: Deferred MUST；M-008 CHARTER ACCEPTED，经真实 USB Camera 验收）。章程 M-008 的“摄像头或 RTSP”条件已满足；远端 RTSP 的长期恢复能力本轮未验证。
- **P9-C：部分完成、维持冻结**（PARTIAL / FROZEN）。有限实验强烈支持“真实推理与每周期新建工作线程的组合”与观测到的资源增长相关；具体保留对象和是否无限增长仍未确认。[诊断报告](docs/reports/phase-09/P9C3I_INFERENCE_WORKER_LIFECYCLE_REPORT.md)。
- 模型对遮挡、小目标及复杂交叉场景的广泛准确率没有完成证明；416 像素 CPU 配置也未证明与原 640 像素离线配置在所有场景等效。
- 安全助手采用受控只读工具与进程内审计；持久化 Agent 审计、生产级身份认证、云端部署与全量人工答辩演示均不在当前已验证结论中。

## 文档导航

- [项目 Charter 与 MUST 验收](docs/00_PROJECT_CHARTER.md)
- [当前状态](docs/02_CURRENT_STATUS.md) · [测试门禁](docs/05_TEST_GATES.md)
- [Dataset Card](docs/06_DATASET_CARD.md) · [开源使用与许可记录](docs/07_OPEN_SOURCE_USAGE.md)
- [V1 部署与故障恢复](docs/V1_DEPLOYMENT_GUIDE.md) · [演示与答辩索引](docs/V1_DEMO_AND_DEFENSE.md)
- [V1 补齐与当前限制](docs/reports/phase-09/V1_COMPLETION_REPORT.md) · [CPU 性能报告](docs/reports/phase-09/P9_CPU_24FPS_REPORT.md)

## 许可证及致谢

**本仓库尚未声明独立的源代码许可证；项目自有代码的使用和再分发权限以实际授权为准。** 数据集的 **CC BY 4.0** 许可不能自动用于项目代码；通过依赖使用的 [Ultralytics](https://github.com/ultralytics/ultralytics) 另有 **AGPL-3.0** 义务，公开分发前应分别复核。[完整来源与许可证据](docs/07_OPEN_SOURCE_USAGE.md)。

感谢 [Roboflow Universe Projects / Construction Site Safety](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety) 数据来源，以及 [PyTorch](https://pytorch.org/)、[OpenVINO](https://docs.openvino.ai/)、[OpenCV](https://opencv.org/)、[Streamlit](https://streamlit.io/) 与 [ByteTrack](https://github.com/FoundationVision/ByteTrack) 等开源项目。DeepSeek 仅为可选外部 API；其输出须通过本项目校验，服务不可用时使用本地降级。
