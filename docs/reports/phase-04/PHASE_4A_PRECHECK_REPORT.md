# Phase 4A Precheck Report

Date: 2026-09-23

Status: **PASS / DESIGN WORK MAY PROCEED**

## Current project state

- Repository: `Yhuiwen/odplatform-ppe`
- Branch: `main`
- Starting HEAD: `f525f7d`
- Starting worktree: clean
- Phase 3 release tag: `phase-3-evaluation-release`
- Phase 3 human review: PASS, as confirmed by the current user instruction
- Selected release model: `models/checkpoints/EXP-001/best.pt`
- Selected model SHA256:
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`

The repository contains the Phase 3 evaluation, comparison, selection and
release-freeze evidence. The historical freeze report correctly records that
its content was frozen while human review was pending. The current user
instruction supplies the later human PASS and authorizes Phase 4A design only.

## Phase 3 freeze status

| Item | Status |
| --- | --- |
| P3-G1 independent test evaluation | PASS |
| P3-G2 per-class analysis | PASS |
| P3-G3 checkpoint comparison | PASS |
| P3-G4 model selection | PASS |
| Human review | PASS |
| Release model | `models/checkpoints/EXP-001/best.pt` |
| Dataset | `CSS-PPE-10-V1` / `PPE-MAPPING-V1` |
| Training | EXP-001 COMPLETED |

No dataset, mapping, weight, training configuration or frozen Phase 3
evidence was modified during this precheck.

## Existing inference assets

The repository already contains Phase 0 boundaries and planned configuration.
They are not implemented inference behavior:

| Asset | Current state | Phase 4A action |
| --- | --- | --- |
| `configs/inference.yaml` | planned defaults; `model_path: null`; no runtime binding | Audit only; do not modify |
| `core/detection/schemas.py` | stable `BoundingBox`, `Detection`, `DetectionClass`, `FrameMeta` schemas | Reuse as primitive contracts |
| `core/detection/detector.py` | `Detector.detect()` raises `NotImplementedError` | Keep unchanged; design wrapper contract |
| `core/pipeline/inference_pipeline.py` | `InferencePipeline.run()` raises `NotImplementedError` | Keep unchanged; design pipeline contract |
| `services/inference_service.py` | image/video/stream methods raise `NotImplementedError` | Keep unchanged; design service boundary |
| `scripts/infer_image.py` | Phase 4 placeholder | Keep unchanged |
| `scripts/infer_video.py` | Phase 4 placeholder | Keep unchanged |
| `scripts/infer_stream.py` | Camera/RTSP placeholder | Keep unchanged |

The placeholders deliberately fail rather than returning fabricated results.

## Missing modules for later implementation

- Input adapter contracts for image, local video, Camera and RTSP.
- A YOLO11 detector wrapper that loads an explicitly approved checkpoint and
  resolves device, confidence, IoU and class filters.
- Frame/source lifecycle handling, including observable stream failure and
  shutdown behavior.
- Structured result serialization and output rendering.
- Image, video and real stream integration tests.
- A separately approved inference configuration and runtime freeze.
- Performance, timeout, reconnection and resource-boundary evidence.

## Risks

| Risk | Phase 4A treatment |
| --- | --- |
| Existing placeholder code could be mistaken for working inference | Design document marks all implementation as future work |
| `configs/inference.yaml` is planned and has no model path | Keep it planned; require a later freeze before execution |
| Local runtime lacks Torch and Ultralytics | Record as not ready for inference execution; install nothing |
| Camera/RTSP behavior can silently degrade to local video | Preserve the MUST boundary and require source-specific failure status |
| Duplicate schema definitions could drift | Reuse existing detection primitives and add only the new result envelope |
| Loading the selected checkpoint could be confused with design authorization | No checkpoint loading or inference execution occurs in Phase 4A |

## Conflict decision

No locked Charter, MUST, phase-goal, dataset, mapping or model conflict was
found. The only discrepancy is documentation lag: current prose still says
human review and formal Phase 3 completion are pending, while the user has
provided the later human PASS. Phase 4A will synchronize status fields only.

Phase 4A starts in design-only mode. Phase 4B has not started.
