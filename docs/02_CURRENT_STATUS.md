# Current Status

This is the single entry point for the latest project state. Historical
implementation and validation details are preserved in the
[Phase 4 → Phase 5 handover](worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md)
and the linked phase reports. Earlier snapshots may describe past pending
reviews; the statuses below reflect the current accepted records.

## Current Phase

- Phase 4 — `Offline Inference COMPLETE` for its offline release scope.
- Current subphase: Phase 4 Release Preparation / Phase 5 handover.
- Phase 5 WAITING — Tracking & Association; work has not started.
- `WAIT FOR PHASE 5 AUTHORIZATION` remains the next allowed step.

## Last Completed

- Phase 2 Training: `已经实现`; EXP-001 baseline training completed using its
  single authorized run. M-004 is `已经实现`.
- Phase 3 Evaluation: `已经实现`; model comparison, selection and independent
  evaluation were completed and human review passed. M-005 is `已经实现`.
- Phase 4 Offline Inference: `已经实现` for the scope in ADR-018; offline release
  gates are PASS. Full M-006/M-007 acceptance was not implied by that release.
- Phase 1 Data remains `实现中` in the Master Plan. M-001, M-002 and M-003
  remain `待实现` in the Charter; completed data substeps are not a claim of
  their final acceptance.

## Completed Capabilities

- Frozen `CSS-PPE-10-V1` data artifact, Strategy C mapping and processed
  dataset are recorded; data quality was assessed without source mutation.
- EXP-001 YOLO11n training and Phase 3 test evaluation/model selection have
  reproducible evidence. Selected release checkpoint: EXP-001 `best.pt`.
- Single-image structured inference through `InferenceService` and
  `YOLODetector`; real-image validation used the frozen checkpoint.
- Sequential local MP4 structured inference through `VideoReader` and
  `VideoInferenceService`; real validation processed all 47/47 source frames.
- Camera/RTSP, ByteTrack, Person-PPE association, compliance rules, events,
  alerts, business Web pages, LLM and Agent remain outside completed scope.

## Current Runtime

- Phase 4 runtime ID: `INF-RUNTIME-001`; Windows x86_64, Python `3.10.4`,
  PyTorch `2.5.1+cpu`, torchvision `0.20.1`, Ultralytics `8.4.157`.
- Runtime policy: CPU only. Frozen `configs/inference.yaml` keeps
  `execution_enabled: false`; real validation used separate explicit configs.
- Training used a separately frozen AutoDL RTX 4090 environment. The
  EXP-001 one-run authorization is `CONSUMED`; it does not authorize retraining.

## Frozen Assets

- Dataset: `CSS-PPE-10-V1`, source identity and manifests in
  [Dataset Card](06_DATASET_CARD.md) and `docs/dataset_contracts/`.
- Mapping: Strategy C, seven training classes; five PPE compliance classes
  retain their locked order. See [ADR log](03_TECHNICAL_DECISIONS.md).
- Release checkpoint: `models/checkpoints/EXP-001/best.pt`, SHA256
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
- Training configuration and runtime: `configs/training/exp001_baseline.yaml`
  and `locks/EXP-001/`; inference config: `configs/inference.yaml`.
- Dataset, mapping, training assets, checkpoint and frozen inference config
  must remain unchanged without the applicable approval and new evidence.

## Current Risks

- [Risk Register](08_RISK_REGISTER.md) is authoritative for risk statuses.
  RISK-001 schedule pressure; RISK-004 PPE occlusion; RISK-005 Person-PPE
  misassignment; RISK-006 single-frame alert jitter; RISK-008 RTSP instability.
- RISK-017 retains data-quality findings, including small-object performance
  and perceptual cross-split candidates. Candidates are not confirmed leaks.
- Real Camera/RTSP behavior, annotated video output and downstream event
  behavior have not been validated by the Phase 4 offline release.

## Deferred Requirements

### Deferred MUST ownership

- M-007 annotated video rendering: `待实现`; Phase 7 video page/service
  integration owns delivery, Phase 9 owns final Charter acceptance.
- M-008 Camera/RTSP: `待实现`; Phase 7 live-input/real-time monitoring
  integration owns delivery, Phase 9 owns final Charter acceptance.
- Neither requirement is an Extension. ADR-019 clarifies the assignment;
  Charter definitions and acceptance criteria remain unchanged.
- Phase 4 Offline Inference completion does not set P4-G3 to PASS or complete
  the full M-007/M-008 acceptance criteria.

## Latest Reports

- [Phase 4C-1 real-image validation](reports/phase-04/PHASE_04C1_IMAGE_VALIDATION_REPORT.md).
- [Phase 4C-2 real-MP4 validation](reports/phase-04/PHASE_04C2_VIDEO_VALIDATION_REPORT.md).
- [Phase 4 scope clarification](reports/maintenance/PHASE_SCOPE_CLARIFICATION_REPORT.md)
  and [Phase 4 phase document](phases/PHASE_04_INFERENCE.md).
- [Phase 2 training execution](reports/EXP-001_TRAINING_EXECUTION_REPORT.md)
  and [Phase 3 final release](reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md).
- [Phase 4 → Phase 5 handover](worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md)
  preserves the former 753-line status document in full.
- This documentation cleanup is recorded in
  [Phase B governance report](reports/maintenance/DOCUMENT_GOVERNANCE_PHASE_B_REPORT.md).

## Next Allowed Step

`WAIT FOR PHASE 5 AUTHORIZATION`.

Before starting Phase 5, confirm its [entry conditions](phases/PHASE_05_TRACKING_ASSOCIATION.md):
Phase 4 offline gates PASS, deferred MUST ownership recorded, stable person/PPE
detection output, no frozen asset conflict and separate authorization.
This documentation change does not perform that asset check or begin Phase 5.
