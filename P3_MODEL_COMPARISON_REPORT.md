# P3-G3 Model Comparison Report

Date: 2026-09-22

Status: **P3-G3 PASS / AWAITING HUMAN REVIEW**

## Objects and scope

Comparison CMP-001 evaluates two existing, frozen Project-trained Model checkpoints from EXP-001:

| Candidate | Selection before this comparison | Checkpoint SHA256 |
| --- | --- | --- |
| best.pt | Validation-selected epoch 75 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| last.pt | Final epoch 95 | `acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88` |

Both are YOLO11n checkpoints from the same completed training run, each 5,479,891 bytes.
Their identities are registered in `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml`.
This is a controlled checkpoint comparison, not independent training runs, an architecture comparison, or external-model superiority evidence.

Teacher Baseline REF-002 is excluded: its `head` / `ordinary_clothes` semantics have not been verified as equivalent to `no_hardhat` / `no_vest`. Its historical metrics use an unverified evaluation split. The initialization-only COCO checkpoint also lacks the required PPE class space. No class substitution, model download or training was used to manufacture a comparator.

## Common evaluation protocol

Both checkpoints were evaluated afresh with the same `ValService.evaluate` and unchanged metric/prediction algorithms. The only new evaluator behavior is selection of best/last from the frozen inventory; no training artifact was modified. The original EVAL-001 output, report, summary and config are retained byte-for-byte.

| Condition | Shared value |
| --- | --- |
| Dataset / mapping | CSS-PPE-10-V1 / PPE-MAPPING-V1 |
| Test split | Same 82 images, 561 GT boxes; all image/label hashes and normalized GT compared |
| Full processed manifest SHA256 | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |
| Frozen base evaluation config SHA256 | `796bf9dc6515b7636c805947f72ba8f1a99e7d66493f4a4c7240fee6dca5cbc6` |
| Comparison config SHA256 | `e8384764be1aa80d0819cea96c564d4d4d8990b2e1c809e4fa372c353fe021ca` |
| Class order | person, hardhat, no_hardhat, vest, no_vest, machinery, vehicle |
| Input / batch / device | 640, batch 1, CPU, FP32, rectangular padding disabled |
| Runtime | Python 3.10.4, Torch 2.5.1+cpu, Ultralytics 8.4.157; same complete package fingerprint |
| Seed / threads | 42 / 4; deterministic Torch algorithms |
| Postprocessing | Single-label, class-aware NMS IoU 0.7; max_det 300; no TTA |
| Precision / Recall | Macro over supported classes; confidence >= 0.25, match IoU >= 0.5 |
| AP | Confidence floor 0.001; IoU 0.50:0.05:0.95; 101-point PR-envelope trapezoid |
| Small-object recall | GT normalized area < 0.01; micro TP/GT across all seven classes |

Protocol, test records, full dataset hashes, evaluation source hashes, Python/platform and runtime package fingerprints are equal across both runs. The comparison rejects mismatches rather than presenting incomparable scores. Thresholds and candidates were fixed before inference; there was no test-set tuning.

## Unified results

All differences below are last minus best; values are proportions, not percentages.

| Metric (seven classes) | best.pt | last.pt | Difference |
| --- | ---: | ---: | ---: |
| precision | 0.798669 | 0.781081 | -0.017588 |
| recall | 0.712315 | 0.716522 | +0.004207 |
| mAP50 | 0.733203 | 0.744729 | +0.011526 |
| mAP50-95 | 0.465122 | 0.472776 | +0.007654 |
| no_hardhat_recall | 0.609756 | 0.585366 | -0.024390 |
| no_vest_recall | 0.688889 | 0.700000 | +0.011111 |
| small-object recall | 0.544444 | 0.555556 | +0.011111 |

| Five PPE classes only | best.pt | last.pt |
| --- | ---: | ---: |
| precision | 0.832058 | 0.822707 |
| recall | 0.721077 | 0.726966 |
| mAP50 | 0.739567 | 0.749834 |
| mAP50-95 | 0.454500 | 0.460923 |

## Per-class AP and recall

