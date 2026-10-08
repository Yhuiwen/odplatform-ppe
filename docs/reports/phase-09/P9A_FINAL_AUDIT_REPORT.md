# P9-A FINAL AUDIT REPORT

Date: 2026-09-25. Initial static audit result: **PARTIAL**; superseded by
P9-A.1 **PASS / FINAL-DEMO-RUNTIME-001 FROZEN / VALIDATED**. This report
preserves the initial findings; current runtime evidence is recorded in
`P9A_FINAL_DEMO_RUNTIME_FREEZE_REPORT.md`. No P9-B execution, demo recording,
threshold change, model
download, commit, tag or push occurred.

## 1. PRE-READ

Read `AGENTS.md`, README, Charter, Master Plan, Current Status, Technical
Decisions, Changelog, Test Gates, Risk Register, latest worklog, open-source
usage, reference assets, Dataset Card and Phase 9 document. The two reported
governance conflicts were clarified first. Current phase: Phase 8 FINAL
RELEASED; P9-A authorized and IN PROGRESS. Relevant MUSTs: M-007, M-008,
M-009 through M-020, M-021 through M-023. Relevant gates: P9-G1 through G4.
Open risks: RISK-005/006/008/020 through 027. No new material governance
conflict found after clarification.

## 2. Git Identity / 3. Current Phase

Branch `main`; HEAD and `origin/main` both
`6c38a4ea51eec9a62f433683a3447c073852cbbd`; origin is
`https://github.com/Yhuiwen/odplatform-ppe.git`. The initial worktree was
clean. `phase-8-final-integration-complete` exists; Phase 8 is FINAL
RELEASED. Phase 9 started only for P9-A; P9-B remains unauthorized.

## 4. Runtime Drift Matrix / 5. Dependency Conflicts

See `P9A_RUNTIME_DRIFT_REPORT.md` for all 12 requested packages. Key conflict:
`opencv-python==5.0.0.93` in the frozen EVAL lock and inference config versus
`opencv-python>=4.10,<5` in root requirements. `pyproject.toml` has empty
dependencies. The frozen Python 3.10.4 and successful P7 Python 3.12.1 are
distinct. Current audit host Python 3.13.6 lacks torch, torchvision,
ultralytics, Streamlit, pyttsx3 and plotly; no real model run is claimed.
The initial candidate was subsequently validated and frozen in P9-A.1.

## 6. Placeholder / Dead Code Findings

`scripts/run_demo.py` raises `NotImplementedError` and is a P9 demo blocker.
`web/pages/2_图片检测.py`, `3_视频检测.py`, `4_违规事件.py` and `5_数据大屏.py`
raise at import and are absent from `web/Home.py` navigation. Current
Overview, Event Explorer, Evidence Viewer and Statistics pages supersede
parts of the old event/dashboard concepts; image/video UI is not replaced
by a navigated equivalent. Other placeholder boundaries include
`scripts/infer_image.py`, `infer_video.py`, `infer_stream.py`,
`core/detection/detector.py`, `core/pipeline/inference_pipeline.py`,
`core/events/event_state.py`, `infra/storage/video_storage.py` and
`services/tracking_service.py`. Preserve for P9 disposition review; do not
delete in P9-A.

## 7. Test Coverage Matrix / 8. Full Pipeline Coverage

See `P9A_TEST_COVERAGE_MATRIX.md`. The 15 requested scenarios are assessed:

| Scenario | Current evidence / gap |
| --- | --- |
| 1 real image -> YOLO | REAL RUNTIME TESTED |
| 2 real MP4 -> YOLO | REAL RUNTIME TESTED, short |
| 3 MP4 -> YOLO -> ByteTrack | SHORT SMOKE ONLY |
| 4 Detection -> Association | IMPLEMENTED / SHORT SMOKE |
| 5 Association -> Compliance | IMPLEMENTED / SHORT SMOKE |
| 6 Compliance -> Temporal Event | UNIT / SHORT SMOKE |
| 7 Event -> SQLite | INTEGRATION / SHORT SMOKE |
| 8 Event -> Snapshot | INTEGRATION / SHORT SMOKE |
| 9 Persist -> Alert | INTEGRATION / SHORT SMOKE |
| 10 SQLite -> Dashboard | REAL RUNTIME, small history |
| 11 Event -> Analytics | INTEGRATION with fixture/persisted events |
| 12 Analytics -> Report | INTEGRATION; provider separately validated |
| 13 Report/Query -> Agent | Phase 8 fixture E2E, upstream excluded |
| 14 USB full chain | Camera open/read/close PASS; full live-event chain PENDING |
| 15 RTSP full chain | Local MediaMTX open/read/close PASS; remote/full chain PENDING |

All 15 remain PHASE 9 ACCEPTANCE PENDING. None has long-run evidence.

## 9. Tracking Gaps / 10. Association Gaps

`ByteTrackPersonTrackingAdapter` filters class 0 person; PPE is not tracked.
`tracker.yaml` freezes high/low/new thresholds 0.5/0.1/0.6, buffer 30,
match 0.8. Monitoring resets tracker and event engine at source start; ID
scope is a source session, not a durable person identity. Crossings, ID
switches, occlusion recovery, exit/re-entry and repeated start/stop need real
video evidence. Association uses containment >=0.50, IoU >=0.10, confidence
>=0.25, ambiguity margin 0.10, explicit `unknown`; nearest-distance forced
assignment is disabled. P9-B cases: one person, two people, crossing,
occlusion, entry/exit, multiple PPE, PPE between people, small/occluded PPE,
and conflicting no_hardhat/no_vest. Do not tune thresholds before results.

