# P2-2 Cloud Environment Review

> Date: 2026-09-22
>
> Review status: COMPLETED
>
> Environment selection: PENDING_SELECTION
>
> Provisioning: NOT STARTED
>
> Training authorization: NOT GRANTED

## Purpose

This review identifies every provider-specific decision required before the
P2-1 controlled cloud GPU plan can be executed. Selecting the cloud GPU
architecture in P2-1 did not select a provider, region, GPU SKU, image, budget,
or retention policy.

No cloud resource was created or modified during this review.

## Cloud GPU Review

| Item | Review Result |
| --- | --- |
| Provider | `PENDING_SELECTION` |
| Region | `PENDING_SELECTION` |
| GPU | `PENDING_SELECTION`; design minimum is a CUDA-capable NVIDIA GPU |
| VRAM | `PENDING_SELECTION`; design minimum is `16 GB` |
| CUDA capability | `PENDING_SELECTION`; must support the planned CUDA 12.8 PyTorch wheel |
| OS image | `PENDING_SELECTION`; planned target is Ubuntu 22.04 LTS x86_64 with a recorded image digest |
| Storage | `PENDING_SELECTION`; recommended minimum is `100 GB` |
| Cost estimate | `PENDING_SELECTION`; hourly rate, maximum runtime, and total budget require approval |
| Retention policy | `PENDING_SELECTION`; checkpoint, log, dataset-copy, and volume deletion rules require approval |

## Required Provider Decisions

Before provisioning, the P2-1 setup plan requires:

1. provider and region;
2. exact GPU model and VRAM;
3. CUDA-compatible NVIDIA driver version;
4. immutable OS image identifier and digest;
5. persistent storage size and attachment policy;
6. hourly cost, maximum runtime, and budget ceiling;
7. data-upload and deletion policy;
8. artifact retention period; and
9. secret-management mechanism.

## Risk Assessment

| Risk | Current State | Required Control |
| --- | --- | --- |
| Provider lock-in | Unselected | Keep setup and experiment records portable |
| Driver mismatch | Unselected | Verify the image driver against the CUDA 12.8 wheel before installation |
| Image drift | No digest recorded | Pin the image by immutable identifier or digest |
| Cost overrun | No budget recorded | Set a maximum runtime and cost ceiling |
| Dataset exposure | No cloud copy exists | Use a private volume and delete it when no longer required |
| Credential leakage | No cloud credentials created | Use provider secrets or environment variables only |
| Output loss | No retention policy | Define checkpoint and report persistence before execution |

## Authorization Impact

Environment review is complete as a governance activity, but the environment
is not authorized for provisioning or training:

| Field | State |
| --- | --- |
| Architecture selected | YES, controlled cloud GPU |
| Provider selected | NO |
| Instance provisioned | NO |
| Environment frozen | NO |
| Training authorized | NO |

The cloud environment remains a blocking prerequisite for training. It does
not block generation of this review document.

## Required Next Decision

`WAIT FOR TRAINING AUTHORIZATION`

The next user decision must provide or approve the provider-specific values
listed above. Until then, P2-1 setup must not be executed.
