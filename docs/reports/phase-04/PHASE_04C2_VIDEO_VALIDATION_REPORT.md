# Phase 4C-2 Real MP4 Inference Validation Report

Date: 2026-09-23

Status: **COMPLETE / MP4 VALIDATION PASS / PHASE 5 WAITING**

This report records the authorized Phase 4C-2 validation run. The frozen
EXP-001 release checkpoint was loaded once, and the existing sequential
`VideoReader -> VideoInferenceService -> InferenceService -> YOLODetector`
path processed every frame of one external MP4. No training, evaluation,
tracking, association, compliance, event, alert, Web, LLM or dataset
processing was executed.

## 1. Checkpoint identity

| Field | Value |
| --- | --- |
| Selection ID | SEL-001 |
| Experiment | EXP-001 |
| Checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Checkpoint size | 5,479,891 bytes |
| Checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Frozen inference configuration | `configs/inference.yaml` |
| Frozen inference configuration SHA256 | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| Validation configuration | `configs/video_validation.yaml` |
| Validation configuration SHA256 | `1a0d19bff737ae89b7a8bb2e6d8d130889891dc17b75e9d30be62f1bafbe2693` |

The checkpoint path, size and SHA256 matched the Phase 4B-0 runtime freeze
before the model was constructed. The checkpoint was not modified.

## 2. Runtime

| Field | Observed value |
| --- | --- |
| Runtime ID | `INF-RUNTIME-001` |
| OS | Windows x86_64 |
| Python | 3.10.4 |
| PyTorch | 2.5.1+cpu |
| torchvision | 0.20.1 |
| Ultralytics | 8.4.157 |
| NumPy | 2.2.6 |
| OpenCV | 5.0.0 |
| Device | CPU |
| CUDA | Not used |
| Dependency source | `locks/EVAL-001/requirements.txt` |

The isolated Phase 3 evaluation environment was reused. Frozen
`configs/inference.yaml` remained `execution_enabled: false`; execution was
enabled only by the independent Phase 4C-2 validation configuration.

## 3. Video metadata and provenance

| Field | Value |
| --- | --- |
| Source label | `external:know-your-nailer-public-domain` |
| Provider | NIOSH / Wikimedia Commons |
| Source URL | `https://commons.wikimedia.org/wiki/File:Know_Your_Nailer-_Nail_Gun_Safety_(short_version).webm` |
| License | Public domain |
| Derivation | Two-second MP4 segment from 14.5 seconds; every decoded frame retained |
| Local evidence path | `artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4` |
| Container / codec | MP4 / H.264 |
| Dimensions | 1280 x 720 |
| Source FPS | 23.976023976023978 |
| Declared frame count | 47 |
| Duration | 1.9602916666666665 seconds |
| File size | 409,461 bytes |
| SHA256 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |

The MP4 is external validation media and is not part of `CSS-PPE-10-V1`. It is
stored only under the Git-ignored `artifacts/validation/` tree; `git
check-ignore` confirmed that the MP4 does not enter Git.

## 4. Frame processing

| Field | Result |
| --- | ---: |
| Processed frames | 47 / 47 |
| Frame ID range | 0 through 46 |
| Frame order | Contiguous and source order preserved |
| Timestamps | Monotonic |
| Frame skipping | None |
| Async processing | None |
| Batch inference | None |
| Device migration | None |

The reader and inference service processed the MP4 sequentially. Every
decoded frame was passed through the shared frame-level inference boundary.

## 5. Inference statistics

| Metric | Observed value |
| --- | ---: |
| Total detections | 77 |
| Frames with detections | 47 |
| Frames without detections | 0 |
| Total sequential processing time | 15.192026799995801 seconds |
| End-to-end processing FPS | 3.093728086367843 |

The measured time includes lazy checkpoint loading and first-frame inference,
plus sequential decode and CPU inference for all remaining frames. It is an
end-to-end observation for this run, not a steady-state or GPU claim.

## 6. Detection statistics

| Class | Detection count |
| --- | ---: |
| person | 76 |
| no_vest | 1 |
| Total | 77 |

Per-frame detection distribution:

| Detections in frame | Frames |
| ---: | ---: |
| 1 | 18 |
| 2 | 28 |
| 3 | 1 |

These are per-frame detection counts, not tracked identities. A person may be
counted in multiple frames. The run does not associate PPE with people and
does not make a compliance or violation decision.

## 7. Output evidence

Generated Git-ignored evidence:

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `artifacts/validation/P4C-2/video_validation.json` | 42,014 | `820a673f617df6153eb253c63a9e3ab5e92f412039e06ddc4e762dd64a24f0e1` |
| `artifacts/validation/P4C-2/frame_summary.json` | 7,788 | `d9f11906cf68dabd8c8b3741ccce999bf9d327d25863e54ec4d02805154053aa` |
| `artifacts/validation/P4C-2/validation_report.json` | 962 | `df043a8d048d99cd365915d532265fd780a6418735951b20cca3b0322f398fcd` |

`validation_report.json` is backed by `VideoValidationRecord` and
`InferenceValidationReport`. Its checkpoint identity, frame counts, detection
totals and class counts were accepted by the existing validation schemas.

## 8. Performance baseline

| Field | Value |
| --- | --- |
| Observed throughput | 3.093728086367843 FPS |
| Average detections per frame | 1.6382978723 |
| Model load included | Yes, on the first frame |
| Real-time claim | None |
| Production SLA | None |

The result is a single CPU performance baseline for one short external clip.
It does not establish real-time capability for video, Camera or RTSP.

## 9. Limitations

The following remain unverified and were not executed:

- Camera and RTSP input;
- ByteTrack or any object tracking;
- Person-PPE association;
- temporal compliance confirmation;
- events, alerts, Web, LLM or Agent behavior;
- production accuracy, safety, throughput or real-time performance;
- long-video, concurrency, GPU or optimized inference behavior.

Only one external two-second MP4 was validated. No dataset image or label was
read or modified, no model weight was downloaded, and no training or model
evaluation was run.

## 10. Gate result

| Gate | Result |
| --- | --- |
| P4C2-G1 Frozen checkpoint identity verified | PASS |
| P4C2-G2 Frozen CPU sequential runtime used | PASS |
| P4C2-G3 External MP4 validated without entering Git | PASS |
| P4C2-G4 All 47 source frames processed in order | PASS |
| P4C2-G5 Structured video evidence retained | PASS |
| P4C2-G6 No tracking, association, event or alert work executed | PASS |
| P4C2-G7 Dataset, mapping, checkpoint and training assets unchanged | PASS |

Final status:

```text
Phase 4C-2 video validation: COMPLETE
Phase 5: WAITING
Training: NOT EXECUTED
Dataset modification: NONE
Checkpoint modification: NONE
Commit/push/tag: NOT PERFORMED
```
