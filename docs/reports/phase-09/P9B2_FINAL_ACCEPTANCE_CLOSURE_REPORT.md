# P9-B.2 Final Acceptance Closure Report — 2026-09-25

**P9-B RESULT: PARTIAL. P9-C NOT READY.** G8 and G10 remain partial. No P9-C implementation, commit, tag, push, reset, model change, dataset change, threshold change or dependency change occurred in P9-B.2.

## Governance, Git and runtime

The prescribed AGENTS, README, Charter, master plan, current status, decisions, test gates, risk register, Phase 9 plan and five P9-B reports were re-read. Phase 8 is FINAL RELEASED; Phase 9 P9-A PASS, P9-B authorized and PARTIAL; P9-C not authorized. No new governance conflict was found. Charter M-008 requires **Camera or RTSP** live read, detect and display, with observable failure and no fabricated frames; Phase 9 owns final acceptance.

Branch `main`; HEAD and `origin/main` both `6c38a4ea51eec9a62f433683a3447c073852cbbd`. `phase-8-final-integration-complete` and historical tags were not modified. Verification runtime `.venv-final-demo-verify` is Python 3.12.1 on Windows AMD64, CPU. Frozen identities: `best.pt` SHA256 `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`; `configs/inference.yaml` SHA256 `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`; 79-pin `FINAL-DEMO-RUNTIME-001` lock SHA256 `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4`. These identities match the P9-B.1 freeze. No package installation was requested or observed; preflight checked all lock pins and `pip check` passed.

## Stop timeout and automated lifecycle

`20260925T100121Z-97477388` shows Stop requested during Camera read; read ended at T0+142 ms and an unnecessary cold inference started. Stop timed out at T0+5.017 s; camera close and worker exit completed at T0+12.164 s. A new post-read `stop_event` check prevents that extra inference. `20260925T100508Z-934e63ef` shows the remaining case: Stop during an inference already in progress timed out at T0+5.009 s; inference ended at T0+8.280 s, camera closed at T0+8.904 s and the worker exited at T0+8.905 s. This is observable and unresolved. The configured timeout remains five seconds.

Lifecycle integration tests cover idle and repeated Stop, Stop during blocking read and active inference, source close exactly once, no new inference after cancellation, eventual worker exit, restart and observable timeout. Focused run: 9 passed. Real USB run `20260925T101508Z-04cd2839` completed five start/wait-for-frames/stop cycles on one service. All five processed four frames and reached STOPPED without an error, with worker exited and source closed. Reopen succeeded across cycles. The residual cold-inference edge prevents declaring the timeout fully resolved.

## Real USB and browser review

The 25.395-second Camera 0 service run `20260925T101624Z-b0117ef1` processed 103 frames, 309 detections, 103 tracks and 206 PPE associations. It produced `NO_HELMET` and `NO_VEST` at frame 4, two SQLite rows, two verified snapshots and four delivered alerts, with zero service error. Invalid index 64 run `20260925T101723Z-4083b33b` failed with `SOURCE_OPEN_FAILED`, zero frames, zero events and no preview.

**ASSISTANT DIRECT BROWSER VISUAL REVIEW: PASS. HUMAN VISUAL REVIEW: PENDING separate person sign-off.** A real Streamlit server and browser showed USB Camera 0 preview updating, frames/detections/tracks growing, real recent events, Stop to STOPPED, successful restart and second Stop, and coherent page switching. Event Explorer listed six isolated Camera events; Evidence Viewer showed a VERIFIED snapshot; Statistics showed six total, three NO_HELMET and three NO_VEST. No raw traceback appeared. The Start/Stop page now reruns immediately after an action so button availability reflects the current worker state. Browser test storage was isolated under `artifacts/p9b/browser-p9b2-20260925`.

## Tracking and association real scenes

The 103-frame real USB scene records per-frame track ID, bbox and confidence. One person was visible; track 1 was output on every processed frame, with no observed ID switch or duplicate. The trace records all 206 PPE candidate geometries, including containment and IoU; all selected track 1. Example frame 0: no_hardhat confidence 0.8550, containment 1.0, IoU 0.1093; no_vest confidence 0.8246, containment 1.0, IoU 0.2986. The prior real MP4's low-confidence no_vest remains explicitly UNKNOWN, not forced to a nearest person. No association policy was changed.

The local asset search found no controlled two-person crossing, overlap, occlusion or exit/re-entry clip; the user reported no participant available to stage one. Accordingly, ID switches after occlusion, re-entry behavior, and ambiguous multi-person PPE ownership are **NOT VALIDATED**. A 47-frame smoke clip alone is not used to pass G8. A sustained construction-site violation MP4 also remains unavailable, but the real Camera violation chain means it is not a P9-B blocker by itself.

## Regression and gate recheck

`.venv-final-demo-verify`: `pytest -q` **684 passed, 0 failed**; `compileall -q core infra services utils web scripts` PASS; `scripts/preflight.py` PASS; `scripts/run_demo.py --check` PASS; `pip check` PASS; `git diff --check` PASS (line-ending notices only). The model, inference config, runtime lock, protected dataset and Phase 8 contracts were not edited in P9-B.2. Worktree changes from earlier authorized P9 work remain uncommitted.

| Gate | Result | Basis |
| --- | --- | --- |
| G1 real MP4 full chain | PASS | P9-B.1 clean 47/47 official service run |
| G2 SQLite | PASS | MP4 and real Camera persisted rows and reopen/query |
| G3 snapshot | PASS | Verified JPEG hashes/dimensions, including Camera browser evidence |
| G4 alert | PASS | Real Console/Web deliveries, zero failures |
| G5 Dashboard | PASS | AppTest and direct browser Event Explorer/Evidence/Statistics |
| G6 Analytics / Report / Agent | PASS | Prior same-DB grounded projection, unchanged contracts |
| G7 real event trace | PASS | MP4 UNKNOWN plus Camera NO_HELMET/NO_VEST |
| G8 tracking / association real scene | PARTIAL | 103-frame per-frame USB trace; complex scenes unavailable |
| G9 temporal / dedup / recovery / cooldown | PASS | Prior deterministic gates and real event confirmation |
| G10 Camera OR RTSP / M-008 | PARTIAL | Live Camera path/failure/browser evidenced; cold inference Stop timeout remains |
| G11 full tests | PASS | 684 passed, zero failed; compileall PASS |
| G12 frozen runtime/assets | PASS | Preflight/package checks and hashes match, no P9-B.2 protected edits |
| G13 Git diff | PASS | `git diff --check` exit 0; no Git publication action |

## Files changed in P9-B.2

`services/monitoring_service.py`, `tests/integration/test_monitoring_service.py`, `scripts/run_p9b_full_chain.py`, `web/pages/1_实时监控.py`, `web/dashboard_support.py`, `web/monitoring_support.py`, this report and the P9-B report/status/gate/changelog updates. All remain in the working tree for review.

**P9-B RESULT: PARTIAL. P9-C NOT READY.**
