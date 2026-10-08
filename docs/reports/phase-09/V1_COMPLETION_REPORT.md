# V1 completion report — 2026-10-08

## Authorized scope

Implement the audit closure items, excluding remote RTSP and long-duration stability at the user's request. This is scoped V1 readiness, not unrestricted production acceptance. Locked Charter descriptions and historical frozen assets remain unchanged. ADR-028 records the independent split revision and closure decisions.

## Closure matrix

| Item | Implementation and evidence | Result |
| --- | --- | --- |
| Assistant session regression | Preserve an injected/legacy runtime with no fingerprint, initialize its opaque fingerprint, rebuild only on actual configuration changes; provider settings remain server-owned | Implemented; session and configuration tests pass |
| Offline test isolation | Absent local credential path plus process-variable clearing and Windows-user resolution disabled inside tests; explicit test configuration still works | Implemented; no implicit real API calls |
| Dataset candidate review | Two groups visually confirmed same-scene neighboring frames; new independent split R2 moves two test image/label pairs to validation | Quality PASS; training bytes identical, original source hash unchanged |
| Distribution charts | Quality writer exports class-box and split-box SVGs and references them from generated Markdown | PASS; parse/series tests; real R2 charts retained |
| Real current report | Actual SQLite scope contains 52 events; DeepSeek result valid, LLM, degraded=false; previous malformed/truncated result safely degraded | PASS; V1_REAL_REPORT_VALIDATION.json |
| Deployment/recovery | docs/V1_DEPLOYMENT_GUIDE.md includes environment, commands, local secrets, backup, shutdown and symptom/recovery mapping | Implemented; preflight and pip check PASS |
| Demo/defense | docs/V1_DEMO_AND_DEFENSE.md contains a repeatable sequence, capture checklist, indexed evidence and speaking outline | Implemented; a fresh complete human walkthrough is not implied |
| Final acceptance bookkeeping | Current status and gates record scoped closure; exclusions and old metric caveats retained | No wholesale Charter acceptance asserted |

## Dataset integrity

Original payload: `bc762204e2305164cfdbc492d15269b84c4ce4ff3cfdcdc805baf84c5616237b`, verified unchanged.
Revised payload: `c08aff491e086fb8f97ebda28d1db738ab2fee6d4ea1c8959fa2e3cb1f0d12a3`.
R2 train/valid/test image counts: 2603/116/80. The unchanged training set and frozen checkpoint are retained. Old EVAL-001 and training validation metrics are historical, not retroactively corrected. New evaluation is supplemental, not retraining. Zero candidates refers to exact hash and dHash threshold 5, not a proof of all possible semantic similarity. Source files and interrupted staging copy remain outside Git.

[Quality report](V1_SPLIT_R2_QUALITY.md), [revision record](V1_SPLIT_R2_REVISION.json), [class chart](quality_classes.svg), [split chart](quality_splits.svg).

## LLM verification and fix

The previous request produced incomplete JSON at 19,967 bytes. Report calls now specify a bounded 16,384 output-token budget; the 262,144-byte ceiling, timeout, parser and grounding checks remain. Actual current SQLite report passed structure and grounding with no fallback. The earlier failure on the same scope confirmed safe fallback. No key is included in tracked evidence.

[Real report evidence](V1_REAL_REPORT_VALIDATION.json). DeepSeek documents truncated output when generation reaches its token limit: [official API reference](https://api-docs.deepseek.com/api/create-chat-completion/).

## Verification record

- Full regression after runtime/isolation repair: 810 passed in 736.68 seconds.
- Subsequent output-budget/chart/hash changes: 61 targeted tests passed in 38.29 seconds.
- Final full rerun: 808 passed, 2 documentation failures in 760.16 seconds. Both failures occurred while the completion report/README were being written; repaired checks subsequently passed (2/2, then 5/5 including configuration tests). Thus all 810 collected cases have passing evidence across the full run and focused repair reruns; a single post-documentation full-suite run is not claimed. No business test failed in that rerun.
- preflight PASS; pip check: no broken requirements; compileall PASS.
- Private configuration ignored and untracked; no commit/push performed.

## Repeatable commands

```powershell
& '.\.venv-final-demo\Scripts\python.exe' scripts/check_v1_delivery.py
& '.\.venv-final-demo\Scripts\python.exe' -m pytest -q
& '.\.venv-final-demo\Scripts\python.exe' scripts/prepare_dataset.py quality --source data/processed/css-ppe-10-v1-split-r2 --dataset-id CSS-PPE-10-V1-SPLIT-R2 --json-output artifacts/reports/V1-quality.json --markdown-output artifacts/reports/V1-quality.md
```

`revise_dataset_split.py` requires a new output directory and fails if it exists. `evaluate_split_revision.py` likewise preserves existing evaluation output; choose a new --output for reruns. Never overwrite historical evidence. These scripts are additive; original frozen evaluation commands remain valid for the original dataset.

## Remaining limits

Remote RTSP and long stability are explicitly excluded. No broad-scene accuracy guarantee, public-cloud deployment, production authentication or durable Agent audit store is inferred. Camera acceptance and full chain evidence remain the prior human-reviewed P9-B records. Final deck artwork and a new human walkthrough are not claimed by an index/speaker outline. Final Charter status changes require the full applicable acceptance review; the scoped exclusions must not be silently removed from release statements.

## Supplemental evaluation completed

80/80 revised test images processed with unchanged EXP-001. Input image/label hashes unchanged; Ultralytics matching/AP reference check PASS. Overall seven-class metrics: Precision 0.795859, Recall 0.709828, mAP50 0.729892, mAP50-95 0.462068. Five PPE classes and two scene classes are individually retained in [evaluation record](V1_SPLIT_R2_EVALUATION.json). These are actual revised-test results, not the historical training-validation metrics.

## Final scoped result

All six audit closure items are implemented and verified at the stated evidence scope. `scripts/check_v1_delivery.py` PASS; `git diff --check` PASS; private-key scan of tracked and publishable untracked files PASS. V1 is ready for the documented local demonstration with RTSP/long stability excluded. Unrestricted final Charter acceptance and a new human walkthrough remain separate from this implementation record.
