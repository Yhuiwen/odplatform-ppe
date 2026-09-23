# Phase C-1 Batch-2 Migration Audit

Date: 2026-09-23
HEAD: `ce937bf88d4a06fcc65c8121b0a62aca8a3bde6a`
Status: analysis only; no migration, commit or push.

## Scope

- Phase 4 Offline Inference is COMPLETE; Phase 5 remains WAITING. Batch-1 is committed and its ten report moves are excluded here.
- Working tree was clean at entry. `AGENTS.md`, `docs/README.md`, and the Batch-1 report were read. `docs/reports/maintenance/DOCUMENT_GOVERNANCE_PHASE_C_AUDIT_REPORT.md` could not be read because it was explicitly deleted before Batch-1 and never committed; this inventory was rebuilt from current tracked files.
- Selection: unarchived tracked Markdown basenames beginning `PHASE_2_`, `P2-`, `PHASE_3_`, or `P3-`; names containing dataset, quality, training manifest, EXP-001, weights, model, or contract are excluded.
- This scan found 22 candidates: 9 HIGH, 13 MEDIUM, 0 LOW. Five MEDIUM files are designs/plans and belong under `docs/designs/phase-02/` only in a separately approved design migration.

## Candidate Inventory

| File | Phase | Type | Suggested Target | Risk |
| --- | --- | --- | --- | --- |
| `P2-5.1_CONFIGURATION_FREEZE_REPORT.md` | 02 | report/audit | `docs/reports/phase-02/P2-5.1_CONFIGURATION_FREEZE_REPORT.md` | HIGH |
| `P2-5.2_WEIGHT_REGISTRATION_REPORT.md` | 02 | report/audit | `docs/reports/phase-02/P2-5.2_WEIGHT_REGISTRATION_REPORT.md` | HIGH |
| `P2-5.3_DEPENDENCY_FREEZE_REPORT.md` | 02 | report/audit | `docs/reports/phase-02/P2-5.3_DEPENDENCY_FREEZE_REPORT.md` | HIGH |
| `P2-5_TRAINING_AUTHORIZATION_REPORT.md` | 02 | report/audit | `docs/reports/phase-02/P2-5_TRAINING_AUTHORIZATION_REPORT.md` | MEDIUM |
| `PHASE_3_EVALUATION_REPORT.md` | 03 | report/audit | `docs/reports/phase-03/PHASE_3_EVALUATION_REPORT.md` | HIGH |
| `docs/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` | 02 | report/audit | `docs/reports/phase-02/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` | MEDIUM |
| `docs/P2-4_FINAL_PROVISIONING_REPORT.md` | 02 | report/audit | `docs/reports/phase-02/P2-4_FINAL_PROVISIONING_REPORT.md` | MEDIUM |
| `docs/reports/P2-0_DEPENDENCY_STRATEGY.md` | 02 | design/planning | `docs/designs/phase-02/P2-0_DEPENDENCY_STRATEGY.md` | MEDIUM |
| `docs/reports/P2-0_TRAINING_READINESS.md` | 02 | report/audit | `docs/reports/phase-02/P2-0_TRAINING_READINESS.md` | MEDIUM |
| `docs/reports/P2-0_VERSION_MATRIX.md` | 02 | design/planning | `docs/designs/phase-02/P2-0_VERSION_MATRIX.md` | MEDIUM |
| `docs/reports/P2-1_DEPENDENCY_SPECIFICATION.md` | 02 | design/planning | `docs/designs/phase-02/P2-1_DEPENDENCY_SPECIFICATION.md` | MEDIUM |
| `docs/reports/P2-1_ENVIRONMENT_DECISION.md` | 02 | design/planning | `docs/designs/phase-02/P2-1_ENVIRONMENT_DECISION.md` | MEDIUM |
| `docs/reports/P2-1_SETUP_PLAN.md` | 02 | design/planning | `docs/designs/phase-02/P2-1_SETUP_PLAN.md` | MEDIUM |
| `docs/reports/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` | 02 | report/audit | `docs/reports/phase-02/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` | MEDIUM |
| `docs/reports/P2-2_DEPENDENCY_FREEZE.md` | 02 | report/audit | `docs/reports/phase-02/P2-2_DEPENDENCY_FREEZE.md` | MEDIUM |
| `docs/reports/P2-2_EXP001_EXECUTION_REVIEW.md` | 02 | report/audit | `docs/reports/phase-02/P2-2_EXP001_EXECUTION_REVIEW.md` | MEDIUM |
| `docs/reports/P2-2_TRAINING_AUTHORIZATION.md` | 02 | report/audit | `docs/reports/phase-02/P2-2_TRAINING_AUTHORIZATION.md` | HIGH |
| `docs/reports/P2-3_CLOUD_PROVIDER_SELECTION.md` | 02 | report/audit | `docs/reports/phase-02/P2-3_CLOUD_PROVIDER_SELECTION.md` | HIGH |
| `docs/reports/P2-5.1_CONFIGURATION_FREEZE.md` | 02 | report/audit | `docs/reports/phase-02/P2-5.1_CONFIGURATION_FREEZE.md` | HIGH |
| `docs/reports/P2-5.3_DEPENDENCY_FREEZE.md` | 02 | report/audit | `docs/reports/phase-02/P2-5.3_DEPENDENCY_FREEZE.md` | HIGH |
| `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | 02 | report/audit | `docs/reports/phase-02/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | HIGH |
| `docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md` | 02 | report/audit | `docs/reports/phase-02/P2-7_TRAINING_RESULT_FREEZE_REPORT.md` | MEDIUM |

