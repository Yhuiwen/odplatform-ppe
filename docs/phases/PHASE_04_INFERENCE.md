# Phase 04 — Offline Inference

## 1. 阶段目标

【LOCKED】本地图片与 MP4 视频结构化离线推理流水线。Camera/RTSP 与实时源
由 ADR-018 延期实施，仍保留 V1 MUST 归属，不属于本离线阶段完成声明。

## 2. 进入条件

- Phase 3 Gate 全部 PASS。
- 已选择模型及其推理配置。

## 3. 当前子任务

Phase 4A — Inference Architecture Design 已完成。设计记录见
`docs/phases/PHASE_04_INFERENCE_DESIGN.md`。

Phase 4B-0 — Inference Runtime Freeze 已完成。CPU runtime、release
checkpoint、device、threshold、input/output schema 和错误处理边界记录在
`docs/phases/PHASE_04B_RUNTIME_FREEZE.md`，机器可读配置为
`configs/inference.yaml` 且 `execution_enabled: false`。

Phase 4B-1 — Single Image Inference 已实现并保持 execution disabled。
`core/inference/detector.py`、`services/inference_service.py` 和
`scripts/run_image_inference.py` 完成 `Image -> YOLO11 -> DetectionResult`
链路；报告见 `docs/reports/phase-04/PHASE_04B1_IMAGE_INFERENCE_REPORT.md`。Camera
和 RTSP 仍未实现。

Phase 4B-2a — Video Inference Architecture Design 已完成。设计记录见
`docs/phases/PHASE_04B2_VIDEO_DESIGN.md`；新增
`core/schemas/video.py` 的纯数据结构契约。该子阶段只处理本地 MP4，
采用顺序 CPU 处理、禁止跳帧和 async，并明确 Camera/RTSP 不属于本次范围。
Phase 4B-2b — MP4 Video Inference Implementation 已完成：新增
`core/video/reader.py`、`services/video_inference_service.py` 和
`scripts/run_video_inference.py`，通过共享的 `InferenceService`/detector
策略逐帧生成 `VideoInferenceResult`。默认 execution disabled，未加载模型或
执行真实大规模视频测试。

Phase 4C-0 — Real Inference Validation Design 已完成。设计记录见
`docs/phases/PHASE_04C_VALIDATION_DESIGN.md`；新增
`core/schemas/validation.py` 的真实 image/video validation evidence
contracts。设计定义 frozen checkpoint、external inputs、detection/latency/
FPS statistics、Git-ignored `artifacts/validation/` 和 fail-closed errors。
Phase 4C-1 — Real Image Inference Validation 已完成一次授权图片实测：使用
`INF-RUNTIME-001` 加载冻结 `best.pt`，处理一张 external public-domain
construction image，生成 Git-ignored raw JSON 和 schema-backed validation
report。热推理返回 5 个检测，cold start 为 14.237 s，warm inference 为
176.386 ms。

Phase 4C-2 — Real MP4 Inference Validation 已完成独立授权的视频实测：使用
同一 frozen runtime/checkpoint 顺序处理 external public-domain MP4 的全部
47/47 帧，未跳帧、未 batch、未 async、未迁移 CUDA。该 run 返回 77 个
检测（person 76、no_vest 1），端到端耗时 15.1920268 s，processing FPS 为
3.0937281；raw result、frame summary 和 schema report 保存在 Git-ignored
`artifacts/validation/P4C-2/`。RTSP、Camera、tracking、association、
compliance、events、alerts、Web 和 LLM 未执行。Phase 5 等待授权。

Phase 4 release boundary 已由 ADR-018 正式调整为
`Offline Inference COMPLETE`。Camera/RTSP、实时源行为、M-008 和 annotated
video rendering 保持 `Deferred MUST`，不得被本 release tag 宣称为已完成。

### ADR-019 scope clarification

Completed scope: offline image inference, offline MP4 sequential inference,
and real validation evidence. Camera/RTSP and annotated video rendering are
deferred from this phase, not deleted or downgraded to Extensions. M-007 and
M-008 remain unchanged. Phase 7 owns their implementation and integration;
Phase 9 owns final Charter acceptance. Phase 5 uses the Offline Inference
Gates and ADR-019 entry conditions. P4-G3 remains deferred, not PASS.

## 4. 实现设计

共享检测器与帧元数据 schema，按输入源实现逐帧处理、绘制和结构化输出；
Camera/RTSP 路径必须具备超时、断流和失败状态。

Camera/RTSP 与 annotated rendering 当前是 deferred MUST implementation。未来恢复该
工作时必须使用真实流或经批准的测试端点，并保留超时、断流和失败证据；
不得用本地 MP4 冒充实时源。

## 5. 测试要求

- 小图片 fixture 的检测结构测试。
- 短本地视频顺序、帧数和输出测试。
- RTSP 协议解析/失败路径测试属于 deferred MUST implementation，不允许用本地视频
  冒充 RTSP。

## 6. Gate

| Gate | Requirement | Status |
| --- | --- | --- |
| P4-G1 | 图片检测输出框、类别、置信度和结构结果 | PASS（structured output） |
| P4-G2 | 视频检测顺序正确并输出统计结果 | PASS（structured output；annotated rendering deferred） |
| P4-G3 | Camera/RTSP 路径真实可用且失败可观察 | DEFERRED MUST / ADR-018 |

