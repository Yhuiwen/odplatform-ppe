# P9-C.2 Long-Run Stability & Memory Attribution — 2026-09-25

## Decision

**P9-C.2 RESULT: PARTIAL. P9-C.3 RESOURCE LEAK ATTRIBUTION REQUIRED. P9-D is not authorized.** Both 60-minute business chains completed with intact evidence, but the bounded-observer MP4 loop retained a sustained warm RSS rise. The observation is sufficient to block a stability PASS; it does not yet identify a leaking component or prove indefinite growth. P9-A, P9-B and P9-C.1 remain PASS; their gates are not reopened. Phase 9 final delivery acceptance remains pending.

## PRE-READ, Git and runtime identity

Before changes, read `AGENTS.md`, `README.md`, Charter, Master Plan, Current Status, Technical Decisions, Test Gates, Risk Register, Phase 9 plan and the named P9-A/P9-B/P9-C.1 reports. No governance conflict was found. The user authorized P9-C.2 only. `main`, HEAD and `origin/main` were `6c38a4ea51eec9a62f433683a3447c073852cbbd`; the Phase 8 final release tag is `phase-8-final-integration-complete`. Existing working-tree changes were preserved. No commit, tag, push, reset, model, dataset or production configuration change was made.

The runtime was `.venv-final-demo-verify`, Python 3.12.1, Windows 11, Intel Core i5-1340P, CPU only. Preflight, demo check, pip check and `git diff --check` passed before measurement. Frozen identities: `models/checkpoints/EXP-001/best.pt` SHA256 `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`; `configs/inference.yaml` SHA256 `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`; `locks/FINAL-DEMO-RUNTIME-001/requirements.txt` SHA256 `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4`. The real MP4 is the frozen 47-frame asset, SHA256 `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852`.

## Observer redesign and boundedness

`scripts/run_p9b_full_chain.py` now offers an optional bounded diagnostic recorder; the default historical recorder remains available. Every detailed frame/timing/tracking/association/timeline/resource record is appended to JSONL, while in-memory rolling lists and dictionaries retain at most 200 records. Cumulative counters and finite category summaries remain in memory. The official `MonitoringService` source → YOLO → ByteTrack → association → compliance → temporal event → SQLite → snapshot → Console/Web graph is unchanged. `scripts/run_p9c_long_run.py` drives isolated long runs and verifies post-run evidence; `scripts/analyze_p9c2_resources.py` computes windows and trends; `scripts/run_p9c2_postrun.py` checks Dashboard pages. A synthetic 20,000-record test per container verified a 100-row in-memory cap and 20,000 JSONL lines. Resource samples target five-second intervals and use monotonic clocks. Raw diagnostics are in ignored `artifacts/p9c2/<run_id>/`.

## USB Camera 0: 60-minute chain and restart

Run `20260925T120850Z-0d6791eb` used one uninterrupted 60-minute Camera 0 service cycle, followed by a normal Stop and a 40-second same-service restart. The main cycle processed 31,965 frames; restart processed 394; total 32,359. Across both cycles there were 15 unique events, 15 reopened SQLite rows, 15 snapshot metadata rows and files with verified hash/dimensions, 30 successful Console/Web deliveries and zero delivery failures. Source opened and closed twice and both workers exited. The main Stop, requested during `infer_frame`, returned in 375.22 ms; worker exit and camera close occurred at 375.09 and 374.96 ms. Restart Stop returned in 334.86 ms, with worker exit/camera close at 334.74/334.60 ms. Neither returned an error. No event loss, duplicate ID, orphan evidence or silent snapshot failure was found.

**USB memory classification: STABLE_PLATEAU for the uninterrupted 60-minute main cycle.** The 10–60-minute linear RSS slope was +0.0484 MiB/min; warm-window mean rose only from 437.24 to 439.15 MiB. The overall peak 457.86 MiB and final 457.23 MiB include the subsequent restart, so they must not be used as the main-cycle trend. Threads, handles and open-file counts reached a warm plateau (means near 55, 1,020 and 14 respectively). The restart transient requires separate consideration in future repeated-lifecycle testing.

## MP4: 60-minute loop and integrity

Run `20260925T131019Z-f934be1f` used a new Python process. It completed **675 full source cycles × 47 frames = 31,725 actual frames** over at least 60 minutes. Every cycle had 47 processed frames, EOF/COMPLETED, a source open and close, and a worker exit. There was no partial final cycle or fabricated frame. All 675 unique `PPE_UNKNOWN` events persisted as 675 SQLite rows, with 675 metadata rows, 675 files and 675 verified hashes/dimensions; 1,350 Console/Web deliveries succeeded and none failed. Each source lifecycle is recorded in `metrics/cycles.jsonl` and `metrics/timeline.jsonl`.

**MP4 memory classification: SUSPICIOUS_MONOTONIC_GROWTH.** Warm RSS means rose in every window, from 471.65 MiB at 10–20 minutes to 522.09 MiB at 50–60 minutes; 10–60-minute linear slope was +1.2478 MiB/min. Peak was 530.60 MiB and final 527.89 MiB. Thread, handle and open-file means stayed near 69, 622 and 10, so the observed RSS growth is not accompanied by a corresponding thread/handle/file count increase. These measurements cannot distinguish retained Python objects from native allocation, allocator caching or fragmentation. See the [attribution report](P9C2_MEMORY_ATTRIBUTION_REPORT.md).

## Resource windows and slope

Values below are RSS mean / median / min / max in MiB. The cold 0–10-minute window includes imports and model initialization and is excluded from the reported warm slope.

