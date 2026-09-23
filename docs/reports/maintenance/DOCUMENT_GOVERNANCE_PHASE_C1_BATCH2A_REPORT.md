# Documentation Governance Phase C-1 Batch-2A Report

Date: 2026-09-23
Base HEAD: `9fd4d888b185b6214b8319e819d9dd36bfdc87d3`
Status: migration complete for human review; no commit or push.

## Moved Files

| Original | New path |
| --- | --- |
| `P2-5_TRAINING_AUTHORIZATION_REPORT.md` | `docs/reports/phase-02/P2-5_TRAINING_AUTHORIZATION_REPORT.md` |
| `docs/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` | `docs/reports/phase-02/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` |
| `docs/P2-4_FINAL_PROVISIONING_REPORT.md` | `docs/reports/phase-02/P2-4_FINAL_PROVISIONING_REPORT.md` |
| `docs/reports/P2-0_TRAINING_READINESS.md` | `docs/reports/phase-02/P2-0_TRAINING_READINESS.md` |
| `docs/reports/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` | `docs/reports/phase-02/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` |
| `docs/reports/P2-2_DEPENDENCY_FREEZE.md` | `docs/reports/phase-02/P2-2_DEPENDENCY_FREEZE.md` |
| `docs/reports/P2-2_EXP001_EXECUTION_REVIEW.md` | `docs/reports/phase-02/P2-2_EXP001_EXECUTION_REVIEW.md` |
| `docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md` | `docs/reports/phase-02/P2-7_TRAINING_RESULT_FREEZE_REPORT.md` |

## Rename Detection

All eight moves used `git mv` and appear as `R100` in `git diff --cached --name-status --find-renames=100%`. Each staged destination has the same Git blob ID as its original HEAD path. Report bodies were not edited.

## Reference Updates

- `README.md`: updated the P2-4 final provisioning entry.
- `docs/04_CHANGELOG.md`: updated seven current path mentions for moved reports.
- `docs/05_TEST_GATES.md`: updated seven evidence paths; Gate decisions were not changed.
- `docs/phases/PHASE_02_TRAINING.md`: updated the P2-5 authorization and P2-7 result-freeze paths; Phase status was not changed.
- No moved report contained a Markdown navigation link requiring a body edit. Older inline paths in dated reports, the Batch-2 audit, `README_SYNC_REPORT.md` and the archived worklog snapshot remain historical records. No test, script, configuration or manifest file was edited.

## BATCH2A_PRE_MIGRATION_HASH and Hash Verification

The table records pre-move Git blob IDs and SHA256 of working-tree bytes. Post-move Git blob IDs and SHA256 matched for every file.

| Original | Git blob ID before and after | SHA256 before and after |
| --- | --- | --- |
| `P2-5_TRAINING_AUTHORIZATION_REPORT.md` | `87f89d2c10255ee74340026c412871b76012ced0` | `f129fb3d21df788c52c99ba7afdd6c2f26b1c24cffc2ac6faeaa08f6f5c3a3a5` |
| `docs/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md` | `a07f84cf599df6c555c50a514a353294cd20e48c` | `87ffe170775dd3750daccad541b8cb324bd71e851933c95e8088dca3a4e74779` |
| `docs/P2-4_FINAL_PROVISIONING_REPORT.md` | `d18f1956c1cd4e0ff803b4d83c309a3af0cf2f80` | `1c5fd5d7308d0a70190924dbe147d7ce2e155a56c49de0a86892544dcd403c9e` |
| `docs/reports/P2-0_TRAINING_READINESS.md` | `0f159ee9933be402b62bb68def57f4505f6d7a68` | `8a00271a489b5286c7e4abcf12f43d9a2432d843a130dd0c53cb2dbf83cccf88` |
| `docs/reports/P2-2_CLOUD_ENVIRONMENT_REVIEW.md` | `099d7965c2b274a75702fec7e58e33dd575a309b` | `4378d535cf8501720a12a6671ba3b552a5f99d07f5698a726f520e9a3a6f4add` |
| `docs/reports/P2-2_DEPENDENCY_FREEZE.md` | `9daa3598d3cfab265f552b7960764c2d2345cdf0` | `b3a4adcd535afb3c162541896f83a7efa40c3794a9991f900af6b86ac954cfd3` |
| `docs/reports/P2-2_EXP001_EXECUTION_REVIEW.md` | `0789d0f6f2d3e30d175fe49dc9e61a47dd1d4d0d` | `3560053f1b32ed57bc95b4b8f2b20b1c721325f79d3534b4d42bb7fa7d035851` |
| `docs/reports/P2-7_TRAINING_RESULT_FREEZE_REPORT.md` | `02e098d7993ce76a77c46151ab1e4ca98aca1cd9` | `8e2e6a17406f2c6d7b4b5f012490a954a10d0915170803d7154ffcc96ae650bb` |

## Tests

- `python -m pytest tests/unit/test_documentation_governance.py`: **31 passed**.
- `python -m pytest tests/unit/test_data_source_evidence.py tests/unit/test_dataset_quality_service.py`: **31 passed**.
- `python -m pytest tests/unit/test_training_preparation.py`: **13 passed**.
- All 13 local Markdown links resolve; no Markdown image links were found.
- `git diff --check` and `git diff --cached --check`: PASS before this report was written.
- No model, data, experiment artifact, business code, test, configuration or manifest content was changed.

## Remaining Risks

- Dated reports and the archived historical snapshot still contain old textual paths. Those records were retained intentionally; future readers should use current indexes for navigation.
- The full test suite was not run. This migration was validated with the three requested test commands, link resolution, and blob/hash checks.
- Additional HIGH-risk Phase 2/3 files and design/planning files remain in place pending separately scoped migration work.

Next step: human review of the Batch-2A diff. Do not commit or push as part of this task.