| Class | GT | Best AP50 | Last AP50 | Best AP50-95 | Last AP50-95 | Best recall | Last recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| person | 174 | 0.791029 | 0.806564 | 0.493147 | 0.505887 | 0.747126 | 0.764368 |
| hardhat | 110 | 0.838850 | 0.852429 | 0.522313 | 0.528459 | 0.772727 | 0.781818 |
| no_hardhat | 41 | 0.547286 | 0.539634 | 0.290488 | 0.302780 | 0.609756 | 0.585366 |
| vest | 61 | 0.803755 | 0.812619 | 0.524126 | 0.537468 | 0.786885 | 0.803279 |
| no_vest | 90 | 0.716918 | 0.737922 | 0.442427 | 0.430021 | 0.688889 | 0.700000 |
| machinery | 44 | 0.819520 | 0.836854 | 0.581197 | 0.587666 | 0.795455 | 0.795455 |
| vehicle | 41 | 0.615062 | 0.627080 | 0.402156 | 0.417149 | 0.585366 | 0.585366 |

The first five rows are the locked PPE surface. The remaining two are scene-context classes. AP at all ten IoU thresholds and TP/FP/FN counts are in `docs/reports/P3_MODEL_COMPARISON_SUMMARY.json`.

| Recall detail | Ground truth | Best TP | Last TP |
| --- | ---: | ---: | ---: |
| no_hardhat | 41 | 25 | 24 |
| no_vest | 90 | 62 | 63 |
| small objects | 270 | 147 | 150 |
| non-small objects | 291 | 262 | 264 |

## Evidence-based interpretation

- last.pt increases seven-class mAP50 by 0.011526 and mAP50-95 by 0.007654 (1.153 and 0.765 percentage points respectively). Overall macro recall rises by 0.004207, while precision falls by 0.017588.
- no_hardhat recall decreases by one detected GT (25/41 to 24/41). Its AP50 falls while AP50-95 rises; the AP curve and fixed operating point measure different behavior.
- no_vest recall increases by one detected GT (62/90 to 63/90), while its AP50-95 falls from 0.442427 to 0.430021. Small-object recall improves by three GT detections (147/270 to 150/270).
- The checkpoints differ in learned state after twenty additional training epochs within the already completed run. Aggregate counts alone cannot prove which training mechanism caused a change. The mixed class/threshold results do not establish a uniformly better checkpoint.
- Test-set ordering differs from the original validation-based best selection. This does not invalidate that selection, and this task does not replace best.pt, rename weights, or select a deployment model using the test set.

Both runs retain prediction-level evidence, error analysis and confusion matrices. best.pt metrics match EVAL-001 exactly. Official matching agrees for both candidates; maximum AP absolute error versus pinned Ultralytics is 2.220446049250313e-16. Both runs and the comparison replay successfully without model execution.

## Runtime and artifact inventory

Runs use the existing isolated CPU environment and dependency pins in `locks/EVAL-001/requirements.txt`. No cloud instance or dependency change was needed. Durations include evaluation bookkeeping, plotting and integrity verification; they are not latency benchmarks. The sequential runs have different warm-up/cache conditions, so speed ranking is not claimed.

| Candidate | Start UTC | Finish UTC | Recorded seconds |
| --- | --- | --- | ---: |
| best | 2026-09-22T13:35:04.060313+00:00 | 2026-09-22T13:35:48.539678+00:00 | 44.478895 |
| last | 2026-09-22T13:36:09.973991+00:00 | 2026-09-22T13:36:39.495109+00:00 | 29.520958 |

