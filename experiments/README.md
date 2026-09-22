# Training Experiment Management

> Status: DESIGN ONLY / EXECUTION DISABLED

This directory is the single home for reproducible training experiment
definitions, run artifacts, reports, and review evidence. P1E-0 creates the
structure and configuration contracts only. It does not download weights,
start training, tune hyperparameters, or modify the frozen dataset.

## Layout

```text
experiments/
├── README.md
├── configs/
│   ├── baseline.yaml
│   └── augmentation.yaml
├── runs/
│   └── .gitkeep
└── reports/
    └── .gitkeep
```

Training outputs must not be scattered outside this directory. Model binaries
remain Git-ignored under `models/`; run logs and diagnostics belong under
`experiments/runs/`; result summaries and review reports belong under
`experiments/reports/`.

## Required Experiment Record

Every experiment must be represented by an immutable configuration and must
record at least:

| Field | Requirement |
| --- | --- |
| `experiment_id` | Must match `EXP-\d{3}` and be unique |
| `date` | Run date in ISO format |
| `dataset_id` | Frozen dataset identity; currently `CSS-PPE-10-V1` |
| `model` | Model family and variant, such as `YOLO11n` |
| `model_version` | Exact implementation or package version |
| `weights` | Starting weight identity and provenance; no weight is downloaded by P1E-0 |
| `hyperparameters` | Complete parameter mapping, including image size, batch, epochs, optimizer, learning rate, augmentation, and seed |
| `hardware` | Device, accelerator, memory, and runtime environment |
| `metrics` | Required evaluation outputs |
| `notes` | Deviations, observations, and limitations |
| `checkpoint` | Best/last checkpoint identity or a clear failure state |

The experiment record must be sufficient to reconstruct the run without relying
on an untracked command history.

## Configuration Rules

1. An experiment is defined by a version-controlled YAML file under
   `configs/training/` or `experiments/configs/`.
2. Manual command-line-only experiments are not accepted as reproducible
   records.
3. Dataset identity must reference the frozen release contract and must not
   permit an implicit latest version.
4. Values that have not been reviewed must remain explicit placeholders; they
   must not be replaced with guessed tuned values.
5. Configuration is immutable for a recorded run. A changed configuration
   creates a new experiment ID or a documented revision.
6. Run outputs must preserve the configuration fingerprint, software versions,
   dataset fingerprints, hardware description, metrics, and checkpoint status.

## Baseline And Augmentation

- `configs/baseline.yaml` is a non-canonical design template alias for
  EXP-001; the canonical experiment definition remains
  `configs/training/exp001_baseline.yaml`.
- `configs/augmentation.yaml` is the augmentation design template.
- Both are placeholders until the P1E-1 review approves exact values.
- `configs/training/exp001_baseline.yaml` is the canonical experiment
  definition template.
- The JSON-compatible schema contract is
  `configs/training/schema.yaml`.

## Execution Boundary

P1E-0 must not execute training. The next allowed step is P1E-1 Baseline
Training Preparation Review; it must not run training either. Phase 2 training
remains prohibited until Phase 1 release gates and the Phase 1 to Phase 2
entry conditions are both approved.
