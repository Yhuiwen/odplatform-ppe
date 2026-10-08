# P9-C.1 Performance Baseline & Reliability Harness — 2026-09-25

## 1. Result and authority

**P9-C.1 RESULT: PASS.** This is a measured CPU-only baseline, not a new Charter FPS acceptance threshold. P9-A and P9-B remain PASS; P9B-G1–G13 remain PASS. Phase 9 final delivery acceptance remains pending. P9-C.2 long-run stability is not authorized in this report.

The mandatory PRE-READ covered `AGENTS.md`, `README.md`, the Charter, Master Plan, Current Status, Technical Decisions, Test Gates, Risk Register, Phase 9 plan, all eight named Phase 9 P9-A/P9-B reports, and the applicable worklog. No new governance conflict was found. Phase 9 requires latency, throughput, resources and stability measurements with machine, data and command evidence; it sets no mandatory 10/15/30 FPS threshold. The already-authorized P9-A/P9-B working-tree changes were preserved.

## 2. Runtime identity and hardware

| Item | Identity |
| --- | --- |
| Git | `main`; HEAD = `origin/main` = `6c38a4ea51eec9a62f433683a3447c073852cbbd` |
| Phase 8 final tag | `phase-8-final-integration-complete`; historical tags unchanged |
| Runtime | `.venv-final-demo-verify`; Python 3.12.1; Windows 11 Home Chinese, build 22631; CPU only |
| CPU | Intel Core i5-1340P, 12 cores / 16 logical processors |
| Host | HP ProBook 450 15.6 inch G10; 33,982,361,600 bytes physical RAM |
| Model | `models/checkpoints/EXP-001/best.pt`; SHA256 `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Inference config | `configs/inference.yaml`; SHA256 `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| Frozen lock | `locks/FINAL-DEMO-RUNTIME-001/requirements.txt`; SHA256 `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |

Model, inference config, dataset identity, frozen runtime and Phase 8 contracts were not modified. `git diff --check` passed. The preflight, `run_demo.py --check` and `pip check` passed before and after measurement.

## 3. Method and source assets

`scripts/run_p9c_performance.py` reuses `scripts/run_p9b_full_chain.py` and the official `MonitoringService` graph: source → real YOLO checkpoint → ByteTrack → association → compliance → temporal event → SQLite → snapshot → Console/Web alerts. Diagnostic wrappers forward calls and results without changing business decisions. Monotonic `perf_counter_ns` measures stages; UTC event timestamps remain separate. Resource sampling uses `psutil` about once per second. Isolated outputs are under Git-ignored `artifacts/p9c/`.

The MP4 is `artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4`, SHA256 `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852`, 1280×720, 47 frames, nominal 23.976 FPS. USB Camera 0 reports 640×480 and nominal 30 FPS. Nominal source FPS is not processing FPS: the monitoring worker processes frames sequentially. Every measured frame has a row in `performance/frame-timing.jsonl`; event-only database, snapshot and alert fields are `null` on other frames. Raw stage and resource samples are in each run's `outputs/full_chain.json`, with summaries in `performance/profile.json`.

Commands used, with `.venv-final-demo-verify\Scripts\python.exe` as `python`:

```text
python scripts/run_p9c_performance.py --source mp4                 # three independent processes
python scripts/run_p9c_performance.py --source usb --seconds 60
python scripts/run_p9c_performance.py --source usb --seconds 600
python scripts/run_p9c_performance.py --source mp4 --min-duration 600
python scripts/run_p9c_database.py
python scripts/run_p9c_dashboard.py
python scripts/run_p9c_stop.py
python scripts/run_p9c_stop.py --scenario D_cold_inference --repeat 1  # twice, separate processes
python scripts/run_p9c_model_init.py
python scripts/run_p9c_tts.py
python scripts/build_p9c_frame_timings.py
```

## 4. Three independent MP4 runs and effective FPS

Each run started a new Python process and initialized its own service and model. No frame was dropped or fabricated. Each produced 77 detections, 66 track outputs, one association, one `PPE_UNKNOWN` event, one SQLite row, one verified snapshot, two delivered alerts, and zero alert failures.

| Run ID suffix | Frames | Elapsed s | Processing FPS | First inference ms | Remaining inference P50 / P95 ms | Peak RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `18f5b495` | 47/47 | 15.314 | 3.069 | 9,974 | 95.2 / 111.8 | 428.7 |
| `6ef2a3fb` | 47/47 | 15.957 | 2.945 | 10,511 | 86.7 / 113.1 | 430.1 |
| `57a4940c` | 47/47 | 14.125 | 3.327 | 9,241 | 80.7 / 94.6 | 429.0 |

Mean FPS **3.114**, median **3.069**, worst **2.945**, best **3.327**. The cold frame is included in elapsed time and overall FPS. P9-A's 47 frames / 16.36 s / about 2.87 FPS is a historical reference: this three-run mean is about **8.5% higher**, within ordinary cold-start and machine-load variation, with no evidence of a correctness regression. The three runs are independent cold runs, not a deliberately warmed model.

## 5. Model initialization and stage latency

The first `MonitoringService` inference lazily imports/assembles YOLO and predicts. Model lifetime is persistent within one service instance: later frames and MP4 restart cycles reuse its loaded detector. Official service timing: first `_load_model` in the three independent MP4 processes took **5,474 / 5,927 / 5,069 ms**; first `infer_frame` took **9,974 / 10,511 / 9,241 ms**. On 5,969 frames in the repeated run, `_load_model` P50 was only **0.0023 ms** after initialization. Checkpoint SHA256 verification occurs on **every frame**, with repeated-run P50 **11.11 ms** and P95 **15.39 ms**.

An isolated, warm-import diagnostic in `artifacts/p9c/model-initialization.json` measured `torch.load` deserialization at **65.68 ms** and `YOLO(...)` construction (which loads the checkpoint again) at **88.83 ms**. These overlap and must not be added. They exclude cold Python/torch/Ultralytics imports and therefore do not replace the official 5–6 second first model-init measurements.

Selected official repeated-MP4 stage samples (milliseconds; 5,969 frame samples unless noted):

| Stage | Count | Mean | P50 | P95 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Source read, including 127 EOF reads | 6,096 | 3.02 | 2.42 | 3.51 | 51.86 |
| Checkpoint verification | 5,969 | 11.37 | 11.11 | 15.39 | 30.99 |
| Detection / `infer_frame`, including cold frame | 5,969 | 93.30 | 90.31 | 117.53 | 9,816.82 |
| Detection after first frame | 5,968 | 91.67 | 90.29 | 117.49 | 159.07 |
| Tracking | 5,969 | 1.01 | 0.84 | 1.63 | 257.12 |
| Association | 5,969 | 0.024 | 0.022 | 0.039 | 0.187 |
| Compliance | 5,969 | 0.077 | 0.069 | 0.129 | 0.815 |
| Temporal/event | 5,969 | 0.032 | 0.016 | 0.030 | 1.552 |
| SQLite ingest, event frames | 127 | 13.77 | 13.66 | 20.54 | 36.73 |
| Snapshot capture, event frames | 127 | 65.44 | 66.00 | 82.29 | 113.57 |
| Alert dispatch, event frames | 127 | 0.248 | 0.212 | 0.473 | 0.914 |
| Whole frame pipeline | 5,969 | 96.67 | 91.98 | 124.25 | 10,074.38 |

Mean/min/max/P50/P95/P99 and individual per-frame values remain in the machine-readable artifacts. Detection dominates steady frames; snapshot encoding/storage is material only on event frames. Stage intervals can nest, so their values should not simply be summed.

## 6. USB Camera baseline

Run `20260925T110824Z-f8fa522a` lasted **60.424 s**, processed **440 frames** (**7.282 processing FPS**), with 1,320 detections, 440 tracks, 880 associations, two actual Camera events (`NO_HELMET`, `NO_VEST`), two SQLite rows, two verified snapshots, four delivered alerts and zero failures. Camera nominal rate was 30 FPS. First inference was **9,196 ms**; remaining inference P50/P95 was **98.8/124.5 ms**. Source was closed and worker exited normally with `state=stopped`, `error_code=None`.

The scene was the camera's actual view and is not asserted to be a construction-site violation clip. This P9-C.1 measurement does not reopen accepted P9-B gates.

## 7. Ten-minute short stability and resources

| Source / run | Duration s | Total frames | Effective FPS | Events / verified snapshots | Delivered alerts | Lifecycle |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| USB `10ac6f11` | 600.362 | 5,631 | 9.379 | 2 / 2 | 4 | Camera closed; worker exited |
| MP4 `d351609e` | 600.887 | 5,969 = 127×47 | 9.934 | 127 / 127 | 254 | 127/127 EOF completions; worker exited each cycle |

No database error, snapshot integrity failure, alert failure, duplicate event ID or lost event was observed. The 127 MP4 cycles each reopened/closed the source and completed exactly 47 frames. CPU percentage is `psutil` process CPU usage, where 100% is approximately one logical CPU; it is not total host utilization.

| Run | CPU initial / mean / peak / final % | RSS initial / mean / peak / final MiB | Threads initial / mean / peak / final | Handles initial / final |
| --- | --- | --- | --- | --- |
| USB 60 s | 0.0 / 35.1 / 125.8 / 38.5 | 26.9 / 378.2 / 438.9 / 438.9 | 5 / 54.8 / 61 / 58 | 210 / 1,003 |
| USB 600 s | 0.0 / 45.5 / 124.7 / 50.8 | 26.9 / 455.0 / 489.6 / 488.9 | 5 / 56.2 / 61 / 55 | 210 / 992 |
| MP4 600 s | 0.0 / 43.5 / 97.0 / 29.2 | 27.3 / 470.7 / 505.5 / 500.9 | 5 / 69.5 / 76 / 70 | 210 / 598 |

The initial CPU 0.0% is the `psutil` baseline call; the initial RSS sample precedes lazy model import. A meaningful warm trend is USB RSS mean **437.2 → 457.9 → 486.5 MiB** across 30–90, 240–300 and 540–600 s; MP4 is **452.2 → 470.4 → 499.8 MiB** over the same windows. Thread means were USB **58.5 → 56.5 → 55.1** and MP4 **73.3 → 68.3 → 69.1**; no monotonic thread growth. The observer deliberately retains per-frame timings, tracking details and associations in memory, and its long-run JSON grew to 20.0 MB (USB) and 6.8 MB (MP4). These runs reveal an RSS growth trend but do **not** establish a production memory leak. P9-C.2 should use a bounded or streaming observer for attribution. Raw one-second resource rows include elapsed time, frames, CPU, RSS, threads, handles, event/alert counts, database size and snapshot-directory size; they exceed the requested five-second sampling frequency.

## 8. SQLite and Dashboard larger-history baseline

The isolated database benchmark uses deterministic **SYNTHETIC PERFORMANCE DATA** at 100, 1,000 and 5,000 events, each with matching snapshot metadata and an actual synthetic JPEG. These are never presented as real runtime events. Fifty read repetitions per scale used real repository and dashboard query services. All figures below are P95 milliseconds.

| Rows | Event insert | Snapshot metadata insert | List query | Detail query | Snapshot join | Statistics | DB MiB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 16.44 | 15.29 | 16.08 | 6.67 | 6.63 | 7.08 | 0.12 |
| 1,000 | 16.61 | 15.44 | 11.97 | 4.25 | 3.96 | 5.46 | 0.74 |
| 5,000 | 16.39 | 15.03 | 23.97 | 7.51 | 6.03 | 21.54 | 3.30 |

Mean, P50, P95, minimum and maximum for each operation are recorded in `artifacts/p9c/synthetic-database/database-benchmark.json`. The 100-row reads were sometimes slower than 1,000-row reads because these are short, sequential single-host measurements with cache/startup noise; no monotonic claim is made from one pass.

Streamlit AppTest ran Overview, Event Explorer, Evidence Viewer and Statistics at all three scales: **12/12 page loads**, zero exceptions, correct total/type counts, and a `VERIFIED` Evidence Viewer image at each scale. At 5,000 rows, page load times were **520 / 642 / 700 / 716 ms** respectively. The first 100-row Overview load took **3,349 ms** due to first AppTest/page startup; these are test-harness load times, not browser network latency. Full values are in `dashboard-benchmark.json`.

## 9. Snapshot growth and retention

Real MP4 snapshots averaged **181,300 bytes** across 127 captures; real USB snapshots averaged **70,489.5 bytes** across four captures. Estimated file-only storage, excluding SQLite/filesystem overhead:

| Event count | MP4-like 720p estimate MiB | USB-like 480p estimate MiB |
| ---: | ---: | ---: |
| 100 | 17.29 | 6.72 |
| 1,000 | 172.90 | 67.22 |
| 10,000 | 1,729.01 | 672.24 |

The 10,000-event row is an **estimate**, not 10,000 observed real snapshots. RISK-023 remains open: there is atomic write, hash/dimension verification and date partitioning, but no implemented retention/archive policy, disk monitor or database/file reconciliation. No cleanup system was introduced in P9-C.1.

## 10. Alert timing and failure isolation

For 127 actual MP4 event deliveries, Console adapter P50/P95 was **0.096/0.235 ms**, Web adapter **0.028/0.061 ms**, and `AlertService.dispatch_event` **0.212/0.473 ms**. The harness has Console/Web adapters, as in P9-B. All 254 sends succeeded. SQLite persistence and verified snapshot counts matched events throughout. Existing P9-B injected-failure evidence still demonstrates that alert failure does not undo persistence; this run observed no failure to inject.

The live dashboard runtime also enables TTS. An **isolated live-backend diagnostic** (`artifacts/p9c/tts-diagnostic.json`) delivered one short spoken message: engine initialization **524 ms**, `say` enqueue **0.012 ms**, `runAndWait` speech wait **1,863 ms**, and full adapter call **2,387 ms**. This is one diagnostic, not a percentile or a simultaneous USB pipeline measurement. Speech wait can block the event frame in the default live alert graph; it must not be mislabeled as Console/Web dispatch cost. No TTS setting was changed.

## 11. Stop, EOF and source-failure boundary

`scripts/run_p9c_stop.py` used actual Camera 0 and the official 5-second Stop join. Two repetitions each:

| Scenario | Requested stage | Stop return ms | Camera close / worker exit | Outcome |
| --- | --- | --- | --- | --- |
| A, warm steady after 20 frames | `source.read` | 379 / 389 | both <389 ms | stopped, no error |
| B, request just after read completion | next `infer_frame` had begun | 418 / 410 | both <419 ms | stopped, no error |
| C, warm inference | `infer_frame` | 476 / 507 | both <508 ms | stopped, no error |
| D, **fresh Python process**, first inference | `infer_frame` | 5,059 / 5,027 | 9,591 / 10,135 ms | `MONITORING_STOP_TIMEOUT`, then worker exited |

The B trigger proves a completed read was observed; the worker had already entered warm inference when Stop was requested, so it is **not** falsely reported as a Stop during read. The D attempts deliberately used separate fresh processes because two same-process attempts reused warm framework state and did not reproduce the timeout; their diagnostic records remain in `stop-boundary.json` but are not used as cold results. Fresh-process records are `stop-boundary-D_cold_inference-20260925T114343Z-0c4f0aa8.json` and `stop-boundary-D_cold_inference.json`. The previously accepted P9-B report independently observed a 5.009-second Stop timeout and eventual worker exit at 8.905 seconds. This is a quantified known cold-inference limitation, not a reopened P9-B failure.

The MP4 long run observed **127/127 `COMPLETED` EOF cycles**, source close and worker exit, with no extra fabricated frames. USB 60/600-second runs closed the source and exited. Invalid Camera index 64 returned `FAILED / SOURCE_OPEN_FAILED`, **0 frames**, and worker exit in run `20260925T114555Z-62dee20b`. P9-B's five processed-frame repeated-start/stop cycles remain valid and were not needlessly repeated dozens of times.

## 12. Package stability, correctness and regression

`pip freeze` before/after performance testing was **identical** (`artifacts/p9c/identity/`). No AutoUpdate or dynamic install was observed. Preflight, Demo check, `pip check`, `compileall -q core infra services utils web scripts`, and `git diff --check` passed. `python -m pytest -q`: **684 passed, 0 failed**. The before/after hashes of model, inference config and runtime lock match section 2. No dataset, configuration, model or historical Git tag was changed. Correctness checks matched frame, event, SQLite, snapshot and alert counts on every benchmark. P9-B acceptance evidence remains intact.

## 13. Bottleneck ranking, Demo judgment and candidates

1. **Cold model/import/first prediction**: roughly 9–10.5 seconds on a fresh process; directly explains the >5-second cold Stop boundary.
2. **Steady detection**: roughly 90–100 ms P50, much larger than tracking, association, compliance and temporal processing.
3. **Per-frame checkpoint SHA256**: about 11 ms P50, providing integrity assurance at measurable CPU/I/O cost.
4. **Event-frame snapshot capture**: 66 ms P50 on 720p MP4; infrequent and correctly persisted before alert.
5. **Live TTS speech wait**: one measured 1.86-second playback wait; applies only when TTS delivers an event.
6. SQLite list/statistics at 5,000 synthetic rows and Console/Web dispatch were much smaller than detection on this host.

The current CPU-only Demo is **usable with an explicit performance limitation**: USB processed continuously at 7.28 FPS in the 60-second cold run and 9.38 FPS over 10 minutes, events and pages remained functional, and no crash occurred. Camera nominal 30 FPS is not a display/update guarantee. No arbitrary FPS threshold was introduced. The unresolved RSS trend and cold Stop timeout require candid Demo documentation and longer follow-up.

| Candidate for later decision | Expected benefit | Risk / evidence |
| --- | --- | --- |
| Keep a model-ready process before live demonstration | Avoid ~9–10 s first frame | Startup/RAM cost; existing service already reuses model after first frame |
| Profile detection internals and import path | Reduce dominant steady/cold latency | Frozen model/config must remain unchanged until separately authorized |
| Review checkpoint verification frequency with integrity controls | Recover ~11 ms per frame | Any caching could weaken tamper detection; no change in this phase |
| Stream benchmark diagnostics in later long run | Distinguish observer growth from runtime growth | Current observer intentionally accumulates frame records; no production change needed |
| Review TTS scheduling after user-visible needs are agreed | Avoid event-frame speech wait | Speech timing/order could change; one diagnostic only |
| Reassess snapshot/storage and history indexes if data grows | Limit event-frame I/O and 5,000-row query growth | Current results do not justify immediate schema/storage changes |

## 14. Files changed and local work Gates

P9-C.1 added this report, `scripts/run_p9c_performance.py`, `run_p9c_database.py`, `run_p9c_dashboard.py`, `run_p9c_stop.py`, `run_p9c_model_init.py`, `run_p9c_tts.py`, and `build_p9c_frame_timings.py`; it extended the existing untracked `scripts/run_p9b_full_chain.py` with optional diagnostic wrappers/metrics and added `artifacts/p9c/` to `.gitignore`. Production services, thresholds, dataset, checkpoint and frozen runtime were not changed. P9-A/P9-B working-tree changes were preserved.

| Local Gate | Result | Evidence |
| --- | --- | --- |
| C1-1 repeated MP4 | PASS | Three independent 47/47 cold runs |
| C1-2 stage latency | PASS | Per-frame JSONL and full stage samples, cold/warm split |
| C1-3 USB baseline | PASS | Real Camera 0, 60.424 seconds |
| C1-4 CPU/RAM/thread profile | PASS | One-second process samples, handles included |
| C1-5 short stability | PASS | MP4 and USB each >600 seconds; known RSS trend documented |
| C1-6 SQLite and larger history | PASS | Isolated synthetic 100/1,000/5,000; 12 AppTest page loads |
| C1-7 Stop boundary | PASS | Warm A/B/C plus two fresh-process cold D timeouts quantified |
| C1-8 runtime package set | PASS | Exact `pip freeze` match |
| C1-9 correctness | PASS | Counts and evidence integrity matched; EOF/source-failure checked |
| C1-10 full tests | PASS | 684 passed, 0 failed |

**P9-C.2 LONG-RUN STABILITY READY / WAITING FOR HUMAN AUTHORIZATION.**