Raw artifact root: `artifacts/reports/EXP-001-evaluation/CMP-001/` (Git-ignored).

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `best/confusion_matrix.json` | 1085 | `8f54dc25ff391144b5bccefc68c4bc206234bb39f5394db5a0f2726abdfc0b39` |
| `best/confusion_matrix.png` | 88451 | `5f99e6dcbe094dfc3c2222b6e91826eab91c21306b94e5dec1dec0940616887f` |
| `best/dataset_before.json` | 818040 | `9246d2110cabc9c5f7344050f7c88e6728d74677b51ce3fc6c90071102116cdf` |
| `best/error_analysis.json` | 109242 | `37a60603eb70262d3bba530a21bab758a7a72617b0e2b8eb13594a459ddf4811` |
| `best/metrics.json` | 115773 | `6a6f01502120afdf0102da2d7a63b76267a814f289275803bbfe3d969b4c2e2a` |
| `best/predictions.json` | 1661286 | `047415d90fd7d2ee8af9bf5b803b399c4fe42e40ebf22b93cf844b2669164480` |
| `best/run_record.json` | 5162 | `83f8f0ea6256f0efea80704bfa2933482671e4facfbf43d8879605e181f1603f` |
| `comparison.json` | 15683 | `6926a1a2105836ff1abb170e7ef0cf753bfa9cda5e58188da417fff7827f3eb3` |
| `execution.log` | 18277 | `85e3729ac7c55f05b26b86c272b545048592205ddf47a425cfa7f6fa6a9a1f97` |
| `framework_settings.json` | 502 | `89ba196a0897793f4f969019706ecee550253b5e08b999b8168cdfe359ba8312` |
| `last/confusion_matrix.json` | 1085 | `9fef44eb77790ea41c3e80d9f29a72f3bebd4222ec00392fed57953c1641bf8a` |
| `last/confusion_matrix.png` | 90781 | `188faf7f045f81701c7fb56c4b08037a55626545ea4ca673a487d4253c5c688a` |
| `last/dataset_before.json` | 818040 | `9246d2110cabc9c5f7344050f7c88e6728d74677b51ce3fc6c90071102116cdf` |
| `last/error_analysis.json` | 110154 | `bbc01c3b2bcba934ae385080aed6f3425d479c592fd3e99fa7e1918b736d73d2` |
| `last/metrics.json` | 116665 | `43c174f31b5169df568e1560975d35628f9099aa44b76c09272d704de47b434f` |
| `last/predictions.json` | 1865872 | `82ea1575887dde1fb44ea5e425e382fac5fc76da16ffe14b128c2a66ac97dde7` |
| `last/run_record.json` | 5317 | `84be1183c97385e42ec97c0ad086948b03fb4a740de958d9d41c783c1131b7aa` |

The framework emitted a settings-directory fallback warning; its generated settings were retained as `framework_settings.json` under the ignored comparison root. No settings file remains as a source-tree change. Deprecation warnings for the explicit FP32 `half=False` argument are retained in `execution.log`.

Execution (already completed; existing output directories are rejected):

```powershell
& "$env:LOCALAPPDATA\ODPlatform-PPE\phase3-eval\Scripts\python.exe" -m scripts.compare_models --config configs/evaluation/exp001_comparison.yaml
```

Offline replay (no model load, no training):

```powershell
python -m scripts.compare_models --replay artifacts/reports/EXP-001-evaluation/CMP-001
```

## Tests, integrity and gate decision

- Full suite: `python -m pytest` -> 213 passed, 1 skipped (base Python has no Torch).
- Isolated runtime: evaluation/comparison tests -> 29 passed, including the official AP reference test.
- Tests reject differing protocol/image hashes/runtime/source, identical checkpoint hashes, unregistered checkpoint selection, modified checkpoint bytes, and altered retained comparison results.
- `python -m compileall .`: PASS. Offline comparison replay: PASS.
- `git diff --check`: PASS. Charter, master plan, ADRs and protected Phase 2 paths have no Git diff.
- Task-entry SHA256 audit: 11,463 existing files checked; exactly six authorized existing files changed (evaluation service/test and the four current-phase governance documents). Dataset, mapping, weights, training config/locks, Phase 2 artifacts and original EVAL-001 files are byte-for-byte unchanged. Dataset/model/training-run/original-evaluation file sets are unchanged as well.
- The retained comparison source fingerprints match the evaluated code; the report JSON summary equals the raw comparison result.
- HEAD remains `9256a5b21743b5952bfc966da798a0b32129dbfe`. Old tag `phase-2-training-complete` still resolves to `77d9dadcf9a613bfe2499e9251a6c66499437f96`; `phase-2-exp001-training-complete` still resolves to `2c8b6185f48911e8b8c390e238e033f403be7947`.
- P3-G3: PASS for this explicitly scoped best-versus-last controlled comparison; human review PENDING.
- P3-G4: PENDING. No final comparative model selection, Phase 3 release or Phase 4 entry.
- No commit/push. Changes remain local for review.

## Limitations

The 82-image test split retains two recorded valid/test perceptual near-duplicate candidate groups and class imbalance. Both checkpoints share the same training data/history and are not independent replicates. Small-object recall remains about 0.55. No statistical significance, production acceptance threshold or deployment readiness is claimed. Teacher Baseline and other architectures were not evaluated. A future independently validated selection requires explicit scope and review; no dataset repair or additional training was performed here.