## Reference Impact

References were searched in tracked `*.md`, `*.py`, `*.yaml`, `*.yml`, `*.json`, and `*.toml`. Every candidate has at least one textual reference. Markdown references include links, inline-code paths and prose mentions; each must be classified before migration because historical prose may be intentionally preserved.

| File | Referenced By (examples) | Reference Type | Migration Impact | Risk |
| --- | --- | --- | --- | --- |
| `P2-5.1_CONFIGURATION_FREEZE_REPORT.md` | `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml:306`, `tests/unit/test_training_preparation.py:30`, `README.md:251`, `docs/04_CHANGELOG.md:375` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `P2-5.2_WEIGHT_REGISTRATION_REPORT.md` | `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml:307`, `tests/unit/test_training_preparation.py:37`, `docs/04_CHANGELOG.md:398`, `docs/phases/PHASE_02_TRAINING.md:336` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `P2-5.3_DEPENDENCY_FREEZE_REPORT.md` | `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml:308`, `tests/unit/test_training_preparation.py:51`, `README.md:253`, `docs/04_CHANGELOG.md:422` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `P2-5_TRAINING_AUTHORIZATION_REPORT.md` | `docs/04_CHANGELOG.md:364`, `docs/05_TEST_GATES.md:343` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `PHASE_3_EVALUATION_REPORT.md` | `EXP-001_RELEASE_MODEL.yaml:53`, `P3_MODEL_SELECTION_REPORT.md:31`, `docs/04_CHANGELOG.md:765` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `docs/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` | `docs/04_CHANGELOG.md:322`, `docs/05_TEST_GATES.md:296` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/P2-4_FINAL_PROVISIONING_REPORT.md` | `P2-5_TRAINING_AUTHORIZATION_REPORT.md:43`, `README.md:247` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-0_DEPENDENCY_STRATEGY.md` | `docs/04_CHANGELOG.md:229`, `docs/05_TEST_GATES.md:237` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-0_TRAINING_READINESS.md` | `docs/04_CHANGELOG.md:234`, `docs/05_TEST_GATES.md:236` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-0_VERSION_MATRIX.md` | `docs/04_CHANGELOG.md:231`, `docs/05_TEST_GATES.md:238` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-1_DEPENDENCY_SPECIFICATION.md` | `docs/04_CHANGELOG.md:257`, `docs/05_TEST_GATES.md:251` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-1_ENVIRONMENT_DECISION.md` | `docs/04_CHANGELOG.md:255`, `docs/05_TEST_GATES.md:250` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-1_SETUP_PLAN.md` | `docs/04_CHANGELOG.md:261`, `docs/05_TEST_GATES.md:252` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` | `docs/04_CHANGELOG.md:273`, `docs/05_TEST_GATES.md:265` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-2_DEPENDENCY_FREEZE.md` | `P2-5_TRAINING_AUTHORIZATION_REPORT.md:42`, `docs/04_CHANGELOG.md:276` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-2_EXP001_EXECUTION_REVIEW.md` | `P2-5_TRAINING_AUTHORIZATION_REPORT.md:40`, `docs/04_CHANGELOG.md:279` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |
| `docs/reports/P2-2_TRAINING_AUTHORIZATION.md` | `tests/unit/test_training_preparation.py:54`, `tests/unit/test_training_preparation.py:483`, `P2-5.3_DEPENDENCY_FREEZE_REPORT.md:64`, `P2-5_TRAINING_AUTHORIZATION_REPORT.md:41` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `docs/reports/P2-3_CLOUD_PROVIDER_SELECTION.md` | `tests/unit/test_training_preparation.py:482`, `docs/04_CHANGELOG.md:292`, `docs/05_TEST_GATES.md:280` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `docs/reports/P2-5.1_CONFIGURATION_FREEZE.md` | `tests/unit/test_training_preparation.py:28`, `P2-5.1_CONFIGURATION_FREEZE_REPORT.md:78`, `README.md:250` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `docs/reports/P2-5.3_DEPENDENCY_FREEZE.md` | `tests/unit/test_training_preparation.py:49`, `README.md:252`, `docs/04_CHANGELOG.md:421` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml:305`, `docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md:16`, `docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md:25` | test/config path + Markdown | update code/config path references and affected tests; preserve dated report prose | HIGH |
| `docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md` | `docs/phases/PHASE_02_TRAINING.md:369`, `docs/reports/phase-02/PHASE_2_FINAL_RELEASE_REPORT.md:103` | Markdown path/prose | update navigational Markdown references; preserve dated report prose | MEDIUM |

Specific cross-cutting references: `README.md`, `docs/04_CHANGELOG.md`, `docs/05_TEST_GATES.md`, `docs/phases/PHASE_02_TRAINING.md`, and `docs/phases/PHASE_03_EVALUATION.md` cite several candidates. `tests/unit/test_training_preparation.py` hard-codes multiple P2 paths; `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml` and `EXP-001_RELEASE_MODEL.yaml` cite additional reports. No candidate was referenced by a runtime script in this scan.

## Risk Assessment

- **HIGH (9):** fixed paths occur in a test or configuration/manifest. Movement must be paired with explicitly authorized path-only updates and relevant tests. Frozen manifest semantics and any embedded hash statements need review before editing.
- **MEDIUM (13):** Markdown references need navigation updates. Five are design/planning files outside the requested report-directory migration.
- **LOW (0):** no unreferenced candidate was found. Historical references in existing reports may remain literal dated records; active links and current indexes must point to the new location.

## Historical Integrity

SHA256 values below are calculated from current working-tree bytes. A later migration should record the original and destination Git blob IDs as well as byte hashes, allowing for Git line-ending normalization; report body content must remain unchanged.

| Current Path | SHA256 | Target Path |
| --- | --- | --- |
| `P2-5.1_CONFIGURATION_FREEZE_REPORT.md` | `528e8a7851a8a90ef4e76bfe0b59a6823a72d9c117d8181641b62043cd77e294` | `docs/reports/phase-02/P2-5.1_CONFIGURATION_FREEZE_REPORT.md` |
| `P2-5.2_WEIGHT_REGISTRATION_REPORT.md` | `31c848dbb4a852265dd562e4b7b35533d77264b0be2faf04cf9a4d4ee2f892c1` | `docs/reports/phase-02/P2-5.2_WEIGHT_REGISTRATION_REPORT.md` |
| `P2-5.3_DEPENDENCY_FREEZE_REPORT.md` | `330a0ac36a0951bbe09b9fc3dd99a19051ce0dffc07eb867c6a1e866b97af35f` | `docs/reports/phase-02/P2-5.3_DEPENDENCY_FREEZE_REPORT.md` |
| `P2-5_TRAINING_AUTHORIZATION_REPORT.md` | `f129fb3d21df788c52c99ba7afdd6c2f26b1c24cffc2ac6faeaa08f6f5c3a3a5` | `docs/reports/phase-02/P2-5_TRAINING_AUTHORIZATION_REPORT.md` |
| `PHASE_3_EVALUATION_REPORT.md` | `203078900e39d10cde114fd0ee1f064d0ba99b3cdf620683282ce1f39ec4a7b9` | `docs/reports/phase-03/PHASE_3_EVALUATION_REPORT.md` |
| `docs/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` | `87ffe170775dd3750daccad541b8cb324bd71e851933c95e8088dca3a4e74779` | `docs/reports/phase-02/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` |
| `docs/P2-4_FINAL_PROVISIONING_REPORT.md` | `1c5fd5d7308d0a70190924dbe147d7ce2e155a56c49de0a86892544dcd403c9e` | `docs/reports/phase-02/P2-4_FINAL_PROVISIONING_REPORT.md` |
| `docs/reports/P2-0_DEPENDENCY_STRATEGY.md` | `eed6eaa2a8680df663c41c01de74569cbdaf398c2755be7e28cd4b1aa22d43d2` | `docs/designs/phase-02/P2-0_DEPENDENCY_STRATEGY.md` |
| `docs/reports/P2-0_TRAINING_READINESS.md` | `8a00271a489b5286c7e4abcf12f43d9a2432d843a130dd0c53cb2dbf83cccf88` | `docs/reports/phase-02/P2-0_TRAINING_READINESS.md` |
| `docs/reports/P2-0_VERSION_MATRIX.md` | `d8ce6c17a8e13fcb8ad0948e40fd43c9ebefc8548ab35486e0971c34951347b5` | `docs/designs/phase-02/P2-0_VERSION_MATRIX.md` |
| `docs/reports/P2-1_DEPENDENCY_SPECIFICATION.md` | `18017974b1e7bb1b6fe9908431ec1c435c9f85b799553d1f86073e56c55ce521` | `docs/designs/phase-02/P2-1_DEPENDENCY_SPECIFICATION.md` |
| `docs/reports/P2-1_ENVIRONMENT_DECISION.md` | `4a7afc7921baa4e501c4eb14d564674ddd149c0c31c1f3b325c7fbb1ec1dcba6` | `docs/designs/phase-02/P2-1_ENVIRONMENT_DECISION.md` |
| `docs/reports/P2-1_SETUP_PLAN.md` | `48a0740449e3d0ba1633f282e325009ba59abbd3e8c5c61fc3540dd7b62449d3` | `docs/designs/phase-02/P2-1_SETUP_PLAN.md` |
| `docs/reports/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` | `4378d535cf8501720a12a6671ba3b552a5f99d07f5698a726f520e9a3a6f4add` | `docs/reports/phase-02/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` |
| `docs/reports/P2-2_DEPENDENCY_FREEZE.md` | `b3a4adcd535afb3c162541896f83a7efa40c3794a9991f900af6b86ac954cfd3` | `docs/reports/phase-02/P2-2_DEPENDENCY_FREEZE.md` |
| `docs/reports/P2-2_EXP001_EXECUTION_REVIEW.md` | `3560053f1b32ed57bc95b4b8f2b20b1c721325f79d3534b4d42bb7fa7d035851` | `docs/reports/phase-02/P2-2_EXP001_EXECUTION_REVIEW.md` |
| `docs/reports/P2-2_TRAINING_AUTHORIZATION.md` | `6c5285e88640a2873c3e89eec39843bdb443f6d3dbe4404bf8ff6c265b7f0258` | `docs/reports/phase-02/P2-2_TRAINING_AUTHORIZATION.md` |
| `docs/reports/P2-3_CLOUD_PROVIDER_SELECTION.md` | `87b4ec6e2aa32df79c08ee1d1c9d410ced0247afb74e3f9beebd90d08098823f` | `docs/reports/phase-02/P2-3_CLOUD_PROVIDER_SELECTION.md` |
| `docs/reports/P2-5.1_CONFIGURATION_FREEZE.md` | `1d165d61afc33a2fed2b21d9f20f0c4c3c7bb0a0a73ad0eaf9d6a3ea7d962689` | `docs/reports/phase-02/P2-5.1_CONFIGURATION_FREEZE.md` |
| `docs/reports/P2-5.3_DEPENDENCY_FREEZE.md` | `627fe2b29f6a45dac07dd209bb98d6771a361dd39b0a3f668374aa71a305e8e8` | `docs/reports/phase-02/P2-5.3_DEPENDENCY_FREEZE.md` |
| `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` | `022cd055dfc4ab01ecec6a4e19b33b2865a63c54ae7ea242c2707e12685ec48d` | `docs/reports/phase-02/P2-6_TRAINING_AUTHORIZATION_REQUEST.md` |
| `docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md` | `8e2e6a17406f2c6d7b4b5f012490a954a10d0915170803d7154ffcc96ae650bb` | `docs/reports/phase-02/P2-7_TRAINING_RESULT_FREEZE_REPORT.md` |

## Recommended Migration Plan

### SAFE TO MOVE

None without reference work: every eligible report has at least one inbound mention.

### NEEDS REFERENCE UPDATE

- The eight MEDIUM report/audit files can form a document-only batch once README, Changelog, Test Gates, phase plans and inbound report navigation are mapped. Use `git mv`, update active links, preserve historical body text and verify SHA256/Git blob identity.
- The nine HIGH reports require a separate batch with path-only changes in cited tests or configuration/manifest files and focused test execution. These are not a safe first report-only batch.

### DO NOT MOVE YET

- Five design/planning candidates (`P2-0_DEPENDENCY_STRATEGY`, `P2-0_VERSION_MATRIX`, `P2-1_DEPENDENCY_SPECIFICATION`, `P2-1_ENVIRONMENT_DECISION`, `P2-1_SETUP_PLAN`) should be reviewed for a `docs/designs/phase-02/` batch, not moved to `docs/reports/phase-02/` by default.
- No Phase 3 design candidate remains after the stated name exclusions; `PHASE_3_EVALUATION_REPORT.md` is HIGH due to a configuration reference.

## Excluded High Risk Files

- `P3_MODEL_COMPARISON_REPORT.md` and `P3_MODEL_SELECTION_REPORT.md` are excluded by the `model` term and have release-model configuration dependencies.
- Files named for dataset, quality, EXP-001, weights, model, training manifest or contract were excluded from this Batch-2 candidate set regardless of directory. Keep them at current paths pending a different audit.
- Already archived Batch-1 files under `docs/reports/phase-02/` and `docs/reports/phase-03/` are excluded to avoid repeat migration.

## Required Actions Before Migration

1. Approve a bounded document-only batch for the eight MEDIUM reports, or separately authorize the test/config/manifest path edits needed for any HIGH item.
2. Enumerate every active Markdown link, README/Changelog/Test Gates/phase reference, test path, configuration value, and manifest reference for the selected files. Distinguish navigational references from historical prose.
3. Capture pre-move SHA256 and Git blob IDs; after `git mv`, verify each report blob remains identical. Do not rewrite report history.
4. Run targeted tests for any changed test/config path and a local Markdown-link check, then inspect `git diff --check`, `git status --short`, and rename detection.

## Validation

- `git diff --check`: run after report creation; it does not include untracked files.
- `git status --short`: expected to list only this new report. No rename, code modification, test change, configuration change, commit or push is authorized here.
