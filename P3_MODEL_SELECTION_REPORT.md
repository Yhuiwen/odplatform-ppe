# P3-G4 Final Comparative Model Selection

Date: 2026-09-22

Selection ID: SEL-001

Decision: **SELECT EXP-001 best.pt (epoch 75)**.

Record status: COMPLETED / AWAITING HUMAN REVIEW. The selection decision is
recorded; human approval and Phase 3 publication have not occurred.

## Candidate summary

Both candidates are immutable YOLO11n Project-trained Model checkpoints from
the same completed EXP-001 training run. Neither is an independent training
replicate. Both use the frozen seven-class PPE-MAPPING-V1 order.

| Candidate | Original role | SHA256 | Disposition |
| --- | --- | --- | --- |
| best.pt, epoch 75 | Selected by the completed training validation procedure | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | SELECTED |
| last.pt, epoch 95 | Final checkpoint after early stopping | `acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88` | Retained for reference; not selected |

Each file is 5,479,891 bytes. The existing Phase 2 manifest
`docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml` records both identities.
No checkpoint was copied, renamed, rewritten or deleted.

## Evaluation evidence

This decision uses only the existing EVAL-001 and CMP-001 evidence:

- `PHASE_3_EVALUATION_REPORT.md`: original best.pt evaluation and error analysis.
- `P3_MODEL_COMPARISON_REPORT.md`: best-versus-last controlled comparison.
- `docs/reports/P3_MODEL_COMPARISON_SUMMARY.json`: exact per-class metrics,
  recall counts, candidate hashes and replay evidence.
- `EXP-001_RELEASE_MODEL.yaml`: selected artifact and SHA256-bound evidence references.

CMP-001 used the same 82 CSS-PPE-10-V1 test images and 561 ground-truth boxes,
image/label hashes, evaluator implementation, runtime and parameters for both
candidates. Precision/Recall use confidence 0.25 and matching IoU 0.5; AP uses
confidence floor 0.001 and IoU 0.50:0.05:0.95. Small objects have normalized GT
area below 0.01. No thresholds, class mappings or scoring formulas changed here.

| Existing metric | best.pt | last.pt |
| --- | ---: | ---: |
| Seven-class Precision | 0.798669 | 0.781081 |
| Seven-class Recall | 0.712315 | 0.716522 |
| Seven-class mAP50 | 0.733203 | 0.744729 |
| Seven-class mAP50-95 | 0.465122 | 0.472776 |
| Five-PPE-class Precision | 0.832058 | 0.822707 |
| Five-PPE-class Recall | 0.721077 | 0.726966 |
| Five-PPE-class mAP50 | 0.739567 | 0.749834 |
| Five-PPE-class mAP50-95 | 0.454500 | 0.460923 |
| no_hardhat Recall | 0.609756 (25/41) | 0.585366 (24/41) |
| no_vest Recall | 0.688889 (62/90) | 0.700000 (63/90) |
| Small-object Recall, all seven classes | 0.544444 (147/270) | 0.555556 (150/270) |

| PPE class | Best AP50 | Last AP50 | Best AP50-95 | Last AP50-95 |
| --- | ---: | ---: | ---: | ---: |
| person | 0.791029 | 0.806564 | 0.493147 | 0.505887 |
| hardhat | 0.838850 | 0.852429 | 0.522313 | 0.528459 |
| no_hardhat | 0.547286 | 0.539634 | 0.290488 | 0.302780 |
| vest | 0.803755 | 0.812619 | 0.524126 | 0.537468 |
| no_vest | 0.716918 | 0.737922 | 0.442427 | 0.430021 |

All ten IoU AP values and the two scene-context classes remain available in
the comparison summary. Context classes do not acquire PPE violation semantics.

## PPE compliance oriented criteria

The Charter requires both helmet and vest compliance, person-PPE association,
and temporal confirmation. The following is a qualitative engineering review
of existing evidence, documented after CMP-001. It is not a claim that new
criteria were preregistered before seeing test results, and it introduces no
numeric score, metric weights or new pass/fail thresholds.

