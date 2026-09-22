# Training Strategy

> Status: CONFIGURATION FROZEN / DEPENDENCY FROZEN / EXP-001 TRAINING COMPLETED
>
> P1E-0 defined the strategy. P2-5.1 freezes the canonical EXP-001 parameters.
> P2-5.5 records one authorized execution without modifying the frozen
> `CSS-PPE-10-V1` dataset.

## Scope And Inputs

The first reproducible experiment is a YOLO11 object-detection baseline using
the frozen processed dataset and mapping:

| Field | Value |
| --- | --- |
| Dataset | `CSS-PPE-10-V1` |
| Processed dataset | `data/processed/css-ppe-10-v1/` |
| Mapping | `PPE-MAPPING-V1` |
| Dataset contract | `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml` |
| Quality report | `docs/17_DATASET_QUALITY_REPORT.md` |
| Task | Object detection |
| Classes | `7` |
| Class order | `person`, `hardhat`, `no_hardhat`, `vest`, `no_vest`, `machinery`, `vehicle` |

The dataset contract binds the source `data.yaml` and source/processed manifest
fingerprints. Training must not silently substitute a newer Roboflow version,
the rejected CSS-V1 metadata identity, or a differently mapped export.

## Model Candidates

The following comparison is a design-level comparison. The parameter and speed
figures are approximate Ultralytics model-family expectations and must be
verified against the pinned package release before a training run.

| Candidate | Parameter count | Relative inference speed | Expected accuracy | Deployment cost | Baseline role |
| --- | ---: | --- | --- | --- | --- |
| YOLO11n | Approx. `2.6M` | Fastest of the two candidates | Lower than YOLO11s; suitable baseline for edge/CPU-sensitive deployment | Lower memory and storage cost | Selected for EXP-001 |
| YOLO11s | Approx. `9.4M` | Slower than YOLO11n | Typically higher accuracy and better small-object capacity | Higher memory, compute, and storage cost | Future controlled comparison only |

The selection rule is not "largest model wins." The baseline must first
establish a reproducible pipeline, metric record, and deployment-cost baseline.
Any YOLO11s comparison requires a separate experiment ID and the same frozen
dataset contract.

## Baseline Experiment

### EXP-001

| Field | Frozen design value |
| --- | --- |
| Experiment ID | `EXP-001` |
| Model | `YOLO11n` |
| Dataset | `CSS-PPE-10-V1` |
| Classes | `7` |
| Task | `object detection` |
| Status | Executed; best epoch 75; early stopped after epoch 95 |

The baseline must use the exact class order recorded in the dataset contract.
`machinery` and `vehicle` are scene-context classes and must not be interpreted
as PPE compliance states.

## Training Parameters

The canonical parameters are frozen by P2-5.1. Changing any value requires a
new reviewed configuration revision; a run must use the exact canonical file.

| Parameter | Frozen value |
| --- | --- |
| Model implementation version | Ultralytics `8.4.157` |
| Starting weights | `yolo11n.pt`, Ultralytics official pretrained checkpoint |
| Image size | `640` |
| Batch size | `16` |
| Epochs | `100` |
| Optimizer | `AdamW` |
| Initial learning rate | `0.001` |
| LR strategy | `cosine`, final fraction `0.01` |
| Weight decay | `0.0005` |
| Warmup epochs | `3.0` |
| Early-stopping patience | `20` |
| Augmentation | `experiments/configs/augmentation.yaml` |
| Seed | `42` |
| Device | `cuda:0` |
| Device strategy | Single AutoDL RTX 4090 24GB |
| Workers | `8` |
| Deterministic | `true` |
| AMP | `true` |
| Cache | `false` |
| Dependency versions | FROZEN by P2-5.3: `locks/EXP-001/conda-environment.yml`, `conda-explicit.lock`, and `pip-freeze-all.txt` |

The canonical configuration is `configs/training/exp001_baseline.yaml`. The
schema is `configs/training/schema.yaml`. No command-line-only run is an
acceptable experiment record.

P2-5.2 subsequently registered the official Ultralytics `yolo11n.pt` asset:

```text
path:   models/pretrained/yolo11n.pt
size:   5613764 bytes
sha256: 0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1
```

The version-controlled manifest is
`docs/weights/EXP-001_WEIGHT_MANIFEST.yaml`. The binary remains Git-ignored.
The one-time authorization was consumed by EXP-001.

