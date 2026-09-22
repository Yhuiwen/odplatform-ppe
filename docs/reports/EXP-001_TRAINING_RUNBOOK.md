# EXP-001 Training Runbook

> STATUS: DESIGN ONLY
>
> TRAINING EXECUTION: NOT STARTED
>
> This runbook does not authorize a training run.

## 1. Environment Requirements

- Repository root must contain the frozen project source tree.
- Python, PyTorch, and Ultralytics versions must be resolved and recorded.
- CUDA availability and device strategy must be verified before execution.
- The current P1E-1 environment audit result is `NOT READY FOR TRAINING`.
- Do not install dependencies or download weights as part of this runbook.
- Phase 2 preparation and explicit user approval are required before execution.

## 2. Data Paths

| Item | Path |
| --- | --- |
| Frozen dataset ID | `CSS-PPE-10-V1` |
| Training contract | `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml` |
| Processed dataset | `data/processed/css-ppe-10-v1/` |
| Processed YOLO data YAML | `data/processed/css-ppe-10-v1/data.yaml` |
| Mapping | `PPE-MAPPING-V1` |
| Quality report | `docs/17_DATASET_QUALITY_REPORT.md` |

The processed dataset is immutable. The runbook must never delete, relabel,
resize, augment, remap, resplit, or rewrite its payload.

## 3. Configuration Entry

Canonical experiment configuration:

```text
configs/training/exp001_baseline.yaml
```

Schema:

```text
configs/training/schema.yaml
```

The config is currently `DESIGN_PLACEHOLDER` and
`execution_enabled: false`. All unresolved values remain
`PENDING_DESIGN_REVIEW`.

## 4. Training Entry

The future entry point is:

```text
scripts/train.py
```

It currently raises `NotImplementedError` and is intentionally not executable.
The planned invocation is design-only:

```text
python -m scripts.train --config configs/training/exp001_baseline.yaml
```

This command must not be run until the Phase 2 implementation and
training-execution authorization are complete.

## 5. Output Directories

| Artifact | Reserved path |
| --- | --- |
| Run output | `experiments/runs/EXP-001` |
| Logs | `artifacts/logs/EXP-001` |
| Reports | `experiments/reports/EXP-001` |
| Checkpoints | `models/checkpoints/EXP-001` |

Model binaries, datasets, and run output must remain outside Git as defined by
the repository ignore policy.

## 6. Reproduction Procedure

1. Verify the dataset contract and all three fingerprints.
2. Verify the processed dataset class order and image/label structure.
3. Resolve and record Python, PyTorch, Ultralytics, CUDA, and device versions.
4. Review and freeze every `PENDING_DESIGN_REVIEW` parameter.
5. Store a copy of the canonical configuration in the run directory.
6. Store the dataset fingerprint and environment record in the run directory.
7. Execute only after Phase 2 authorization.
8. Save logs, metrics, confusion matrix, speed, model size, and checkpoint.
9. Re-run the same configuration and compare deterministic evidence.

## 7. Stop Conditions

Stop before execution if any of the following is true:

- dataset fingerprint mismatch;
- class order mismatch;
- output path collision;
- unresolved hyperparameter, seed, or device strategy;
- environment audit remains `NOT READY FOR TRAINING`;
- a weight download or external install would be required; or
- the current instruction still prohibits training.
