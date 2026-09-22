# Training Strategy

> Status: DESIGN FROZEN / TRAINING NOT EXECUTED
>
> This document defines the P1E-0 training-preparation strategy only. It does
> not download weights, execute training, tune hyperparameters, or modify the
> frozen `CSS-PPE-10-V1` dataset.

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
| Status | Design only; not executed |

The baseline must use the exact class order recorded in the dataset contract.
`machinery` and `vehicle` are scene-context classes and must not be interpreted
as PPE compliance states.

## Training Parameters

The following values are intentionally unresolved until P1E-1 review. They
must not be guessed or copied from another project merely to make a run
possible.

| Parameter | P1E-0 state |
| --- | --- |
| Image size | `PENDING_DESIGN_REVIEW` |
| Batch size | `PENDING_DESIGN_REVIEW` |
| Epochs | `PENDING_DESIGN_REVIEW` |
| Optimizer | `PENDING_DESIGN_REVIEW` |
| Learning rate | `PENDING_DESIGN_REVIEW` |
| Augmentation | `PENDING_DESIGN_REVIEW` |
| Seed | `PENDING_DESIGN_REVIEW` |
| Hardware/device | `PENDING_DESIGN_REVIEW` |
| Dependency versions | `PENDING_DESIGN_REVIEW` |

The canonical template is `configs/training/exp001_baseline.yaml`. The schema is
`configs/training/schema.yaml`. No command-line-only run is an acceptable
experiment record.

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

## Non-Goals

P1E-0 does not:

- train or evaluate a model;
- download `yolo11n.pt` or any other checkpoint;
- create training code or run logs;
- modify images, labels, `data.yaml`, metadata, or processed fingerprints;
- select tuned hyperparameters;
- claim any metric for this project; or
- begin Phase 1E release execution or Phase 2.
