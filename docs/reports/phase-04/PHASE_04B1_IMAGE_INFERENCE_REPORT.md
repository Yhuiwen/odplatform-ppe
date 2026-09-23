# Phase 4B-1 Single Image Inference Report

Date: 2026-09-23

Status: **COMPLETE / EXECUTION DISABLED**

Phase 4B-1: COMPLETE

Phase 4B-2: WAITING

## 1. Architecture

The implemented single-image path is:

```text
image path
  -> InferenceService path and format validation
  -> YOLODetector lazy checkpoint verification
  -> YOLO11 CPU inference
  -> list[DetectionResult]
  -> JSON serialization
```

The detector reads the frozen Phase 4B-0 configuration from
`configs/inference.yaml`. Configuration values are not duplicated or changed
by the implementation.

## 2. Implementation

### YOLODetector

File: `core/inference/detector.py`

Implemented behavior:

- lazy Ultralytics/Pillow import and model construction
- explicit `execution_disabled` failure before model loading
- checkpoint existence, size and SHA256 verification
- CPU-only device enforcement
- fixed `imgsz: 640`, confidence `0.25`, IoU `0.45`, `max_det: 300`
- explicit class filter `[0, 1, 2, 3, 4]`
- model class-order validation for the five filtered PPE classes
- conversion of framework boxes into project `Detection` and
  `DetectionResult` schemas
- stable machine-readable error codes

### InferenceService

File: `services/inference_service.py`

Implemented behavior:

- source type, existence, file and extension validation
- delegation to `YOLODetector`
- pure `DetectionResult` return type
- video and Camera/RTSP boundaries remain explicit future-phase failures

The service does not return Ultralytics `Results` objects.

### CLI

File: `scripts/run_image_inference.py`

Command:

```powershell
python scripts/run_image_inference.py image.jpg
```

Success output is JSON with `status`, `image`, and serialized `detections`.
Failure output is JSON with `status`, stable `error`, and `message`.

Current default configuration keeps `execution_enabled: false`, so the CLI
returns an explicit `execution_disabled` error until a later, separately
authorized change enables execution.

## 3. Frozen identity and runtime

| Item | Value |
| --- | --- |
| Runtime ID | `INF-RUNTIME-001` |
| Device | CPU only |
| Python | 3.10.4 |
| PyTorch | 2.5.1+cpu |
| Ultralytics | 8.4.157 |
| Checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Output schema | `core/schemas/detection.py` / `DetectionResult` |

No model was loaded and no real image inference was executed while completing
this implementation. Tests use injected fake model objects and image loaders.

## 4. Tests

Added: `tests/test_image_inference.py`

Covered:

- missing image rejection
- unsupported image format rejection
- disabled execution without model construction
- lazy model construction
- fixed device and inference parameters
- structured `DetectionResult` output and JSON serialization
- checkpoint SHA256 mismatch
- CLI JSON error behavior for disabled execution

The existing video and stream placeholder tests remain in place. The prior
image-service placeholder test was removed because the image path is now
implemented.

## 5. Limitations

- The frozen default still disables execution; no production inference was
  run.
- CPU performance, memory usage, Camera/RTSP latency and throughput are not
  established.
- Only one image is implemented. Video, Camera and RTSP remain unimplemented.
- No tracking, association, compliance rule, event, alert, UI, LLM or Agent
  behavior is included.
- The optional Torch reference test remains skipped in the base Python
  environment because Torch is not installed there.

## 6. Next phase

Phase 4B-1 is implementation-complete with execution disabled. The next
allowed step is:

```text
PHASE 4B-2 IMPLEMENTATION AUTHORIZATION
```

Any real checkpoint load or inference execution still requires explicit
authorization and an execution-enabled reviewed configuration.
