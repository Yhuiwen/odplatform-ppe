# Phase 3 EXP-001 Evaluation Report

Date: 2026-09-22

Status: **M-005 EVALUATION COMPLETED / AWAITING HUMAN REVIEW**

## Scope and acceptance boundary

Implemented and executed an independent test-split evaluation of the frozen
EXP-001 best.pt. This report supplies all four overall metrics, the five locked
PPE per-class AP values, both additional scene classes, a confusion matrix,
error analysis, raw predictions/labels and an offline replay command.

No training, new training experiment, dataset/mapping mutation, weight update,
Phase 2 tag movement, commit or push was performed. EVAL-001 is an evaluation
record of EXP-001, not a new training experiment. The Phase 2 release artifacts
and training configuration remain unchanged.

M-005 technical evidence is complete and submitted for human review. The
Charter formal acceptance status remains pending until that review; no locked
criterion was weakened. Phase 3 as a whole is not declared complete: cross-model
comparison (P3-G3) and final comparative model selection (P3-G4) remain pending.

## Identity and fixed protocol

| Field | Value |
| --- | --- |
| Training experiment / evaluation record | EXP-001 / EVAL-001 |
| Model | YOLO11n, Project-trained Model |
| Checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Original selection | Best validation epoch 75; selected before this test evaluation |
| Dataset / mapping | CSS-PPE-10-V1 / PPE-MAPPING-V1 |
| Split / images / instances | test / 82 / 561 |
| Class order | person, hardhat, no_hardhat, vest, no_vest, machinery, vehicle |
| Evaluation configuration | `configs/evaluation/exp001_test.yaml` |
| Evaluation config SHA256 | `796bf9dc6515b7636c805947f72ba8f1a99e7d66493f4a4c7240fee6dca5cbc6` |
| Image size / batch | 640 / 1 |
| Device / arithmetic | CPU / FP32 |
| Seed / Torch threads | 42 / 4 |
| Detection confidence floor | 0.001, for AP accumulation |
| NMS | IoU 0.7, class-aware, single-label predict postprocessing, max_det 300 |
| Operating Precision/Recall | Fixed confidence >= 0.25 and matching IoU >= 0.5 |
| AP IoU thresholds | 0.50:0.05:0.95 |
| Augmentation / rectangular padding | Disabled / disabled |
| Small-object definition | Normalized ground-truth area < 0.01 |

The test split and thresholds were configured before model execution. No threshold
search, checkpoint reselection, split changes or test-set tuning occurred. The
pipeline loads images through PIL and reads label files directly; it does not invoke
the framework dataset loader or write label caches into the frozen dataset.

Precision and Recall are macro averages over classes with ground-truth support at
the fixed operating threshold. All seven classes have support. AP uses confidence-ranked
detections and the 101-point interpolated PR-envelope trapezoid convention of
Ultralytics 8.4.157, closing the curve at achieved recall. Matching is recomputed for
each IoU threshold, with one prediction and one target per match.

