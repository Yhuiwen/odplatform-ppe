# P9-C.3i Inference Worker / Session Lifecycle Isolation — 2026-10-07

## 1. Scope and decision

**P9-C.3i RESULT: PASS as a diagnostic attribution increment; P9-C OVERALL: PARTIAL.** This authorized study isolates real inference execution context from `MonitoringService` session orchestration. It changes only diagnostic runners, tests and records. It does not change production services, YOLO, model/config, dependencies, thread settings or business semantics. P9-C.4 and P9-D/E/F remain unauthorized.

**REAL INFERENCE × FRESH WORKER THREAD: STRONGLY SUPPORTED** as the observed 20-minute resource-growth mechanism. Direct main-thread inference (T0), one persistent inference worker (T1), and H0 with a persistent inference bridge (T4) approached a plateau. A fresh worker per cycle without `MonitoringService` (T2) and formal H0 (T3) grew at virtually the same rate. **MEMORY LEAK OWNER: NOT IDENTIFIED; PRODUCTION UNBOUNDED MEMORY LEAK: NOT CONFIRMED.**

## 2. Frozen identity and motivation

The required pre-read found no governance conflict. Phase 8 is FINAL RELEASED; P9-A/B PASS; P9-C overall PARTIAL. Historical P9-C.3h H0 (real inference, precomputed Track, formal `MonitoringService`, empty downstream) grew +0.10318 MiB/cycle over 20 minutes, matching full RP +0.10255. Earlier inference-only M approached a plateau without formal session wiring. The present controls discriminate thread reuse, thread churn and session handling.

All runs used Windows/Python 3.12.1, CPU-only `.venv-final-demo-verify`, the same 47 cached decoded MP4 frames and `FrameData.image` objects, the same real `InferenceService`/YOLO model per process, approximately eight-second post-cycle pacing, separate fresh Python processes and the P9-C.3f external psutil sampler at about five-second intervals. Timed runs used no per-frame recorder, `tracemalloc`, GC scan, heavy observer, new video decode or image copy. The service/detector/model object IDs stayed constant across cycles in every cell.

