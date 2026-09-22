# EXP-001 Training Runbook

> STATUS: CONFIGURATION FROZEN / EXECUTED
>
> TRAINING EXECUTION: COMPLETED
>
> The one-run authorization has been consumed. This runbook does not authorize
> another training run.

## 1. Environment Requirements

- Repository root must contain the frozen project source tree.
- Python, PyTorch, and Ultralytics versions must be resolved and recorded.
- P2-5.3 freezes the exact conda and pip environment under
  `locks/EXP-001/`.
- CUDA availability and device strategy must be verified before execution.
- P2-4 verified the AutoDL RTX 4090 environment and transferred dataset.
- Training authorization was granted by explicit user instruction and consumed
  by EXP-001.
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

The config is currently `CONFIGURATION_FROZEN` and
`execution_enabled: false`. P2-5.1 freezes the baseline parameters while
keeping execution disabled until explicit authorization.

## 4. Training Entry

The implemented entry point is:

```text
scripts/train.py
```

The one authorized invocation was:

```bash
/root/miniconda3/envs/ppe-exp001/bin/python -m scripts.train \
  --config configs/training/exp001_baseline.yaml \
  --authorization configs/training/exp001_authorization.yaml \
  --data-yaml /root/autodl-tmp/datasets/css-ppe-10-v1/data.yaml \
  --weights /root/autodl-tmp/models/pretrained/yolo11n.pt
```

Executing this command again is not authorized. The authorization record is
marked `CONSUMED`, and the populated output destinations reject a collision.

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
4. Verify the frozen configuration fingerprint and every parameter value.
5. Store a copy of the canonical configuration in the run directory.
6. Store the dataset fingerprint and environment record in the run directory.
7. Execute only after a new explicit authorization is recorded.
8. Save logs, metrics, confusion matrix, speed, model size, and checkpoint.
9. If a new comparison run is authorized, use a new experiment ID and
   authorization record rather than overwriting `EXP-001`.

## 7. Stop Conditions

Stop before execution if any of the following is true:

- dataset fingerprint mismatch;
- class order mismatch;
- output path collision;
- configuration fingerprint mismatch;
- missing explicit human training authorization;
- dependency lock and weight provenance are not present and verified at the
  remote execution host;
- a weight download or external install would be required; or
- the current instruction still prohibits training.