| Criterion | Interpretation and consequence |
| --- | --- |
| Preserve reproducible validation selection | Retain the pre-test validation-selected best.pt unless the available evidence justifies replacement. Do not switch simply to maximize observed test mAP. |
| Inspect both violation-class recalls | best detects one more no_hardhat GT; last detects one more no_vest GT. Neither dominates both tasks. The project has no approved cost ratio assigning one violation class greater severity. |
| Inspect precision and false detections | best has higher overall and five-PPE macro precision. This supports retaining it as a detector baseline, but these averages do not measure violation-event false-alarm rates. |
| Preserve per-class localization evidence | last has higher overall AP and no_hardhat AP50-95; best has higher no_vest AP50-95. Do not hide this mixed result behind one aggregate score. |
| Account for small objects | last detects three more small GT boxes. Both retain substantial small-object misses; neither meets an established production recall threshold because none exists. |
| Traceability and compatibility | Both satisfy existing hash, class-order and same-protocol checks. No additional model download, remapping or training is needed for best. |

## Final selection decision

Select `models/checkpoints/EXP-001/best.pt` as the recorded EXP-001 release-model
choice and the intended integration baseline after human review. Retain last.pt
as a reference candidate. The manifest is a selection record, not deployment
configuration or authorization to begin Phase 4.

The primary basis is continuity with the validation-selected checkpoint. The
existing comparison shows mixed tradeoffs rather than a clear reason to replace
it: best retains higher no_hardhat recall and macro precision, while last improves
aggregate AP, no_vest recall and small-object recall. This decision accepts those
documented costs without claiming best is superior on every metric or safer in
operation. The one-box differences are not evidence of statistical significance.

The test results are disclosed as comparative evidence, not reused for parameter
search or checkpoint optimization. There was no new inference, threshold sweep,
metric optimization, synthetic metric generation or training in this task.
Offline replay only verifies the already retained results.

## Limitations

- The test set contains only 82 images and retains two valid/test perceptual
  near-duplicate candidate groups and class imbalance. Generalization may be
  optimistic; no new independent holdout was evaluated.
- Both candidates share training data and history. Teacher Baseline semantics
  remain unverified, so there is no external-model or architecture comparison.
- Selected best.pt misses 16/41 no_hardhat GT and 28/90 no_vest GT at the fixed
  operating point. It detects only 147/270 small GT boxes. Selection does not
  establish acceptable production safety performance.
- Box-level detection precision/recall cannot establish person-PPE association,
  temporal confirmation or event false-alarm performance. M-010 through M-014
  remain future implementation/acceptance work.
- No production acceptance threshold, statistical significance or speed advantage
  is claimed. Comparison durations include warm-up and bookkeeping.
- Test results were already visible when this written review was formed. Keeping
  the prior validation choice avoids a test-mAP-driven replacement, but does not
  turn this review into an independent prospective validation.

## Verification and gate decision

- `python -m pytest`: **213 passed, 1 skipped**. The optional Torch reference test
  is skipped in base Python because Torch is absent; it passed in the existing
  CMP-001 isolated-runtime verification. No model evaluation was rerun here.
- `python -m compileall .`: PASS; `git diff --check`: PASS.
- Existing CMP-001 offline replay: PASS. Retained summary equals raw comparison.
- Selection YAML schema fields, candidate path/size/epoch/hash, frozen class order,
  evidence hashes and pending-review boundary: PASS.
- Task-entry SHA256 audit: **11,486 existing files** checked. Only the four intended
  current-phase governance documents changed. Source code, tests, dataset, mapping,
  EXP-001 weights/config, Phase 2 artifacts, EVAL-001 and CMP-001 remain unchanged.
  Dataset/model/training/artifact file sets are unchanged.
- Charter, master plan, ADR and protected Phase 2 Git diffs are empty.
  HEAD remains `9256a5b21743b5952bfc966da798a0b32129dbfe`; both Phase 2 tags retain
  their prior targets. No commit, tag creation or push occurred.
- **P3-G4: PASS** for the completed written selection and limitation record.
  P3-G1 through P3-G4 technical evidence is complete; human acceptance is pending.

P3-G4 technical completion requires the written choice, immutable artifact
identity, evidence and limitations above. Human review remains PENDING; Phase 3
is not published, and no Phase 4 work, commit or push is authorized by this record.
