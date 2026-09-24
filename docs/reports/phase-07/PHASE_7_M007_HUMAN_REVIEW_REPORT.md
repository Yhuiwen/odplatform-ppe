# Phase 7 M-007 Human Review Report

Date: 2026-09-24

Review scope: read-only audit of the M-007 annotated demo video implementation,
real MP4 output, metadata, frame-count integrity and frozen-asset boundaries.

Review status: `PASS`

Publication status: `NOT AUTHORIZED`

## 1. Reviewed Evidence

| Evidence | Result |
| --- | --- |
| `docs/reports/phase-07/PHASE_7_M007_IMPLEMENTATION_REPORT.md` | Present and reviewed |
| `artifacts/inference/annotated/P7-M007-RUN-002/demo.mp4` | Present and independently decoded |
| `artifacts/inference/annotated/P7-M007-RUN-002/run.json` | Present and complete |
| `artifacts/inference/annotated/P7-M007-RUN-002/frames.jsonl` | Present; 47 ordered records |
| `artifacts/inference/annotated/P7-M007-RUN-002/summary.json` | Present and complete |
| `artifacts/inference/annotated/P7-M007-RUN-002/renderer.log` | Present and successful |
| `artifacts/inference/annotated/P7-M007-preview-frame-020.png` | Visually inspected |

The output directory contains exactly the five artifacts defined by the output
contract. No M-007 staging directory remains.

## 2. Gate Audit

| Gate | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| P7-M007-G1 | Frozen checkpoint and inference contract verified | PASS | Checkpoint SHA256 and `configs/inference.yaml` SHA256 match `run.json`; checkpoint, class order, device and thresholds remain frozen |
| P7-M007-G2 | Local MP4 processed sequentially without frame skipping | PASS | Frame IDs are contiguous from 0 through 46 and timestamps are non-decreasing |
| P7-M007-G3 | Deterministic clipped boxes and labels rendered | PASS | Preview frame shows aligned boxes and readable class/confidence labels; rendering behavior is covered by focused unit tests |
| P7-M007-G4 | Source, processed, written and decoded frame counts equal | PASS | All count paths resolve to 47 |
| P7-M007-G5 | Final output published atomically | PASS | Complete final directory is present; no staging directory remains; atomic publish and conflict rejection are unit-tested |
| P7-M007-G6 | Failure paths remove staging output and expose no partial demo | PASS | Rollback tests pass; no partial output or staging artifact is present |
| P7-M007-G7 | Unit tests and real output-integrity validation pass | PASS | Focused suite: 7 passed; full suite: 414 passed, 1 skipped |
| P7-M007-G8 | Charter, model, dataset, training and Phase 5/6 modules unchanged | PASS | Frozen-path diff is empty and Charter diff is empty |

## 3. MP4 Output Verification

Independent OpenCV decode of `demo.mp4`:

| Item | Observed |
| --- | --- |
| Decoded frame count | 47 |
| Dimensions | 1280 x 720 |
| FPS | 23.976 |
| File size | 736,856 bytes |
| SHA256 | `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949` |
| Codec | `mp4v` |

The output SHA256 matches `summary.json`, both inside the nested output object
and at the top-level `output_sha256` field.

## 4. Metadata Completeness

`run.json` records:

- schema and implementation versions
- run ID and creation timestamp
- source path, SHA256, FPS, dimensions, frame count and duration
- inference config path and SHA256
- checkpoint path, SHA256 and size
- runtime identity and dependency versions
- class order, class filter, thresholds and device policy
- output directory, video filename and codec

`frames.jsonl` contains one JSON record per frame with no raw image payload.
Frame IDs are contiguous, timestamps are non-decreasing, and the detection
records produce 77 total detections.

`summary.json` records:

- source, processed, written and verified output frame counts
- elapsed time and processing FPS
- total detections and frames with detections
- all five class counts, including zero counts
- renderer and writer error lists
- output frame count, FPS, dimensions, duration, SHA256, size and codec

The implementation report describes the decoded output count in prose, while
the machine-readable field is named `verified_output_frame_count`. Both resolve
to 47; this is a terminology difference only and is not a release blocker.

## 5. Frame-Count Consistency

| Count source | Value |
| --- | --- |
| Source metadata | 47 |
| Processed frames | 47 |
| Written frames | 47 |
| Verified output frames | 47 |
| `frames.jsonl` records | 47 |
| Independent decoded MP4 frames | 47 |

Result: `PASS`.

## 6. Detection Statistics

| Class | Count |
| --- | ---: |
| person | 76 |
| hardhat | 0 |
| no_hardhat | 0 |
| vest | 0 |
| no_vest | 1 |
| Total | 77 |

The independent `frames.jsonl` recount matches the complete zero-filled class
counts in `summary.json`, the total detection count and the number of frames
with detections.

## 7. Frozen-Asset and Repository Checks

| Check | Result |
| --- | --- |
| Charter diff | EMPTY |
| Frozen detector/schema/video/tracking/association/compliance diff | EMPTY |
| Training configuration diff | EMPTY |
| Model directory diff | EMPTY |
| Source MP4 SHA256 | Matches `run.json` |
| Checkpoint SHA256 | Matches `run.json` |
| Inference config SHA256 | Matches `run.json` |
| `artifacts/inference/` ignored by Git | PASS (`.gitignore:46`) |
| `git diff --check` | PASS |

## 8. Tests

Focused review command:

```text
python -m pytest tests/unit/test_annotated_demo_video.py -q
7 passed
```

Full repository command:

```text
python -m pytest -q
414 passed, 1 skipped
```

The skip is the existing optional Torch-dependent evaluation test:
`could not import 'torch': No module named 'torch'`.

## 9. Known Limitations

- Real validation used one 47-frame public-domain MP4.
- CPU processing measured approximately 2.4674 FPS in the implementation run.
- Long-duration video and disk-headroom behavior were not validated.
- Codec portability beyond the frozen `mp4v` environment was not validated.
- The real clip contains only person and no-vest detections; other PPE class
  rendering is covered by unit tests.
- Full M-007 Phase 9 acceptance and alteration of the Charter M-007 status
  remain pending.

These limitations do not invalidate the G1-G8 evidence and do not constitute a
need-fix condition for this implementation gate.

## 10. Final Decision

```text
PHASE 7 M-007 HUMAN REVIEW: PASS
Gates P7-M007-G1 through P7-M007-G8: PASS
Demo MP4: VERIFIED
Metadata: COMPLETE
Frame-count consistency: PASS
Code changes: NO
Existing documentation changes: NO
Commit: NO
Tag: NO
Push: NO
Next step: WAIT FOR HUMAN ACCEPTANCE
```
