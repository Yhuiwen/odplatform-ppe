# P2-6 EXP-001 Training Authorization Request

> Date: 2026-09-22
>
> Request status: **READY_FOR_HUMAN_AUTHORIZATION**
>
> Authorization granted: NO
>
> Training execution: NOT STARTED
>
> This document is an authorization request. It is not an execution
> authorization and must not be treated as one.

## Scope

This request asks for an explicit human decision on whether `EXP-001` may
execute one YOLO11n baseline training run in the prepared AutoDL environment.
It records the already frozen experiment identity and the controls that must
remain unchanged during execution.

The request does not download data or weights, install dependencies, modify
the dataset, modify the class mapping, modify the canonical configuration, or
execute training.

## Experiment Identity

| Field | Frozen value |
| --- | --- |
| Experiment ID | `EXP-001` |
| Experiment type | YOLO11n baseline |
| Model | `YOLO11n` |
| Model family | YOLO11 |
| Model implementation | Ultralytics `8.4.157` |
| Dataset | `CSS-PPE-10-V1` |
| Canonical configuration | `configs/training/exp001_baseline.yaml` |
| Configuration status | `CONFIGURATION_FROZEN` |
| Execution control | `execution_enabled: false` |
| Current authorization | `NOT GRANTED` |
| Epochs | `100` |
| Image size | `640` |
| Batch size | `16` |
| Optimizer | `AdamW` |
| Initial learning rate | `0.001` |
| LR strategy | Cosine, final fraction `0.01` |
| Seed | `42` |
| Device | `cuda:0`, single AutoDL RTX 4090 24GB |
| Workers | `8` |

Any change to the model, dataset, mapping, seed, hyperparameters,
augmentation, device strategy, or output paths requires a new reviewed
configuration identity and is outside this request.

## Dataset Identity

| Field | Frozen value |
| --- | --- |
| Dataset ID | `CSS-PPE-10-V1` |
| Mapping | `PPE-MAPPING-V1` |
| Source workspace | `roboflow-universe-projects` |
| Source project | `construction-site-safety` |
| Source version | `27` |
| Export format | `yolov8` |
| Images | `2,799` |
| Splits | train `2,603` / valid `114` / test `82` |
| Training class count | `7` |
| Training classes | `person`, `hardhat`, `no_hardhat`, `vest`, `no_vest`, `machinery`, `vehicle` |
| Source `data.yaml` SHA256 | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Source manifest SHA256 | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |
| Processed manifest SHA256 | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |
| Local processed dataset | `data/processed/css-ppe-10-v1/` |
| Remote processed dataset | `/root/autodl-tmp/datasets/css-ppe-10-v1/` |
| Dataset contract | `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml` |
| Quality report | `docs/17_DATASET_QUALITY_REPORT.md` |
| Mutation policy | Immutable; no delete, relabel, remap, resize, resplit, or rewrite |

The remote dataset was transferred and verified in P2-4-G4. Its 5,604 files,
2,799 images, 2,799 labels, seven-class order, and full checksum manifest must
be rechecked before execution.

## Configuration Hash

The canonical configuration hash is:

```text
configs/training/exp001_baseline.yaml
SHA256 df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989
```

Related frozen configuration identities:

| File | SHA256 |
| --- | --- |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` |
| `configs/training/schema.yaml` | `909457210c97e1139df978a5f89d50436cfdb2e22577696a930236b3a24c2477` |
| `experiments/configs/augmentation.yaml` | `bb925382ff9deba525d57eced7762326d8bfb7ae82f49390c42bfa81b6f29f59` |
| `experiments/configs/baseline.yaml` | `206308e7c0bfcdf83aa6e50bc531a18d6ef155adb82c116e7b4980491937165b` |

Execution must stop if any hash differs before the run begins.

## Weight Hash

The registered checkpoint is an initialization weight only, not a training
output and not the teacher checkpoint.

| Field | Value |
| --- | --- |
| Filename | `yolo11n.pt` |
| Local path | `models/pretrained/yolo11n.pt` |
| Local size | `5,613,764` bytes |
| SHA256 | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` |
| Source | Ultralytics assets release `v8.3.0` |
| Role | Initialization weights |
| Git tracking | `NO`, ignored by `*.pt` |
| Weight manifest | `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` |

A remote weight whose SHA256 differs from this value is a stop condition. It
must not be overwritten or used for training without a reviewed correction.

## Runtime Fingerprint

| Field | Frozen value |
| --- | --- |
| Provider | AutoDL |
| Region | `bjb1` |
| Instance | `bcb849a74f-38320766` |
| Hostname | `autodl-container-bcb849a74f-38320766` |
| Machine ID | `08dfa3464dbc42b1afb9de0b5f908acb` |
| OS | Ubuntu 20.04.5 LTS |
| Kernel | `Linux 5.15.0-97-generic x86_64 GNU/Linux` |
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB |
| GPU UUID | `GPU-ad5f1f4a-5bdb-4a26-9b62-5eb190196bb4` |
| Compute capability | `8.9` |
| NVIDIA driver | `560.35.03` |
| CUDA driver API | `12.6` |
| PyTorch CUDA runtime | `12.4` |
| cuDNN | `90100` |
| Conda environment | `/root/miniconda3/envs/ppe-exp001` |
| Python | `3.10.21` |
| PyTorch | `2.5.1+cu124` |
| torchvision | `0.20.1+cu124` |
| torchaudio | `2.5.1+cu124` |
| Ultralytics | `8.4.157` |
| OpenCV | `5.0.0.93` |
| NumPy | `2.2.6` |
| Dependency consistency | `python -m pip check`: PASS |

