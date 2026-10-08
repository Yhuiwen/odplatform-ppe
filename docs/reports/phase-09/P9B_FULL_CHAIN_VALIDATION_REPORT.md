# P9-B Full Chain Validation Report — 2026-09-25

## Result

**PARTIAL. P9-C NOT READY.** The official `MonitoringService` processed a real 47-frame MP4 through real `best.pt`, Ultralytics, ByteTrack, association, compliance, temporal event engine, SQLite, snapshot storage and Console/Web alerts. One `PPE_UNKNOWN` event was persisted and its evidence verified. This is a smoke baseline, not full Charter acceptance.

## Identity and source

- Branch `main`; HEAD and `origin/main` `6c38a4ea51eec9a62f433683a3447c073852cbbd`. Historical Phase 8 tag `phase-8-final-integration-complete` was untouched. No commit, tag, push, reset or force operation.
- P9-A is recorded PASS; Phase 8 FINAL RELEASED. P9-B was explicitly authorized. P9-C through P9-F and Phase 9 Charter acceptance remain pending. M-007 implementation and real MP4 human review passed; final Charter acceptance pending. M-008 Camera OR RTSP final acceptance pending.
- Windows 11 AMD64, Python 3.12.1, CPU, `.venv-final-demo`. Initial `pip check` and `scripts/preflight.py` passed.
- Run `20260925T091230Z-21b1895e`; isolated ignored workspace `artifacts/p9b/20260925T091230Z-21b1895e`. Source `artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4`, SHA256 `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852`.
- `best.pt` SHA256 `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`; inference config SHA256 `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`. Frozen source assets and Phase 8 contracts were not edited in this run.

## Real MP4 chain

Command: `.venv-final-demo\Scripts\python.exe scripts/run_p9b_full_chain.py --source mp4`. MonitoringService opened and closed the source and processed frames 0–46 in order: 47/47, no silent skip observed. Elapsed 21.674 s, effective 2.169 FPS. 77 detections (76 person, 1 no_vest), 66 track outputs, one association result (unknown), 66 `PPE_UNKNOWN` findings/candidates, one confirmed `PPE_UNKNOWN` event, one SQLite row, one snapshot and two delivered alerts (Console, Web), zero alert failures. No `NO_HELMET` or confirmed `NO_VEST` finding/event. See event, scene and timing reports for the limits of this evidence.

**Runtime drift:** During the first real ByteTrack call Ultralytics detected missing `lap>=0.5.12` and automatically installed `lap==0.5.13` into `.venv-final-demo`. `lap` is absent from the 78-pin `FINAL-DEMO-RUNTIME-001` lock. The lock file and frozen model/config remain unchanged, and `pip check` passes, but the environment no longer exactly matches the validated freeze. Subsequent real pipeline runs were paused. This blocks frozen-runtime acceptance until the dependency is resolved through a separately reviewed freeze update and clean validation.

## Downstream, camera and evidence

The same real run database was reopened through `web.dashboard_support.build_runtime` and `EventQueryService`: event count 1, `PPE_UNKNOWN` count 1, event ID unchanged, snapshot `evidence(...).verified=True`. `SafetyAnalyticsService` returned one fact, `SafetyContextBuilder` one observed fact, and deterministic `ReportService.generate` returned `GroundingStatus.VALID`. Streamlit AppTest ran Overview, Event Explorer, Evidence Viewer and Statistics against this same runtime: zero exceptions; metrics showed one event, the actual event ID, verified image and matching type counts. Agent Web projection ran summary, statistics, details and report against the same database; the report returned `success / TEMPLATE_FALLBACK / degraded / grounding=valid`. The projection evidence is `outputs/agent_projection.json`.

Isolated copies under `destructive/missing` and `destructive/corrupt` retained the event row after database reopen; `EventQueryService.evidence` returned `verified=False` with `SNAPSHOT_WRITE_FAILED` and `SNAPSHOT_HASH_MISMATCH`, respectively, without crashing. Source artifacts were untouched. Duplicate identical/conflicting event tests and a default full-service E2E test are **NOT RUN**. Invalid Track ID UI behavior remains unverified and unchanged.

USB full business chain **NOT RUN** after runtime drift; the prior P9-A camera open/read/close check is not P9-B evidence. Local RTSP full chain **NOT RUN**; historical open/read/close remains separate prior evidence. M-008 final acceptance is pending. No network video was downloaded; the user's later request authorized searching, while the P9-B instruction explicitly prohibited automatic download. Search results did not establish a qualifying sustained violation clip.

## Gate assessment

