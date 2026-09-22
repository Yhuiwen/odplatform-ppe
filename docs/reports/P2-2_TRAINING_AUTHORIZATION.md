# P2-2 Training Authorization Checklist

> Date: 2026-09-22
>
> Overall authorization: NOT GRANTED
>
> Training execution: PROHIBITED
>
> P2-3 provider selection: COMPLETED / DESIGN ONLY

## Authorization Checklist

| Area | Status | Evidence |
| --- | --- | --- |
| Dataset | PASS | `CSS-PPE-10-V1` fingerprints remain unchanged; 2,799 images and 7 processed classes are frozen |
| Mapping | PASS | `PPE-MAPPING-V1` seven-class order remains unchanged |
| Experiment | PASS | `EXP-001` identity, model, dataset, output paths, logging paths, and metrics reviewed |
| Environment | DESIGN SELECTED / NOT PROVISIONED | P2-3 selects AutoDL with an RTX 4090 24GB design target; region, image ID, driver, and actual host remain unverified |
| Dependencies | PENDING | No dependency is installed and no lock or runtime fingerprint exists |
| GPU | DESIGN SELECTED / NOT VERIFIED | RTX 4090 24GB is the design target; no cloud GPU or NVIDIA driver has been provisioned or verified |
| Authorization | NOT GRANTED | Training cannot start in P2-2 |

## Blocking Conditions

1. Approve the P2-3 provider, GPU, region, image, cost, and retention policy.
2. Provision the isolated environment.
3. Install and verify the planned dependency stack without training.
4. Freeze the resolved environment and record a runtime fingerprint.
5. Resolve the model version, weight source, and weights SHA256.
6. Freeze seed, image size, batch, epochs, optimizer, learning rate,
   augmentation, device, and device strategy.
7. Obtain explicit training authorization.

## P2-2 Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P2-2-G1 | Cloud environment reviewed | PASS |
| P2-2-G2 | Dependencies reviewed | PASS |
| P2-2-G3 | EXP-001 reviewed | PASS |
| P2-2-G4 | Authorization checklist created | PASS |
| P2-2-G5 | No training executed | PASS |
| P2-2-G6 | Charter unchanged | PASS |

## Decision

`P2-2 COMPLETED`

P2-3 adds a provider selection record but does not change the authorization
state.

## P2-4 Provisioning Update

P2-4-G3 provisioned and verified the isolated AutoDL dependency environment,
and P2-4-G4 transferred and integrity-verified `CSS-PPE-10-V1` on the remote
host. The corresponding current states are:

| Area | Status | Evidence |
| --- | --- | --- |
| Dataset | PASS | P2-4-G4 report; 5,604-file transfer and full manifest verification |
| Mapping | PASS | Frozen seven-class order verified remotely |
| Experiment | PASS | EXP-001 identity remains unchanged |
| Environment | PROVISIONED | `ppe-exp001` on AutoDL instance `bcb849a74f-38320766` |
| Dependencies | INSTALLED / VERIFIED; FREEZE PENDING | P2-4-G3 report; no approved complete environment lock yet |
| GPU | VERIFIED | RTX 4090 visible to PyTorch; CUDA available |
| Authorization | NOT GRANTED | Environment freeze, weights, parameters, and explicit authorization remain outstanding |

Next Allowed Step: `WAIT FOR HUMAN TRAINING AUTHORIZATION`

Under the P2-4 update, no training, `YOLO(...).train(...)`, weight download,
dataset mutation, class mapping mutation, or frozen experiment identity change
was permitted. P2-5.2 separately registers the initialization weight; training
and all other prohibited operations remain blocked.

## P2-5.2 Weight Registration Update

P2-5.2 registered the official Ultralytics YOLO11n initialization checkpoint.
The binary remains Git-ignored; the version-controlled manifest records its
provenance and checksum.

| Area | Status | Evidence |
| --- | --- | --- |
| Configuration | FROZEN | P2-5.1 config freeze; canonical config SHA256 `df6c55ae...cacff989` |
| Weights | REGISTERED | `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml`; `models/pretrained/yolo11n.pt`; SHA256 `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` |
| Weight size | VERIFIED | `5,613,764` bytes |
| Weight source | VERIFIED | Ultralytics assets release `v8.3.0` |
| Remote training copy | NOT TRANSFERRED | The binary is registered locally and remains ignored by Git |
| Authorization | NOT GRANTED | Environment freeze and explicit human authorization remain outstanding |

Updated blocking conditions:

1. Approve the complete dependency lock/environment freeze.
2. Transfer the registered weight to the selected remote training environment
   under a separately authorized execution step.
3. Obtain explicit human training authorization.

Next Allowed Step: `WAIT FOR HUMAN TRAINING AUTHORIZATION`.

## P2-5.3 Dependency Freeze Update

P2-5.3 exported the resolved conda and pip environment and recorded the GPU,
driver, CUDA, and runtime fingerprint. The dependency-freeze blocker is now
resolved.

| Area | Status | Evidence |
| --- | --- | --- |
| Dependencies | FROZEN / VERIFIED | `locks/EXP-001/conda-environment.yml`, `conda-explicit.lock`, and `pip-freeze-all.txt`; `python -m pip check` PASS |
| Runtime | FROZEN / VERIFIED | `locks/EXP-001/runtime-fingerprint.yaml`; RTX 4090 UUID `GPU-ad5f1f4a...`; driver `560.35.03`; PyTorch CUDA runtime `12.4` |
| Weight | REGISTERED / REMOTE COPY NOT TRANSFERRED | P2-5.2 manifest remains unchanged |
| Authorization | NOT GRANTED | Remote weight transfer and explicit human authorization remain outstanding |

Updated blocking conditions:

1. Transfer and re-verify the registered `yolo11n.pt` in the remote training
   environment under separate authorization.
2. Obtain explicit human training authorization.

Next Allowed Step: `WAIT FOR HUMAN TRAINING AUTHORIZATION`.

## P2-5.4 Remote Weight Transfer Verification Update

The registered Ultralytics initialization weight was transferred to the
selected AutoDL environment and independently verified without executing the
checkpoint or starting training.

| Area | Status | Evidence |
| --- | --- | --- |
| Remote weight copy | VERIFIED | `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md`; `/root/autodl-tmp/models/pretrained/yolo11n.pt` |
| Remote weight size | VERIFIED | `5,613,764` bytes, matching the local artifact |
| Remote weight SHA256 | VERIFIED | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`, matching locally |
| Authorization | NOT GRANTED | Explicit human training authorization remains outstanding |

Updated blocking conditions:

1. Obtain explicit human training authorization.

Next Allowed Step: `WAIT FOR HUMAN TRAINING AUTHORIZATION`.

## P2-5.5 EXP-001 Training Execution Update

The user subsequently granted explicit one-run authorization for EXP-001.
Training completed and the authorization record was consumed.

| Area | Status | Evidence |
| --- | --- | --- |
| Authorization | GRANTED AND CONSUMED | `configs/training/exp001_authorization.yaml` |
| Training | COMPLETED | `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md` |
| Best checkpoint | PRODUCED / GIT-IGNORED | `models/checkpoints/EXP-001/best.pt`; SHA256 `1c144eef...871f61` |
| Second run | NOT AUTHORIZED | The one-run record is `CONSUMED` |

Next Allowed Step: `WAIT FOR PHASE 3 EVALUATION AUTHORIZATION`.
