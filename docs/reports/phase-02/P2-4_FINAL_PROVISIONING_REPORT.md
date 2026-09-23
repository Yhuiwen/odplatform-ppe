# P2-4 Final AutoDL Provisioning Report

> Date: 2026-09-22
>
> P2-4 FINAL STATUS: PASS
>
> Training: NOT STARTED
>
> Model weights: NOT DOWNLOADED
>
> Experiment: NOT EXECUTED / WAITING FOR TRAINING AUTHORIZATION

## 1. Instance Information

| Field | Value |
| --- | --- |
| Provider | AutoDL |
| Instance ID | `bcb849a74f-38320766` |
| Region | `bjb1` |
| GPU | NVIDIA GeForce RTX 4090 |
| VRAM | 24,564 MiB |
| GPU UUID | `GPU-ad5f1f4a-5bdb-4a26-9b62-5eb190196bb4` |
| OS | Ubuntu 20.04.5 LTS |
| Kernel | `5.15.0-97-generic` |
| NVIDIA driver | `560.35.03` |

## 2. Runtime Fingerprint

| Field | Value |
| --- | --- |
| Conda environment | `/root/miniconda3/envs/ppe-exp001` |
| Python | `3.10.21` |
| pip | `26.2.1` |
| PyTorch | `2.5.1+cu124` |
| torchvision | `0.20.1+cu124` |
| torchaudio | `2.5.1+cu124` |
| CUDA runtime | `12.4` |
| CUDA available | `True` |
| GPU detected by PyTorch | NVIDIA GeForce RTX 4090 |

The runtime fingerprint is recorded for `EXP-001` provisioning. It does not
grant training authorization.

## 3. Dependency Verification

| Dependency | Verified Version |
| --- | --- |
| Ultralytics | `8.4.157` |
| ultralytics-thop | `2.1.6` |
| OpenCV | `5.0.0.93` |
| NumPy | `2.2.6` |
| PyYAML | `6.0.3` |
| tqdm | `4.70.1` |
| matplotlib | `3.10.9` |
| psutil | `7.2.2` |

Planned Ultralytics `8.4.158` was unavailable from the configured package
index. The resolved and verified version is `8.4.157`; no forced downgrade or
unsafe package modification was performed.

## 4. Dataset Verification

| Field | Value |
| --- | --- |
| Dataset | `CSS-PPE-10-V1` |
| Mapping | `PPE-MAPPING-V1` |
| Remote path | `/root/autodl-tmp/datasets/css-ppe-10-v1/` |
| Transfer method | Recursive SCP without compression or restructuring |
| Images | `2799` |
| Labels | `2799` |
| Total files | `5604` |
| Train split | `2603` |
| Valid split | `114` |
| Test split | `82` |

Classes in frozen order:

```text
person
hardhat
no_hardhat
vest
no_vest
machinery
vehicle
```

Fingerprints:

```text
Source data.yaml:
5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34

Processed data.yaml:
45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a

Processed manifest file:
dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c

Full dataset manifest:
aeb7bb66906245e48ff92c43aecd66154b292d1c0bfdf5181bb43410ebe492cc
```

The remote metadata manifest verified 5,602 entries, and the full external
manifest verified all 5,604 files.

## 5. Safety Constraints

| Constraint | Result |
| --- | --- |
| `yolo train` executed | NO |
| `python train.py` executed | NO |
| Model weights downloaded | NO |
| Benchmark executed | NO |
| Evaluation executed | NO |
| Dataset labels modified | NO |
| `data.yaml` modified | NO |
| Annotation regeneration performed | NO |
| Class mapping changed | NO |
| EXP-001 configuration modified | NO |
| Credentials or private keys committed | NO |

## 6. Final Gate Status

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-4-G1 | Instance created | PASS |
| P2-4-G2 | Runtime fingerprint recorded | PASS |
| P2-4-G3 | Dependencies installed and verified | PASS |
| P2-4-G4 | Dataset transferred and verified | PASS |
| P2-4-G5 | Training not executed | PASS |
| P2-4-G6 | Charter unchanged | PASS |

```text
Environment: READY
Dataset:     READY
Training:    PENDING AUTHORIZATION
```

`P2-4 FINAL STATUS: PASS`