P2-5.3 froze the resolved AutoDL runtime at:

```text
fingerprint: locks/EXP-001/runtime-fingerprint.yaml
instance:    bcb849a74f-38320766 / bjb1
GPU:         NVIDIA GeForce RTX 4090 / GPU-ad5f1f4a-5bdb-4a26-9b62-5eb190196bb4
driver:      560.35.03 / CUDA API 12.6
pytorch:     2.5.1+cu124 / CUDA runtime 12.4
python:      3.10.21
```

Dependency freeze is not training authorization. The registered weight was
transferred to the remote training environment and used as the single
initialization checkpoint for EXP-001.

## Experiment Record

Every executed experiment must preserve:

1. `experiment_id`
2. `date`
3. `dataset_id`
4. `model`
5. `model_version`
6. `weights`
7. `hyperparameters`
8. `hardware`
9. `metrics`
10. `notes`
11. `checkpoint`

The run directory must also retain the exact configuration file, resolved
package versions, dataset fingerprints, logs, and the relationship between the
recorded checkpoint and the selected metric.

## Evaluation Metrics

Every experiment must report:

| Metric | Requirement |
| --- | --- |
| `mAP50` | Overall detection quality at IoU 0.50 |
| `mAP50-95` | Overall detection quality across IoU thresholds |
| `precision` | Overall precision |
| `recall` | Overall recall |
| `per-class AP` | AP for each of the seven frozen classes |
| `confusion matrix` | Class-level error and background behavior |
| `inference speed` | Measured with the recorded hardware and batch/image configuration |
| `model size` | Checkpoint and exported artifact size where applicable |

Per-class reporting is mandatory because the P1D-1 quality assessment recorded
class imbalance and HIGH small-object risk for `hardhat`, `no_hardhat`, `vest`,
and `vehicle`. Aggregate metrics alone are not sufficient evidence of
compliance-detection quality.

## EXP-001 Result

EXP-001 completed 95 of 100 configured epochs. The best validation result was
obtained at epoch 75, and early stopping then ended the run after 20 epochs
without improvement.

| Class | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| all | 0.899 | 0.649 | 0.767 | 0.480 |
| person | 0.935 | 0.693 | 0.797 | 0.515 |
| hardhat | 0.945 | 0.722 | 0.819 | 0.526 |
| no_hardhat | 0.843 | 0.522 | 0.634 | 0.327 |
| vest | 0.966 | 0.689 | 0.888 | 0.555 |
| no_vest | 0.862 | 0.604 | 0.739 | 0.461 |
| machinery | 0.979 | 0.835 | 0.924 | 0.636 |
| vehicle | 0.761 | 0.476 | 0.564 | 0.337 |

The best checkpoint is recorded as a Git-ignored artifact with size
`5,479,891` bytes and SHA256
`1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
These are training validation metrics. They satisfy the M-004 experiment
archive but do not replace the independent Phase 3 evaluation required by
M-005.

Ultralytics also downloaded `yolo26n.pt` for its one-time AMP compatibility
check. The training log records that it was not used for training and it did
not replace the frozen `yolo11n.pt` initialization checkpoint.

## Quality And Risk Handling

P1D-1 findings are inputs to evaluation, not permission to repair the dataset:

- two perceptual cross-split candidate groups across `valid` and `test` must
  remain visible as risk evidence;
- HIGH small-object risk must be reflected in per-class and size-aware
  validation;
- class imbalance must be reported and investigated rather than hidden by a
  single aggregate score; and
- empty labels remain valid image-without-object records.

No deletion, relabeling, resizing, augmentation, remapping, or resplitting is
allowed in P1E-0 or as an implicit part of training preparation.

## Configuration-Driven Governance

ADR-016 requires all experiments to be defined by immutable configuration
files. A manual command-line experiment is not accepted as a reproducible
record, even if metrics were produced. The configuration and dataset
fingerprint must be sufficient to reconstruct the run.

## P2-5.1 Historical Non-Goals

P2-5.1 did not:

- train or evaluate a model;
- download `yolo11n.pt` or any other checkpoint;
- create training code, checkpoints, or run logs;
- modify images, labels, `data.yaml`, metadata, or processed fingerprints;
- claim any metric for this project; or
- grant training authorization.

The subsequent P2-5.5 execution is recorded in
`docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`.