| Window | USB RSS | MP4 RSS |
| --- | --- | --- |
| 0–10 | 427.58 / 436.48 / 27.19 / 438.44 | 449.38 / 456.30 / 27.38 / 466.46 |
| 10–20 | 437.24 / 436.91 / 436.62 / 438.92 | 471.65 / 472.58 / 458.98 / 479.69 |
| 20–30 | 438.06 / 437.91 / 437.68 / 440.06 | 485.78 / 486.18 / 476.00 / 492.99 |
| 30–40 | 438.61 / 438.77 / 437.84 / 440.86 | 497.63 / 497.87 / 489.03 / 505.37 |
| 40–50 | 438.98 / 438.94 / 438.76 / 440.99 | 509.57 / 509.39 / 501.41 / 516.24 |
| 50–60 | 439.15 / 439.07 / 438.79 / 440.94 | 522.09 / 521.92 / 514.18 / 530.60 |

The USB warm-window mean thread counts were 55.14, 55.21, 54.94, 54.95 and 55.05; handle means 1020.24, 1020.61, 1019.78, 1019.47 and 1020.73. MP4 thread means were 68.96, 68.26, 68.88, 68.75 and 69.04; handle means 622.00, 621.99, 622.24, 622.20 and 622.68. No sustained thread or handle growth was observed. MP4 per-cycle source close and stable open-file counts provide lifecycle evidence; they do not explain the RSS rise.

## Disk, database, alerts and Dashboard

Five-minute disk samples are in each run's `outputs/resource-analysis.json`. USB reached 10 events at minute 25; the database remained 86,016 bytes and snapshots 756,668 bytes through minute 60. MP4 grew from 110 events / 200,704-byte database / 19,943,000-byte snapshots at minute 10 to 675 events / 741,376-byte database / 122,377,500-byte snapshots at minute 60. Growth tracks the intentional per-event evidence creation; no orphan files were found. SQLite was reopened after service exit and every event ID/evidence reference was checked through repository/query and file-integrity verification. First, middle and last event IDs were captured in `outputs/validation.json`.

Both databases loaded Overview, Event Explorer, Evidence Viewer and Statistics through Streamlit AppTest after the runs. All pages had zero exceptions; Overview and Statistics totals matched 15 USB and 675 MP4 rows; Evidence Viewer showed `VERIFIED`. USB page loads were 2372/488/583/386 ms; MP4 11550/738/1210/707 ms (Overview includes cold AppTest startup). This headless long-run graph exercised Console and Web delivery, two per event. TTS was not registered or measured in this graph; the existing P9-C.1 isolated native TTS diagnostic remains the applicable evidence. No claim of 60-minute TTS stability is made. The P9-C.1 cold Stop observation was reused; this run tested warm Stop.

## Package stability and regression

The before and after inventories are `artifacts/p9c2/identity/pip-freeze-before.txt` and `pip-freeze-after.txt`; exact comparison **matched**. Final `.venv-final-demo-verify` regression: `python -m pytest -q` **685 passed, 0 failed**; `python -m compileall -q core infra services utils web scripts` exit 0; `python scripts/preflight.py`, `python scripts/run_demo.py --check`, `pip check` and `git diff --check` passed. The three frozen file SHA256 values above matched the pre-run values. `main`, HEAD and `origin/main` remained `6c38a4ea51eec9a62f433683a3447c073852cbbd`; the Phase 8 tag still exists. Dataset identity, Phase 8 contracts and P9-B acceptance were not changed in P9-C.2. No runtime optimization or production service change was made.

## Gate matrix

| Gate | Evidence | Outcome |
| --- | --- | --- |
| C2-G1 | 20,000 synthetic records, rolling cap and JSONL completeness | PASS |
| C2-G2 | Uninterrupted USB main cycle over 60 minutes | PASS |
| C2-G3 | 15 unique rows/files; hashes/dimensions; 30 deliveries | PASS |
| C2-G4 | 375 ms warm Stop; 40-second restart; 335 ms Stop; workers/camera released | PASS |
| C2-G5 | 675 full MP4 cycles over 60 minutes | PASS |
| C2-G6 | 675 × 47 = 31,725; EOF/open/close/exit each cycle | PASS |
| C2-G7 | 675 unique rows/files; hashes/dimensions; 1,350 deliveries | PASS |
| C2-G8 | Both RSS trends classified; MP4 sustained rise remains unattributed | EVIDENCE PASS / STABILITY BLOCKED |
| C2-G9 | Warm thread/handle/open-file windows classified stable | PASS |
| C2-G10 | SQLite reopened; all event/evidence references verified | PASS |
| C2-G11 | Four Dashboard pages per DB; zero exceptions; totals match | PASS |
| C2-G12 | Exact before/after pip inventory comparison | PASS |
| C2-G13 | 685 pytest passed; compileall exit 0 | PASS |
| C2-G14 | Frozen asset/runtime hashes and Git identity unchanged | PASS |

## Limitations, decision and changed files

The MP4 uses one short scene replayed many times, so its event rate and source lifecycle are deliberately heavier than a normal varied live feed. RSS is process-level and does not attribute ownership. The bounded recorder removes its own unbounded per-frame retention but cannot prove every harness component is bounded or distinguish Python from native heap. Windows working-set RSS may remain high after freed allocations. TTS, RTSP, multi-person crossing and on-screen browser interaction were not part of this long-run test. The stable USB result does not cancel the suspicious MP4 result. **P9-C overall remains incomplete; P9-C.3 must attribute MP4 growth before a P9-C PASS decision. P9-D/E/F remain unauthorized.**

P9-C.2 changed only diagnostic scripts, the boundedness test, `.gitignore`, this report, the attribution report and governance/status/worklog documents. Prior P9-A/B/C.1 working-tree changes were preserved.
