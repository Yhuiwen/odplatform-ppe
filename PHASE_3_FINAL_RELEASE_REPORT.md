# Phase 3 Final Release Freeze Report

Date: 2026-09-22

Freeze status: **COMPLETED / AWAITING HUMAN REVIEW**

GitHub release status: **NOT_RELEASED**. Phase 4 development: **NOT_STARTED**.

## Freeze scope and completion

This report freezes the local Phase 3 evaluation, comparison and selection evidence for review. It is not a commit, tag, push, deployment or record of human approval. Existing EVAL-001, CMP-001 and SEL-001 artifacts remain unchanged. Earlier reports retain their historical gate states; the current closure summary is below.

| Gate | Completion | Evidence |
| --- | --- | --- |
| P3-G1 | PASS | EVAL-001 four overall metrics retained and replayable |
| P3-G2 | PASS | Five PPE per-class AP entries in frozen order; two context classes separately retained |
| P3-G3 | PASS | CMP-001 best/last checkpoint comparison with identical test data, protocol, code and runtime |
| P3-G4 | PASS | SEL-001 written selection of best.pt with PPE tradeoffs and limitations |

All four gates are technically complete. Human acceptance remains PENDING. P3-G3 is explicitly a same-training-run checkpoint comparison; it does not establish superiority over independently trained models or Teacher Baseline.

## M-005 status

**Technical implementation and evidence: COMPLETE. Formal human acceptance: PENDING.**
The four overall metrics and all five required PPE AP entries exist and can be recomputed from saved predictions. `docs/00_PROJECT_CHARTER.md` still records M-005 as `待实现`, and the master-plan formal Phase 3 status is retained pending review. This freeze does not silently change those formal acceptance fields. Human approval and the ensuing status synchronization remain explicit follow-up work.

## Final release model

| Field | Frozen value |
| --- | --- |
| Experiment / selection | EXP-001 / SEL-001 |
| Model | YOLO11n, Project-trained Model |
| Selected checkpoint | `models/checkpoints/EXP-001/best.pt` |
| SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Bytes / epoch | 5479891 / 75 (one-based) |
| Release-model record | `EXP-001_RELEASE_MODEL.yaml` |
| Alternative | last.pt, epoch 95, retained for reference |
| Alternative SHA256 | `acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88` |
| Dataset / mapping | CSS-PPE-10-V1 / PPE-MAPPING-V1 |
| Test split | 82 images / 561 GT boxes |
| Classes | person, hardhat, no_hardhat, vest, no_vest, machinery, vehicle |

best.pt retains the pre-test validation choice. Existing comparison evidence shows higher macro precision and no_hardhat recall, while last.pt has higher mAP, no_vest recall and small-object recall. SEL-001 accepts these documented tradeoffs without introducing new metric weights, thresholds or test tuning. No checkpoint was rewritten, copied or renamed.

| Selected-model test metric | Value |
| --- | ---: |
| Seven-class Precision | 0.798669 |
| Seven-class Recall | 0.712315 |
| Seven-class mAP50 | 0.733203 |
| Seven-class mAP50-95 | 0.465122 |
| no_hardhat Recall | 0.609756 |
| no_vest Recall | 0.688889 |
| Small-object Recall | 0.544444 |

P/R use fixed confidence 0.25 and matching IoU 0.5; AP uses confidence floor 0.001 and IoU 0.50:0.05:0.95. These evaluation settings are frozen evidence, not an approved production inference configuration.

## Artifact inventory and SHA256 references

Hashes below are SHA256 of the exact local file bytes at freeze, including line endings. This is a content freeze of the current uncommitted working tree. It must not be described as a new Git commit. Any later intentional revision requires a reviewed update to the affected hash references.