The saved-prediction matching and all per-class AP values were independently checked
against the installed pinned BaseValidator.match_predictions and ap_per_class APIs.
The maximum absolute AP difference is 2.220446049250313e-16. This
does not claim byte-for-byte equivalence to a separate model.val run: prediction NMS
is single-label, and summary P/R use the fixed threshold rather than a test-selected
maximum-F1 threshold. Reference: [Ultralytics validation documentation](https://docs.ultralytics.com/modes/val/)
and the installed 8.4.157 source, whose matching/AP implementation was inspected.

## Overall metrics

| Scope | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| All seven training classes | 0.798669 | 0.712315 | 0.733203 | 0.465122 |
| Five locked PPE classes | 0.832058 | 0.721077 | 0.739567 | 0.454500 |

These are new test-split results. Phase 2 values were training-workflow validation
results on a different split, with a different P/R operating-point policy. They
must not be treated as a controlled before/after comparison.

## Per-class results

| ID | Class | GT | TP | FP | FN | Precision | Recall | AP50 | AP50-95 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | person | 174 | 130 | 46 | 44 | 0.738636 | 0.747126 | 0.791029 | 0.493147 |
| 1 | hardhat | 110 | 85 | 6 | 25 | 0.934066 | 0.772727 | 0.838850 | 0.522313 |
| 2 | no_hardhat | 41 | 25 | 5 | 16 | 0.833333 | 0.609756 | 0.547286 | 0.290488 |
| 3 | vest | 61 | 48 | 10 | 13 | 0.827586 | 0.786885 | 0.803755 | 0.524126 |
| 4 | no_vest | 90 | 62 | 13 | 28 | 0.826667 | 0.688889 | 0.716918 | 0.442427 |
| 5 | machinery | 44 | 35 | 12 | 9 | 0.744681 | 0.795455 | 0.819520 | 0.581197 |
| 6 | vehicle | 41 | 24 | 11 | 17 | 0.685714 | 0.585366 | 0.615062 | 0.402156 |

Classes 0-4 are the locked compliance surface; machinery and vehicle remain
scene-context classes and do not acquire PPE violation semantics. Per-class AP at
all ten IoUs is preserved in `docs/reports/EXP-001_EVALUATION_SUMMARY.json`.

## Confusion matrix

Rows are predicted classes; columns are true classes; background is last.
Correct-class matches are assigned first, then residual cross-class IoU matches
attribute classification errors. The background row contains missed targets; the
background column contains unmatched predictions. A cross-class confusion counts
as one FP for the predicted class and one FN for the true class.

| Predicted / True | person | hardhat | no_hardhat | vest | no_vest | machinery | vehicle | background |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| person | 130 | 0 | 0 | 0 | 1 | 0 | 0 | 45 |
| hardhat | 0 | 85 | 1 | 0 | 0 | 0 | 0 | 5 |
| no_hardhat | 0 | 1 | 25 | 0 | 0 | 0 | 0 | 4 |
| vest | 0 | 0 | 0 | 48 | 0 | 0 | 0 | 10 |
| no_vest | 0 | 0 | 0 | 1 | 62 | 0 | 0 | 12 |
| machinery | 0 | 0 | 0 | 0 | 0 | 35 | 0 | 12 |
| vehicle | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 11 |
| background | 44 | 24 | 15 | 12 | 27 | 9 | 17 | 0 |

The numerical matrix and rendered figure are retained as `confusion_matrix.json`
and `confusion_matrix.png` under the artifact root. The rendered figure was visually
checked for labels, axes, values and clipping.

## Error analysis

At the fixed operating point there are **409 true positives, 103 false positives
and 152 false negatives**. The four class confusions contribute four FP and four FN.

| Diagnostic category | Count | Interpretation |
| --- | ---: | --- |
| Missed ground truth | 148 | No retained correct/cross-class IoU >= 0.5 match |
| Class confusion | 4 | Matched location, wrong class |
| Background false positive | 23 | Maximum IoU with any GT below 0.1 |
| Localization candidate | 41 | Maximum IoU in [0.1, 0.5) |
| Duplicate or unmatched overlap | 35 | Residual prediction has IoU >= 0.5 with some GT |

These are geometric diagnostic categories, not manually proven causes or automatic
label corrections. A localization candidate may reflect a different object, missing
annotation or inaccurate localization; an unmatched overlap is not necessarily a
duplicate. Every diagnostic includes the image path, box/class/confidence and relevant
IoU in `error_analysis.json`. No image or annotation was changed.

Key observations:

- no_hardhat has the lowest AP50-95 (0.290488), with 16 FN among 41 GT.
- vehicle recall is 0.585366, with 17 FN among 41 GT.
- person contributes 46 FP and 44 FN, the largest absolute counts for both.
- The four class confusions are hardhat -> no_hardhat, no_hardhat -> hardhat,
  no_vest -> person, and vest -> no_vest (true -> predicted), one each.

| Object size | GT | TP | Recall |
| --- | ---: | ---: | ---: |
| small | 270 | 147 | 0.544444 |
| non_small | 291 | 262 | 0.900344 |

Small-object recall (0.544444) is materially below non-small recall (0.900344).
This is evidence of an association with box size, not proof of a single causal
failure mode. It is consistent with the retained P1D-1 small-object risk.

Highest-error images, ranked by FP + FN:

| Test image | GT | TP | FP | FN |
| --- | ---: | ---: | ---: | ---: |
| `test/images/Image36_jpg.rf.8704f3450f736cdd01a61dcee588f2c2.jpg` | 44 | 24 | 13 | 20 |
| `test/images/youtube-152_jpg.rf.9147878e3ddda845e58f7d9c041f1338.jpg` | 34 | 8 | 3 | 26 |
| `test/images/IMG_5846_jpg.rf.0b9984069116e2acd928568eb7a8e214.jpg` | 63 | 58 | 22 | 5 |
| `test/images/2008_008519_jpg.rf.1798c8eed7de04399a0e7e297b4b4c9e.jpg` | 13 | 2 | 6 | 11 |
| `test/images/ka_01181_png_jpg.rf.154ee4ef254eabd62e316be50470c578.jpg` | 17 | 2 | 0 | 15 |

## Runtime and reproducibility

| Field | Value |
| --- | --- |
| Environment | Isolated Windows CPU environment at `%LOCALAPPDATA%/ODPlatform-PPE/phase3-eval` |
| Python / Torch / torchvision | 3.10.4 / 2.5.1+cpu / 0.20.1 |
| Ultralytics / NumPy / OpenCV | 8.4.157 / 2.2.6 / 5.0.0.93 |
| Start UTC | 2026-09-22T13:18:17.912950+00:00 |
| Finish UTC | 2026-09-22T13:19:15.171953+00:00 |
| Recorded evaluation duration | 57.258607 seconds (excludes initial preflight) |
| Dependency pins | `locks/EVAL-001/requirements.txt` |
| PyPI torch wheel SHA256 | `32a037bd98a241df6c93e4c789b683335da76a2ac142c0973675b715102dc5fa` |

The training RTX 4090 runtime was not started or modified. This CPU runtime is
separately identified; no GPU speed comparison is claimed. No weight was downloaded.
The dependency-only torch wheel was acquired from official PyPI and SHA256-verified.

Execution from the repository root (already completed; output collisions are refused):

```powershell
& "$env:LOCALAPPDATA\ODPlatform-PPE\phase3-eval\Scripts\python.exe" -m scripts.evaluate --config configs/evaluation/exp001_test.yaml
```

Offline replay (no model execution and no PyTorch requirement):

```powershell
python -m scripts.evaluate --replay artifacts/reports/EXP-001-evaluation/EVAL-001
```

Replay verifies retained file hashes and recomputes metrics, confusion matrix and
errors from saved labels/predictions, requiring exact agreement with metrics.json.
Reproducing inference later requires a separately named empty evaluation output path;
the existing result directory is never overwritten.

## Artifacts and integrity

Artifact root: `artifacts/reports/EXP-001-evaluation/EVAL-001/` (Git-ignored).

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `confusion_matrix.json` | 1085 | `8f54dc25ff391144b5bccefc68c4bc206234bb39f5394db5a0f2726abdfc0b39` |
| `confusion_matrix.png` | 88451 | `5f99e6dcbe094dfc3c2222b6e91826eab91c21306b94e5dec1dec0940616887f` |
| `dataset_before.json` | 818040 | `9246d2110cabc9c5f7344050f7c88e6728d74677b51ce3fc6c90071102116cdf` |
| `error_analysis.json` | 109242 | `37a60603eb70262d3bba530a21bab758a7a72617b0e2b8eb13594a459ddf4811` |
| `metrics.json` | 115773 | `6a6f01502120afdf0102da2d7a63b76267a814f289275803bbfe3d969b4c2e2a` |
| `predictions.json` | 1661246 | `2636025df3a8e85ed534fe8eca54c700c4384da5d4983be9b9e9539dfe60ea57` |
| `run_record.json` | 5118 | `181c7500308bd5459e8f248cabbd3342003c449bd32cbb46f409a2552c52f45c` |

`predictions.json` includes all 82 image and label hashes, normalized GT and
post-NMS detections (including the low-confidence AP pool), and the fixed config.
`run_record.json` includes exact runtime package versions, source-code hashes,
input hashes, timing and the reference-check result.

The full 5,602-entry processed manifest passed before execution. All 5,604 processed
dataset files and their file set were compared before/after; unchanged. Checkpoint,
canonical training config, mapping/training contracts and Phase 2 model manifest
hashes were unchanged. Full task-entry source/processed/model/Phase 2 artifact
verification is recorded with final test results below.

## Validation and gate decision

- P3-G1: PASS — all four overall metrics retained and replayed.
- P3-G2: PASS — all five locked per-class AP entries in the required order; two context classes also retained.
- M-005 technical evidence: COMPLETE / AWAITING HUMAN REVIEW.
- P3-G3: NOT EXECUTED — no additional model/checkpoint comparison was requested or performed.
- P3-G4: PENDING COMPARATIVE REVIEW — best.pt remains the preselected EXP-001 validation winner; no claim of best deployment model.
- Phase 3 overall: IN PROGRESS, not released. No Phase 4 entry.

- `python -m pytest`: 205 passed, 1 skipped. The base Python environment lacks Torch;
  the optional official AP comparison was executed successfully in the isolated runtime.
- Isolated runtime evaluation tests: 21 passed, including the official AP comparison.
- `python -m compileall .`: PASS.
- `git diff --check`: PASS.
- Offline replay: PASS, exact agreement with the retained metrics.
- Task-entry SHA256 comparison of 11,450 existing files: only the eight intended
  existing Phase 3 source/test/documentation files changed. Dataset, mapping,
  checkpoints, frozen training config, Phase 2 release documents and Charter unchanged.
  Dataset/model/training-run file sets also remain identical.
- HEAD remains `9256a5b21743b5952bfc966da798a0b32129dbfe`; the old Phase 2 tag still
  resolves to `77d9dadcf9a613bfe2499e9251a6c66499437f96`, and the EXP-001 release tag
  still resolves to `2c8b6185f48911e8b8c390e238e033f403be7947`.
- Working tree intentionally contains the uncommitted Phase 3 implementation and
  documentation for human review; no commit or push.

## Limitations retained for human review

The frozen dataset has two previously recorded valid/test perceptual near-duplicate
candidate groups. This test split is separate from the training-validation procedure
but is not proven free of near-duplicate dependence; results may be optimistic.
No candidate image was removed or moved. The test set is only 82 images; class
support varies from 41 to 174 boxes. No production acceptance threshold was set,
so metric completeness does not establish operational safety or deployment readiness.

Teacher-model class semantics remain unverified; its historical metrics are not
presented as a controlled baseline. Future comparison must use the same test split
and postprocessing and an approved compatible mapping. Any future dataset remedy
requires a new reviewed dataset identity; no such work occurred here.
