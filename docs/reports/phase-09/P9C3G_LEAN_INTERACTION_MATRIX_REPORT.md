# P9-C.3g Lean Inference × Tracker Interaction Matrix — 2026-10-04

## 1. Scope and final decision

**P9-C.3g RESULT: PASS as an attribution increment. P9-C OVERALL: PARTIAL.** Four fresh-process, 20-minute cached-frame controls used the same unwrapped MonitoringService graph, real downstream business services and external psutil sampler. Only the inference and tracker implementation varied. All four completed full cycles with consistent event, SQLite, snapshot and alert semantics. Real inference with either precomputed or real tracking showed a much larger continuing RSS rise than either precomputed-inference control. The matrix supports an **inference × downstream interaction** direction. It does not establish a production-owned retained object or indefinite leak.

**LEAN PP:** LOW-RATE CONTINUED RISE / eventual bound INCONCLUSIVE. **LEAN PR:** NEAR STABLE_PLATEAU over 20 minutes. **LEAN RP and RR:** SUSPICIOUS_CONTINUED_GROWTH. **INFERENCE × DOWNSTREAM:** SUPPORTED. **TRACKER × DOWNSTREAM:** NOT SUPPORTED as a material positive effect in this matrix. **INFERENCE × TRACKER INTERACTION:** WEAK. **SOURCE/DECODE REQUIRED FOR GROWTH:** NO for the 20-minute cached-frame controls. **PRODUCTION UNBOUNDED LEAK:** NOT CONFIRMED.

No production code, model, configuration, threshold, runtime, SQLite schema, snapshot, alert or UI code changed. P9-C.4 and P9-D/E/F were not started. Phase 8 remains FINAL RELEASED; P9-A/B remain PASS and Phase 9 final Charter acceptance remains pending.

## 2. PRE-READ and frozen identity

Read the mandatory protocol, README, Charter, Master Plan, Current Status, ADRs, Changelog, Test Gates, Risk Register, latest worklog, open-source/reference/dataset documents, Phase 9 plan and P9-C.2/C.3/C.3a–f reports before editing. No new governance conflict was found. The latest P9-C.3f result was a 3602.625-second real decoded-MP4 lean full-graph run with 692 correct cycles/events/snapshots but warm RSS means 469.88 → 483.40 → 496.78 → 510.16 → 521.17 MiB and 30–60-minute slope +1.2200 MiB/min. It is a real resource-growth observation under lean sampling, not proof of an unbounded retained owner.

All runs used Windows 11, Python 3.12.1, CPU-only `.venv-final-demo-verify`. Entry and exit preflight, `run_demo.py --check` and `pip check` passed. The exact `pip freeze` inventories at `artifacts/p9c3/p9c3g-pip-before.txt` and `p9c3g-pip-after.txt` matched byte-for-byte.

