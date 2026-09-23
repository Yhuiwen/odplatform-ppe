# P2-7 EXP-001 Training Result Freeze Report

> Date: 2026-09-22
> Status: FROZEN / COMPLETED
> Current Phase: P2-7 Training Result Freeze
> EXP-001 Training: COMPLETED
> Phase 3: NOT STARTED

## Scope and evidence

This freeze archives the completed EXP-001 result by reading existing local artifacts.
No training, evaluation, inference, dataset mutation, mapping change, or remote
runtime startup was performed. M-004 retains its existing completed status;
M-005 remains pending. No commit or push is authorized or performed.

The P2-6 authorization request is at `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md`
(no root-level copy exists). Its NOT GRANTED state, and the P2-5 freeze reports,
are historical preparation records. The execution report and consumed external
authorization record establish the later completed run; this freeze does not
rewrite those historical records or grant another run.

Inputs reviewed:

- `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md`
- `docs/reports/P2-6_TRAINING_AUTHORIZATION_REQUEST.md`
- `P2-5.1_CONFIGURATION_FREEZE_REPORT.md`
- `P2-5.2_WEIGHT_REGISTRATION_REPORT.md`
- `P2-5.3_DEPENDENCY_FREEZE_REPORT.md`
- `docs/02_CURRENT_STATUS.md`
- `configs/training/exp001_baseline.yaml`

## Frozen identity

