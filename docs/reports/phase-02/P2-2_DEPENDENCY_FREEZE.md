# P2-2 Dependency Freeze Review

> Date: 2026-09-22
>
> Freeze status: PENDING
>
> Installation status: NOT INSTALLED
>
> Training authorization: NOT GRANTED

## Review Result

The dependency specification from P2-1 is a planned compatibility set, not an
installed environment. No package was installed, no wheel was downloaded, and
no runtime fingerprint or dependency lock exists.

## Frozen Dependency Candidates

| Component | Planned Version | Installed | Freeze Status |
| --- | --- | --- | --- |
| Python | `3.11.16` | NO | `PENDING` |
| PyTorch | `2.11.0+cu128` | NO | `PENDING` |
| CUDA runtime | `12.8` | NO | `PENDING` |
| torchvision | `0.26.0+cu128` | NO | `PENDING` |
| Ultralytics | `8.4.158` | NO | `PENDING` |
| NumPy | `2.2.6` | NO | `PENDING` |

Supporting planned dependencies also remain `PENDING`: `opencv-python`
`4.12.0.88`, Pillow `12.3.0`, PyYAML `6.0.3`, psutil `7.2.2`,
ultralytics-thop `2.1.6`, and ultralytics-platform `0.1.54`.

## Freeze Evidence

| Evidence | State |
| --- | --- |
| Cloud image digest | NOT AVAILABLE |
| GPU model and UUID | NOT AVAILABLE |
| NVIDIA driver version | NOT AVAILABLE |
| CUDA build reported by PyTorch | NOT AVAILABLE |
| Python executable fingerprint | NOT AVAILABLE |
| Exact package lock | NOT CREATED |
| Wheel hashes verified locally | NO |
| Import smoke test | NOT RUN |
| CUDA visibility smoke test | NOT RUN |
| Dataset-contract snapshot | Frozen locally |

## Freeze Decision

`Dependency Freeze: PENDING`

The dependency set cannot be marked `FROZEN` until:

1. the cloud provider and host are selected;
2. the selected packages are installed in an isolated environment;
3. all transitive versions are resolved and locked;
4. import and CUDA-visibility checks pass without training;
5. the GPU, driver, image, and package evidence is recorded; and
6. the frozen dataset and EXP-001 configuration hashes are captured together
   with the runtime fingerprint.

No dependency installation or training is authorized by this review.

## P2-5.3 Resolution

P2-5.3 subsequently captured the resolved AutoDL environment and runtime:

| Field | Frozen value |
| --- | --- |
| Instance | AutoDL `bcb849a74f-38320766`, region `bjb1` |
| GPU | NVIDIA GeForce RTX 4090, `24,564 MiB` |
| GPU UUID | `GPU-ad5f1f4a-5bdb-4a26-9b62-5eb190196bb4` |
| Driver / driver API | `560.35.03` / CUDA `12.6` |
| PyTorch CUDA runtime | `12.4` |
| Python | `3.10.21` |
| PyTorch / torchvision / torchaudio | `2.5.1+cu124` / `0.20.1+cu124` / `2.5.1+cu124` |
| Ultralytics | `8.4.157` |
| Conda environment lock | `locks/EXP-001/conda-environment.yml` |
| Conda explicit lock | `locks/EXP-001/conda-explicit.lock` |
| pip freeze lock | `locks/EXP-001/pip-freeze-all.txt` |
| Runtime fingerprint | `locks/EXP-001/runtime-fingerprint.yaml` |

The exported locks match the live remote output and `python -m pip check`
reports no broken requirements. `Dependency Freeze: FROZEN`.

This update does not grant training authorization.
