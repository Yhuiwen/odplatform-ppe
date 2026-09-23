# Phase 4C-1 Real Image Inference Validation Report

Date: 2026-09-23

Status: **COMPLETE / IMAGE VALIDATION PASS / VIDEO DEFERRED**

This report records the single authorized Phase 4C-1 validation run. It loaded
the frozen EXP-001 release checkpoint and executed real single-image inference
through the existing `Image -> InferenceService -> YOLODetector ->
DetectionResult` path. It did not execute video, Camera, RTSP, tracking,
association, compliance, event, alert, Web, LLM, training, evaluation or
dataset-processing work.

## 1. Checkpoint identity

| Field | Value |
| --- | --- |
| Selection ID | SEL-001 |
| Experiment | EXP-001 |
| Model | YOLO11n project-trained model |
| Checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Checkpoint size | 5,479,891 bytes |
| Checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Frozen inference config | `configs/inference.yaml` |
| Frozen inference config SHA256 | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| Validation config | `configs/validation.yaml` |

The checkpoint path and SHA256 matched the Phase 4B-0 freeze before model
construction. The checkpoint was not modified.

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
| Pillow | 12.3.0 |
| Device | CPU |
| CUDA | Not used |
| Dependency source | `locks/EVAL-001/requirements.txt` |

The isolated Phase 3 evaluation environment was reused. `configs/inference.yaml`
kept `execution_enabled: false`; execution was enabled only through the
validation-only configuration and an explicit call-level override in
`scripts/run_image_validation.py`.

## 3. Input information

| Field | Value |
| --- | --- |
| Source label | `external:construction-workers-public-domain` |
| Provider | NIOSH / Wikimedia Commons |
| Source URL | `https://commons.wikimedia.org/wiki/File:Construction_workers_not_wearing_fall_protection_equipment.jpg` |
| License | Public domain |
| Format | JPEG |
| Dimensions | 1024 x 766 |
| File size | 427,864 bytes |
| SHA256 | `23aba350f9eace6466851d7e4b0178a3bf02ef208b31f20cbf46e71e049b8e42` |

The external image is not part of `CSS-PPE-10-V1`, is not a test-set image and
does not enter Git. Its local path is intentionally omitted.

## 4. Model loading and inference result

The frozen checkpoint loaded successfully through Ultralytics 8.4.157. The run
completed two schema-producing calls:

1. A cold-start call measured model construction/loading plus first-image
   inference.
2. A warm call measured the second inference on the same already-loaded model.

The warm result is the retained validation result. The detector returned five
`DetectionResult` objects and no Ultralytics framework result objects crossed
the service boundary.

## 5. Detection statistics

| Class | Count |
| --- | ---: |
| person | 2 |
| hardhat | 1 |
| no_hardhat | 1 |
| vest | 0 |
| no_vest | 1 |
| Total | 5 |

Confidence values in returned order:

```text
0.8684056997299194
0.5178987979888916
0.5166388154029846
0.4684692919254303
0.437183141708374
```

The result demonstrates execution and schema output only. It is not an accuracy
measurement, a compliance event decision or evidence that the image contains a
confirmed violation.

## 6. Latency

| Measurement | Observed value |
| --- | ---: |
| Cold start, model load plus first inference | 14,237.083 ms |
| Warm second-image inference | 176.386 ms |

These values describe this one CPU machine, runtime and image only. They are not
a production SLA, throughput claim or GPU comparison.

## 7. Output validation

Generated Git-ignored evidence:

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `artifacts/validation/P4C-1/image_validation.json` | 2,845 | `5347e328670681bab35d182d0b78660cb43731568059777484ee607e7231c610` |
| `artifacts/validation/P4C-1/validation_report.json` | 1,105 | `aa2569776a133b65d70f08b87fd0c93d64da89963d583d1b64cb8019a42e3d41` |

`validation_report.json` was reconstructed through
`ImageValidationRecord` and `InferenceValidationReport`; its detection count,
class counts, confidence count and model identity were accepted by the existing
validation schema. No video record was created.

## 8. Limitations

The following remain unverified and were not executed:

- video inference and processing throughput;
- Camera and RTSP behavior;
- ByteTrack or any object tracking;
- Person-PPE association;
- temporal compliance confirmation;
- events, alerts, Web, LLM or Agent behavior;
- production accuracy, safety or real-time performance.

Only one external image was validated. No dataset image was read or modified,
no model weight was downloaded, and no training or model evaluation was run.

## 9. Gate result

| Gate | Result |
| --- | --- |
| P4C1-G1 Frozen checkpoint identity verified | PASS |
| P4C1-G2 Frozen runtime used | PASS |
| P4C1-G3 External image validated without entering Git | PASS |
| P4C1-G4 Real image inference executed | PASS |
| P4C1-G5 Structured output and schema evidence retained | PASS |
| P4C1-G6 Video and downstream capabilities not executed | PASS |
| P4C1-G7 Dataset, mapping, checkpoint and training assets unchanged | PASS |

Final status:

```text
Phase 4C-1 image validation: COMPLETE
Phase 4C-1 video validation: DEFERRED / NOT AUTHORIZED
Training: NOT EXECUTED
Dataset modification: NONE
Checkpoint modification: NONE
Commit/push/tag: NOT PERFORMED
```
