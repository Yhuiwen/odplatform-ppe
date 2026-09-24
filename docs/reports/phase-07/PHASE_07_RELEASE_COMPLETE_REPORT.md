# Phase 7 Release Complete Report

Date: 2026-09-24

Status: `PASS / RELEASED`

Release scope: Phase 7-6 runtime finalization, M-007 annotated demo video,
validation evidence and final release documentation.

## 1. Release Identity

| Field | Value |
| --- | --- |
| Branch | `main` |
| Release base HEAD | `a30b73c080c18d010fbaa08642868e86acb68022` |
| Final Release Commit SHA | `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20` |
| Final HEAD / report commit | The documentation commit containing this report; resolve with `git rev-parse HEAD` |
| Commit message | `phase-7: finalize runtime and annotated demo release` |
| New tag | `phase-7-release-freeze-complete` |
| Tag object SHA | `abb365cb4029ad079717da6cce9abb13eb18317b` |
| Tag target commit | `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20` |
| Existing Phase 7 tag | `phase-7-web-alert-platform-complete` |
| Existing tag object | `d97c8249c756dec33a9bb149bf837871b59b3503` |
| Existing tag target | `a30b73c080c18d010fbaa08642868e86acb68022` |
| Existing tag mutation | NONE |
| Remote | `https://github.com/Yhuiwen/odplatform-ppe.git` |

The existing annotated tag was audited before release and was not deleted,
moved, replaced or force-pushed.

## 2. Release Scope

- Phase 7-0 through Phase 7-6: PASS and human-reviewed.
- Phase 7-6 runtime targets: MP4 regression, real USB Camera, native TTS,
  browser Streamlit and controlled local RTSP.
- M-007 annotated demo video implementation, real MP4 validation and
  G1 through G8 human review.
- Final documentation and release publication.

No Phase 8 work is included.

## 3. Changed Files

The release change set contains source, tests, configuration and documentation:

```text
.gitignore
README.md
configs/monitoring.yaml
configs/p7_6_validation.yaml
core/rendering/__init__.py
core/rendering/annotated_frame.py
docs/01_MASTER_PLAN.md
docs/02_CURRENT_STATUS.md
docs/04_CHANGELOG.md
docs/05_TEST_GATES.md
docs/08_RISK_REGISTER.md
docs/designs/phase-07/PHASE_7_M007_ANNOTATED_DEMO_VIDEO_DESIGN.md
docs/phases/PHASE_07_WEB_ALERTS.md
docs/reports/phase-07/PHASE_07_FINAL_RELEASE_REPORT.md
docs/reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_REPORT.md
docs/reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_RESULT.md
docs/reports/phase-07/PHASE_7_M007_HUMAN_REVIEW_REPORT.md
docs/reports/phase-07/PHASE_7_M007_IMPLEMENTATION_REPORT.md
docs/reports/phase-07/PHASE_07_RELEASE_COMPLETE_REPORT.md
docs/worklogs/2026/09/2026-09-23-16-phase7-release-finalization.md
docs/worklogs/2026/09/2026-09-23-17-phase7-release-freeze-preparation.md
docs/worklogs/2026/09/2026-09-23-18-phase7-m007-implementation.md
docs/worklogs/2026/09/2026-09-24-01-phase7-release-closure.md
infra/alerts/__init__.py
infra/alerts/tts.py
infra/storage/annotated_video_writer.py
infra/tts/__init__.py
infra/tts/tts_service.py
scripts/render_annotated_demo_video.py
services/annotated_video_service.py
services/monitoring_service.py
tests/integration/test_monitoring_service.py
tests/unit/test_annotated_demo_video.py
tests/unit/test_dashboard_contract.py
tests/unit/test_imports.py
tests/unit/test_phase7_finalization_config.py
tests/unit/test_placeholders.py
tests/unit/test_structure.py
tests/unit/test_tts_alert.py
web/Home.py
web/dashboard_support.py
web/monitoring_support.py
web/pages/1_实时监控.py
```

