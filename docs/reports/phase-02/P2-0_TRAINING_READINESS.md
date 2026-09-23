# P2-0 Training Readiness

> Date: 2026-09-22
>
> Overall readiness: NOT READY FOR TRAINING
>
> P2-0 status: COMPLETED AFTER FINAL TEST VERIFICATION
>
> Training execution: NOT STARTED

## P2-1 Reproducibility Update

| Field | State |
| --- | --- |
| Environment Decision | SELECTED: D. Controlled Cloud GPU |
| Provisioning | NOT STARTED |
| Dependency Freeze | PENDING |
| Training Authorization | NOT GRANTED |

The selected architecture is documented in
`docs/reports/P2-1_ENVIRONMENT_DECISION.md`. Planned versions remain
uninstalled and are recorded in
`docs/reports/P2-1_DEPENDENCY_SPECIFICATION.md`. Provisioning and verification
steps are defined in `docs/reports/P2-1_SETUP_PLAN.md`.

## Readiness Summary

| Area | Status | Evidence |
| --- | --- | --- |
| Dataset | PASS | Frozen `CSS-PPE-10-V1` contract and immutable fingerprints remain valid |
| Experiment | PASS | `EXP-001` configuration schema and canonical config are present and remain non-executable |
| Environment | NOT READY | PyTorch and Ultralytics are absent; CUDA is unavailable |
| GPU | PENDING | No NVIDIA GPU detected; Intel Iris Xe is the only detected adapter |
| Dependencies | PENDING | No runtime dependency was installed; exact versions remain unresolved |
| Authorization | PENDING | The current instruction prohibits training |

## Dataset Readiness

| Item | Evidence |
| --- | --- |
| Dataset ID | `CSS-PPE-10-V1` |
| Mapping | `PPE-MAPPING-V1` |
| Processed dataset | `data/processed/css-ppe-10-v1/` |
| Class order | `person`, `hardhat`, `no_hardhat`, `vest`, `no_vest`, `machinery`, `vehicle` |
| Source `data.yaml` SHA256 | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Source manifest SHA256 | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |
| Processed manifest SHA256 | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |
| Current hash verification | PASS; all three frozen fingerprint files match the training contract |
| Immutable boundary | PASS; no image, label, `data.yaml`, metadata, or fingerprint was modified in P2-0 |

## Experiment Readiness

| Item | Evidence |
| --- | --- |
| Experiment ID | `EXP-001` |
| Canonical config | `configs/training/exp001_baseline.yaml` |
| Schema | `configs/training/schema.yaml` |
| Model | `YOLO11n` |
| Dataset | `CSS-PPE-10-V1` |
| Execution flag | `execution_enabled: false` |
| Frozen status | PASS; no frozen experiment field was changed |
| Pending parameters | Model version, weights, epochs, image size, batch, optimizer, learning rate, augmentation, seed, device strategy, and dependency versions remain `PENDING_DESIGN_REVIEW` |

## Environment Audit

| Item | Observation |
| --- | --- |
| Operating system | Windows 11 Home Chinese, `10.0.22631` |
| Architecture | 64-bit |
| Python | `3.13.6` |
| pip | `25.3` |
| PyTorch | `NOT INSTALLED` |
| Ultralytics | `NOT INSTALLED` |
| CUDA availability | `False` |
| CUDA device count | `0` |
| NVIDIA driver / `nvidia-smi` | NOT FOUND |
| `nvcc` | NOT FOUND |
| GPU | Intel(R) Iris(R) Xe Graphics, driver `32.0.101.7088` |
| System memory | Approximately `31.65 GiB` visible |
| CPU | 13th Gen Intel Core i5-1340P, 12 cores, 16 logical processors |

The environment audit was read-only. No package, driver, model weight, or
dataset was downloaded or installed.

## Required P2-1 Work

Under a new explicit instruction, P2-1 may:

1. select a Windows+NVIDIA, WSL2+CUDA, or controlled cloud GPU environment;
2. create or provision the isolated runtime;
3. install and verify PyTorch, Ultralytics, and their exact versions without
   downloading a training checkpoint;
4. record the hardware, driver, CUDA, and package fingerprint;
5. resolve the model version, weight source, and hash without training; and
6. update the version matrix and readiness record.

P2-1 must still stop before training. A training run requires a separate
authorization after the environment and frozen parameters are reviewed.

## P2-0 Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-0-G1 | Environment audited | PASS |
| P2-0-G2 | Dependency strategy documented | PASS |
| P2-0-G3 | Version matrix documented | PASS |
| P2-0-G4 | Training readiness documented | PASS |
| P2-0-G5 | No training executed | PASS |
| P2-0-G6 | Charter unchanged | PASS |

## Decision

`P2-0 COMPLETED`

The preparation and audit work is complete, but the environment remains
`NOT READY FOR TRAINING`. The next allowed step is
`P2-1 TRAINING ENVIRONMENT SETUP`; training remains prohibited.