Offline release gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P4-OFF-G1 | Image architecture and runtime freeze verified | PASS |
| P4-OFF-G2 | Single-image structured inference implemented | PASS |
| P4-OFF-G3 | Sequential MP4 structured inference implemented | PASS |
| P4-OFF-G4 | Real image validation against frozen checkpoint | PASS |
| P4-OFF-G5 | Real MP4 validation across every source frame | PASS |
| P4-OFF-G6 | Camera/RTSP and M-008 explicitly deferred | PASS |

## 7. 已知问题

实时源、网络、Camera/RTSP 和 GPU 推理速度尚未验证。Camera/RTSP、M-008
与 annotated video rendering 保持 deferred MUST implementation；M-006/M-007 的完整
Charter acceptance 仍需独立审核。

## 8. 开发记录

- 2026-09-23: ADR-019 corrects the prior Extension classification without
  deleting the ADR-018 release record. Deferred MUST ownership is Phase 7
  implementation/integration and Phase 9 final acceptance. Phase 4 completion
  and Phase 5 waiting status are unchanged.


- 2026-09-21: 计划建立，未开始实现。
- 2026-09-23: Phase 4A 完成 PRE-READ 和 repository audit；确认现有
  Detector、Pipeline、InferenceService 及 CLI 均为 `NotImplementedError`
  占位，`configs/inference.yaml` 仍为 planned defaults。新增架构设计文档、
  `core/schemas/detection.py` 的无模型依赖 `DetectionResult` 接口和最小测试。
  未加载 `best.pt`、未执行推理、未修改 dataset/mapping/weights/config，未进入
  Phase 4B。
- 2026-09-23: Phase 4B-0 完成 inference runtime freeze。冻结
  `INF-RUNTIME-001`（Python 3.10.4、PyTorch 2.5.1+cpu、Ultralytics
  8.4.157）、CPU-only device policy、release checkpoint SHA256、固定阈值、
  输入格式、`DetectionResult` reference 和 fail-closed error policy；
  `configs/inference.yaml` 仍禁用执行。未加载模型、未执行推理、未修改 dataset
  或训练产物，未 commit/push/tag。
- 2026-09-23: Phase 4B-1 完成单图推理实现。新增 `core/inference/`、
  `YOLODetector`、`InferenceService` 和 `scripts/run_image_inference.py`；
  测试使用 fake model/image loader，验证 lazy load、固定参数、schema 输出和
  error codes。未加载真实模型、未执行真实推理，未修改 dataset/mapping/
  training artifacts/checkpoint；Phase 4B-2 等待授权。
- 2026-09-23: Phase 4B-2a 完成本地 MP4 视频推理架构设计。新增
  `docs/phases/PHASE_04B2_VIDEO_DESIGN.md`、
  `docs/reports/phase-04/PHASE_04B2_VIDEO_DESIGN_REPORT.md` 和纯数据 schema
  `core/schemas/video.py`。设计固定 sequential processing、CPU-only、
  no frame skipping、no async、fail-closed errors 和 Camera/RTSP non-goals；
  未修改 detector/service，未加载模型、未执行真实视频推理。Phase 4B-2b
  等待授权。
- 2026-09-23: Phase 4B-2b 完成 MP4 视频推理实现。新增 sequential
  `VideoReader`、`VideoInferenceService` 和 JSON CLI；为 `YOLODetector`/
  `InferenceService` 增加共享 frame-level entry point，避免复制检测逻辑。
  测试使用 fake capture 和 fake inference service，覆盖顺序、metadata、
  result serialization 及 missing/format/empty/decode errors。未加载
  `best.pt`、未执行真实大规模视频测试，未修改 dataset、mapping、training
  config 或 checkpoint；Phase 4B-3 等待授权。
- 2026-09-23: Phase 4C-0 完成真实推理验证设计。新增
  `PHASE_04C_VALIDATION_DESIGN.md`、`core/schemas/validation.py` 和 schema
  tests，定义 external image / short MP4 validation evidence、model/runtime
  identity、latency/FPS statistics、Git-ignored artifacts 政策和
  fail-closed failure handling。未加载 `best.pt`、未执行真实推理，未修改
  dataset、training assets 或 checkpoint；Phase 4C-1 等待授权。
- 2026-09-23: Phase 4C-1 完成图片-only真实推理验证。新增
  `configs/validation.yaml` 和 `scripts/run_image_validation.py`，通过显式
  validation override 启用执行而不修改 frozen `configs/inference.yaml`。
  加载 checkpoint SHA256
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`，
  对 external public-domain image 完成 cold/warm 两次推理并输出 5 个
  `DetectionResult`。结果保存在 Git-ignored `artifacts/validation/P4C-1/`；
  未执行 video、tracking、association、compliance、events 或 alerts，未
  修改 dataset、mapping、training config 或 checkpoint，未 commit/push/tag。
- 2026-09-23: Phase 4C-2 完成真实 MP4 验证。新增 independent
  `configs/video_validation.yaml` 和 `scripts/run_video_validation.py`，
  使用冻结 `best.pt`/`INF-RUNTIME-001` 顺序处理 47/47 帧并生成
  `video_validation.json`、`frame_summary.json`、`validation_report.json`；
  frozen inference config 保持 disabled。未执行 RTSP、Camera、tracking、
  association、compliance、events、alerts、Web 或 LLM，未修改 dataset、
  mapping、training config 或 checkpoint，未 commit/push/tag。
- 2026-09-23: ADR-018 正式调整 Phase 4 scope 为 Offline Inference。Image、
  MP4 structured inference 和两类真实 validation 构成 release scope；
Camera/RTSP、M-008 和 annotated rendering 明确延期实施，仍保留 V1 MUST 归属，Phase 4
release tag 明确为 `phase-4-offline-inference-complete`。Phase 5 仍未开始。