No model, dataset, training output, MP4, database, runtime artifact,
credential or token is included.

## 4. Test Results

| Check | Result |
| --- | --- |
| `python -m pytest -q` | `414 passed, 1 skipped` |
| Skip | Existing optional Torch-dependent evaluation test |
| `python -m compileall -q .` | PASS |
| `git diff --check` | PASS |

## 5. Frozen Asset Verification

| Asset | Expected SHA256 | Result |
| --- | --- | --- |
| Release checkpoint | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| Training configuration | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| Inference configuration | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| Processed `data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |
| Processed dataset payload | `bc762204e2305164cfdbc492d15269b84c4ce4ff3cfdcdc805baf84c5616237b` | MATCH |
| Processed checksum manifest file | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` | MATCH |
| M-007 demo MP4 | `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949` | MATCH |

## 6. Runtime Validation Status

| Target | Status | Evidence |
| --- | --- | --- |
| MP4 regression | PASS | 47/47 frames; Git-ignored `artifacts/validation/P7-6/` |
| USB Camera | PASS | 60 frames; open/read/close lifecycle |
| Native TTS | PASS | Windows SAPI through `pyttsx3` |
| Streamlit browser | PASS | Overview, Event Explorer, Evidence Viewer, Statistics and realtime MP4 session |
| RTSP | PASS for controlled local MediaMTX | 60 frames; clean release |

Remote RTSP, reconnect/backoff and long-running recovery remain unverified.

## 7. M-007 Status

| Item | Result |
| --- | --- |
| Implementation | COMPLETE |
| Real MP4 validation | PASS |
| Human review | PASS |
| Gates P7-M007-G1 through G8 | PASS |
| Output | 47/47 frames, 1280x720, 23.976 FPS |
| Output size | 736,856 bytes |
| Output SHA256 | `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949` |
| Metadata and frame counts | PASS |

## 8. Charter Governance Exception

The locked Charter body was not modified. M-007 remains `待实现` because
Phase 7 delivery and Human Review do not replace the locked Phase 9 final
acceptance. This exception is intentional and is not a release blocker.

Phase goals, MUST definitions, acceptance criteria, dataset, mapping,
checkpoint, training configuration and inference contract remain unchanged.

## 9. Publication Verification

| Ref | Local SHA | Remote SHA | Status |
| --- | --- | --- | --- |
| `refs/heads/main` | `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20` | `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20` | MATCH |
| `refs/tags/phase-7-web-alert-platform-complete` | `d97c8249c756dec33a9bb149bf837871b59b3503` | `d97c8249c756dec33a9bb149bf837871b59b3503` | MATCH / UNCHANGED |
| `refs/tags/phase-7-release-freeze-complete` | `abb365cb4029ad079717da6cce9abb13eb18317b` | `abb365cb4029ad079717da6cce9abb13eb18317b` | MATCH |

The final release commit and annotated tag object were verified against the
remote before this metadata-only report commit. A commit cannot contain its own
final commit hash; this report therefore records the immutable release commit
and tag identities and resolves final report HEAD with `git rev-parse HEAD`.

## 10. Known Limitations

- Remote RTSP, reconnect/backoff, stale-frame recovery and long-running
  monitoring remain unverified.
- TTS validates backend invocation, not audio quality.
- Streamlit browser resource usage and long-session recovery were not
  instrumented.
- M-007 validation used one 47-frame MP4; long-duration throughput and codec
  portability remain open.
- Python 3.12.1 was used for Phase 7-6 validation while the frozen inference
  runtime records Python 3.10.4.
- M-007 and M-008 retain their locked Charter statuses until Phase 9
  acceptance.

## 11. Final Status

```text
Phase 7: COMPLETE / RELEASED
Phase 8: NOT STARTED
Publication: AUTHORIZED AND VERIFIED
Working tree: CLEAN AFTER REPORT COMMIT
```
