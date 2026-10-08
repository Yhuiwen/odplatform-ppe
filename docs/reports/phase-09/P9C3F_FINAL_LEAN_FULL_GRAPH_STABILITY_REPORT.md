# P9-C.3f Final Lean Real Full-Graph Stability — 2026-09-27

## 1. Scope, decision and authority

**P9-C.3f RESULT: PARTIAL. LEAN FULL-GRAPH RESOURCE BEHAVIOR: SUSPICIOUS_CONTINUED_GROWTH. P9-C OVERALL: PARTIAL.** The authorized 60-minute, fresh-process, real-MP4 full business graph completed with correct events, SQLite, evidence and alerts. Its warm RSS means continued rising in every 10-minute window, including the final 30 minutes. The resource-stability condition for P9-C PASS was therefore not met. **Production unbounded memory leak: NOT CONFIRMED**: a specific retained owner and indefinite growth have not been proven. P9-D/E/F and P9-C.4 were not started. Further decision is required.

P9-A and P9-B remain PASS. Phase 8 remains FINAL RELEASED. Phase 9 final Charter acceptance remains pending. This increment changed diagnostic launch, external sampling, offline validation/analysis, tests and documentation only. No production service, config, model, dependency, schema, adapter or UI change was made.

## 2. PRE-READ and frozen identity

Read `AGENTS.md`, `README.md`, Charter, Master Plan, Current Status, Technical Decisions, Changelog, Test Gates, Risk Register, latest worklog, open-source usage, reference assets, dataset card, Phase 9 plan and the P9-C.1/C.2/C.3/C.3a–e reports before editing. No new governance conflict was found. The current authorized scope was lean real full-graph confirmation, without further component attribution or production repair.

Runtime: Windows 11, Python 3.12.1, CPU-only `.venv-final-demo-verify`. Entry and exit preflight, `run_demo.py --check` and `pip check` passed. `pip freeze` before/after inventories in `artifacts/p9c3/p9c3f-pip-before.txt` and `p9c3f-pip-after.txt` match byte-for-byte.

