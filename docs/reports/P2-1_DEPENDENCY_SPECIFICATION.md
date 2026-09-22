# P2-1 Dependency Specification

> Date: 2026-09-22
>
> State: PLANNED VERSION / NOT INSTALLED
>
> Target: Controlled Linux cloud GPU with NVIDIA CUDA
>
> Training execution: PROHIBITED

## Purpose

This document records the candidate dependency stack for `EXP-001`. Published
package metadata was inspected, but nothing was installed and no package was
downloaded. Every row remains a planned version until P2-2 authorizes
provisioning and verification.

## Planned Runtime

| Component | Planned Version | State | Compatibility Basis |
| --- | --- | --- | --- |
| Operating system | Ubuntu 22.04 LTS x86_64 | PLANNED | Stable CUDA-capable cloud image base; exact image digest must be recorded |
| Python | `3.11.16` | PLANNED VERSION | Compatible with the selected PyTorch and Ultralytics package requirements |
| pip | `25.3` | PLANNED VERSION | Used for the isolated environment and recorded package lock |
| PyTorch | `2.11.0+cu128` | PLANNED VERSION | Official Linux x86_64 CUDA 12.8 wheel is published for CPython 3.11 |
| CUDA runtime | `12.8` | PLANNED VERSION | Matched to the PyTorch `cu128` wheel; the wheel supplies its runtime libraries |
| torchvision | `0.26.0+cu128` | PLANNED VERSION | Its metadata requires exactly `torch==2.11.0` |
| Ultralytics | `8.4.158` | PLANNED VERSION | Requires Python `>=3.8`, `torch>=1.8.0`, and `torchvision>=0.9.0` |
| NumPy | `2.2.6` | PLANNED VERSION | Satisfies Ultralytics `>=1.23.0` and OpenCV `>=2,<2.3` |
| opencv-python | `4.12.0.88` | PLANNED VERSION | Compatible with Python 3.11 and NumPy below `2.3` |
| Pillow | `12.3.0` | PLANNED VERSION | Requires Python `>=3.10` |
| PyYAML | `6.0.3` | PLANNED VERSION | Requires Python `>=3.8` |
| psutil | `7.2.2` | PLANNED VERSION | Requires Python `>=3.6` |
| ultralytics-thop | `2.1.6` | PLANNED VERSION | Required by the planned Ultralytics release |
| ultralytics-platform | `0.1.54` | PLANNED VERSION | Requires Python `>=3.11` and satisfies the planned Ultralytics constraint |

All transitive packages must be captured in an exact environment lock during
P2-2. The table is a candidate specification, not an installed environment
fingerprint.

## Planned Wheel Evidence

| Artifact | SHA256 |
| --- | --- |
| `torch-2.11.0+cu128-cp311-cp311-manylinux_2_28_x86_64.whl` | `c9a7ca4c74fae10a58e6175b4b2cea953f9322bb6562bbf339ad6a05f52190ad` |
| `torchvision-0.26.0+cu128-cp311-cp311-manylinux_2_28_x86_64.whl` | `8f2629d056570c929b0a1d5473d9cb0320b90bda1764bda353553a72cc6b2069` |

These hashes are evidence for the planned wheels. They do not mean the wheels
were downloaded in P2-1.

## Compatibility Constraints

1. PyTorch and torchvision must come from the same CUDA 12.8 package index.
2. Python, PyTorch, torchvision, NumPy, and OpenCV must be installed as one
   locked set.
3. The cloud host must expose a CUDA-compatible NVIDIA driver. The exact
   minimum driver version must be verified against the selected base image.
4. Ultralytics must be checked for YOLO11 model-family support before any
   training command is enabled.
5. The model weight is not a dependency to be fetched implicitly. Its source,
   license, version, and SHA256 remain a separate P2-2 item.
6. Installing a newer version after freeze requires a new environment record
   and invalidates the previous runtime fingerprint.

## Current Installation State

| Check | State |
| --- | --- |
| Python 3.11.16 installed | NO |
| PyTorch installed | NO |
| torchvision installed | NO |
| CUDA runtime available | NO |
| Ultralytics installed | NO |
| Environment lock created | NO |
| Training weight downloaded | NO |

## Future Freeze Output

P2-2 must produce a machine-readable environment lock containing:

- cloud image identifier and image digest;
- GPU model, UUID, memory, and driver version;
- Python executable and exact version;
- exact package versions and wheel hashes;
- `pip freeze --all` output;
- import and CUDA visibility results;
- the frozen dataset fingerprints; and
- the canonical EXP-001 configuration hash.

No package installation is performed in P2-1.
