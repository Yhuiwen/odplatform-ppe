# P2-3 Cloud Provider Selection Report

> Date: 2026-09-22
>
> Status: COMPLETED / DESIGN SELECTION COMPLETE
>
> Provisioning: NOT STARTED
>
> Training authorization: NOT GRANTED

## Purpose

This report completes the provider and cost review required before the P2-1
controlled cloud GPU setup can be provisioned. It compares providers using
public product documentation and planning estimates. It does not create an
instance, install a dependency, download a model weight, transfer the dataset,
or authorize training.

All costs below are planning envelopes, not provider quotations. The live
provider price, availability, image identity, and driver version must be
recorded and approved before provisioning.

## Decision Summary

| Field | Decision |
| --- | --- |
| Provider strategy | AutoDL primary |
| Provider status | SELECTED / NOT PROVISIONED |
| GPU | NVIDIA GeForce RTX 4090 24GB |
| Fallback GPU | RTX 3090 24GB contingency only; it is not the same frozen runtime |
| Region | Select at provisioning from hosts exposing the required GPU and Ubuntu 20.04 image; record region and host ID |
| Operating system | Ubuntu 20.04 LTS x86_64, or a provider image that exposes an equivalent glibc 2.31+ Linux userland |
| Python | 3.11.16 |
| CUDA runtime | 12.8 via the PyTorch `cu128` wheel |
| PyTorch | 2.11.0+cu128 |
| torchvision | 0.26.0+cu128 |
| Ultralytics | 8.4.158 |
| NumPy | 2.2.6 |
| Dependency freeze | PENDING until the isolated environment is actually installed and locked |
| Maximum planning runtime | 40 GPU-hours before a new budget approval |
| Compute budget ceiling | CNY 150 for the AutoDL path, subject to live-price verification |

The Ubuntu 20.04 minimum is intentional: the planned `manylinux_2_28` PyTorch
wheel requires glibc 2.28 or newer. AutoDL documentation states that its base
images are Ubuntu but that most are Ubuntu 18.04 and a smaller subset are
Ubuntu 20.04. An Ubuntu 18.04 image is not acceptable for this runtime unless
the exact wheel and runtime compatibility are independently proven.

## Candidate Provider Review

### AutoDL

| Item | Review Result |
| --- | --- |
| GPU model | RTX 4090 24GB primary; RTX 3090 24GB contingency |
| VRAM | 24GB |
| CUDA support | Provider documents newer CUDA 12.8/PyTorch images and requires CUDA 11.1+ for RTX 40-series hardware |
| Ubuntu image | Provider images are Ubuntu; require Ubuntu 20.04 or newer-equivalent userland and record the exact image identifier |
| Cost estimate | Planning envelope up to CNY 3/hour for the RTX 4090 path; 40 GPU-hours plus storage is capped at CNY 150 pending live-price verification |
| Data upload | Use provider netdisk transfer or SCP/FileZilla for a compressed, immutable `CSS-PPE-10-V1` payload only; re-verify SHA-256 after extraction |
| Retention | Instance data is retained while the instance exists; a continuously powered-off instance is documented for release after 15 days |
| Main advantages | Lowest planning cost, 24GB VRAM, Linux/CUDA workflow, simple Chinese-network data transfer, and sufficient capacity for YOLO11n |
| Main risks | Base-image version may not be cryptographically pinned; available hosts and prices are dynamic; no Docker inside a standard container instance; local data disks do not carry a provider reliability guarantee; instance release and paid storage require explicit cleanup |

### Alibaba Cloud GPU ECS

| Item | Review Result |
| --- | --- |
| GPU model | GN7i A10 family; A10 24GB is the design-level equivalent |
| VRAM | 24GB |
| CUDA support | Provider permits NVIDIA driver and CUDA installation; exact driver/image combination must be verified |
| Ubuntu image | Ubuntu 22.04 LTS x86_64 is available through ECS image selection and can be pinned more formally |
| Cost estimate | Planning envelope CNY 10-25/hour; a 40-hour run plus storage/transfer is capped at CNY 1,200 pending a current quotation |
| Data upload | ECS public endpoint, private network, or OSS transfer; security-group and credential review required |
| Main advantages | Strong image/instance identity controls, mature networking, enterprise controls, and predictable support boundaries |
| Main risks | Much higher cost than AutoDL, more provisioning complexity, storage and egress charges, quota availability, and unnecessary operational overhead for a YOLO11n baseline |

