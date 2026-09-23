# Phase 4C Real Inference Validation Design

Date: 2026-09-23

Status: **COMPLETE / IMAGE AND VIDEO VALIDATION PASS / PHASE 5 WAITING**

Phase 4C-0: COMPLETE

Phase 4C-1: COMPLETE (IMAGE)

Phase 4C-2: COMPLETE (MP4 VIDEO)

## 1. Validation goal

Phase 4C will validate that the implemented inference path works with the
actual frozen release checkpoint, external real inputs and the frozen runtime:

```text
frozen checkpoint
  + external image or MP4
  + INF-RUNTIME-001
  -> real structured output
  -> reproducible validation evidence
```

The goal is execution validation, not model accuracy evaluation. It must not
reuse the Phase 3 test set to claim new metrics, tune thresholds, retrain, or
replace the completed M-005 evaluation.

Phase 4C-0 only defines the process and evidence schema. It does not load
`best.pt`, open an external input, execute inference or write a result artifact.

Phase 4C-1 was later authorized for image validation only. The actual execution
loaded the frozen checkpoint, processed one external image and wrote the
image-validation evidence. Phase 4C-2 was subsequently authorized separately
for MP4 validation and processed every frame of one external short video.

## 2. Image validation

### Preconditions

- explicit Phase 4C-2 human authorization
- execution-enabled configuration reviewed separately
- runtime identity `INF-RUNTIME-001`
- checkpoint path and SHA256 match the Phase 4B-0 freeze
- at least one external image that is not part of the frozen dataset

The external input remains outside Git. Its committed or retained evidence is
an opaque `source_label`, never a machine-specific absolute path.

### Procedure

1. Verify the checkpoint path, size and SHA256 before model construction.
2. Validate that the image exists, is a supported format and can be decoded.
3. Measure model-load and inference latency with a monotonic clock.
4. Run `Image -> InferenceService -> list[DetectionResult]`.
5. Record the number, classes and confidence values of returned detections.
6. Serialize an `ImageValidationRecord`.

### Required evidence

| Field | Meaning |
| --- | --- |
| `source_label` | non-secret external input label |
| `model_sha256` | frozen release checkpoint digest |
| `load_success` | decode and inference completed |
| `width`, `height` | decoded image dimensions |
| `detection_count` | number of returned detections |
| `class_counts` | per-class detection counts |
| `confidences` | ordered confidence values |
| `latency_ms` | measured image inference latency |
| `error_code` | stable failure code when unsuccessful |

Latency is an observation for this machine and input only. It is not a
production performance guarantee.

## 3. Video validation

### Preconditions

- explicit Phase 4C-1 human authorization
- execution-enabled configuration reviewed separately
- frozen checkpoint and `INF-RUNTIME-001`
- one short external MP4 outside Git
- sequential processing with no frame skipping or parallel inference

### Procedure

1. Verify the checkpoint before opening the video.
2. Read the MP4 with `VideoReader` and preserve source frame order.
3. Record source FPS, declared frame count, dimensions and duration metadata.
4. Process every frame through `VideoInferenceService`.
5. Measure total elapsed time with a monotonic clock.
6. Record detection totals, frames containing detections and per-class counts.
7. Serialize a `VideoValidationRecord`.

### Required evidence

| Field | Meaning |
| --- | --- |
| `source_label` | non-secret external video label |
| `model_sha256` | frozen release checkpoint digest |
| `source_fps` | source video FPS |
| `declared_frame_count` | decoder metadata when available |
| `processed_frames` | frames actually processed |
| `processing_time_seconds` | total sequential wall time |
| `processing_fps` | processed frames divided by wall time |
| `total_detections` | all returned detections |
| `frames_with_detections` | frames with at least one detection |
| `class_counts` | per-class detection counts |
| `error_code` | stable failure code when unsuccessful |

`processing_fps` is observed end-to-end CPU throughput and must not be described
as real-time capability or camera/RTSP performance.

## 4. Evidence policy

External validation media does not enter Git.

- Keep images, MP4 files, model weights and large evidence outside tracked
  source paths.
- Use a local configuration value or environment variable to locate external
  media; do not commit machine-specific paths.
- Store generated validation output under Git-ignored
  `artifacts/validation/<validation-id>/`.
- Keep JSON records machine-readable and deterministic apart from measured
  timing values.
- Do not copy the checkpoint, external media or model binary into evidence.
- Do not include API keys, tokens, credentials or private machine paths.

The planned evidence files are:

```text
artifacts/validation/P4C-1/image_validation.json
artifacts/validation/P4C-1/validation_report.json
artifacts/validation/P4C-2/video_validation.json
artifacts/validation/P4C-2/frame_summary.json
artifacts/validation/P4C-2/validation_report.json
```

The model-independent contracts are in `core/schemas/validation.py`.

## 5. Failure handling

Validation must fail closed:

| Failure | Required result |
| --- | --- |
| Checkpoint missing or SHA256 mismatch | Stop before model or input execution |
| Runtime/package mismatch | Stop with `runtime_unavailable` |
| Model load failure | Record failed validation; do not substitute a model |
| Unsupported image | Record `invalid_image_format` |
| Unsupported video | Record `invalid_video_format` |
| Empty or truncated video | Record `empty_video` or `video_decode_failed` |
| Inference error | Stop and record the stable detector error code |
| Empty detections | Valid successful result with zero counts |
| Result write failure | Record `result_write_failed`; do not claim success |

No silent retry, model substitution, device substitution, frame skipping or
fabricated detection is allowed.

## 6. Non-goals

Phase 4C does not include:

- model accuracy benchmarking or test-set tuning
- training or checkpoint modification
- dataset, mapping or training-asset modification
- RTSP or Camera validation
- ByteTrack or other tracking
- Person-PPE association
- compliance rules, temporal confirmation or events
- alerts, Web, LLM or Agent behavior
- annotated video rendering

## 7. Phase 4C-1 and Phase 4C-2 entry conditions

Each validation subphase may start only after its own explicit human
authorization. It must:

1. use the frozen release checkpoint and `INF-RUNTIME-001`;
2. use newly supplied external image and MP4 inputs;
3. enable execution only in a reviewed validation configuration;
4. write evidence only under Git-ignored `artifacts/validation/`;
5. produce `image_validation.json`, `video_validation.json` and
   `validation_report.json`;
6. stop on any failure rather than substituting an input, model or device.

Phase 4C-1 completed the image path. Phase 4C-2 completed the MP4 path with
47/47 sequential frames, no frame skipping, no batch inference, no async
processing and no CUDA migration. The detailed evidence is recorded in
`PHASE_04C2_VIDEO_VALIDATION_REPORT.md`.

## 8. Phase 4C-0 gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P4C-0-G1 | Validation goal and anti-benchmark boundary defined | PASS |
| P4C-0-G2 | Image validation evidence defined | PASS |
| P4C-0-G3 | Video validation evidence defined | PASS |
| P4C-0-G4 | External asset and `artifacts/` policy defined | PASS |
| P4C-0-G5 | Failure behavior defined | PASS |
| P4C-0-G6 | No model or real inference execution | PASS |

## 9. Phase 4C-2 result

Phase 4C-2 loaded the frozen checkpoint and processed one external
public-domain MP4 through the existing sequential video path. It recorded
47 processed frames, 77 detections (`person` 76, `no_vest` 1), 15.1920268
seconds of end-to-end CPU time and 3.0937281 processing FPS. The video, raw
result, frame summary and schema-backed report remain Git-ignored. RTSP,
Camera, tracking, association, compliance, events and alerts remain outside
the completed scope. Phase 5 is waiting for authorization.
