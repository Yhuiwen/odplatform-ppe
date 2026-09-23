# P2-4-G3 Dependency Verification Report

> Date: 2026-09-22
>
> Status: PASS
>
> Training: NOT STARTED
>
> Dataset transfer: NOT PERFORMED
>
> Model weights: NOT DOWNLOADED

## Instance

| Field | Value |
| --- | --- |
| Instance ID | `bcb849a74f-38320766` |
| Provider | AutoDL |
| Region | `bjb1` |
| GPU | NVIDIA GeForce RTX 4090 |
| VRAM | 24,564 MiB |
| NVIDIA driver | `560.35.03` |
| CUDA driver API | 12.6 |
| GPU UUID | `GPU-ad5f1f4a-5bdb-4a26-9b62-5eb190196bb4` |
| OS | Ubuntu 20.04.5 LTS |
| Kernel | `5.15.0-97-generic` |
| Disk | 30 GiB overlay filesystem |

## Isolated Environment

| Field | Value |
| --- | --- |
| Conda environment | `ppe-exp001` |
| Environment path | `/root/miniconda3/envs/ppe-exp001` |
| Python | 3.10.21 |
| pip | 26.2.1 |
| Base environment modified | NO |

The base environment retains its pre-existing packages. All P2-4-G3 package
operations were performed inside `ppe-exp001`.

## Installed Stack

| Package | Installed Version |
| --- | --- |
| PyTorch | `2.5.1+cu124` |
| torchvision | `0.20.1+cu124` |
| torchaudio | `2.5.1+cu124` |
| Ultralytics | `8.4.157` |
| ultralytics-thop | `2.1.6` |
| OpenCV | `5.0.0.93` |
| NumPy | `2.2.6` |
| PyYAML | `6.0.3` |
| tqdm | `4.70.1` |
| matplotlib | `3.10.9` |
| psutil | `7.2.2` |

The P2-1 planned Ultralytics version `8.4.158` was not published by the
configured package index. P2-4-G3 therefore pinned the nearest published
release, `8.4.157`. This resolved version must be treated as the installed
environment version; it is not silently substituted back into the earlier
planning record.

## Verification

```text
torch: 2.5.1+cu124
torch_cuda: 12.4
cuda_available: True
gpu: NVIDIA GeForce RTX 4090
gpu_count: 1
ultralytics: 8.4.157
opencv: 5.0.0
numpy: 2.2.6
```

All required imports completed successfully. CUDA access is available to the
isolated environment.

## Safety Boundary

| Control | Result |
| --- | --- |
| Training command executed | NO |
| YOLO training started | NO |
| Dataset uploaded | NO |
| Pretrained weights downloaded | NO |
| Dataset or class mapping modified | NO |
| EXP-001 configuration modified | NO |
| Project source code modified | NO |

## Decision

`P2-4-G3 PASS`

The dependency layer is provisioned and verified. Environment freeze,
dataset-transfer verification, runtime fingerprint approval, and training
authorization remain separate gates.