| Frozen item | SHA256, unchanged at exit |
| --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| `configs/tracker.yaml` | `42ec753ee1511b9de652a750b2d67a384f4aea95d56b43a98d287c877121f10a` |
| `locks/FINAL-DEMO-RUNTIME-001/requirements.txt` | `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |
| Frozen 47-frame MP4 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |
| Detection fixture | `c8c53966fb1117a26f23df648f6e21179555e32f0cb6bd1a7a4f48addedd8f38` |
| Track fixture | `0e42709fab781ba79eb135da09789212ff932e7ee412c33c0b571919f8ec76c1` |
| Source dataset `data.yaml` | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| Processed checksum manifest | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |

Branch `main`, HEAD, `origin/main` and the historical `phase-8-final-integration-complete` tag target remained `6c38a4ea51eec9a62f433683a3447c073852cbbd`. Existing worktree changes were preserved. No commit, tag, push, reset or clean was performed.

## 3. Why a unified matrix was required

Historical K/L/N used different attribution instrumentation, so their slopes cannot be treated as a clean factorial comparison. P9-C.3e's matched H/J experiment showed heavy diagnostics materially amplify RSS: H +0.03127 MiB/cycle versus J +0.00408 for the same 150 cached/precomputed cycles/events. P9-C.3f then reproduced continuing growth with real inference/tracking/source under minimal external observation. This matrix holds source frames and downstream wiring fixed while changing only the two upstream components.

J was inspected before PP. Its S4 wiring uses `EngineEventBoundary` with a discard event store, an in-process `Probe` including tracemalloc/GC scans and a counting source factory. P9-C.3g requires formal `EventService` + JSON business store and only external resource sampling. Therefore J is **not wiring equivalent to PP** and was not reused as its baseline. PP was freshly run under the same harness as PR/RP/RR. The J result remains historical evidence of harness contribution, not an exact PP measurement.

## 4. Matrix design and shared lean harness

| Inference input | Precomputed Track | Real ByteTrack |
| --- | --- | --- |
| Precomputed Detection | **PP** | **PR** |
| Real YOLO inference | **RP** | **RR** |

All cells decode the frozen MP4 once *before* measurement, cache the same 47 formal `FrameData` images, then replay those identical objects through a small `CachedFrameSource`. No per-cycle VideoCapture/decode or fresh decoded ndarray exists. Each cell uses a fresh Python process and its own `artifacts/p9c3g/<cell-run-id>/` database, snapshot directory and JSON business event store.

`scripts/run_p9c3g_lean_matrix.py` builds the same formal `MonitoringService`, `PPEPersonAssociationAdapter`, `ComplianceService`, `EventService`/`EventEngine`, `EventIngestService`, SQLite repositories, `SnapshotService` and Console/Web `AlertService` in all four cells. PP/PR use the verified `PrecomputedInferenceService`; RP/RR use real `InferenceService`/YOLO. PP/RP use the verified `PrecomputedTrackingAdapter`; PR/RR use real `ByteTrackPersonTrackingAdapter`. The cached source factory is the same class in all four cells. TTS was not registered in the historical headless graph and was not added.

No `Observed*`, `BoundedRecorder`, `TimedAlertAdapter`, per-frame timing/tracking/association/timeline JSONL, `tracemalloc` or GC object scan is imported by the matrix runner. It retains only the 47 cached input frames, formal service state, aggregate counters and the current cycle; one small cycle summary is flushed to disk. The independent P9-C.3f psutil sampler streams RSS, VMS/private, CPU, thread, handle and open-file counts at a five-second target interval without retaining sample history. Complete validation and statistical analysis were performed only after each business process exited.

Each cell targets an eight-second cycle period by sleeping **after** a faster completed cycle. Real inference cycles that take longer are not shortened. No skipping, parallel inference or model parameter change was used. The actual cycle counts therefore differ slightly and are normalized below.

## 5. One-cycle semantic equivalence gate

One fresh-process smoke per cell completed before formal controls. All four had **47 frames, 77 detections, 66 tracks, one association/unknown association, one `PPE_UNKNOWN` event at frame 24 for track 1 and source timestamp 1.001, one SQLite row, one verified snapshot and two delivered alerts**. Event bbox/confidence and JPEG SHA256 `92452ae640a19bab64bca4e194612eff72143f95c00cb9a10ef2731aa6721b40` matched. Event UUIDs, wall clocks and timing were excluded from equality. `scripts/compare_p9c3g_smokes.py` saved the exact common signature in `artifacts/p9c3g/semantic-gate.json` and passed. The RP/RR real inference output was thus compatible with the frozen Detection fixture and its derived Track fixture on the complete 47-frame cycle.

Smoke roots: `pp-20261003T141818Z-c4405ea7`, `pr-20261003T141830Z-d57b99b9`, `rp-20261003T141841Z-366e16fc`, `rr-20261003T141902Z-103daee8` under `artifacts/p9c3g/`. Each external sampler attached to the correct business PID, wrote at least two samples and exited cleanly.

## 6. Formal PP, PR, RP and RR integrity

| Cell | Run root under `artifacts/p9c3g/` | Seconds | Cycles | Frames | Events/SQLite/verified snapshots | Delivered/failed alerts | External samples |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PP | `pp-20261003T142047Z-cb6d1b94` | 1200.109 | 150 | 7050 | 150/150/150 | 300/0 | 230 |
| PR | `pr-20261003T144200Z-46510543` | 1200.156 | 150 | 7050 | 150/150/150 | 300/0 | 230 |
| RP | `rp-20261003T150306Z-4e483e67` | 1205.406 | 149 | 7003 | 149/149/149 | 298/0 | 223 |
| RR | `rr-20261003T152426Z-66c54569` | 1201.250 | 148 | 6956 | 148/148/148 | 296/0 | 222 |

Each cycle was `COMPLETED` with 47 frames before the next start. `MonitoringService._run()` closes the cached source in `finally` before `COMPLETED`; `wait()` joins its worker. `source_created == completed_cycles` and final workers/samplers exited in every cell. The post-run validator reopened SQLite, paged through every unique event ID in each isolated database, verified every snapshot file/hash/dimension, matched business JSON event lines and Console/Web totals. All four validation artifacts report PASS. Across the matrix: **597 full cycles, 28,059 frames, 597 event rows and verified snapshots, 1,194 successful alerts and zero failures**.

## 7. Resource windows and shapes

External RSS window means are MiB; min/max and medians, plus CPU/VMS/private/thread/handle/file windows, are preserved in each run's `outputs/resource-analysis.json`. The first two minutes are excluded from regression to avoid import/model-init transients. Absolute RSS levels across fresh processes are not used as attribution evidence.

| Cell | 2–5 mean | 5–10 mean | 10–20 mean | 2–20 MiB/min | 2–20 MiB/cycle and event | 10–20 MiB/min | Reviewed 20-minute shape |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| PP | 175.890 | 176.130 | 176.901 | +0.09340 | +0.01245 | +0.10620 | LOW-RATE CONTINUED RISE; eventual bound inconclusive |
| PR | 324.294 | 324.361 | 324.446 | +0.01170 | +0.00156 | +0.00790 | NEAR PLATEAU over 20 min |
| RP | 491.100 | 494.083 | 499.881 | +0.76345 | +0.10231 | +0.74024 | SUSPICIOUS CONTINUED GROWTH |
| RR | 492.367 | 495.275 | 501.269 | +0.78556 | +0.10512 | +0.79554 | SUSPICIOUS CONTINUED GROWTH |

PP has a small but continuing rise, so it is not asserted to be strictly bounded. PR's 2–5 to 10–20 mean change is only 0.152 MiB, and its late slope remains near horizontal in the context of that run's small fluctuations. RP and RR rise by about 8.8–8.9 MiB between early and late window means, with clearly positive late slopes; neither shows a plateau in 20 minutes. The analyzer's `MONOTONIC_RISE` flag only records mean direction; the reviewed classifications above account for magnitude and within-run dispersion. No arbitrary universal PASS threshold is applied. Threads, handles and open files remain roughly stable after warmup in each cell; for example 10–20 means are approximately 16/351/2 (PP), 16/446/2 (PR), 37/562/2 (RP) and 38/562/2 (RR).

## 8. Directional 2×2 interaction calculations

The following contrasts use the **2–20-minute RSS slope in MiB/completed cycle**, not absolute RSS. Event/cycle ratio was one in all four runs, so per-event slopes have the same numerical values. These are directional comparisons of distinct processes, not additive physical byte attribution or confidence intervals.

| Contrast | Calculation | MiB/cycle | Interpretation |
| --- | --- | ---: | --- |
| Inference with precomputed tracker | RP − PP | +0.08986 | strong positive increment |
| Inference with real tracker | RR − PR | +0.10356 | strong positive increment |
| Tracker with precomputed detection | PR − PP | −0.01089 | no positive tracker increment |
| Tracker with real inference | RR − RP | +0.00281 | small increment relative to inference effect |
| Factorial interaction direction | RR − PR − RP + PP | +0.01370 | weak positive direction; no precise interaction attribution |

The inference effect persists whether tracking is precomputed or real. PR is flatter than PP, while RR is only slightly steeper than RP. Accordingly: **INFERENCE × DOWNSTREAM: SUPPORTED** by this matrix together with the prior M inference-only near-plateau control; **TRACKER × DOWNSTREAM: NOT SUPPORTED** as a material positive effect here; **INFERENCE × TRACKER INTERACTION: WEAK** directional signal, insufficient to call it the main contributor. Prior standalone tracker P/Q/R controls approached plateaus, consistent with this decision. The result does not identify which downstream stage interacts with real inference.

## 9. Source/decode implication, ranking and production-bug boundary

RR uses cached decoded frames yet retains +0.10512 MiB/cycle and +0.79554 MiB/min 10–20 growth. RP does likewise without real ByteTrack. Therefore **SOURCE/DECODE REQUIRED FOR GROWTH: NO** over this controlled 20-minute interval. Fresh VideoCapture/decode could still change the magnitude or long-run shape of the P9-C.3f 60-minute observation; that contribution is not separately quantified by this matrix. The P9-C.3f slope (+1.2935 MiB/min over 10–60 minutes) is a different-duration, unpaced process and cannot be subtracted as an exact source cost.

Updated suspect ranking: (1) real inference combined with formal downstream lifecycle, strongly supported; (2) native allocator/high-water behavior within that combination, still possible; (3) source/decode as an additional modifier, possible but unnecessary for growth; (4) inference × ByteTrack as a main effect, weak; (5) standalone tracker × downstream, unsupported by this matrix; (6) alert `_completed` map, known long-horizon risk with small previously measured contribution. The exact retained owner and indefinite bound remain unknown. **PRODUCTION UNBOUNDED LEAK: NOT CONFIRMED.** No production repair was attempted or authorized.

The smallest next authorized attribution experiment would compare the existing lean RP cell against one **matched lean real-inference + precomputed-track control ending after formal association/compliance**, with event persistence, snapshot and alert fan-out disabled only in that diagnostic control. The same cached frames, pacing and external sampler would test whether the event/storage/alert block is required for RP's rise. Depending on that result, split only the responsible block in a later control. This is a proposal requiring separate authorization, not P9-C.4 or P9-D work started here.

## 10. Gates, regression and final state

| Gate | Decision |
| --- | --- |
| C3G-G1 unified lean matrix harness | PASS; one builder, source factory and external sampler |
| C3G-G2 four semantic gates | PASS; exact common business signature and snapshot SHA |
| C3G-G3 PP | PASS; 150 cycles, full integrity |
| C3G-G4 PR | PASS; 150 cycles, full integrity |
| C3G-G5 RP | PASS; 149 cycles, full integrity |
| C3G-G6 RR | PASS; 148 cycles, full integrity |
| C3G-G7 normalized matrix | PASS; per-minute, per-cycle/event and late slopes |
| C3G-G8 interaction decisions | PASS; supported/unsupported/weak distinctions above |
| C3G-G9 source/decode requirement | PASS; not required for 20-minute cached-frame growth |
| C3G-G10 next minimal action | PASS; matched RP downstream-block control proposed |
| C3G-G11 full regression | PASS; 742 tests, compileall, preflight, demo check, pip check, diff check |
| C3G-G12 frozen identity | PASS; exact pip inventory, frozen hashes, dataset and Git identity unchanged |

Eleven new deterministic tests cover the unified graph, four wiring cells, fixture identity, common downstream types, heavy-observer exclusion, sampler schema, matrix math and semantic-signature projection. Full suite: **742 passed, 0 failed**. `compileall -q core infra services utils web scripts diagnostics`, preflight, demo check, pip check and `git diff --check` passed. No package drift or frozen-asset change occurred. Raw run and analysis artifacts remain ignored under `artifacts/p9c3g/`.

**P9-C.3g PASS / P9-C OVERALL PARTIAL.** Inference × downstream interaction is the leading direction; the production retained owner and long-run bound are still unproven. P9-C.4 and P9-D/E/F remain unauthorized pending a new human decision.

Changed this increment: `diagnostics/p9c3g_cached_source.py`, `scripts/run_p9c3g_lean_matrix.py`, `scripts/validate_p9c3g_matrix.py`, `scripts/compare_p9c3g_smokes.py`, `scripts/analyze_p9c3g_matrix.py`, `tests/test_p9c3g_lean_matrix.py`, this report, the P9-C.3 aggregate report, Phase 9 plan, Current Status, Changelog, Test Gates, Risk Register and worklog.
