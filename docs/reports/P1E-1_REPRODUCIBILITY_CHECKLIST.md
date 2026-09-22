# P1E-1 Reproducibility Checklist

> Status: REVIEW COMPLETE / TRAINING NOT STARTED
>
> This checklist records the minimum evidence required before an EXP-001
> training run can be considered reproducible.

## Dataset

- [ ] Dataset ID confirmed: `CSS-PPE-10-V1`
- [ ] Mapping confirmed: `PPE-MAPPING-V1`
- [ ] Processed path confirmed: `data/processed/css-ppe-10-v1/`
- [ ] Source `data.yaml` SHA256 confirmed:
      `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`
- [ ] Source manifest SHA256 confirmed:
      `ea0de4b0ca379c5aae066e500b1e0bf30b69ae71467c2bb99e4f2cbd5f98d795`
- [ ] Processed manifest SHA256 confirmed:
      `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c`
- [ ] Class order confirmed: `person`, `hardhat`, `no_hardhat`, `vest`,
      `no_vest`, `machinery`, `vehicle`
- [ ] Quality report confirmed: `docs/17_DATASET_QUALITY_REPORT.md`
- [ ] Immutable boundary confirmed: no dataset mutation is allowed

## Experiment

- [ ] Experiment ID confirmed: `EXP-001`
- [ ] Canonical config confirmed:
      `configs/training/exp001_baseline.yaml`
- [ ] Schema confirmed: `configs/training/schema.yaml`
- [ ] Model family confirmed: `YOLO11`
- [ ] Model variant confirmed: `YOLO11n`
- [ ] Model version remains explicitly pending
- [ ] Starting weight remains explicitly pending
- [ ] Seed remains explicitly pending
- [ ] Dependency versions remain explicitly pending
- [ ] Required metrics confirmed: `mAP50`, `mAP50-95`, `precision`, `recall`,
      `per-class AP`, `confusion matrix`, `inference speed`, `model size`

## Runtime

- [ ] Python version recorded: `3.13.6`
- [ ] PyTorch availability recorded: `NOT INSTALLED`
- [ ] Ultralytics availability recorded: `NOT INSTALLED`
- [ ] CUDA availability recorded: `False`
- [ ] Device strategy resolved before execution
- [ ] Hardware profile recorded before execution
- [ ] Dependency lock or exact resolved versions recorded before execution

Current runtime decision: `NOT READY FOR TRAINING`

## Artifacts

- [ ] Run path reserved: `experiments/runs/EXP-001`
- [ ] Logs path reserved: `artifacts/logs/EXP-001`
- [ ] Reports path reserved: `experiments/reports/EXP-001`
- [ ] Checkpoint path reserved: `models/checkpoints/EXP-001`
- [ ] Configuration snapshot planned for the run directory
- [ ] Dataset fingerprint snapshot planned for the run directory
- [ ] Environment snapshot planned for the run directory
- [ ] Metrics and checkpoint relationship planned for the run report

## Reproducibility Sequence

1. Freeze and verify the dataset contract.
2. Freeze the canonical experiment configuration.
3. Resolve and record runtime dependencies and device strategy.
4. Verify the environment without training.
5. Record a configuration fingerprint before execution.
6. Execute only after Phase 2 authorization.
7. Save the configuration, environment, metrics, logs, and checkpoint together.
8. Re-run the same frozen configuration to verify reproducibility.

Do not execute steps 6 through 8 during P1E-1.
