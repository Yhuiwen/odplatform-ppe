# P2-0 Version Matrix

> Date: 2026-09-22
>
> Status: DESIGN / PENDING VERIFICATION
>
> Installation action: NONE
>
> Training execution: PROHIBITED

## Purpose

This matrix records the version decisions that must be made before the
`EXP-001` training run. It separates observed facts from planned constraints.
It does not claim compatibility that has not been verified on a selected
runtime.

## Matrix

| Component | Current Observation | P2-0 State | Compatibility Policy | Required P2-1 Action |
| --- | --- | --- | --- | --- |
| Python | `3.13.6` in the current audit environment | AUDITED, NOT PINNED | The selected Python version must be supported by the exact PyTorch and Ultralytics releases; a shared global interpreter is not required | Create or select the isolated training environment and record the exact interpreter version |
| PyTorch | `NOT INSTALLED` | PENDING | Must match the selected Python version, CPU/GPU device, and CUDA wheel/runtime policy; exact version and build must be recorded | Install only under P2-1 authorization, then record `torch.__version__`, CUDA build, and device visibility |
| CUDA | Not available to PyTorch; `nvidia-smi` and `nvcc` not found | PENDING | A GPU run requires a compatible NVIDIA driver and a PyTorch wheel with the selected CUDA runtime; a system toolkit is not assumed | Confirm the selected host and driver, then record exact runtime and wheel metadata |
| Ultralytics | `NOT INSTALLED`; repository range is `>=8.3,<9` | PENDING | Version must support the YOLO11 family, the selected PyTorch version, and the frozen YOLO dataset layout; range membership alone is not a freeze | Install only under P2-1 authorization, then pin the exact package version and inspect its YOLO11 support |
| YOLO11 | Model family `YOLO11`; baseline variant `YOLO11n` | MODEL FAMILY SELECTED, VERSION AND WEIGHTS PENDING | The exact model version, weight source, license, and file hash must be recorded; no implicit download or substitution is allowed | Resolve the model version and weight provenance, record the hash, and keep checkpoints outside Git |

## Compatibility Rules

1. Python, PyTorch, CUDA runtime, and Ultralytics must be validated as one
   combination, not selected independently.
2. The environment must be created with an exact package inventory before
   training. A mutable range such as `>=8.3,<9` is not an execution freeze.
3. CPU and GPU runs are distinct runtime profiles. A CPU diagnostic result
   must not be labelled as a GPU baseline.
4. The YOLO11 model name is not sufficient dataset or checkpoint identity.
   The exact model artifact, source, and SHA-256 are required.
5. Dataset fingerprints and the frozen class order are inputs to the training
   environment and must not be changed by dependency setup.
6. Any dependency change after a training run invalidates the environment
   fingerprint unless the change is recorded as a separate experiment
   environment.

## Version Freeze Gate

Before training is authorized, all rows in the matrix must move from
`PENDING` to `VERIFIED` with:

- exact package versions;
- the resolved Python interpreter;
- the device and driver inventory;
- an import smoke-test result that does not start training;
- the model weight source and hash; and
- a recorded environment snapshot.

No installation, download, or training is part of P2-0.