| Frozen item | SHA256, unchanged at exit |
| --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| `configs/tracker.yaml` | `42ec753ee1511b9de652a750b2d67a384f4aea95d56b43a98d287c877121f10a` |
| `locks/FINAL-DEMO-RUNTIME-001/requirements.txt` | `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |
| Frozen 47-frame real MP4 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |
| Source `data.yaml` | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Processed checksum manifest | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |

Branch `main`, HEAD, `origin/main` and the historical `phase-8-final-integration-complete` tag target all remained `6c38a4ea51eec9a62f433683a3447c073852cbbd`. Existing uncommitted work was preserved. No commit, tag, push, reset or clean was performed.

## 3. Why this confirmation was necessary

Historical P9-C.2 real-MP4 60-minute growth was measured with heavy diagnostic assembly. P9-C.3e reproduced historical N's direction/order in a matched H bridge: H ran 150 cycles/events over 20 minutes with +0.03127 MiB/cycle RSS and +0.22384 MiB/min at 10–20 minutes. Lean J ran the same 150 cycles/events over 20 minutes with +0.00408 MiB/cycle and +0.02986 MiB/min. This supports a material diagnostic-harness contribution; it does not prove the real full graph is bounded. P9-C.3f removed that observation assembly and measured the actual real graph for 60 minutes.

## 4. Lean graph and observation exclusions

`scripts/run_p9c3f_lean_full_graph.py` builds `MonitoringService` with real MP4 decoding, `InferenceService`/YOLO `best.pt`, `ByteTrackPersonTrackingAdapter`, `PPEPersonAssociationAdapter`, `ComplianceService`, `EventService`/`EventEngine`, `EventIngestService`, file-backed SQLite `EventRepository`/`SnapshotRepository`, `SnapshotService`, and formal `AlertService` with Console and Web adapters. The Console sink discards display text while retaining formal delivery semantics. TTS was not registered in the P9-C.2 headless comparison graph and was not added here; its separate P9-C.1 evidence still applies.

The launcher does not import or construct `Observed*`, `BoundedRecorder`, `TimedAlertAdapter`, fixture detections/tracks, per-frame timing/tracking/association/timeline records, `tracemalloc` or GC object scans. It holds aggregate counters and the current `MonitoringStatus`; each completed cycle writes one small JSONL summary and flushes. There is no artificial 8-second pacing, frame skipping or parameter adjustment. The formal JSON event store remains part of business persistence, not a diagnostic recorder.

`scripts/sample_p9c3f_process.py` runs as a separate process, targets the business PID with existing `psutil`, and streams timestamp, monotonic elapsed time, RSS, VMS/private, CPU, thread, handle and open-file counts to CSV with a five-second target interval. It retains no sample history in memory. The measurement process performs no RSS probe or full database/file scan. Offline verification and Dashboard AppTest ran only after the business process exited.

## 5. Sampler smoke and formal 60-minute run

The pre-run smoke used two real MP4 cycles in a fresh process: 94 frames, 2 events, 2 SQLite rows, 2 verified snapshots, 4 delivered alerts, 0 failures and 5 external samples. Both processes exited normally. Artifacts: `artifacts/p9c3/p9c3f-20260927T113352Z-9a920840/`.

The formal fresh-process run is `artifacts/p9c3/p9c3f-20260927T113427Z-442f873b/`. It ran **3602.625 seconds**, completing **692 full cycles × 47 frames = 32,524 real frames** at natural speed. The external CSV has 691 samples from 0.0 to 3599.609 seconds; actual intervals were 5.156–5.312 seconds (mean 5.217) against a five-second target. Every cycle summary reports `COMPLETED` and 47 frames, and the launcher joins its worker before the next `start()`. At the deadline the current cycle was allowed to finish; there was no partial cycle or force kill. Final action was `completed_current_cycle`; final worker exited and the sampler exited 0.

The formal `MonitoringService._run()` closes its source in `finally` before setting `COMPLETED`; `wait()` joins the worker. Thus each recorded `COMPLETED`/joined cycle implies source close without inserting a source wrapper. This is code-path/lifecycle evidence, not a separately timed source-close trace. The 692 cycles yielded 53,284 detections, 45,672 tracks, 692 associations and 692 events. The repeated short scene produced one `PPE_UNKNOWN` event per cycle in this run; the validator compares actual counters and storage rather than forcing that expected behavior.

## 6. Post-run correctness and Dashboard

`scripts/validate_p9c3f_lean_full_graph.py` reopened the final SQLite after process exit and paged through every event ID. It found **692 unique rows**, 692 JSON business events, 692 snapshot metadata references, 692 JPG files and **692 verified hashes and dimensions**. There were 1,384 successful Console/Web deliveries, zero failures and no orphan/missing evidence. Database size was 0 to 770,048 bytes; snapshot directory 0 to 125,459,600 bytes, consistent with intentional disk evidence creation. The validation result is `outputs/validation.json` under the run root.

Post-run Streamlit AppTest loaded Overview, Event Explorer, Evidence Viewer and Statistics from that final database with zero exceptions. Overview and Statistics each displayed 692 total events; Evidence Viewer displayed `VERIFIED`. Page loads were 7625, 735, 1224 and 686 ms respectively (first page includes cold startup). Its artifact is `outputs/dashboard-postrun.json`.

## 7. External resource windows and classification

Values are RSS **mean / median / minimum / maximum MiB** from the external CSV. The 0–10-minute window includes cold imports/model initialization and is excluded from warm-slope decisions.

| Minutes | Samples | RSS MiB | Threads mean | Handles mean | Open files mean |
| --- | ---: | --- | ---: | ---: | ---: |
| 0–10 | 116 | 449.19 / 455.37 / 24.28 / 471.65 | 68.59 | 592.52 | 2.98 |
| 10–20 | 115 | 469.88 / 470.24 / 417.91 / 478.91 | 67.49 | 592.90 | 3.01 |
| 20–30 | 115 | 483.40 / 483.57 / 473.00 / 492.32 | 68.15 | 594.42 | 3.01 |
| 30–40 | 115 | 496.78 / 496.43 / 485.82 / 505.71 | 68.12 | 594.16 | 3.00 |
| 40–50 | 115 | 510.16 / 509.98 / 501.79 / 516.79 | 68.24 | 595.19 | 3.00 |
| 50–60 | 115 | 521.17 / 521.13 / 511.74 / 528.38 | 68.16 | 594.57 | 3.00 |

Ordinary least-squares RSS slopes are **+1.2935 MiB/min (10–60)**, **+1.2710 (20–60)** and **+1.2200 (30–60)**. The last three window means rise 496.78 → 510.16 → 521.17 MiB, successive increases +13.37 and +11.01 MiB. All five warm-window means rise clearly; even the final half-hour remains strongly positive. Per-minute single-point dips do not form a plateau. This is **SUSPICIOUS_CONTINUED_GROWTH**, based on the observed shape rather than an arbitrary numerical PASS threshold. `outputs/resource-analysis.json` contains the complete window metrics. The window mean VMS/private values also rise from 1758.23 MiB at 10–20 to 3675.45 MiB at 50–60; on this Windows psutil view, `private` reflects committed virtual memory and is not proof of resident retained objects. Thread, handle and open-file means remain broadly stable after warmup.

Historical P9-C.2 heavy-MP4 warm means were 471.65 → 485.78 → 497.63 → 509.57 → 522.09 MiB, with +1.2478 MiB/min over 10–60 minutes. P9-C.3f's **shape and slope direction** are similar, while absolute cross-process RSS baselines are not attribution evidence. The H/J result still supports an observation contribution under its matched cached/precomputed workload, but that contribution did not eliminate the real full-graph 60-minute trend. The new lean measurement independently reproduces resource growth under production-like observation. It does not identify an allocation owner or prove indefinite growth.

The P9-C.2 real USB 60-minute result remains a separate **STABLE_PLATEAU** with +0.0484 MiB/min and clean Stop/restart. It was not rerun. The production alert `_completed` maps still retain unique event IDs; the prior 10,000-event micro showed a small short-run contribution, and this known long-horizon risk was not changed. TTS, RTSP, multi-person crossing and visual polish were outside this memory confirmation scope.

## 8. Gate decision, regression and next state

| Gate | Decision |
| --- | --- |
| C3F-G1 lean graph excludes heavy observers | PASS, builder/source audit and quick tests |
| C3F-G2 external sampler smoke | PASS, two cycles/five samples, normal exits |
| C3F-G3 real full graph ≥60 minutes | PASS, 3602.625 s |
| C3F-G4 47-frame EOF lifecycle | PASS, 692 `COMPLETED` cycles; formal close/final-state/join path |
| C3F-G5 events/SQLite/snapshot/alert consistency | PASS, 692/692/692/1384, zero failures |
| C3F-G6 snapshot integrity | PASS, 692 file/hash/dimension checks |
| C3F-G7 RSS windows and slopes | PASS, six windows and 10–60/20–60/30–60 slopes |
| C3F-G8 resource classification | EVIDENCE PASS; **SUSPICIOUS_CONTINUED_GROWTH**, stability condition failed |
| C3F-G9 worker/source final lifecycle | PASS, joined worker and source close implied by formal `COMPLETED` path |
| C3F-G10 Dashboard smoke | PASS, four pages, zero exceptions, counts/VERIFIED |
| C3F-G11 package inventory | PASS, byte-for-byte `pip freeze` match |
| C3F-G12 full regression | PASS, 731 tests; compileall, preflight, demo check, pip check, diff check |
| C3F-G13 frozen assets | PASS, model/config/lock/MP4/dataset/Git identity unchanged |

Eight new deterministic tests guard graph wiring and excluded observation, sampler schema/streaming, cycle streaming, analysis slopes and shape candidates. Full suite **731 passed, 0 failed**. `python -m compileall -q core infra services utils web scripts diagnostics`, preflight, demo check, pip check and `git diff --check` passed. No production code or dependency set changed.

**P9-C.3f PARTIAL / P9-C OVERALL PARTIAL.** The business and reliability path passed, but the final lean MP4 resource-stability criterion did not. P9-D UI/UX POLISH is **NOT READY / NOT AUTHORIZED**. The next step is a human decision on whether to authorize focused resource attribution or a revised acceptance decision; P9-C.4/D/E/F must not start automatically.

Changed this increment: `scripts/run_p9c3f_lean_full_graph.py`, `scripts/sample_p9c3f_process.py`, `scripts/validate_p9c3f_lean_full_graph.py`, `scripts/analyze_p9c3f_lean_resources.py`, `tests/test_p9c3f_lean_confirmation.py`, this report, the P9-C.3 aggregate report, Phase 9 plan, Current Status, Test Gates, Risk Register, Changelog and worklog. Raw run artifacts are ignored and retained for review.