### Documents, configuration, implementation and tests

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `PHASE_3_EVALUATION_REPORT.md` | 14431 | `203078900e39d10cde114fd0ee1f064d0ba99b3cdf620683282ce1f39ec4a7b9` |
| `P3_MODEL_COMPARISON_REPORT.md` | 12031 | `e8e4f6f0f9cbab08868dc3d3072c4013bc89874e37e50a0fdab679b0a1f4d870` |
| `P3_MODEL_SELECTION_REPORT.md` | 8610 | `99e8ed4c7388923853d18e7c8808ae4f1d6d4a34bbffdf141867419c7c124f24` |
| `EXP-001_RELEASE_MODEL.yaml` | 3423 | `321703a6fecf316f65d05a675abb32cf4f3897f8a4b773e4e44eff467029c29b` |
| `docs/reports/EXP-001_EVALUATION_SUMMARY.json` | 8407 | `388103b5dcf2896bdf95a99bdd4b6091106be72d08ced21661c3a428e9feb7f7` |
| `docs/reports/P3_MODEL_COMPARISON_SUMMARY.json` | 15683 | `6926a1a2105836ff1abb170e7ef0cf753bfa9cda5e58188da417fff7827f3eb3` |
| `configs/evaluation/exp001_test.yaml` | 516 | `796bf9dc6515b7636c805947f72ba8f1a99e7d66493f4a4c7240fee6dca5cbc6` |
| `configs/evaluation/exp001_comparison.yaml` | 356 | `e8384764be1aa80d0819cea96c564d4d4d8990b2e1c809e4fa372c353fe021ca` |
| `locks/EVAL-001/requirements.txt` | 841 | `885474fd6124dd4e86139f3594ccdf651ef7dea4093c26c9e721606d3a5e7823` |
| `services/val_service.py` | 16907 | `ca747f2cc16d2ae077360b4f2934d08ec331a47850b9b3cbb777dfddab2c21ae` |
| `services/model_comparison_service.py` | 6390 | `21f84b0eec635af974e130be75c39bd2b4e748d3569fa3ef7ed14427487ab2bb` |
| `utils/evaluation_metrics.py` | 10050 | `3385470e2a570cd79529ce7142bff182f8d537e03b9e83c061e071c43bd91895` |
| `scripts/evaluate.py` | 904 | `b9cf754b370b372f837428758dd6a95d96d52017708b03d345567754145cd764` |
| `scripts/compare_models.py` | 814 | `5813caa2a58b776d3a96d0f76aa28320621e0d0afeae2be33461563c09279adf` |
| `tests/unit/test_evaluation.py` | 11413 | `a28ed9a304dacd4a5b627d1b1b172e001e117583750daa3f41b5e7bb5cf51f09` |
| `tests/unit/test_model_comparison.py` | 4523 | `7c8fbac9532fe32350db7d1142dd098e1e9b940019ac7adca253204e0d489fb7` |
| `tests/unit/test_placeholders.py` | 3220 | `e938b919c92675aed04f68f20f5f3a476a12f8ac5924f3ebe7bb86eda4901399` |
| `docs/02_CURRENT_STATUS.md` | 35377 | `3ef426fb0757a6a0f7d8f14760598aad14d853b1b0773239dbd7c94849c6046b` |
| `docs/04_CHANGELOG.md` | 32604 | `aafb82c630fa92fefda127e0a56118fd22478b5656c8b6e14a16f6f3e2729b00` |
| `docs/05_TEST_GATES.md` | 47388 | `4812b0ac93e7d3b831fe34e4279506d3a1fdcfc5634ad3df2514786cb93e6c5f` |
| `docs/07_OPEN_SOURCE_USAGE.md` | 3995 | `dd082ea013f38c520bd2ed9e366dbdd99d67761134e82538788d5dac33e1ff67` |
| `docs/phases/PHASE_03_EVALUATION.md` | 5752 | `abdab4b377091da66ee901e3d6db88beea72ec324ec626ab5f925a5b5ec8261d` |

This final report is the inventory carrier and does not contain its own recursive hash. Earlier evaluation source fingerprints identify the code used at their run time; CMP-001 records the current evaluator with frozen checkpoint selection added. Original EVAL-001 metrics exactly match CMP-001 best metrics.

