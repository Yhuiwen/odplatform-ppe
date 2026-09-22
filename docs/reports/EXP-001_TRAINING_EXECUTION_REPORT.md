# EXP-001 Training Execution Report

> Status: COMPLETED
>
> Training authorization: GRANTED BY EXPLICIT USER INSTRUCTION
>
> Training execution: COMPLETED
>
> Evaluation phase: NOT STARTED

## Experiment Identity

| Field | Value |
| --- | --- |
| Experiment | `EXP-001` |
| Model | YOLO11n |
| Implementation | Ultralytics `8.4.157` |
| Dataset | `CSS-PPE-10-V1` |
| Mapping | `PPE-MAPPING-V1` |
| Classes | `person`, `hardhat`, `no_hardhat`, `vest`, `no_vest`, `machinery`, `vehicle` |
| Canonical configuration | `configs/training/exp001_baseline.yaml` |
| Configuration SHA256 | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` |
| Initialization weight | `yolo11n.pt` |
| Weight SHA256 | `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1` |
| Processed `data.yaml` SHA256 | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` |
| Seed | `42` |

The canonical configuration remained byte-for-byte frozen with
`execution_enabled: false`. The explicit one-run authorization was recorded
separately in `configs/training/exp001_authorization.yaml`, so executing the
run did not alter the frozen experiment configuration or its fingerprint.

## Runtime

| Field | Value |
| --- | --- |
| Provider / instance | AutoDL `bcb849a74f-38320766` |
| Region | `bjb1` |
| GPU | NVIDIA GeForce RTX 4090 24GB |
| OS | Ubuntu 20.04.5 LTS |
| Python | `3.10.21` |
| PyTorch | `2.5.1+cu124` |
| CUDA runtime | `12.4` |
| NVIDIA driver | `560.35.03` |
| Environment | `/root/miniconda3/envs/ppe-exp001` |
| Dependency fingerprint | `locks/EXP-001/runtime-fingerprint.yaml` |

## Execution Command

```bash
/root/miniconda3/envs/ppe-exp001/bin/python -m scripts.train \
  --config configs/training/exp001_baseline.yaml \
  --authorization configs/training/exp001_authorization.yaml \
  --data-yaml /root/autodl-tmp/datasets/css-ppe-10-v1/data.yaml \
  --weights /root/autodl-tmp/models/pretrained/yolo11n.pt
```

## Run Result

| Field | Value |
| --- | --- |
| Started at UTC | `2026-09-22T08:00:02Z` |
| Finished at UTC | `2026-09-22T08:19:29Z` |
| Configured epochs | `100` |
| Completed epochs | `95` |
| Best epoch | `75` |
| Stop reason | Early stopping after `20` epochs without improvement |
| Training duration | Approximately `19 minutes 27 seconds` |
| Best checkpoint size | `5,479,891` bytes |
| Best checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Last checkpoint size | `5,479,891` bytes |
| Last checkpoint SHA256 | `acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88` |

## Validation Metrics

These are validation metrics emitted during the training run. They satisfy
experiment archival for M-004; they are not the independent Phase 3 model
evaluation required by M-005.

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

Validation speed on the recorded RTX 4090 runtime:

| Stage | Time per image |
| --- | ---: |
| Preprocess | `0.7 ms` |
| Inference | `12.3 ms` |
| Postprocess | `0.4 ms` |

The best model was selected at epoch 75 because it produced the best
validation result in the run. The final epoch did not overwrite `best.pt`.

## Artifact Record

All run artifacts remain Git-ignored. The following relative locations are
outside the committed source tree:

| Artifact | Relative location | SHA256 |
| --- | --- | --- |
| Best checkpoint | `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Last checkpoint | `models/checkpoints/EXP-001/last.pt` | `acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88` |
| Run checkpoint | `experiments/runs/EXP-001/weights/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Run checkpoint | `experiments/runs/EXP-001/weights/last.pt` | `acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88` |
| Training log | `artifacts/logs/EXP-001/training.log` | `12d1f872a0aed34625dc50f399a1385f123e3be6d4beac7a05386298eef87456` |
| Run record | `experiments/reports/EXP-001/run_record.yaml` | `e97f86c12942887c5772176ccfacae91c4c85064e208fff0e93d290638e72a50` |
| Resolved arguments | `experiments/runs/EXP-001/args.yaml` | `c886ab6a206feb7744d66f3dfa1c5ae91d4d4620f77531707f5b70983d744e3d` |
| Epoch metrics | `experiments/runs/EXP-001/results.csv` | `3aafff966f4b7a851e1f9e1051aa928627c0a93e155c44611fd0fc4ee78e6d87` |
| Configuration snapshot | `experiments/runs/EXP-001/exp001_baseline.frozen.yaml` | Matches canonical configuration SHA256 |

The run directory also contains the required confusion matrices, PR/F1
curves, validation plots, and training/validation batch images generated by
Ultralytics.

## Integrity And Deviations

- Dataset identity and class order were checked before training.
- The processed dataset was not modified.
- The class mapping and dataset fingerprint were not modified.
- The frozen canonical configuration was not modified.
- The registered `yolo11n.pt` initialization weight was not replaced.
- The authorization file was consumed as a one-run gate.
- After the run, the AutoDL host reported no remaining training process and
  `0 %` GPU utilization; a shutdown command was issued to stop the GPU
  instance and avoid further compute charges. The remote dataset, weights, and
  run artifacts were not deleted.
- Ultralytics 8.4.157 ran its AMP compatibility check and automatically
  downloaded `yolo26n.pt` for that check. The log explicitly records
  `one-time, not used for training`; this file did not replace the frozen
  YOLO11n initialization checkpoint.

## M-004 Boundary

M-004 is satisfied by the recorded run because the project now has:

1. a frozen configuration and dataset identity;
2. a fixed random seed and recorded runtime;
3. a completed training run with early stopping;
4. a best checkpoint, last checkpoint, log, configuration snapshot, resolved
   arguments, epoch metrics, and a run record; and
5. an executable command that can reconstruct the experiment entry point.

M-005 remains `待实现`. Phase 3 independent evaluation, model selection, and
the final acceptance metrics have not started.
