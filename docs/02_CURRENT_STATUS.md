# Current Status

This is the single entry point for the latest project state. Historical
implementation and validation details are preserved in the
[Phase 4 → Phase 5 handover](worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md)
and the linked phase reports. Earlier snapshots may describe past pending
reviews; the statuses below reflect the current accepted records.

## Current Phase

- Phase 6 COMPLETE / RELEASED — PPE Compliance Event Engine; current subphase
  is Phase 6 final release.
- Phase 5 COMPLETE / RELEASED — Tracking & Association. Release tag
  `phase-5-tracking-association-complete` targets
  `6da6213f0cc541765f231c81b4264a98f01d5f4a`.
- P5-0, P5-1 and P5-2 are human-reviewed PASS. P5-3 synthetic pipeline
  validation is PASS. The frozen-checkpoint/video runtime validation is
  prepared with an execution-disabled config and passed static preflight, but
  is `BLOCKED / NOT RUN` because this host has no `torch` or `ultralytics`.
- Historical state: Phase 5 IN PROGRESS during P5-0 through the final audit.
  P5-3-G5 was originally recorded as `BLOCKED / NOT RUN`. A subsequent
  explicit human release authorization created the annotated tag
  `phase-5-tracking-association-complete` at commit
  `6da6213f0cc541765f231c81b4264a98f01d5f4a`; the current documentation is
  now synchronized to `COMPLETE / RELEASED`.
- Phase 4 remains `Offline Inference COMPLETE` for its released offline scope.
- Current next allowed step: `WAIT FOR PHASE 6 RELEASE REVIEW`; Phase 7 has
  not started.

## Last Completed

- Phase 2 Training: `已经实现`; EXP-001 baseline training completed using its
  single authorized run. M-004：已经实现.
- Phase 3 Evaluation: `已经实现`; model comparison, selection and independent
  evaluation were completed and human review passed. M-005：已经实现.
- Phase 4 Offline Inference: `已经实现` for the scope in ADR-018; offline release
  gates are PASS. Full M-006/M-007 acceptance was not implied by that release.
- Phase 5 Tracking & Association: `已经实现（COMPLETE / RELEASED）`; P5-0 froze `TrackResult`,
  `AssociationResult`, person-only ByteTrack boundaries and unknown-safe
  containment/IoU policy. P5-1 implements the person-only ByteTrack adapter
  behind that boundary. P5-2 implements conservative Person-PPE association
  with explicit `unknown`. P5-3 validates the complete adapter composition
  with deterministic synthetic frames; real runtime and integrated video
  verification remain blocked by missing runtime dependencies. At the
  implementation-audit layer, M-009 and M-010 are
  `IMPLEMENTED / Runtime Evidence Pending`; the locked Charter statuses remain
  `待实现` until real runtime acceptance is proven. The release tag records the
  implemented, synthetically validated and human-authorized Phase 5 package;
  it does not convert the blocked real-runtime evidence into a PASS.
- Phase 6 PPE Compliance Event Engine: `已经实现（COMPLETE / RELEASED）`;
  `AssociationResult -> ComplianceInput -> ComplianceResult ->
  ComplianceEvent` is implemented with conservative Helmet/Vest/Unknown
  rules, five-frame and one-second confirmation, event deduplication,
  recovery, cooldown and JSONL storage. M-011 through M-014 remain
  `待实现` until the full Charter acceptance evidence is reviewed.
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
- P5-1 person-only ByteTrack adapter: lazy backend isolation, class-0 filtering,
  confidence filtering, fail-closed errors and project-owned `TrackResult`
  output. Adapter behavior is tested with an injected backend; real
  Ultralytics ByteTrack execution is not verified.
- P5-2 conservative Person-PPE association: containment `0.50`, IoU `0.10`,
  confidence `0.25`, ambiguity margin `0.10`, deterministic ranking and
  explicit `unknown`. Synthetic tests cover single/multiple people, wrong
  candidates, ambiguity, missing PPE and empty input; real video integration
  is not verified.
- P5-3 integrated synthetic validation: the full
  `DetectionResult -> TrackResult -> AssociationResult` adapter chain passes
  single-person, multi-person, PPE-present, missing-PPE and ambiguous cases.
  A validation-only config and script prepare frozen checkpoint/video
  execution and report dependency readiness without loading the model.
- P5 release final audit: completed evidence, frozen identities, limitations
  and gates are consolidated in the Phase 5 final audit report. M-009 and
  M-010 are implemented at the audit layer. The historical P5-3-G5 block
  remains recorded, while the later explicit release authorization is
  recorded by `phase-5-tracking-association-complete`.
- Phase 6 compliance/events: Project-owned `ComplianceInput`,
  `ComplianceResult` and `ComplianceEvent` contracts; conservative
  Helmet/Vest/Unknown rules; five-frame/one-second temporal confirmation;
  active-cycle deduplication; recovery/cooldown; and Git-ignored JSONL event
  storage are implemented. The offline fixture and tests require no model
  runtime, GPU, camera or network stream.
- Camera/RTSP, alerts, business Web pages, LLM and Agent remain outside
  completed scope. ByteTrack and association adapters are implemented and
  synthetically integrated; real runtime acceptance remains unverified.

## Current Runtime

- Phase 4 runtime ID: `INF-RUNTIME-001`; Windows x86_64, Python `3.10.4`,
  PyTorch `2.5.1+cpu`, torchvision `0.20.1`, Ultralytics `8.4.157`.
- Runtime policy: CPU only. Frozen `configs/inference.yaml` keeps
  `execution_enabled: false`; real validation used separate explicit configs.
- The P5-3 preflight host is Python `3.13.6` with OpenCV `5.0.0`; `torch`,
  `torchvision` and `ultralytics` are not installed. The frozen P5-3
  validation config remains `execution_enabled: false`.
- Phase 6 validation ran on the same Python `3.13.6` governance host using
  only project-owned schemas and standard-library JSONL storage; no model
  runtime dependency was added.
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

- [Phase 6 final release report](reports/phase-06/PHASE_06_FINAL_RELEASE_REPORT.md).
- [Phase 6 test report](reports/phase-06/PHASE_06_TEST_REPORT.md).
- [P5 final release preparation](reports/phase-05/P5_FINAL_RELEASE_REPORT.md).
- [P5 release final audit](reports/phase-05/P5_RELEASE_FINAL_AUDIT.md).
- [P5 documentation sync report](reports/phase-05/P5_DOCUMENTATION_SYNC_REPORT.md).
- [P5 release final audit worklog](worklogs/2026/09/2026-09-23-07-phase5-release-final-audit.md).
- [P5 final release worklog](worklogs/2026/09/2026-09-23-06-phase5-final-release-preparation.md).
- [P5-3 tracking and association validation](reports/phase-05/P5-3_VALIDATION_REPORT.md).
- [P5-3 validation worklog](worklogs/2026/09/2026-09-23-05-phase5-p5-3-validation.md).
- [P5-2 Person-PPE association implementation](reports/phase-05/P5-2_IMPLEMENTATION_REPORT.md).
- [P5-1 ByteTrack adapter implementation](reports/phase-05/P5-1_IMPLEMENTATION_REPORT.md).
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

`WAIT FOR PHASE 6 RELEASE REVIEW`.

Phase 6 is recorded as `COMPLETE / RELEASED` after the offline rule, temporal,
event and storage gates passed. The release does not close the historical
P5-3-G5 real-runtime block, does not alter frozen model/data/training assets,
and does not change M-011 through M-014 from `待实现`.