## 11. Compliance/Event Gaps

`rules.yaml` freezes NO_HELMET, NO_VEST and PPE_UNKNOWN; confirmation requires
5 consecutive frames and 1.0 second; recovery requires 5 compliant frames;
cooldown is 30 seconds. Event state keys use `(track_id, event_type)` and an
active-cycle deduplication boundary. P9-B must measure first detection,
temporal confirmation, event creation, SQLite commit, snapshot publication
and each alert delivery. Compute detection->event, event->persist,
persist->alert and total alert latency with a common monotonic clock and
event ID. Real conflict and recovery/cooldown cycles remain unmeasured.

## 12. Monitoring Lifecycle Gaps

`MonitoringService` owns a worker thread, stop event and bounded join;
`finally` closes the source. `web/monitoring_support.py` stores one runtime
per Streamlit session. Tests cover ordered frames, source failure, close,
persistence-first alerts and event identity with injected components. Actual
short MP4/browser, USB and local RTSP paths were run in Phase 7. Page refresh,
session reconnect/browser close, repeated starts, blocked read/stop timeout,
stale frames, remote disconnect/reconnect/backoff and long running sessions
are not verified. MP4 EOF is represented as completion; open/read failures
have observable states. Worker ownership after browser session loss needs
destructive lifecycle testing.

## 13. Persistence/Evidence Gaps

SQLite has versioned checksum migrations, foreign keys, WAL, 5000 ms busy
timeout and transactions. Event ingestion preserves event IDs and rejects
conflicting duplicate identities. Snapshots use safe relative POSIX paths,
atomic publication, SHA256 and dimension checks. Dashboard evidence lookup
checks integrity. Destructive checklist for P9-B: delete/corrupt evidence,
duplicate event, DB reopen/process restart, DB busy lock, invalid snapshot
reference, orphan file/DB row, partial write and low disk. Retention, disk
growth monitoring, reconciliation and cleanup are not implemented/validated.

## 14. UI/UX Findings

English navigation coexists with Chinese filenames and old Chinese pages.
Realtime uses an absolute/working-directory MP4 path and manual RTSP URL;
these are engineering inputs for a demo. Event Explorer reports an invalid
Track ID then continues with `track_id=None`, potentially showing all events.
Realtime catches generic exceptions and shows class name plus raw message;
source error text may also expose internals. Overview uses a basic bar chart;
empty states exist, but loading and detailed recovery guidance are thin.
Realtime shows frames/detections/tracks/events and alert counts but not
end-to-end latency, source freshness or queue/backlog. P9-D should unify
language, fix invalid-filter fail-closed behavior, sanitize errors, provide
curated source selection and clearer loading/empty/error/success states.

## 15. Demo Readiness / 16. CI/Delivery Findings

`python scripts/run_demo.py` currently fails by design. Proposed chain:
read-only `preflight.py` -> environment/package validation -> checkpoint and
inference hash -> DB open/schema check -> demo asset existence/hash -> printed
Streamlit launch instructions. `reset_demo_data.py` requires a separately
reviewed isolated demo-data policy. No `.github/workflows` CI exists.
Recommended CI: Python 3.10 import/compileall, lightweight pytest and diff
whitespace check, without model download, camera or provider calls. Branch
protection was not verifiable from this local Git checkout.

## 17. P0/P1/P2 Issues

- P0: No verified final demo runtime or launch script; root OpenCV conflict.
- P1: Full real pipeline/USB/remote RTSP, lifecycle, evidence reconciliation
  and latency/long-run acceptance remain pending; invalid Track ID broadens
  query; raw monitoring exception may be displayed.
- P2: Stale placeholder pages/scripts, mixed UI language, no CI, incomplete
  loading/empty/error states and retention policy.

## 18. Files Changed / 19. Test Results

Governance clarification: `docs/02_CURRENT_STATUS.md`,
`docs/03_TECHNICAL_DECISIONS.md`. P9-A documents: Phase 9 document and
three reports in this directory. `python -m compileall -q core infra services
utils web scripts`: PASS. `python -m pytest -q`: **1 failed, 666 passed,
1 skipped**. The failing documentation-governance test asserts M-007 must
start with standalone `待实现`; that assertion contradicts the authorized
two-layer status wording and needs a separately authorized test update. The
skip is optional Torch; this host has no Torch installation. No real model,
camera, Streamlit, TTS or provider test was run here:
`BLOCKED_RUNTIME_DEPENDENCY`.

## 20. Frozen Asset Verification / 21. Git Diff Check

Checkpoint SHA256 matches `configs/inference.yaml` expected value
`1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
Inference config, dataset identity and Phase 8 contracts have no Git diff.
Historical tags have not been changed. Final `git diff --check` result is
PASS after documentation completion. Inference config SHA256 is
`0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`.

## 22. Recommended P9-B Entry Conditions / 23. Final Gate

Resolve the stale governance test without weakening the Charter; validate and
lock FINAL-DEMO-RUNTIME-001 in a clean environment; fix or explicitly gate
the OpenCV packaging conflict; establish read-only preflight and a working
demo launch plan. Review the P9-B evidence matrix and scene assets before
running acceptance. P9-G1 through G4 remain pending.

**Initial P9-A RESULT: PARTIAL.** The P9-A.1 continuation repaired the
governance assertion, validated the clean environment and froze the runtime.
**Current P9-A RESULT: PASS. P9-B READY / WAITING FOR HUMAN AUTHORIZATION.**
