# P2-1 Environment Setup Plan

> Date: 2026-09-22
>
> Status: DESIGN ONLY
>
> Installation action: NOT AUTHORIZED
>
> Training execution: PROHIBITED

## Scope

This plan defines how to provision and verify the selected controlled cloud
GPU environment after P2-2 authorization. None of the steps below were
executed during P2-1.

The setup must not modify `CSS-PPE-10-V1`, `PPE-MAPPING-V1`, the processed
dataset, or any frozen fingerprint.

## Preconditions

1. P2-2 approves the provider, region, GPU SKU, maximum runtime, and cost.
2. The provider image is immutable and its identifier or digest is recorded.
3. The project commit and EXP-001 configuration hash are frozen.
4. The dataset transfer plan preserves the local immutable snapshot.
5. Credentials are supplied through environment variables or provider secrets,
   never committed to Git.
6. The training entry point remains disabled until release authorization.

## Target Cloud Profile

| Resource | Planned Minimum |
| --- | --- |
| Operating system | Ubuntu 22.04 LTS x86_64 |
| GPU | NVIDIA CUDA-capable, `16 GB` VRAM minimum |
| System RAM | `32 GB` preferred, `16 GB` minimum |
| CPU | `4` vCPU minimum |
| Storage | `100 GB` persistent workspace recommended |
| Driver | NVIDIA driver compatible with the CUDA 12.8 PyTorch wheel |
| Network | HTTPS access to PyPI and the official PyTorch wheel index during one-time setup |

The GPU SKU and driver are not selected in P2-1. A T4-16GB or newer L4/A10
class GPU is sufficient at the design level for YOLO11n, but the exact SKU
must be reviewed against cost and image availability.

## Setup Procedure

### Step 1: Provision The Isolated Host

1. Create a provider instance from a recorded Ubuntu 22.04 LTS image.
2. Confirm the image digest, region, GPU identity, driver, RAM, CPU, and disk.
3. Create a non-root workspace user.
4. Confirm no model checkpoint is present before project setup.

### Step 2: Create The Project Workspace

1. Obtain the repository version approved for environment setup.
2. Create an isolated environment at `.venv/`.
3. Keep datasets, checkpoints, logs, and run output outside Git-ignored
   content boundaries.
4. Never edit, remap, resplit, resize, or delete the processed dataset.

Planned environment commands, to run only after authorization:

```text
python3.11 -m venv .venv
python -m pip install --upgrade pip==25.3
```

### Step 3: Install The Planned GPU Stack

Install PyTorch and torchvision first from the official CUDA 12.8 index:

```text
python -m pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.11.0+cu128 torchvision==0.26.0+cu128
```

Then install the pinned application and training dependencies:

```text
python -m pip install ultralytics==8.4.158 numpy==2.2.6 opencv-python==4.12.0.88 Pillow==12.3.0 PyYAML==6.0.3 psutil==7.2.2 ultralytics-thop==2.1.6 ultralytics-platform==0.1.54
```

The actual installation must use a constraints or lock file generated from
the approved plan. If a resolver changes a pinned direct dependency, stop and
return to dependency review.

### Step 4: Prepare Data Read-Only

1. Upload or mount a read-only copy of `CSS-PPE-10-V1`.
2. Recompute source `data.yaml`, source manifest, and processed manifest
   SHA256 values.
3. Compare them with `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml`.
4. Confirm seven classes in `PPE-MAPPING-V1` order.
5. Stop if any fingerprint or class order differs.

### Step 5: Verify Without Training

Run only non-training checks:

```text
nvidia-smi
python -c "import sys; print(sys.version)"
python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO_CUDA')"
python -c "import torchvision; print(torchvision.__version__)"
python -c "import ultralytics; print(ultralytics.__version__)"
python -c "import numpy, cv2; print(numpy.__version__); print(cv2.__version__)"
```

These checks must not invoke `YOLO(...)`, `model.train(...)`, `model.val(...)`,
or a download command for `yolo11n.pt`.

### Step 6: Freeze The Runtime

Record:

- provider instance and image identifiers;
- GPU model, UUID, memory, and driver;
- CUDA runtime and PyTorch build;
- Python and every package version;
- `pip freeze --all` output;
- wheel hashes;
- import and CUDA visibility results;
- dataset contract hashes; and
- EXP-001 configuration hash.

The runtime fingerprint must be stored with the experiment record before P2-2
authorization review.

## Rollback

| Stage | Rollback |
| --- | --- |
| Before provisioning | No action required |
| After instance creation | Destroy the instance and attached temporary volume according to the retention policy |
| After Python environment creation | Delete `.venv/`; no global Python packages are changed |
| After package installation | Recreate the environment from the recorded lock |
| After failed data verification | Stop and destroy the remote data copy; never modify local source data |
| After any accidental training start | Stop immediately, preserve logs, and report a governance violation; do not continue or claim the run as EXP-001 |

## Freeze Outputs Required Before P2-2

| Output | State |
| --- | --- |
| Planned dependency specification | DOCUMENTED |
| Setup plan | DOCUMENTED |
| Cloud provider and GPU SKU | PENDING P2-2 |
| Installed environment lock | PENDING |
| Runtime fingerprint | PENDING |
| Model weight source and hash | PENDING |
| Training authorization | NOT GRANTED |