### Tencent Cloud GPU

| Item | Review Result |
| --- | --- |
| GPU model | GN7 A10 24GB or GN7 T4 16GB |
| VRAM | A10 24GB or T4 16GB |
| CUDA support | Provider documents NVIDIA A10/T4 GPU instances and requires the selected Tesla driver plus CUDA stack |
| Ubuntu image | Ubuntu images can be selected; exact image ID and driver compatibility must be recorded |
| Cost estimate | Planning envelope CNY 8-30/hour depending on GPU and billing; a 40-hour run plus storage/transfer is capped at CNY 1,500 pending a current quotation |
| Data upload | CVM endpoint or cloud storage transfer with security-group review |
| Main advantages | Strong enterprise controls and multiple GPU choices |
| Main risks | Higher cost, quota and network setup, billing complexity, and a T4 16GB fallback that is slower and offers less memory headroom |

### Other Options

RunPod or Vast.ai can provide a 24GB RTX 4090 at a lower international
planning rate, commonly in the USD 0.35-0.80/hour range before storage and
transfer. They remain fallbacks rather than the selected path because
cross-border payment, account provisioning, network variability, host
heterogeneity, and data-transfer latency add avoidable operational risk for
this project. Lambda and similar managed GPU services have comparable
reproducibility benefits but are not cost-effective for a single small-model
baseline.

## Cost And Retention Controls

The cost envelope assumes up to 40 GPU-hours for environment setup, a
non-training smoke test, EXP-001 baseline execution, and short verification.
It does not authorize those actions by itself.

1. Do not provision if the live RTX 4090 price exceeds CNY 3/hour without a
   new human approval.
2. Keep the project payload below the provider's free storage allowance where
   possible; upload only the processed dataset and required source code.
3. Download checkpoints, logs, metrics, configuration snapshots, and runtime
   fingerprints before releasing the instance.
4. Delete the remote dataset copy and temporary volumes after verification.
5. Do not upload teacher assets, `history.db`, credentials, `.env` files, or
   model weights supplied by another party.
6. Record the provider region, host ID, image ID or digest, GPU UUID, driver,
   CUDA runtime, package lock, and storage policy before training.

## Dataset Transfer Boundary

Only the immutable `CSS-PPE-10-V1` processed payload may be uploaded after
authorization. The transfer archive must preserve source-relative paths.
After extraction on the cloud host, the source `data.yaml`, source manifest,
and processed manifest SHA-256 values must be recomputed and compared with the
training contract. Any mismatch stops the environment setup and invalidates the
remote copy.

No dataset file, fingerprint, class mapping, or frozen EXP-001 field may be
modified during provisioning.

## Training Authorization Impact

P2-3 selects the provider and design target but does not satisfy the GPU
provisioning or dependency-freeze requirements. The P2-2 authorization record
therefore remains:

| Field | State |
| --- | --- |
| Dataset | PASS |
| Mapping | PASS |
| Experiment | PASS |
| Environment | DESIGN SELECTED / NOT PROVISIONED |
| Dependencies | PENDING |
| GPU | DESIGN SELECTED / NOT VERIFIED |
| Authorization | NOT GRANTED |

Training remains prohibited until a separate explicit authorization is issued.

## Required Next Decision

`WAIT FOR HUMAN TRAINING AUTHORIZATION`

Before that decision, the human reviewer must approve the selected provider,
live price, region/host, image identity, driver, storage, retention policy, and
the maximum runtime. Provisioning, installation, data transfer, weight
resolution, and training are all outside P2-3.

## Public Evidence

Accessed 2026-09-22:

- AutoDL GPU selection: https://www.autodl.com/docs/gpu/
- AutoDL base images and CUDA matrix: https://www.autodl.com/docs/base_config/
- AutoDL data retention: https://www.autodl.com/docs/instance_data/
- AutoDL billing rules: https://www.autodl.com/docs/price/
- Alibaba Cloud GN7i product overview: https://help.aliyun.com/zh/ecs/product-overview/gpu-accelerated-compute-optimized-gn7i
- Tencent Cloud GPU instance selection: https://cloud.tencent.com/document/product/560/19700

The cost figures are planning envelopes derived from these public product
classes and common market rates. They are not current quotations and must be
replaced by provider-console evidence at provisioning time.
