# Phase 7 M-007 Annotated Demo Video Tool Design

Date: 2026-09-23

Status: DESIGN COMPLETE / IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING

## 1. Goal

Define a deterministic offline tool that renders a local MP4 into an
annotated demonstration MP4 while preserving source frame order and recording
processing statistics.

The design covers the remaining M-007 acceptance gap: structured video
inference already exists, but annotated video output does not.

## 2. Scope

- Input: local MP4 only.
- Runtime: the frozen checkpoint and inference policy.
- Processing: sequential, single-frame inference, no frame skipping.
- Output: annotated MP4 plus machine-readable run metadata and summary.
- Rendering: person and PPE detection boxes, class names and confidence.

The tool is for local demonstration and reproducible evidence. It is not a
real-time source runner.

## 3. Non-Goals

The design does not include:

- Camera, USB or RTSP execution;
- ByteTrack or track-ID overlays;
- Person-PPE association or compliance-event overlays;
- alert, TTS, dashboard or database changes;
- violation clip retention under Extension E-005;
- model download, retraining, evaluation reruns or class remapping;
- asynchronous, batched or frame-skipping inference;
- changes to the frozen detector or `VideoInferenceService`.

## 4. Frozen Inputs

| Input | Frozen boundary |
| --- | --- |
| Runtime config | `configs/inference.yaml` |
| Checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Class filter | `person`, `hardhat`, `no_hardhat`, `vest`, `no_vest` |
| Device policy | CPU only |
| Image size / batch | `640` / `1` |

The checkpoint hash shown above is the current frozen asset identity and must
be checked again at implementation time. The implementation must refuse to run
if the configured and observed hashes differ.

## 5. Proposed Module Boundaries

The authorized implementation adds only these project-owned components:

| Module | Responsibility |
| --- | --- |
| `services/annotated_video_service.py` | Compose the existing `VideoReader` and `InferenceService`; render and write one ordered output video |
| `core/rendering/annotated_frame.py` | Pure drawing contract for one frame and its `FrameInferenceResult` |
| `infra/storage/annotated_video_writer.py` | Video writer lifecycle, frame-count checks and atomic output publication |
| `scripts/render_annotated_demo_video.py` | CLI entry point and structured error output |
| `tests/unit/test_annotated_demo_video.py` | Unit tests with fake frames and an injected detector |

The implementation must not modify `core/schemas/detection.py`,
`core/schemas/video.py`, `core/inference/detector.py`,
`services/video_inference_service.py` or any Phase 5/6 module.

## 6. Pipeline

```text
MP4 path
  -> VideoReader
  -> FrameData
  -> InferenceService.infer_frame()
  -> FrameInferenceResult
  -> AnnotatedFrameRenderer
  -> AnnotatedVideoWriter
  -> demo.mp4 + run.json + summary.json
```

The service owns the loop. It must not return or persist Ultralytics result
objects and must not alter the source video.

## 7. CLI Contract

The future command is:

```text
python scripts/render_annotated_demo_video.py \
  --video <local.mp4> \
  --output-dir artifacts/inference/annotated/<run-id> \
  --config configs/inference.yaml
```

Required behavior:

- reject missing or non-MP4 input;
- reject a checkpoint or runtime mismatch;
- reject `execution_enabled: false`;
- fail closed on decode, inference, rendering or write failure;
- print one JSON object containing `status`, `run_id`, `output_video`,
  `processed_frames`, `source_frames`, `elapsed_seconds` and `error`.

No option may override the frozen class mapping, checkpoint identity, device
policy, `imgsz`, confidence threshold or batch size.

## 8. Rendering Contract

- Draw only detections returned for the current frame.
- Use the frozen class names and class IDs without remapping.
- Draw a clipped axis-aligned box and a label containing class name and
  confidence.
- Use deterministic colors per class ID.
- Do not draw a track ID, compliance state or event ID in this M-007 slice.
- Do not invent a box when a source frame contains no detections.
- Preserve the source frame dimensions and sequential order.
- Write the output at the source FPS unless the source metadata is invalid;
  invalid metadata is a fail-closed error rather than a guessed value.

## 9. Output Contract

The default future output root is Git-ignored:

```text
artifacts/inference/annotated/<run-id>/
  demo.mp4
  run.json
  frames.jsonl
  summary.json
  renderer.log
```

`run.json` records:

- run ID and UTC creation time;
- source path and source SHA256;
- source metadata;
- inference config path and SHA256;
- checkpoint path and SHA256;
- class order and thresholds;
- output path and codec;
- implementation version.

`summary.json` records:

- source frame count and processed frame count;
- written frame count;
- elapsed processing time;
- processing FPS;
- per-class detection count;
- renderer and writer errors;
- output SHA256 and output dimensions.

`frames.jsonl` records one ordered record per processed frame with frame ID,
timestamp, detection count and detection summaries. It must not contain raw
frame binaries.

The final output video and metadata must be written to temporary paths and
published atomically only after the processed frame count equals the source
frame count.

## 10. Runtime and Error Policy

- Sequential processing only.
- CPU-only policy inherited from the frozen inference config.
- No model download, CUDA migration, batching, async processing or frame
  skipping.
- A decode failure terminates the run with a structured error.
- A writer failure terminates the run; no partial output is presented as a
  successful demo.
- A count mismatch is a failed run and remains recorded as failed evidence.
- Output media remains Git-ignored.

## 11. Verification Plan

Before M-007 can be marked implemented, the implementation authorization must
require:

1. Unit tests with fake frames proving order, count, color/label determinism
   and fail-closed errors.
2. An integration test that uses a short local MP4 and the frozen checkpoint.
3. Verification that output frame count equals input frame count.
4. Verification that source, checkpoint and config hashes match the freeze.
5. A report containing the output video hash, dimensions, codec, duration,
   source frame count, processed frame count and elapsed time.
6. A human review confirming that the annotated output is inspectable and
   that no upstream asset changed.

## 12. M-007 Acceptance Mapping

| M-007 requirement | Current state |
| --- | --- |
| Local video frame-by-frame detection | Implemented and validated in Phase 4/7 |
| Preserve temporal order | Implemented and validated |
| Record processed frame count and elapsed time | Implemented in `summary.json`; one real 47/47-frame run is recorded |
| Output annotated video | Implemented with atomic publication and real output validation |

M-007 therefore remains `待实现` in the locked Charter until human review and
Phase 9 acceptance. The implementation and runtime evidence do not authorize
a Charter release-status change.

## 13. Next Allowed Step

`WAIT FOR PHASE 7 M-007 HUMAN REVIEW`

No model, dataset, training, inference or core-pipeline change is authorized by
this design document.
