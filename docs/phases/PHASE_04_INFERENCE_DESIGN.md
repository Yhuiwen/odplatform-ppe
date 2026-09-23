# Phase 4 Inference Architecture Design

Date: 2026-09-23

Status: **PHASE 4A DESIGN ONLY / NOT IMPLEMENTED**

This document defines the target architecture for Phase 4. It does not load a
checkpoint, execute inference, create a tracking pipeline, associate PPE with a
person, evaluate compliance, persist events or send an alert.

## 1. Goal

建立统一 detection pipeline，为图片、本地视频、Camera 和 RTSP 输入提供一致的：

- input source abstraction
- model loading and device policy
- frame processing and source failure handling
- detection result schema
- rendering and structured-output boundary

The same detector contract must be usable by the later tracking, compliance,
event, web and reporting phases without embedding those future concerns in the
Phase 4 detector.

## 2. Input layer

All input types implement one logical `InputAdapter` contract. The adapter
owns source opening, iteration, timestamps and closure; it does not own model
loading or compliance rules.

| Source | Adapter responsibility | Required visible state |
| --- | --- | --- |
| Image | Validate and open one image; emit one frame | source opened, frame decoded, failure |
| Video | Open a local video; emit frames in order; report frame count and timing | position, end of video, decode failure |
| RTSP | Open a real network stream with timeout; emit frames in order; expose reconnect/disconnect state | connecting, active, timeout, disconnected |
| Camera | Open a device-backed camera or approved stream-backed camera; expose device state | opening, active, unavailable, stopped |

The adapter contract must expose frame ID, timestamp and source identity.
RTSP and Camera cannot be represented by silently substituting a local video.
If a future environment lacks a physical camera or RTSP endpoint, the failure
path must be observable and must not return fabricated frames.

## 3. Inference engine

`YOLO11Detector` is a future wrapper around the approved Ultralytics YOLO11
runtime. Its responsibilities are:

1. Load only an explicitly configured, verified checkpoint path.
2. Resolve `auto`, CPU or CUDA device selection without silently changing the
   configured model identity.
3. Apply the configured image size, confidence threshold, IoU threshold and
   allowed class filter.
4. Convert framework-native boxes into the project `Detection` schema.
5. Return structured detections plus timing metadata to the pipeline.

The wrapper must not implement ByteTrack, person-PPE association, rule logic,
event creation, alerting or persistence. It must fail explicitly when the
checkpoint is missing, the runtime is unavailable, the device is invalid, or
the class mapping is inconsistent with the checkpoint.

The initial release model candidate is `models/checkpoints/EXP-001/best.pt`
with the SHA256 recorded by Phase 3. Phase 4A does not load or copy it.

## 4. Output schema

Phase 4 uses one result record per detected object. A frame therefore returns
`list[DetectionResult]`, and each record carries its frame and source context.

The code contract is `core/schemas/detection.py`.

| Field | Type | Meaning |
| --- | --- | --- |
| `frame_id` | integer | Monotonic frame identifier within the source run |
| `timestamp` | float | Source-relative timestamp in seconds |
| `source` | string | Source identity, such as `image:...` or `rtsp:...` |
| `class_id` | integer | Frozen training class ID |
| `class_name` | string | Frozen training class name |
| `confidence` | float | Detection confidence in `[0, 1]` |
| `bbox` | `BoundingBox` | Absolute `x1, y1, x2, y2` coordinates |

`DetectionResult.to_dict()` returns a JSON-serializable flat record. The
schema has no Torch, OpenCV, Ultralytics or other model-runtime dependency.
The existing `Detection`, `BoundingBox` and `FrameMeta` primitives remain the
lower-level contracts; Phase 4A does not replace or modify them.

Example:

```json
{
  "frame_id": 7,
  "timestamp": 1.25,
  "source": "image:fixture.jpg",
  "class_id": 1,
  "class_name": "hardhat",
  "confidence": 0.91,
  "bbox": {"x1": 10.0, "y1": 20.0, "x2": 50.0, "y2": 80.0}
}
```

## 5. Pipeline boundary

The future pipeline has this flow:

```text
InputAdapter
  -> frame + FrameMeta
  -> YOLO11Detector
  -> list[DetectionResult]
  -> optional rendering / structured output
```

The pipeline must preserve source order for video and stream inputs, report
processed frame counts and elapsed time, and distinguish a clean end of input
from a decode, timeout or connection failure.

No rendering format is frozen in Phase 4A. Image output, video output and
stream display will be specified in implementation work with tests.

## 6. Future integration

| Phase | Consumes from Phase 4 | Boundary |
| --- | --- | --- |
| P5 | Frame metadata and detections containing person/PPE classes | ByteTrack is added outside the detector |
| P6 | Tracked person-PPE evidence | Compliance and temporal rules are added outside tracking |
| P7 | Confirmed events and evidence references | Persistence, TTS, Web and alerts remain later work |

No association, tracking, rule, event or alert behavior is implemented by this
design. The context classes `machinery` and `vehicle` remain detector output
only and do not acquire PPE violation semantics.

## 7. Configuration and runtime policy

`configs/inference.yaml` is currently a planned-defaults file and is not a
production inference contract. Before Phase 4B execution, a separate review
must bind:

- selected checkpoint path and SHA256
- runtime and dependency identity
- image size, confidence, IoU and class filter
- device policy
- source-specific timeout and shutdown behavior
- output and logging locations

Phase 4A installs nothing and starts no inference process.

## 8. Non-goals

The following are explicitly outside Phase 4A:

- loading `best.pt` or downloading any model weight
- running image, video, Camera or RTSP inference
- ByteTrack
- person-PPE association
- Helmet/Vest compliance rules
- temporal confirmation or event deduplication
- SQLite, screenshot evidence, TTS or alerts
- Streamlit Web implementation
- LLM reports or Agent behavior
- changing the dataset, class mapping, training configuration or model files

## 9. Acceptance direction for Phase 4

The locked Phase 4 gates remain:

| Gate | Requirement |
| --- | --- |
| P4-G1 | Image detection returns boxes, labels, confidence and structured output |
| P4-G2 | Video preserves order and produces annotated video and statistics |
| P4-G3 | Camera/RTSP is a real source path with observable failure states |

Phase 4A only freezes this architecture and its interface direction. Phase 4B
must not start until a later instruction approves implementation and the
inference runtime/configuration boundary.

## 10. Design decisions and open items

Design decisions:

- one adapter contract across all input types, with source-specific lifecycle
  states
- one detector wrapper responsible only for model inference and conversion
- flat, JSON-serializable `DetectionResult` records
- real source failure is observable
- all downstream PPE semantics remain outside Phase 4

Open items for later review:

- exact output formats for annotated images and video
- RTSP timeout, reconnect and shutdown thresholds
- whether Camera is device-backed, stream-backed or both in the final demo
- production inference configuration and performance acceptance thresholds

None of these open items authorizes implementation or model execution in
Phase 4A.

## 11. Phase 4B-0 disposition

Phase 4B-0 subsequently froze `INF-RUNTIME-001` as the CPU-only reference
runtime, the release checkpoint identity, device policy, threshold policy,
input formats, `DetectionResult` schema reference and fail-closed error policy.
The machine-readable contract is `configs/inference.yaml` with
`execution_enabled: false`; the detailed record is
`docs/phases/PHASE_04B_RUNTIME_FREEZE.md`.

This disposition does not change the Phase 4A architecture or authorize
implementation. Phase 4B-1 remains waiting.
