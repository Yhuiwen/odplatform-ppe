# Phase 4B-2 Video Inference Architecture Design

Date: 2026-09-23

Status: **DESIGN COMPLETE / PHASE 4B-2b IMPLEMENTED / EXECUTION DISABLED**

Phase 4B-2a: COMPLETE

Phase 4B-2b: COMPLETE

This document defines the local MP4 video inference architecture and interface
contract only. It does not load `best.pt`, decode a real video, execute
inference, write output artifacts, or introduce tracking.

## 1. Video inference goal

Provide one deterministic, sequential MP4 pipeline that reuses the frozen
single-image detector contract while preserving frame order and source
timestamps:

```text
local MP4
  -> ordered FrameData
  -> existing YOLO11 detector
  -> DetectionResult per detection
  -> VideoInferenceResult
  -> JSON result writer
```

The video layer must not duplicate model loading, threshold selection or
Ultralytics result parsing. It consumes `YOLODetector` through the existing
`InferenceService` boundary.

## 2. Input contract

| Item | Contract |
| --- | --- |
| Input type | Local filesystem file |
| Required extension | `.mp4` |
| Source identity | `video:<basename>` |
| Read order | Decode order, frame ID `0..N-1` |
| Timestamp | Source-relative seconds, non-decreasing |
| Frame skipping | Prohibited |
| Source substitution | Prohibited |

The input is valid only when it is an existing regular file with an `.mp4`
suffix and can be opened by the future video reader. A decode failure is an
observable error and must not return a partial result as success.

Phase 4B-2a explicitly does not support:

- RTSP (`rtsp://` or `rtsps://`)
- Camera devices or camera URIs
- GIF, image-sequence or synthetic-frame replacement inputs
- network downloads

The broader `configs/inference.yaml` video extension list does not expand this
subphase. Any additional container format requires a later reviewed scope
change.

## 3. Frame model

`core/schemas/video.py` defines the model-independent `FrameData` contract:

| Field | Type | Meaning |
| --- | --- | --- |
| `frame_id` | integer | Contiguous zero-based decode index |
| `timestamp` | float | Source-relative timestamp in seconds |
| `image` | runtime object | Decoded frame passed to the detector |

`FrameData` performs contract validation only. It does not import or invoke
OpenCV, Torch, Ultralytics or a detector.

## 4. Video result schema

`VideoMetadata` records:

- source identity
- FPS
- frame width and height
- declared frame count when available
- duration in seconds when available

`FrameInferenceResult` records:

- frame ID
- timestamp
- immutable tuple of `DetectionResult` objects
- serialized detection count

`VideoInferenceResult` records the metadata and all ordered frame results.
Frame IDs must be contiguous from zero, timestamps must be non-decreasing,
and a declared frame count must match the returned frames. Empty detection
lists are valid results.

The complete result is JSON-serializable through `to_dict()`:

```json
{
  "video": {
    "source": "video:fixture.mp4",
    "fps": 25.0,
    "width": 1280,
    "height": 720,
    "frame_count": 2,
    "duration_seconds": 0.08
  },
  "processed_frames": 2,
  "frame_results": [
    {
      "frame_id": 0,
      "timestamp": 0.0,
      "detection_count": 0,
      "detections": []
    }
  ]
}
```

## 5. Pipeline

```text
VideoReader
  -> FrameProcessor
  -> InferenceService
  -> Result Writer
```

`VideoReader`

- validates the MP4 path and format
- opens and closes the decoder deterministically
- emits `FrameData` in decode order
- reports metadata and decode failures

`FrameProcessor`

- receives one `FrameData`
- calls `InferenceService` for that frame
- confirms every returned `DetectionResult` has the correct `frame_id`,
  timestamp and video source
- creates one `FrameInferenceResult`

`InferenceService`

- retains its existing image path and detector contract
- is not modified by Phase 4B-2a
- must be called once per ordered frame in Phase 4B-2b

`Result Writer`

- consumes the completed `VideoInferenceResult`
- writes JSON-serializable frame results under the configured inference root
- may render an annotated MP4 in Phase 4B-2b if separately implemented and
  tested
- must not mutate the source video

No reader, processor, service method or writer is implemented in Phase 4B-2a.

## 6. Runtime policy

The Phase 4B-0 runtime freeze remains authoritative:

| Policy | Frozen value |
| --- | --- |
| Processing | Sequential only |
| Device | CPU only |
| Frame skipping | Prohibited |
| Async processing | Prohibited |
| Parallel frame inference | Prohibited |
| Detector parameters | `imgsz=640`, `conf=0.25`, `iou=0.45`, `max_det=300` |
| Class filter | `[0, 1, 2, 3, 4]` |
| Execution switch | `execution_enabled: false` |

Video inference must not silently fall back to CUDA, another model or a
different source. Real execution remains blocked until a later authorization
and a reviewed execution-enabled configuration.

## 7. Error handling

The future implementation must fail closed with stable machine-readable
errors:

| Condition | Required behavior |
| --- | --- |
| Disabled execution | Stop before decoder or model loading |
| Missing file | `video_not_found` |
| Non-MP4 input | `invalid_video_format` |
| Decode failure | `video_decode_failed` |
| Checkpoint mismatch | Stop before processing |
| Frame inference failure | Stop with frame ID and error code |
| Result write failure | Return `result_write_failed`; do not claim success |
| No objects in a frame | Valid empty detection list |
| End of video | Clean completion |

Silent frame skipping, partial-success masking, automatic retry with another
source, fabricated frames and hidden device changes are prohibited.

## 8. Non-goals

Phase 4B-2a does not include:

- loading or executing `best.pt`
- decoding or executing a real video
- modifying `core/inference/detector.py` or `services/inference_service.py`
- annotated-video or streaming implementation
- ByteTrack or any tracking algorithm
- Person-PPE association
- compliance rules or temporal confirmation
- event creation, persistence, screenshots or alerts
- Web, LLM or Agent behavior
- dataset, mapping, training configuration or checkpoint changes

Camera and RTSP remain separate future Phase 4 work. They must never be
replaced by local MP4 input.

## 9. Phase 4B-2b entry conditions

Phase 4B-2b may begin only after explicit authorization. It must:

1. preserve the Phase 4B-0 runtime and checkpoint freeze;
2. implement the MP4 reader, sequential processor and result writer;
3. keep inference execution disabled in the canonical configuration;
4. use fake readers and fake model objects by default in unit tests;
5. avoid ByteTrack, association, compliance, event and alert behavior.

## 10. Phase 4B-2b implementation disposition

Phase 4B-2b subsequently implemented this design:

- `core/video/reader.py` provides sequential MP4 reading and `FrameData`
  emission.
- `services/video_inference_service.py` reuses `InferenceService` for each
  frame and returns `VideoInferenceResult`.
- `scripts/run_video_inference.py` provides structured JSON CLI output.
- `YOLODetector.detect_frame()` and `InferenceService.infer_frame()` expose the
  shared frozen inference policy without duplicating detector logic.

The canonical configuration remains `execution_enabled: false`; no real model
or large-scale video execution was performed. Phase 4B-2b is COMPLETE and
Phase 4B-3 is WAITING.