Runtime lock files:

| Lock | SHA256 |
| --- | --- |
| `locks/EXP-001/conda-environment.yml` | `95b03d3dfc57f4124dcf370b9bd42cadab86f1701649d3610824c74a86f88fc3` |
| `locks/EXP-001/conda-explicit.lock` | `599ed7c0e6b9ee9817517d140488c382066fc2e9d7e2a14315deefb43f3438d5` |
| `locks/EXP-001/pip-freeze-all.txt` | `34c9b668095029732f1c4c084b81185309c64614fe25e88b69328e1f9b91599e` |
| `locks/EXP-001/runtime-fingerprint.yaml` | `f5f8240d2225219743e0fc3a310a174e5583d0dd405b2ecc315b0433eefbf7aa` |

The provider did not expose an immutable image digest. Runtime identity must
therefore be rechecked against these recorded fields immediately before each
authorized execution.

## Remote Weight Verification

| Check | Local | Remote | Result |
| --- | --- | --- | --- |
| Path | `models/pretrained/yolo11n.pt` | `/root/autodl-tmp/models/pretrained/yolo11n.pt` | PASS |
| Size | `5,613,764` bytes | `5,613,764` bytes | PASS |
| SHA256 | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` | PASS |
| Canonical path | n/a | Same as requested remote path | PASS |

Evidence: `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md`.

This verification confirms asset identity only. It does not authorize model
execution or training.

## Output Directory

| Artifact class | Reserved path |
| --- | --- |
| Run output | `experiments/runs/EXP-001` |
| Logs | `artifacts/logs/EXP-001` |
| Reports | `experiments/reports/EXP-001` |
| Checkpoints | `models/checkpoints/EXP-001` |

Run outputs, checkpoints, and model binaries must remain outside Git. An
existing non-empty run directory is a collision and requires review before
reuse.

## Expected Artifacts

The authorized run must produce auditable evidence sufficient to reproduce
and review `EXP-001`:

- a run-local copy or immutable fingerprint of the canonical configuration;
- dataset identity, mapping, and all dataset fingerprint records used by the
  run;
- the resolved runtime fingerprint and dependency-lock hashes;
- initialization-weight provenance and SHA256;
- training logs and command metadata;
- per-epoch metrics and loss history;
- `best.pt` and `last.pt` checkpoints or equivalent final artifacts;
- validation outputs for Precision, Recall, mAP50, mAP50-95, and per-class AP;
- confusion matrix, inference-speed, and model-size evidence;
- a final run report identifying any interruption, failure, or deviation; and
- explicit confirmation that no dataset, mapping, or configuration file was
  mutated in place.

Expected artifacts do not count as produced until they exist and pass review.
M-001 and M-004 remain `待实现` until the required reproducible evidence is
complete.

## Risk Notes

- RISK-017: dataset quality observations remain relevant; perceptual
  cross-split candidates, small-object risk, class imbalance, and empty labels
  must not be hidden or silently repaired.
- RISK-018: the run would not be reproducible if the canonical configuration,
  dataset fingerprint, dependency lock, seed, or hardware fingerprint changes.
- RISK-019: AutoDL price, storage, instance retention, image state, or network
  availability may drift. A live preflight check and budget control are
  required.
- Ultralytics is AGPL-3.0. Training use is permitted by the recorded
  dependency policy, but distribution and delivery obligations remain subject
  to a later license review.
- The initialization checkpoint is official `yolo11n.pt`; the teacher
  checkpoint is reference-only and must not substitute for this run.
- Cloud credentials must remain outside Git. No API key, token, password, or
  private key may be written into run artifacts.
- A partial or failed run is evidence and must not be presented as a
  successful model.
- Only the recorded class mapping may be used. The seven training classes
  include two scene-context classes, but only the five locked PPE classes
  carry compliance semantics.

## Rollback Plan

1. Before execution, recheck the dataset, configuration, runtime, and weight
   fingerprints. Abort without starting if any identity differs.
2. Confirm that the run, log, report, and checkpoint destinations are free of
   an unreviewed collision. Do not overwrite prior evidence.
3. If a preflight check fails, leave the frozen dataset, mapping, weights, and
   configuration unchanged and report the blocking mismatch.
4. If training fails after start, stop the training process and preserve its
   logs and partial artifacts for review. Do not delete evidence silently.
5. If rollback to a clean execution state is required, quarantine or archive
   the failed run under a reviewed recovery directory or new run ID. Do not
   mutate the frozen source or processed dataset.
6. If the remote weight, dependency lock, or runtime no longer matches, stop
   before training and re-establish the frozen environment under a separate
   reviewed action.
7. After an interrupted or failed cloud run, stop billable GPU work according
   to the provider policy. Retain or remove remote data only under the
   approved retention policy.
8. Never repair a failed run by editing labels, `data.yaml`, the class
   mapping, or the canonical experiment configuration in place.

## Authorization Decision

The preparation evidence is complete enough to request a human decision:

```text
README.md
docs/02_CURRENT_STATUS.md
P2-5.1_CONFIGURATION_FREEZE_REPORT.md
P2-5.2_WEIGHT_REGISTRATION_REPORT.md
P2-5.3_DEPENDENCY_FREEZE_REPORT.md
docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md
configs/training/exp001_baseline.yaml
```

Requested decision:

```text
Authorize or deny the single EXP-001 YOLO11n baseline training run.
```

Current state:

```text
READY_FOR_HUMAN_AUTHORIZATION
AUTHORIZATION GRANTED: NO
TRAINING EXECUTION: NOT STARTED
```