| Field | Value |
| --- | --- |
| Experiment ID | EXP-001 |
| Model | YOLO11n / Ultralytics 8.4.157 / Project-trained Model |
| Dataset identity | CSS-PPE-10-V1; Roboflow roboflow-universe-projects/construction-site-safety v27; yolov8 |
| Mapping | PPE-MAPPING-V1 / Strategy C |
| Images and splits | 2,799; train 2,603 / valid 114 / test 82 |
| Class order | person, hardhat, no_hardhat, vest, no_vest, machinery, vehicle |
| Seed | 42 |
| Config SHA256 | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` |
| Initial weight SHA256 | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` |
| Best checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Processed data.yaml SHA256 | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` |
| Mapping contract SHA256 | `7003f87af9cc8ad5ce7f8c58dffb25f43ab4bb533d0df1fba7033164a6ff40c7` |
| Class mapping metadata SHA256 | `e539bc831526f1532d12870053f827c0f0f37659de0d8964b6443ab9d505870d` |
| source_data_yaml_sha256 | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| source_manifest_sha256 | `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795` |
| processed_manifest_sha256 | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |
| Best epoch | 75 (one-based) |
| Completed / configured epochs | 95 / 100 |
| Stop reason | Early stopping, patience 20 |
| Best checkpoint size | 5,479,891 bytes |
| Started at UTC | 2026-09-22T08:00:02.209838+00:00 |
| Finished at UTC | 2026-09-22T08:19:29.543992+00:00 |
| Training duration (whole command) | 1167.334154 seconds; approximately 19 minutes 27 seconds |
| Epoch-loop duration | 835.678 seconds; log reports 0.232 hours |

Wall-clock duration includes startup and final training-workflow validation.
Epoch-loop time is recorded separately and is not the total command duration.

## Final metrics

These are existing final best.pt validation results from the completed training
workflow, on 114 validation images and 558 instances. Values preserve the
training log rounding. They are not a new evaluation or Phase 3 acceptance.

| Class | Precision | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| all | 0.899 | 0.649 | 0.767 | 0.480 |
| person | 0.935 | 0.693 | 0.797 | 0.515 |
| hardhat | 0.945 | 0.722 | 0.819 | 0.526 |
| no_hardhat | 0.843 | 0.522 | 0.634 | 0.327 |
| vest | 0.966 | 0.689 | 0.888 | 0.555 |
| no_vest | 0.862 | 0.604 | 0.739 | 0.461 |
| machinery | 0.979 | 0.835 | 0.924 | 0.636 |
| vehicle | 0.761 | 0.476 | 0.564 | 0.337 |

Recorded speed: preprocessing 0.7 ms, inference 12.3 ms, postprocessing 0.4 ms
per image on the recorded RTX 4090. No speed measurement was repeated.

The last epoch (95) CSV row is a separate result: precision 0.85966, recall
0.68461, mAP50 0.75966, mAP50-95 0.47044. It does not replace the final best.pt
metrics above or change the recorded best epoch.

## Runtime fingerprint

| Field | Value |
| --- | --- |
| Provider / region / instance | `AutoDL / bjb1 / bcb849a74f-38320766` |
| OS / kernel | `Ubuntu 20.04.5 LTS / Linux 5.15.0-97-generic x86_64 GNU/Linux` |
| GPU | `NVIDIA GeForce RTX 4090 / 24564 MiB / compute capability 8.9` |
| GPU UUID | `GPU-ad5f1f4a-5bdb-4a26-9b62-5eb190196bb4` |
| Driver / CUDA API / PyTorch CUDA / cuDNN | `560.35.03 / 12.6 / 12.4 / 90100` |
| Environment | `/root/miniconda3/envs/ppe-exp001` |
| Python / PyTorch / torchvision / torchaudio | `3.10.21 / 2.5.1+cu124 / 0.20.1+cu124 / 2.5.1+cu124` |
| Ultralytics / OpenCV / NumPy | `8.4.157 / 5.0.0.93 / 2.2.6` |
| Runtime fingerprint SHA256 | `f5f8240d2225219743e0fc3a310a174e5583d0dd405b2ecc315b0433eefbf7aa` |

| Dependency lock | SHA256 |
| --- | --- |
| `locks/EXP-001/conda-environment.yml` | `95b03d3dfc57f4124dcf370b9bd42cadab86f1701649d3610824c74a86f88fc3` |
| `locks/EXP-001/conda-explicit.lock` | `599ed7c0e6b9ee9817517d140488c382066fc2e9d7e2a14315deefb43f3438d5` |
| `locks/EXP-001/pip-freeze-all.txt` | `34c9b668095029732f1c4c084b81185309c64614fe25e88b69328e1f9b91599e` |

This is the recorded training runtime, not the local Windows verification
environment. Lock hashes were rechecked locally; the remote host was not
restarted or contacted. The provider exposes no immutable image digest.

## Artifact inventory

Every file below was found locally and independently SHA256-hashed. All remain
Git-ignored and untracked. Paths are relative to the repository; remote run paths
use `/root/autodl-tmp/odplatform-ppe/` as recorded in run_record.yaml.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `models/checkpoints/EXP-001/best.pt` | 5479891 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `models/checkpoints/EXP-001/last.pt` | 5479891 | `acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88` |
| `experiments/runs/EXP-001/args.yaml` | 1793 | `c886ab6a206feb7744d66f3dfa1c5ae91d4d4620f77531707f5b70983d744e3d` |
| `experiments/runs/EXP-001/BoxF1_curve.png` | 300469 | `31ec9b7a52613f7c96faee4dc168d1be59d6b325eb826ef2f06e24d01f9b48f0` |
| `experiments/runs/EXP-001/BoxP_curve.png` | 236670 | `f7b1fed611114347c6b20cbe726017ba193514fc7b48607fcf28984753a2bc3b` |
| `experiments/runs/EXP-001/BoxPR_curve.png` | 195264 | `4f5ba6e6001e7267abb3ce50adfa65b80fef1dcb29520072b3fbe741b2ad6e4c` |
| `experiments/runs/EXP-001/BoxR_curve.png` | 246650 | `7a2ba0de5371c2c5a856e9da5d63bd32540fe46495b2ca9334796a002c27f2cb` |
| `experiments/runs/EXP-001/confusion_matrix.png` | 173668 | `8166e9780d63fc61071c7baa7c06cc2bc22400713cb36fba734ba72b40d8917d` |
| `experiments/runs/EXP-001/confusion_matrix_normalized.png` | 213691 | `1559a4c48bd095a10df7453a40349af99c00b0e964ca32c91fb957000848a1a1` |
| `experiments/runs/EXP-001/exp001_baseline.frozen.yaml` | 1618 | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` |
| `experiments/runs/EXP-001/labels.jpg` | 186928 | `9cda8b408bf4034a6022422cf569520c7cc95ec815035a5b83783c5dcdf1df03` |
| `experiments/runs/EXP-001/results.csv` | 12090 | `3aafff966f4b7a851e1f9e1051aa928627c0a93e155c44611fd0fc4ee78e6d87` |
| `experiments/runs/EXP-001/results.png` | 273825 | `96b9446902513f3222f838626669791e4309837f071efad5fb0090eede4c9a25` |
| `experiments/runs/EXP-001/train_batch0.jpg` | 735835 | `f8b175fa287792a68d748ea74a1c9d2317611406543d65ab93bce193accffb97` |
| `experiments/runs/EXP-001/train_batch1.jpg` | 712788 | `68348afe2514368e22d7a95e019bc7b99307fcab3789c8beeaa572186f17ed58` |
| `experiments/runs/EXP-001/train_batch14670.jpg` | 603942 | `695895db868fbf21a14fe8bd28deea392acc1e2c5aab13e5281dc7f83dd51c71` |
| `experiments/runs/EXP-001/train_batch14671.jpg` | 601901 | `81b922f15c95e21d54d1869947ab91821202a13b8691ecdfb94fb4aeaf29d9e6` |
| `experiments/runs/EXP-001/train_batch14672.jpg` | 581560 | `52299e678d608c9cf1a8d9da24b1682f1546789d49c7b3d6e1d1ea086748a461` |
| `experiments/runs/EXP-001/train_batch2.jpg` | 649672 | `9a0da13e3a29a39985c8eb39aea1bbf369822a5c9429289f1296f5ff8c3ed1bd` |
| `experiments/runs/EXP-001/val_batch0_labels.jpg` | 759088 | `b2454d5c598c6d9be9a63b930fbc4ae1137dca018643d299117264b31b53f8ec` |
| `experiments/runs/EXP-001/val_batch0_pred.jpg` | 768851 | `e118652321b838eb9d676f79f66db9b1420000ed7b3a3482c95e7eedad7a4ad5` |
| `experiments/runs/EXP-001/val_batch1_labels.jpg` | 685976 | `5784af6d0be95ad6e77c16585d8e55caa66103314e8ebead0cf3b46065b03592` |
| `experiments/runs/EXP-001/val_batch1_pred.jpg` | 700038 | `7de30fbddd0efa111993047000a9e98201338e1096d6be9a1129ca5efd2716ea` |
| `experiments/runs/EXP-001/val_batch2_labels.jpg` | 715540 | `45f86f7666a77be3ebd530cf7757ba55ade4803cc9745b26c80927776d7a6e69` |
| `experiments/runs/EXP-001/val_batch2_pred.jpg` | 725264 | `1b5b5cc53033817470d0a5946942d8923910ea66a24ee806e29c92fdf9ad30a4` |
| `experiments/runs/EXP-001/weights/best.pt` | 5479891 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `experiments/runs/EXP-001/weights/last.pt` | 5479891 | `acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88` |
| `experiments/reports/EXP-001/run_record.yaml` | 922 | `e97f86c12942887c5772176ccfacae91c4c85064e208fff0e93d290638e72a50` |
| `artifacts/logs/EXP-001/training.log` | 1012613 | `12d1f872a0aed34625dc50f399a1385f123e3be6d4beac7a05386298eef87456` |

