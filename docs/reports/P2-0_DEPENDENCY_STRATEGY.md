# P2-0 Dependency Strategy

> Date: 2026-09-22
>
> Status: DESIGN ONLY / NOT INSTALLED
>
> Training execution: PROHIBITED

## Purpose

This document evaluates possible training environments for `EXP-001`
(`YOLO11n` on `CSS-PPE-10-V1`). It does not select or install a runtime,
download a checkpoint, change the frozen experiment configuration, or
authorize training.

The P2-1 step must resolve the environment choice and exact dependency
versions. Until then, all runtime and hyperparameter values remain governed by
the existing `PENDING_DESIGN_REVIEW` markers.

## Common Requirements

The selected environment must:

- run the frozen `yolov8`-exported dataset without modifying it;
- support a reproducible YOLO11n object-detection training run;
- provide a pinned, inspectable Python and package environment;
- record PyTorch, CUDA/runtime, Ultralytics, hardware, and driver evidence;
- retain a lock or exact resolved dependency inventory before execution;
- keep datasets, checkpoints, and run outputs outside Git; and
- preserve `configs/training/exp001_baseline.yaml` frozen fields and
  `execution_enabled: false` until execution is explicitly authorized.

## Environment Options

| Option | Advantages | Disadvantages And Risks | YOLO11n Suitability |
| --- | --- | --- | --- |
| A. Windows + NVIDIA GPU | Native use of the current repository; direct GPU access; simplest local operator workflow | Requires an NVIDIA GPU and a validated Windows driver/wheel combination; package and CUDA compatibility can differ from Linux; local GPU is not present on this host | Suitable when compatible NVIDIA hardware and exact pinned wheels are available. Not currently available on this host. |
| B. WSL2 + CUDA | Linux-oriented PyTorch and Ultralytics workflow; native repository access through `/mnt` or a mirrored workspace; can use a supported NVIDIA GPU | Requires Windows GPU passthrough, a compatible NVIDIA driver, WSL2 support, and careful filesystem/performance policy; local GPU is not present | Suitable only with validated NVIDIA hardware and WSL2 CUDA support. Not currently available on this host. |
| C. Cloud GPU | Provides a controlled GPU environment without local hardware; can make the runtime and driver easier to standardize | Adds cost, network transfer, data-handling, storage-retention, and remote-environment reproducibility risks; exact image, driver, package, and checkpoint provenance must be recorded | Suitable for YOLO11n training when the dataset transfer and runtime fingerprint are controlled. This is the realistic full-GPU path from the current host. |
| D. CPU fallback | No GPU provisioning required; can validate imports and a minimal smoke path | YOLO11n training would be substantially slower and may be thermally constrained; it is not equivalent to GPU training and may not be feasible for the baseline schedule or memory profile | Not recommended as the `EXP-001` baseline environment. A reduced CPU smoke test may be used only after separate authorization and must not be presented as the reproducible M-004 baseline. |

## Recommended Direction

P2-1 should choose either a local NVIDIA GPU environment (A or B, after
hardware provisioning) or a controlled cloud GPU environment (C). The current
host cannot satisfy A or B because no NVIDIA GPU or CUDA runtime is present.

CPU fallback remains a possible diagnostic path, but it is not the preferred
baseline training environment and does not resolve the current dependency or
GPU readiness boundary by itself.

## Dependency Boundary

The following operations remain prohibited in P2-0:

- installing PyTorch, Ultralytics, CUDA packages, or transitive dependencies;
- downloading `yolo11n.pt` or any other model checkpoint;
- changing the Python application's global package state;
- modifying the processed dataset or its fingerprints; or
- enabling or executing the training entry point.

P2-1 may perform environment setup only under a new explicit instruction. It
must use an isolated environment where feasible, record the exact installation
commands and resolved dependency versions, and verify imports without running
training.

## Decision State

| Field | State |
| --- | --- |
| Preferred architecture | Local NVIDIA GPU or controlled cloud GPU |
| Local Windows NVIDIA path | NOT AVAILABLE on the audited host |
| WSL2 CUDA path | NOT AVAILABLE on the audited host |
| Cloud GPU path | AVAILABLE by design, not provisioned |
| CPU fallback | DIAGNOSTIC ONLY / NOT SELECTED |
| Final environment selection | PENDING P2-1 |
| Installation performed | NO |
| Training performed | NO |
