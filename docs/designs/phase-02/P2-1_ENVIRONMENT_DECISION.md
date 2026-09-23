# P2-1 Training Environment Decision

> Date: 2026-09-22
>
> Environment Decision: SELECTED
>
> Selected Option: D. Controlled Cloud GPU
>
> Provisioning Status: NOT PROVISIONED
>
> Training Execution: PROHIBITED

## Decision

`EXP-001` will target a controlled cloud GPU environment running an
NVIDIA CUDA-capable Linux image. The architecture is selected, but no provider,
instance, runtime, dependency, model weight, or training job has been
provisioned or created.

The exact provider, GPU SKU, budget, region, and retention policy must be
approved during P2-2 before provisioning.

## Option Evaluation

| Option | Decision | Reason |
| --- | --- | --- |
| A. Current Windows CPU environment | Reject for EXP-001 baseline | The host has no NVIDIA GPU or CUDA support. CPU execution is not an equivalent YOLO11n baseline environment and would add substantial runtime and thermal risk. |
| B. Local NVIDIA GPU upgrade | Defer | Requires hardware procurement and a new validated Windows driver/wheel combination. The current host cannot provide the GPU. |
| C. WSL2 + NVIDIA CUDA | Defer | WSL2 does not create a GPU. It remains unavailable until the host has a supported NVIDIA GPU and validated Windows driver passthrough. |
| D. Controlled cloud GPU | Select | It is the only currently viable path to a reproducible GPU runtime without local hardware procurement. A pinned image and environment lock can make the runtime auditable. |

## Selection Rationale

Option D best satisfies the P2-0 criteria:

- it can provide an NVIDIA GPU and CUDA runtime without changing the current
  workstation;
- it avoids treating the current CPU-only host as a baseline-equivalent
  environment;
- it can be defined by an immutable container or VM image identifier;
- package, driver, and device evidence can be captured before training; and
- rollback can remove the instance without modifying the local repository or
  frozen dataset.

This selection does not resolve cost, provider, data-transfer, or credential
boundaries. Those remain P2-2 review items.

## Cost And Risk

| Area | Risk | Required Control |
| --- | --- | --- |
| Cost | Hourly GPU charges are unknown until a provider and SKU are selected | Approve a provider budget and maximum runtime before provisioning |
| Data transfer | The processed dataset must reach the cloud workspace without modifying the local snapshot | Transfer a read-only copy and re-verify the frozen fingerprints remotely |
| Provider drift | A mutable base image can invalidate reproducibility | Record the image digest, driver, CUDA runtime, package lock, and GPU identity |
| Credentials | Cloud and dataset credentials must not enter Git | Use environment variables or provider secret storage; never commit tokens |
| Retention | Checkpoints and logs require storage and deletion policy | Define artifact retention and cleanup before execution |
| Vendor access | The selected provider must meet the project's data-handling expectation | Review provider terms and region before uploading data |

## Impact On EXP-001

| Item | Impact |
| --- | --- |
| Dataset | No change; `CSS-PPE-10-V1` and all fingerprints remain frozen |
| Class mapping | No change; `PPE-MAPPING-V1` remains frozen |
| Experiment ID | No change; `EXP-001` remains the canonical baseline |
| Experiment configuration | No change; `execution_enabled` remains `false` |
| Device strategy | Still `PENDING_DESIGN_REVIEW`; P2-1 selects an architecture, not the final device field |
| Dependencies | Planned versions are documented in `P2-1_DEPENDENCY_SPECIFICATION.md`; dependency freeze remains pending |
| Training | Still prohibited until P2-2 authorization |

## Decision State

| Field | State |
| --- | --- |
| Environment architecture | `D. Controlled Cloud GPU` |
| Provisioning | `NOT STARTED` |
| Provider and GPU SKU | `PENDING P2-2` |
| Dependency freeze | `PENDING` |
| Training authorization | `NOT GRANTED` |