| Gate | Result | Evidence / gap |
| --- | --- | --- |
| G1 real MP4 full business chain | PASS | Clean runtime repeat: 47/47, full service path; extra real Camera violation scene recorded separately |
| G2 SQLite event | PASS | One row, reopen/query confirmed |
| G3 snapshot | PASS | One file, SHA256 and dimensions verified |
| G4 alerts | PASS | Console and Web delivered |
| G5 Dashboard | PASS | Four AppTest pages used same real DB, zero exceptions, matching metrics |
| G6 Analytics/Report/Agent | PASS | Same DB; four Agent Web projection requests, grounded fallback |
| G7 real compliance trace | PASS | MP4 `PPE_UNKNOWN`; real USB `NO_HELMET` and `NO_VEST` traces |
| G8 tracking/association scenes | PARTIAL | Limited 47-frame scene, no crossing/occlusion validation |
| G9 temporal/dedup/recovery/cooldown | PASS | Real MP4/USB confirmation plus deterministic 5-frame/1-s/recovery/30-s cooldown tests |
| G10 Camera OR RTSP | PARTIAL | USB full business chain passed; live UI display lacks visual review; short cold-stop timeout observed |
| G11 full tests 0 failed | PASS | Clean verify environment: `pytest -q`: 681 passed; compileall passed |
| G12 frozen assets unchanged | PASS | Model/config unchanged; revised 79-pin lock, clean MP4 package set stable |
| G13 `git diff --check` | PASS | No whitespace errors (Git line-ending notices only) |

The complete per-run machine evidence is `artifacts/p9b/20260925T091230Z-21b1895e/outputs/full_chain.json`. The script and reports remain uncommitted for human review. No P9-C work started.

## P9-B.1 superseding closure evidence (same date)

The preceding first-run drift narrative remains historical. Under the later P9-B.1 authorization, the unpublished `FINAL-DEMO-RUNTIME-001` lock was revised with `lap==0.5.13`. A second clean `.venv-final-demo-verify` installed 79 exact pins. Real MonitoringService MP4 run `20260925T093935Z-c9530763` again processed 47/47 frames, 77 detections and 66 tracks, creating one `PPE_UNKNOWN` event, one SQLite row, one verified snapshot and two delivered alerts. The before/after package inventory and `pip freeze` matched exactly; no AutoUpdate text appeared. Four Dashboard pages, deterministic Analytics/Report and four Agent Web projection requests consumed its same SQLite database (`outputs/downstream_validation.json`).

Real USB run `20260925T094052Z-24a066b4` processed 143 frames in 30.376 s and generated two distinct real Camera events: `NO_HELMET` and `NO_VEST`, each persisted with verified snapshot and Console/Web alerts. Index 64 returned `SOURCE_OPEN_FAILED` and zero fabricated results. Short cold-start stop attempts exposed `MONITORING_STOP_TIMEOUT` despite eventual `stopped`, and live Streamlit display was not visually reviewed; G10 stays PARTIAL. The Camera scene is not asserted to be a construction-site violation clip.

The new default deterministic service E2E passed, as did isolated identical/conflicting duplicate-event checks, 5-frame/1-second confirmation, five-frame recovery and 30-second cooldown tests, and Event Explorer invalid Track ID fail-closed AppTest. Clean-environment full suite: **681 passed**. See `P9B_RUNTIME_DRIFT_REPAIR_REPORT.md`, `P9B_USB_FULL_CHAIN_REPORT.md` and `P9B_REAL_SCENE_ASSET_CANDIDATES.md`.

**Current P9-B RESULT: PARTIAL. P9-C NOT READY.** G8 still lacks controlled crossing, occlusion, exit/re-entry and ambiguous PPE real-scene evidence; G10 needs closure of live display review and cold-stop reliability. A sustained construction-site violation MP4 remains missing. No Phase 9 Charter final acceptance is claimed.

## P9-B.2 superseding evidence (2026-09-25)

The live Streamlit USB page was directly observed in a browser: preview and counters refreshed, two real violation types appeared, Stop and restart worked, and Event Explorer/Evidence Viewer/Statistics consumed the isolated Camera events. Five real USB processed-frame start/stop cycles exited normally. Index 64 again failed observably with zero frames/events. A 103-frame real USB trace now records every track bbox/confidence and PPE candidate geometry. See the USB, tracking, stop-lifecycle and M-008 assessment reports. The missing post-read stop check was repaired, while Stop during an already-running cold inference can still exceed the five-second join. G8 and G10 therefore remain PARTIAL; G1–G7, G9, G11–G13 remain PASS subject to the final regression recorded below. P9-B remains PARTIAL and P9-C NOT READY.

## P9-B.3 Charter-based superseding decision (2026-09-25)

The P9-B.2 paragraph above remains as a historical judgement. The locked Charter does not require controlled crossing/occlusion/re-entry for M-009/M-010, or a five-second Stop bound for M-008. The 103-frame real Camera trace, real associations/UNKNOWN case, live browser display and observable invalid-camera failure meet the authorized G8/G10 criteria. Fresh full regression: 684 passed. G1–G13 now meet their stated technical criteria; **P9-B is READY FOR HUMAN VISUAL SIGN-OFF**, not final PASS until the user confirms the page. P9-C is not authorized. See `P9B3_CHARTER_GATE_READJUDICATION_REPORT.md`.

## P9-B.3 user sign-off closure

The user replied `pass` to the specified USB Camera 0 Realtime Monitoring visual checklist on 2026-09-25. HUMAN VISUAL REVIEW PASS. G1–G13 and P9-B are **PASS**. Historical PARTIAL assessments above remain as dated history; the superseding decision is `P9B3_CHARTER_GATE_READJUDICATION_REPORT.md`. P9-C remains unauthorized.
