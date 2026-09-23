# Phase 4B-2b MP4 Video Inference Implementation Report

Date: 2026-09-23

Status: **COMPLETE / EXECUTION DISABLED**

Phase 4B-2b: COMPLETE

Phase 4B-3: WAITING

## 1. Architecture

The implemented local MP4 path is:

```text
local MP4
  -> VideoReader
  -> FrameData
  -> VideoInferenceService
  -> InferenceService.infer_frame()
  -> YOLODetector.detect_frame()
  -> FrameInferenceResult
  -> VideoInferenceResult
  -> JSON CLI output
```

The existing detector remains the single owner of checkpoint verification,
CPU-only device policy, model loading, fixed inference parameters and
Ultralytics result conversion. The video layer does not duplicate that logic.

## 2. Implementation

### VideoReader

File: `core/video/reader.py`

- accepts only existing local `.mp4` files
- lazily imports OpenCV only when a real capture is opened
- reads frames sequentially and preserves decode order
- emits zero-based `FrameData` IDs and `frame_id / fps` timestamps
- records source, FPS, dimensions, declared frame count and duration
- rejects missing, invalid-format, empty and truncated videos with stable
  machine-readable error codes
- never calls YOLO

### VideoInferenceService

File: `services/video_inference_service.py`

- validates the source before opening the reader
- stops before decoding when execution is disabled
- calls the existing `InferenceService` once per ordered frame
- verifies the frame ID, timestamp and source on every returned detection
- returns a project `VideoInferenceResult`, never an OpenCV or Ultralytics
  object

### Shared frame inference

Files:

- `core/inference/detector.py`
- `services/inference_service.py`

`YOLODetector.detect_frame()` and `InferenceService.infer_frame()` expose the
same frozen CPU checkpoint and parameter policy used by single-image inference.
This extension avoids a second detector implementation.

### CLI

File: `scripts/run_video_inference.py`

```powershell
python scripts/run_video_inference.py path\to\video.mp4
```

Success output is JSON and contains metadata, processed-frame count and ordered
frame results. Expected failures return `status: error`, a stable `error` code
and a message.

Current `configs/inference.yaml` keeps `execution_enabled: false`, so the
canonical CLI returns `execution_disabled` until a later reviewed execution
authorization.

## 3. Tests

Added: `tests/test_video_inference.py`

Covered:

- sequential frame order
- exact frame count and timestamps
- metadata extraction
- `VideoInferenceResult` JSON serialization
- missing file, invalid format, zero-byte file and truncated decode errors
- disabled execution without opening a reader
- structured CLI errors for missing, invalid, empty and disabled cases

Tests use fake capture objects and a fake inference service. No `best.pt`,
real model or real MP4 payload is loaded.

## 4. Validation boundaries

- `models/checkpoints/EXP-001/best.pt`: not loaded or modified
- dataset and mapping: not modified
- training configuration and artifacts: not modified
- no RTSP or Camera implementation
- no ByteTrack, tracking, PPE association, compliance, events or alerts
- no Web, LLM or Agent work
- no large-scale real-video execution
- no commit, push or tag

## 5. Limitations

- Canonical execution remains disabled.
- Real OpenCV + model end-to-end MP4 execution was not performed in this
  implementation phase.
- CPU throughput, memory usage and long-video behavior remain unverified.
- Annotated-video rendering is not part of Phase 4B-2b.

## 6. Next allowed step

```text
WAIT FOR PHASE 4B-3 AUTHORIZATION
```
