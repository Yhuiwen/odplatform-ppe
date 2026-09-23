# Phase 4B-2a Video Inference Design Report

Date: 2026-09-23

Status: **COMPLETE / DESIGN ONLY**

Phase 4B-1: COMPLETE

Phase 4B-2a: COMPLETE

Phase 4B-2b: WAITING

## 1. Scope completed

- Defined a sequential local MP4-only video inference architecture.
- Defined the `VideoReader -> FrameProcessor -> InferenceService -> Result
  Writer` boundary.
- Added model-independent `FrameData`, `VideoMetadata`,
  `FrameInferenceResult` and `VideoInferenceResult` schemas.
- Defined deterministic frame ordering, timestamp and serialization contracts.
- Froze sequential CPU processing, no frame skipping, no async behavior and no
  parallel frame inference.
- Defined fail-closed video error handling and explicit Camera/RTSP non-goals.

## 2. Files added

- `docs/phases/PHASE_04B2_VIDEO_DESIGN.md`
- `core/schemas/video.py`
- `tests/test_video_schema.py`

## 3. Boundaries preserved

- `core/inference/detector.py`: not modified.
- `services/inference_service.py`: not modified.
- `models/checkpoints/EXP-001/best.pt`: not loaded or modified.
- dataset, mapping, training configuration and training artifacts: not
  modified.
- `configs/inference.yaml`: execution remains disabled.
- No tracking, association, event, alert, Web, LLM or Agent work started.

## 4. Validation

The schema tests cover creation, field access, immutable frame ordering and
JSON serialization. No real video or model execution is performed.

## 5. Next allowed step

```text
WAIT FOR PHASE 4B-2b VIDEO INFERENCE IMPLEMENTATION AUTHORIZATION
```
