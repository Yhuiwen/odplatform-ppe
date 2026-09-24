# Phase 7 M-007 Annotated Demo Video Implementation Report

Date: 2026-09-23

Status: `IMPLEMENTATION COMPLETE / REAL MP4 VALIDATION PASS / HUMAN REVIEW PENDING`

Publication: `NOT AUTHORIZED`

## 1. Pre-Read Result

| Item | Result |
| --- | --- |
| Current phase | Phase 7 - Web & Alerts |
| Current subphase | Phase 7 M-007 - Annotated Demo Video Generator |
| Experiment | EXP-001 |
| Training | COMPLETED; no retraining or evaluation authorized |
| Authorization | Implementation and one short MP4 validation authorized |
| Relevant MUST | M-007 |
| Conflicts found | NO |

The implementation uses the existing `VideoReader` and `InferenceService`
boundaries. The detector, video schemas, training configuration, dataset,
release checkpoint, tracking, association and compliance engine were not
modified.

## 2. Implemented Components

| File | Responsibility |
| --- | --- |
| `core/rendering/annotated_frame.py` | Deterministic clipped box, class-name and confidence rendering |
| `core/rendering/__init__.py` | Rendering boundary exports |
| `infra/storage/annotated_video_writer.py` | Staged MP4 writing, metadata writes, decoded frame-count verification, atomic directory publication and rollback |
| `services/annotated_video_service.py` | Ordered MP4 -> inference -> render -> writer composition |
| `scripts/render_annotated_demo_video.py` | CLI with structured success/error JSON |
| `tests/unit/test_annotated_demo_video.py` | Rendering, ordering, metadata, atomic publish, rollback and CLI tests |

Pipeline:

```text
local MP4 -> VideoReader -> FrameData
          -> InferenceService.infer_frame()
          -> FrameInferenceResult
          -> AnnotatedFrameRenderer
          -> AnnotatedVideoWriter
          -> atomic output directory
```

## 3. Frozen Runtime and Configuration

| Item | Observed value |
| --- | --- |
| Runtime | `INF-RUNTIME-001` |
| Python | 3.10.4 |
| PyTorch | 2.5.1+cpu |
| torchvision | 0.20.1 |
| Ultralytics | 8.4.157 |
| OpenCV | 5.0.0 runtime (`opencv-python` 5.0.0.93) |
| NumPy | 2.2.6 |
| Device | CPU only |
| Checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Inference config SHA256 | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |

`configs/inference.yaml` remains execution-disabled. The validation CLI
requires the explicit `--authorized-execution` flag; it does not modify the
configuration or override checkpoint, class order, device, `imgsz`, confidence
threshold, IoU threshold or batch size.

## 4. Output Contract

Each successful run writes exactly:

```text
artifacts/inference/annotated/<run-id>/
  demo.mp4
  run.json
  frames.jsonl
  summary.json
  renderer.log
```

`run.json` records source/config/checkpoint hashes, runtime identity, class
order, thresholds and output location. `frames.jsonl` contains one ordered
record per frame without raw image data. `summary.json` records source,
processed, written and verified output frame counts, elapsed time, processing
FPS, class counts and output SHA256/dimensions.

## 5. Atomicity, Validation and Rollback

- All five artifacts are written to a same-volume hidden staging directory.
- The writer reopens and decodes the staged MP4 before publication.
- Publication occurs only when the declared source frame count, processed
  frame count, appended frame count and decoded output frame count all match.
- Publication is one atomic directory rename to the requested final path.
- The final path must not already exist.
- Decode, inference, rendering, verification or metadata failure removes the
  staging directory and never exposes a partial `demo.mp4`.
- The default `artifacts/inference/` root is Git-ignored.

## 6. Real MP4 Validation

Input:

```text
artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4
SHA256: b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852
```

Run:

```text
run_id: 20260923T144228Z-fed06724
output: artifacts/inference/annotated/P7-M007-RUN-002/
```

| Metric | Result |
| --- | --- |
| Source frame count | 47 |
| Processed frame count | 47 |
| Written frame count | 47 |
| Decoded output frame count | 47 |
| Output dimensions | 1280x720 |
| Output FPS | 23.976 |
| Duration | 1.9603 seconds |
| Elapsed processing time | 19.0486 seconds |
| Processing FPS | 2.4674 |
| Total detections | 77 |
| Person detections | 76 |
| No-vest detections | 1 |
| Output size | 736,856 bytes |
| Output codec | `mp4v` |
| Output SHA256 | `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949` |
| `frames.jsonl` records | 47 |

A decoded frame was visually inspected. Person boxes and confidence labels were
visible, aligned to the source frame and did not alter source dimensions.

## 7. Tests

Commands:

```text
python -m pytest
python -m compileall .
git diff --check
```

Result:

```text
414 passed, 1 skipped
```

The skip is the existing optional Torch evaluation test on the governance
Python runtime. M-007 unit tests cover deterministic color/label generation,
clipped coordinates, class-name binding, ordered frames, complete output
metadata, decoded count mismatch, reader failure rollback, output conflict
rejection and structured CLI errors.

## 8. Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-M007-G1 | Frozen checkpoint and inference contract verified | PASS |
| P7-M007-G2 | Local MP4 processed sequentially without frame skipping | PASS |
| P7-M007-G3 | Deterministic clipped boxes and labels rendered | PASS |
| P7-M007-G4 | Source, processed, written and decoded frame counts equal | PASS |
| P7-M007-G5 | Final output published atomically | PASS |
| P7-M007-G6 | Failure paths remove staging output and expose no partial demo | PASS |
| P7-M007-G7 | Unit tests and real output-integrity validation pass | PASS |
| P7-M007-G8 | Charter, model, dataset, training and Phase 5/6 modules unchanged | PASS |

## 9. Known Limitations

- Validation used one short 47-frame public-domain MP4.
- CPU processing measured 2.4674 FPS; long-duration videos and disk headroom
  were not tested.
- Codec portability beyond the frozen `mp4v` environment was not tested.
- The sample contains person and no-vest detections only; deterministic
  hardhat, no-hardhat and vest rendering is covered by unit tests rather than
  this single real clip.
- Human approval of rendered visual quality and full M-007 Phase 9 acceptance
  remain pending.
- The Charter M-007 status remains `待实现`.

## 10. Final Decision

```text
Phase 7 M-007 implementation: COMPLETE
Real MP4 output validation: PASS
Human review: PENDING
Charter M-007: 待实现
Commit: NO
Tag: NO
Push: NO
Next allowed step: WAIT FOR PHASE 7 M-007 HUMAN REVIEW
```