### Retained runtime artifacts (Git-ignored)

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `artifacts/reports/EXP-001-evaluation/CMP-001/best/confusion_matrix.json` | 1085 | `8f54dc25ff391144b5bccefc68c4bc206234bb39f5394db5a0f2726abdfc0b39` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/best/confusion_matrix.png` | 88451 | `5f99e6dcbe094dfc3c2222b6e91826eab91c21306b94e5dec1dec0940616887f` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/best/dataset_before.json` | 818040 | `9246d2110cabc9c5f7344050f7c88e6728d74677b51ce3fc6c90071102116cdf` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/best/error_analysis.json` | 109242 | `37a60603eb70262d3bba530a21bab758a7a72617b0e2b8eb13594a459ddf4811` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/best/metrics.json` | 115773 | `6a6f01502120afdf0102da2d7a63b76267a814f289275803bbfe3d969b4c2e2a` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/best/predictions.json` | 1661286 | `047415d90fd7d2ee8af9bf5b803b399c4fe42e40ebf22b93cf844b2669164480` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/best/run_record.json` | 5162 | `83f8f0ea6256f0efea80704bfa2933482671e4facfbf43d8879605e181f1603f` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/comparison.json` | 15683 | `6926a1a2105836ff1abb170e7ef0cf753bfa9cda5e58188da417fff7827f3eb3` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/execution.log` | 18277 | `85e3729ac7c55f05b26b86c272b545048592205ddf47a425cfa7f6fa6a9a1f97` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/framework_settings.json` | 502 | `89ba196a0897793f4f969019706ecee550253b5e08b999b8168cdfe359ba8312` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/last/confusion_matrix.json` | 1085 | `9fef44eb77790ea41c3e80d9f29a72f3bebd4222ec00392fed57953c1641bf8a` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/last/confusion_matrix.png` | 90781 | `188faf7f045f81701c7fb56c4b08037a55626545ea4ca673a487d4253c5c688a` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/last/dataset_before.json` | 818040 | `9246d2110cabc9c5f7344050f7c88e6728d74677b51ce3fc6c90071102116cdf` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/last/error_analysis.json` | 110154 | `bbc01c3b2bcba934ae385080aed6f3425d479c592fd3e99fa7e1918b736d73d2` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/last/metrics.json` | 116665 | `43c174f31b5169df568e1560975d35628f9099aa44b76c09272d704de47b434f` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/last/predictions.json` | 1865872 | `82ea1575887dde1fb44ea5e425e382fac5fc76da16ffe14b128c2a66ac97dde7` |
| `artifacts/reports/EXP-001-evaluation/CMP-001/last/run_record.json` | 5317 | `84be1183c97385e42ec97c0ad086948b03fb4a740de958d9d41c783c1131b7aa` |
| `artifacts/reports/EXP-001-evaluation/EVAL-001/confusion_matrix.json` | 1085 | `8f54dc25ff391144b5bccefc68c4bc206234bb39f5394db5a0f2726abdfc0b39` |
| `artifacts/reports/EXP-001-evaluation/EVAL-001/confusion_matrix.png` | 88451 | `5f99e6dcbe094dfc3c2222b6e91826eab91c21306b94e5dec1dec0940616887f` |
| `artifacts/reports/EXP-001-evaluation/EVAL-001/dataset_before.json` | 818040 | `9246d2110cabc9c5f7344050f7c88e6728d74677b51ce3fc6c90071102116cdf` |
| `artifacts/reports/EXP-001-evaluation/EVAL-001/error_analysis.json` | 109242 | `37a60603eb70262d3bba530a21bab758a7a72617b0e2b8eb13594a459ddf4811` |
| `artifacts/reports/EXP-001-evaluation/EVAL-001/metrics.json` | 115773 | `6a6f01502120afdf0102da2d7a63b76267a814f289275803bbfe3d969b4c2e2a` |
| `artifacts/reports/EXP-001-evaluation/EVAL-001/predictions.json` | 1661246 | `2636025df3a8e85ed534fe8eca54c700c4384da5d4983be9b9e9539dfe60ea57` |
| `artifacts/reports/EXP-001-evaluation/EVAL-001/run_record.json` | 5118 | `181c7500308bd5459e8f248cabbd3342003c449bd32cbb46f409a2552c52f45c` |

Raw inventories include normalized predictions/GT, metrics, confusion matrices, error analysis, dataset-before hashes, run records and comparison logs. Their retention is necessary for offline replay; Git summaries alone do not contain the complete replay payload. No model binary, dataset payload or runtime output is added to Git.

### Protected upstream identity references

| Path | SHA256 |
| --- | --- |
| `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml` | `5f20a24869e1d481d0c05389cfe4541789c96a0caa0e2c282e8bb79ca3a66e0d` |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` |
| `docs/dataset_contracts/CSS-PPE-10-V1-MAPPING.yaml` | `7003f87af9cc8ad5ce7f8c58dffb25f43ab4bb533d0df1fba7033164a6ff40c7` |
| `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml` | `84b95b3bf15eb10730bb12fd22e582d4dba013c7fd8527acc1274e578bd15727` |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` |
| `data/processed/css-ppe-10-v1/metadata/checksums.sha256` | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |
| `data/processed/css-ppe-10-v1/metadata/class_mapping.json` | `e539bc831526f1532d12870053f827c0f0f37659de0d8964b6443ab9d505870d` |
| `data/external/css-v27-yolov8/metadata/checksums.sha256` | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |

No Phase 2 manifest, training configuration, dependency lock or training artifact was rewritten.

## Verification

- Current full suite: `python -m pytest` -> 213 passed, 1 skipped. The skip is the optional Torch reference test because base Python lacks Torch; the prior CMP-001 isolated-runtime run recorded 29 passing evaluation/comparison tests including that reference test.
- `python -m compileall .`: PASS.
- Existing EVAL-001 and CMP-001 offline replays: PASS; selected-model identity and every evidence hash in EXP-001_RELEASE_MODEL.yaml: PASS.
- Final inventory: all 54 artifact SHA256 rows and the recorded sizes verified against local files; PASS.
- Task-entry integrity: 11,488 existing files checked. Only the four intended current-phase governance documents changed; source/tests, dataset/mapping, weights, Phase 2 and existing Phase 3 evidence remain unchanged. Protected data/model/training/artifact file sets are identical.
- `git diff --check`: PASS. Charter, master plan, ADR, protected Phase 2 and Phase 4 document diffs are empty. No tracked `.pt`, `.pth` or `.onnx` file was found; model, dataset and runtime artifact ignore rules were verified.
- No training, new inference evaluation, test tuning, dataset/mapping/weight mutation or Phase 4 development occurred.

Offline verification commands (no model execution):

```powershell
python -m scripts.evaluate --replay artifacts/reports/EXP-001-evaluation/EVAL-001
python -m scripts.compare_models --replay artifacts/reports/EXP-001-evaluation/CMP-001
```

## Git state

- HEAD: `9256a5b21743b5952bfc966da798a0b32129dbfe`, unchanged.
- Existing `phase-2-training-complete` target: `77d9dadcf9a613bfe2499e9251a6c66499437f96`, preserved.
- Existing `phase-2-exp001-training-complete` target: `2c8b6185f48911e8b8c390e238e033f403be7947`, preserved.
- Working tree: intentionally uncommitted Phase 3 implementation and documentation, including this freeze report. Not CLEAN and not a published release.
- No new commit/tag/push or remote synchronization claim. Public milestone publication remains a separate, explicitly authorized action.

## Known limitations

- Only 82 test images; class imbalance and two recorded valid/test perceptual near-duplicate candidate groups remain. No dataset repair was performed.
- best/last are from one run. Teacher Baseline class semantics are unverified; no external-model superiority or statistical significance is established.
- Selected-model no_hardhat recall is 25/41, no_vest recall is 62/90 and small-object recall is 147/270. Misses remain material; no production quality threshold was established.
- Box metrics do not validate person-PPE association, temporal confirmation, event false-alarm rates or operational safety. Those requirements remain later-phase work.
- Selection is a qualitative review of already visible evidence that preserves the prior validation choice; it is not independent prospective validation.
- CPU evaluation duration is not a real-time Camera/RTSP benchmark. Inference, source failure handling and deployment runtime remain to be implemented and tested.

## Phase 4 entry conditions

| Condition | Current status |
| --- | --- |
| All Phase 3 technical gates PASS | SATISFIED, P3-G1 through P3-G4 |
| Human review of frozen evidence, model choice and limitations; synchronize formal acceptance status | PENDING |
| Selected model identity available and verifiable | SATISFIED, best.pt SHA256 above |
| Selected inference configuration confirmed, as required by PHASE_04_INFERENCE.md | PENDING; evaluation config is evidence only |
| Explicit user instruction to begin Phase 4 | NOT GRANTED in this freeze request |

Phase 4 remains NOT_STARTED. Its locked scope is image, video, Camera/RTSP inference (M-006 through M-008); future work must preserve real Camera/RTSP handling rather than replace it with local video. Confirming these entry conditions is future work, not authorization supplied by this report. GitHub release, if requested, follows the separate milestone publication procedure; no publication is performed here.

Final disposition: **Release evidence FROZEN; await human review.**