Machine-readable freeze: `docs/weights/EXP-001_BEST_MODEL_MANIFEST.yaml`.
It includes the complete inventory, dataset/mapping hashes, runtime and lock
fingerprints, metric provenance, durations, and execution boundaries.

## Integrity and verification

- Source manifest: 5601 entries rehashed and matched.
- Processed manifest: 5602 entries rehashed and matched.
- Source data.yaml, source manifest and processed manifest match the frozen training contract.
- Canonical config and run-local snapshot are byte-identical and match P2-5.1 SHA256.
- Initialization and best/last checkpoint hashes match their registered execution evidence.
- Runtime dependency lock hashes match the recorded fingerprint.
- Dataset, mapping, configuration and Charter are compared against task-entry bytes after verification.

| Verification | Result |
| --- | --- |
| `python -m pytest` | PASS: 186 passed (after documentation updates) |
| `python -m compileall .` | PASS, exit 0 |
| `git diff --check` | PASS, exit 0 |
| New report/manifest whitespace inspection | PASS |
| YAML parse and artifact size/SHA256 verification | PASS: all 29 inventory entries |
| Task-entry comparison | PASS: 11,439 existing files compared; only four intended existing documentation files changed |
| Dataset unchanged | PASS: all source/processed bytes and file sets unchanged |
| Mapping unchanged | PASS: contracts, mapping metadata and class order unchanged |
| Frozen config unchanged | PASS: registered SHA256 and snapshot match; execution_enabled remains false |
| Charter diff | Existing M-004 status-only change versus HEAD; no P2-7 change |

The Charter diff against HEAD is **not empty**: the pre-existing M-004 status
changes from pending to implemented. No locked goal, MUST definition or
acceptance criterion changes. Its task-entry and final byte SHA256 are both
`46c72e8828ae64e88a8eec551f573fc341a2ec43ecae5230f2eea3fc2227b175`.
The existing Charter change was preserved, not introduced by P2-7.

The four updated existing documents are current status, the Phase 2 document,
changelog and test gates, as required by AGENTS.md. The two new deliverables
are this report and the best-model manifest. No source code was changed.

## Retained limitations

The existing dataset quality risks (perceptual cross-split candidates, small
objects, class imbalance and empty labels) remain unchanged. The log records
an automatic yolo26n.pt AMP compatibility check during the original run; that
file did not replace yolo11n.pt initialization. No model quality acceptance or
Phase 3 model selection is claimed. The consumed authorization cannot be reused.
