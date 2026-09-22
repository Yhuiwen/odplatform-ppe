# P1E-1 Training Data Contract Audit

> Date: 2026-09-22
>
> Audit status: PASS
>
> Dataset state: FROZEN / IMMUTABLE
>
> Training execution: NOT STARTED

This audit is read-only. It inspects the training contract and verifies the
materialized source and processed fingerprints without modifying any dataset,
label, `data.yaml`, mapping, or metadata file.

## Contract

`docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml`

| Check | Result | Evidence |
| --- | --- | --- |
| Dataset ID present | PASS | `CSS-PPE-10-V1` |
| Processed dataset path present | PASS | `data/processed/css-ppe-10-v1/` |
| Mapping version present | PASS | `PPE-MAPPING-V1` |
| Class order present | PASS | `0 person`, `1 hardhat`, `2 no_hardhat`, `3 vest`, `4 no_vest`, `5 machinery`, `6 vehicle` |
| Class count present | PASS | `7` |
| Quality report reference present | PASS | `docs/17_DATASET_QUALITY_REPORT.md` |
| Quality status present | PASS | `PASS` |
| Immutable boundary present | PASS | `immutable: true`, `executable: false`, `training_started: false` |
| Source `data.yaml` fingerprint | PASS | SHA-256 matches `5c393e74...d21b34` |
| Source manifest fingerprint | PASS | SHA-256 matches `ea0de4b0...f98d795` |
| Processed manifest fingerprint | PASS | SHA-256 matches `dbfe43c4...831c2c` |

## Decision

`TRAINING DATA CONTRACT AUDIT REPORT: PASS`

Dataset fingerprint verification: PASS for the source `data.yaml`, source
manifest, and processed manifest.

The contract is internally consistent with the frozen dataset, mapping,
quality report, and training-preparation boundary. No data mutation is
permitted by this audit.