| Frozen item | SHA256, verified unchanged |
| --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| `configs/tracker.yaml` | `42ec753ee1511b9de652a750b2d67a384f4aea95d56b43a98d287c877121f10a` |
| `locks/FINAL-DEMO-RUNTIME-001/requirements.txt` | `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |
| Frozen 47-frame MP4 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |
| Detection fixture | `c8c53966fb1117a26f23df648f6e21179555e32f0cb6bd1a7a4f48addedd8f38` |
| Track fixture | `0e42709fab781ba79eb135da09789212ff932e7ee412c33c0b571919f8ec76c1` |
| Source `data.yaml` | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Processed checksum manifest | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |

Branch `main`, HEAD, `origin/main`, and dereferenced historical `phase-8-final-integration-complete` tag target all remained `6c38a4ea51eec9a62f433683a3447c073852cbbd`. No tag was changed.

## 3. T0–T4 design and semantic gates

| Cell | Real inference execution | Other formal wiring | Diagnostic worker lifecycle |
| --- | --- | --- | --- |
| T0 | Main thread, one reused service/model | None | 0 workers |
| T1 | One persistent worker, reused service/model | None | One create/join |
| T2 | Fresh worker per 47-frame cycle, reused service/model | None | One create/join per cycle |
| T3 | `MonitoringService` H0 worker, reused service/model | Precomputed Track, empty downstream | One create/join per cycle |
| T4 | One persistent inference thread reached synchronously from each H0 worker | Same H0 wiring as T3 | One inference thread plus one H0 worker per cycle |

T4 was triggered only after T2 and T3 both showed material growth. Its diagnostic adapter has a queue of capacity one, returns actual `DetectionResult` synchronously, never batches/skips frames, and joins cleanly at shutdown. `MonitoringService` production code was untouched. Two-cycle fresh-process smoke runs for each cell verified 94 frames/154 detections and each frame's count, class, confidence and bbox against the frozen Detection fixture. T3/T4 also verified 66 precomputed tracks per cycle. All smoke workers and external samplers exited cleanly.

## 4. Formal 20-minute results

All formal runs completed their 47-frame cycles, with 77 real detections per cycle. Post-exit validation checked cycle/frame/detection counts, service/model identity, source count, thread creation/join and sampler exit. Each cell passed.

| Cell | Artifact root under `artifacts/p9c3i/` | Cycles / frames | Threads created/joined | External samples | RSS 2–5 / 5–10 / 10–20 min means (MiB) | RSS 2–20 MiB/cycle | RSS 2–20 / 10–20 MiB/min | Classification |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| T0 | `t0-20261007T024758Z-a02d6959` | 149 / 7003 | 0 / 0 | 230 | 468.224 / 468.181 / 468.322 | +0.001441 | +0.01072 / +0.00970 | STABLE_PLATEAU |
| T1 | `t1-20261007T030911Z-98385110` | 150 / 7050 | 1 / 1 | 231 | 467.798 / 468.011 / 468.083 | +0.002306 | +0.01733 / +0.00250 | STABLE_PLATEAU |
| T2 | `t2-20261007T032941Z-35fcc5b0` | 149 / 7003 | 149 / 149 | 229 | 489.497 / 492.735 / 498.543 | +0.104461 | +0.78137 / +0.76923 | MATERIAL_CONTINUED_GROWTH |
| T3 | `t3-20261007T035041Z-0c0e42a0` | 150 / 7050 | 150 / 150 | 231 | 488.786 / 492.148 / 497.894 | +0.104319 | +0.78268 / +0.77812 | MATERIAL_CONTINUED_GROWTH |
| T4 | `t4-20261007T041309Z-60271d72` | 150 / 7050 | 151 / 151 | 231 | 469.967 / 470.072 / 470.303 | +0.003306 | +0.02479 / −0.00504 | STABLE_PLATEAU |

The corresponding 2–20-minute RSS slopes per frame are T0 +0.0000307, T1 +0.0000491, T2 +0.0022226, T3 +0.0022196 and T4 +0.0000703 MiB/frame. Differences in initial process RSS are not interpreted as growth; slopes and windows are the comparison. T2 and T3 differ by only ~0.000142 MiB/cycle, while the T4 bridge reduces the T3 slope by about 97% and has a flat/slightly negative late slope.

## 5. VMS/private, threads, handles and files

In the 10–20-minute window, VMS/private means were about 1021.37/1021.72/1503.40/1505.35/1023.96 MiB for T0–T4. The respective 2–5-minute means were about 1021.39/1021.39/1146.71/1146.43/1023.07 MiB. Thus VMS/private rose strongly in T2/T3 but stayed near its warm level in T0/T1/T4. The external sampler's Windows `vms` and `private` fields coincide in this run; they are reported as observed, not added together.

In 10–20 minutes, mean process thread counts were T0 36.45 (36–39), T1 37.29 (37–40), T2 36.96 (36–40), T3 37.09 (36–40), T4 38.09 (37–41). Mean handles were 554.20/561.10/552.71/558.67/571.74; open files were about 2/2/2/2/4. T4's extra persistent thread and files are expected bridge overhead. No increasing live thread or open-file count accompanies T2/T3 RSS growth. Stable process thread counts do not rule out native thread-local allocator retention after each worker exits.

## 6. Worker/session attribution and production boundary

T0 and T1 show that direct inference and inference on a reused non-main thread were near stable under this harness. T2 reproduces H0-scale growth without `MonitoringService`, precomputed Track or business downstream, so those components are not required for this 20-minute effect. T3 independently reconfirms H0 at the same scale. T4 retains formal H0 session/worker churn but routes actual YOLO inference through one long-lived thread; its RSS slope collapses toward T1. This strongly supports **real inference execution on a newly created worker thread each cycle** as the interaction that drives the observed resource growth. A separate material `MonitoringService`-specific contribution is **NOT SUPPORTED** by these matched slopes; small overhead cannot be excluded.

The retained owner remains unobserved. PyTorch/Ultralytics/native-runtime thread-local caching, TLS, allocator high-water behavior or predictor state are possible interpretations, not verified diagnoses. The finite 20-minute runs do not prove indefinitely unbounded growth, a Python object leak, or a YOLO standalone leak. No production thread architecture change is authorized here. The next minimal action is a separately authorized boundedness/native-runtime attribution study of inference thread lifecycle, followed by a reviewed production design only if the evidence warrants one.

## 7. Regression, gates and final state

Seven fast P9-C.3i tests passed, including direct/persistent/fresh execution, model reuse, bounded T4 queue/shutdown, semantic rejection and absence of heavy observer imports. Full `pytest -q`: **762 passed, 0 failed**. `compileall`, `scripts/preflight.py`, `scripts/run_demo.py --check`, `pip check`, and `git diff --check` passed. Before/after `pip freeze` was byte-identical (1570 bytes). Frozen hashes and Git release identity in Section 2 were rechecked after the runs.

**C3I-G1–G12: PASS.** T0–T4 completed with matched inputs and valid semantics; T4 ran only after its trigger; worker/session contribution and next minimal action are classified; regression and frozen identity passed. **DIRECT MAIN-THREAD INFERENCE: STABLE. PERSISTENT WORKER INFERENCE: STABLE. FRESH-WORKER-PER-CYCLE INFERENCE: GROWTH. MONITORINGSERVICE H0: GROWTH. REAL INFERENCE × FRESH WORKER THREAD: SUPPORTED (strong evidence). MONITORINGSERVICE-SPECIFIC CONTRIBUTION: NOT SUPPORTED as material here. PRODUCTION UNBOUNDED MEMORY LEAK: NOT CONFIRMED. P9-C OVERALL: PARTIAL.**
