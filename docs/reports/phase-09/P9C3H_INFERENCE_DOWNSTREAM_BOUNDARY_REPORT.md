# P9-C.3h Real-Inference Downstream Boundary Isolation — 2026-10-07

## 1. Scope and final result

**P9-C.3h RESULT: PASS as a boundary-attribution increment. P9-C OVERALL: PARTIAL.** This diagnostic-only study held 47 cached real frames, real YOLO inference, the verified precomputed Track fixture, `MonitoringService` worker/session orchestration, pacing and an external psutil sampler fixed. It progressively added formal downstream stages. No production service, model, config, business threshold, dependency, runtime or UI was changed.

**FIRST MATERIAL DOWNSTREAM DIVERGENCE: NONE.** H0, with real inference and precomputed tracking but no real Association/Compliance/Event/SQLite/Snapshot/Alert, already reproduced RP-scale continuing RSS growth. H1 and H2 did not add a material positive increment. A fresh matched 20-minute H0/RP comparison confirmed the direction. The earliest sufficient path observed here is **real inference inside the MonitoringService cached-frame worker/session and precomputed-track context**. This does not isolate a specific retained object, a YOLO-only defect or an indefinitely unbounded production leak.

## 2. PRE-READ, authorization and frozen identity

Read `AGENTS.md`, README, Charter, Master Plan, Current Status, ADRs, Changelog, Test Gates, Risk Register, Phase 9 plan, latest worklog, source/reference/dataset documents and the P9-C.3, P9-C.3f and P9-C.3g reports before editing. No substantive governance conflict was found. The task text named `docs/CHANGELOG.md`; the repository's authoritative changelog is `docs/04_CHANGELOG.md`. Phase 8 is FINAL RELEASED, P9-A/B PASS, P9-C.3g PASS and P9-C overall PARTIAL. Production repair, P9-C.4 and P9-D/E/F were not authorized.

Runtime: Windows 11, Python 3.12.1, CPU-only `.venv-final-demo-verify`. Entry and exit preflight, `run_demo.py --check`, `pip check` and byte-identical before/after `pip freeze` passed. Branch `main`, HEAD, `origin/main` and dereferenced historical Phase 8 final tag target remained `6c38a4ea51eec9a62f433683a3447c073852cbbd`.

| Frozen item | SHA256, unchanged |
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

## 3. P9-C.3g matrix restatement and changed inference

The prior unified 20-minute PP/PR/RP/RR matrix found RSS slopes +0.01245/+0.00156/+0.10231/+0.10512 MiB per completed cycle. It strongly associated the growth with real inference when the full formal downstream graph was present. Real ByteTrack added little; fresh source/decode was unnecessary over 20 minutes. That matrix **did not isolate the downstream boundary**. P9-C.3h now shows RP-scale growth without the real downstream business stages, so the earlier phrase “inference × formal downstream interaction” is too specific as a causal requirement. P9-C.3g measurements and historical conclusions remain preserved as at-the-time evidence; this report supersedes that narrower interpretation.

## 4. Common harness, wiring and baseline equivalence

`scripts/run_p9c3h_boundaries.py` reuses P9-C.3g's exact cached-source class, MP4 and verified Track fixture loader. All cells use real `InferenceService` and `PrecomputedTrackingAdapter`, a formal `MonitoringService`, fresh Python processes, isolated output roots, approximately eight-second post-cycle pacing and the unchanged P9-C.3f external psutil sampler. No `Observed*`, `BoundedRecorder`, `tracemalloc`, GC object scan or per-frame history recorder runs in timed controls. The 47 input `FrameData.image` objects are cached once before measurement; no new ndarray copies are constructed in the diagnostic path.

The RP builder was compared structurally with P9-C.3g's `build_matrix_graph("RP")`: inference, tracker, association, compliance, event, ingest, snapshot and alert service types match; so do EventEngine, JSONEventStore and two alert adapters. Source factory and sampler are the same reusable implementations. The new RP was rerun fresh for a same-day matched confirmation; the historical RP remains comparison context.

| Stage | Active path | Omitted or diagnostic boundary |
| --- | --- | --- |
| H0 | real inference → precomputed Track, formal MonitoringService session | empty Association/Compliance/Event; no SQLite, snapshot, alert |
| H1 | H0 + real Association and Compliance | empty Event; no persistence, snapshot, alert |
| H2 | H1 + real EventService/EventEngine/TemporalFilter and JSON business store | transient bounded ingest, no SQLite/snapshot/alert |
| RP | H2 + formal SQLite, Snapshot and Console/Web Alert | full P9-C.3g RP equivalent |

H2 and RP use the same `EventService` + `JSONEventStore` choice; H0/H1 do not invoke an event service or write business JSON. Thus H2's boundary includes both temporal/event processing **and JSON append**. The study cannot attribute any hypothetical H2 increment to one of those components alone. H2's diagnostic ingest returns only a transient valid `PersistedEvent`; it retains no event collection. Snapshot's diagnostic replacement returns a bounded placeholder and does not encode or copy an image. RP's real `SnapshotService` encodes the current cached `frame.image` directly.

## 5. One-cycle semantic gates

Fresh H0/H1/H2 smoke processes all passed 47 frames, 77 real detections and 66 precomputed tracks. H0 produced no association or event. H1/H2 each produced one association and one unknown association; their real compliance finding sequence covered all 47 frames with `PPE_UNKNOWN`. H2 generated one real `PPE_UNKNOWN` event for track 1, source timestamp 1.001 and frame 24, matching RP's business event semantic; UUID, wall clock and timing were excluded. H2 wrote one JSON business line but no SQLite row, snapshot or alert. The smokes used a semantic tap that is absent from formal timed controls.

Smoke roots under `artifacts/p9c3h/`: `h0-20261007T011246Z-a14138c0`, `h1-20261007T011327Z-17366d59`, `h2-20261007T011327Z-b3f111cf`.

## 6. H0, H1 and H2 10-minute screening

Each control ran in a separate fresh process. All cycles completed 47 frames and clean worker/source/sampler exit. A post-exit validator checked every cycle count, detection/track count, event JSON line count and the absence of unapproved downstream outputs. The first two minutes were excluded from slope regression. RSS window means and slopes are within-run values; absolute RSS between processes is not attribution evidence.

| Stage | Root under `artifacts/p9c3h/` | Cycles / frames / events | 2–5 RSS mean | 5–10 RSS mean | 2–10 MiB/min | 2–10 MiB/cycle | 5–10 MiB/min | Reviewed shape |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| H0 | `h0-20261007T011356Z-85418e5c` | 72 / 3384 / 0 | 489.835 | 492.667 | +0.71720 | +0.10190 | +0.75256 | MATERIAL_CONTINUED_GROWTH |
| H1 | `h1-20261007T012427Z-204797de` | 68 / 3196 / 0 | 488.323 | 491.195 | +0.71888 | +0.10508 | +0.70195 | MATERIAL_CONTINUED_GROWTH |
| H2 | `h2-20261007T013519Z-ce671445` | 69 / 3243 / 69 | 490.338 | 493.192 | +0.71070 | +0.10653 | +0.73936 | MATERIAL_CONTINUED_GROWTH |

H0 already has the RP-scale positive slope and a positive late window. H1−H0 is +0.00318 MiB/cycle and H2−H1 is +0.00145 MiB/cycle, directional comparisons across separate processes, not additive bytes or confidence intervals. H2's 69 JSON business events match its 69 cycles. The same-duration 2–10-minute slice of historical P9-C.3g RP was +0.10027 MiB/cycle and +0.74397 MiB/min; its different date was not used as confirmation.

## 7. Fresh 20-minute H0/RP confirmation pair

H0 is the first stage already showing material growth, so it has no earlier downstream predecessor to pair. The minimal useful confirmation was a fresh H0 against a fresh full RP in the same runner, sequentially, with identical upstream/source/pacing/sampler. H3/H4/H5 were unnecessary and were not executed.

| Stage | Root under `artifacts/p9c3h/` | Cycles / frames / JSON events / SQLite / snapshots / alerts | 2–5 RSS | 5–10 RSS | 10–20 RSS | 2–20 MiB/cycle | 10–20 MiB/min |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H0 | `h0-20261007T014609Z-b1012447` | 142 / 6674 / 0 / 0 / 0 / 0 | 489.734 | 492.706 | 497.977 | +0.10318 | +0.69995 |
| RP | `rp-20261007T020647Z-7ad12953` | 150 / 7050 / 150 / 150 / 150 / 300 | 491.158 | 494.429 | 500.073 | +0.10255 | +0.74677 |

Both 20-minute slopes remain positive through the last ten minutes. RP−H0 is **−0.00064 MiB per completed cycle** in the matched 2–20-minute comparison. Different cycle counts reflect natural real-inference timing; no cycles were skipped or accelerated. RP's 150 SQLite rows and 150 snapshot files matched JSON events, and 300 Console/Web deliveries succeeded with zero failed alerts. Snapshot input was the current cached real frame image. The validator checked completed-cycle/source counts and final worker/sampler exits. H0 had no business downstream output by design.

## 8. Other resource dimensions and interaction decision

Threads, handles and open files were approximately stable after warmup. For example, late-window means were H0/H1/H2 10-minute: threads 37.79/37.36/37.40, handles 557.18/557.79/557.93, open files 2.00/2.02/2.00. Fresh 20-minute H0/RP late means were threads 37.36/36.95, handles 558.10/560.54, open files 2.01/2.00. Complete RSS min/max/median, VMS/private, CPU and resource windows are in each run's `outputs/resource-analysis.json`; raw five-second samples remain in `resources/external.csv`.

**FIRST MATERIAL DOWNSTREAM DIVERGENCE: NONE; H0 already at RP scale.** Real Association/Compliance, Temporal/Event/JSON store and Persistence/Snapshot/Alert are **not required** to reproduce this 20-minute cached-frame growth. No material additional positive effect from adding those stages is supported by this matrix. This is not proof that they can never contribute under longer or different workloads.

The updated leading direction is the combination of real inference, formal `MonitoringService` frame/session lifecycle and precomputed tracking output handling. The earlier standalone inference-only M control was comparatively near plateau, but its orchestration was not wiring-equivalent to H0. The exact interaction among predictor output lifetime, monitoring status/frame retention, transient result conversion, worker/session reset and allocator high-water remains **INCONCLUSIVE**. A standalone YOLO leak and a standalone ByteTrack leak are not confirmed.

## 9. Production leak boundary, suspect ranking and next action

**PRODUCTION UNBOUNDED LEAK: NOT CONFIRMED.** The P9-C.3f 60-minute full-graph resource rise remains real evidence; this study narrows a sufficient 20-minute diagnostic path but neither identifies a production-owned retained object nor proves indefinite growth. No production repair, `gc.collect()` injection, Torch cache clear or allocator hack was attempted.

Updated suspect ranking: (1) real inference output/predictor lifecycle interacting with `MonitoringService` frame/session state; (2) native allocator high-water or retained buffers in that path; (3) source/decode as an additional modifier to the 60-minute full-MP4 magnitude, unnecessary for 20-minute cached growth; (4) formal downstream business stages as additional long-run modifiers, unsupported as necessary for the matched 20-minute rise; (5) standalone real ByteTrack, unsupported by this matrix; (6) alert `_completed` state, a known small per-event long-horizon risk. The precise owner remains unknown.

The next minimal **separately authorized** attribution experiment should isolate H0's real inference output and `MonitoringService` frame/session lifecycle with a wiring-matched boundary, without adding heavy observers or changing production code. Compare whether the same inference result lifetime under a minimal formal session reproduces the rise; then inspect native/Python ownership only if a specific difference is established. P9-C.4 remains reserved for a separately authorized targeted production fix after a concrete defect is found.

## 10. Gates, regression and final state

| Gate | Decision |
| --- | --- |
| C3H-G1 H0 semantic/wiring | PASS; real inference/precomputed Track, 47/77/66 smoke |
| C3H-G2 H1 semantic/wiring | PASS; matching association/unknown/compliance |
| C3H-G3 H2 semantic/wiring | PASS; matching frame-24 `PPE_UNKNOWN` event |
| C3H-G4 10-minute screens | PASS; H0/H1/H2 72/68/69 cycles and post-exit validation |
| C3H-G5 first divergence | PASS; NONE downstream, H0 already at RP scale |
| C3H-G6 necessary 20-minute confirmation | PASS; fresh H0/RP 142/150 cycles |
| C3H-G7 conditional H3/H4/H5 | NOT TRIGGERED; H0 already material |
| C3H-G8 interaction decision | PASS; business downstream not required over 20 minutes |
| C3H-G9 production leak boundary | PASS; no retained owner/unbounded leak claim |
| C3H-G10 next minimal action | PASS; H0 lifecycle/output attribution proposed |
| C3H-G11 full regression | PASS; 755 tests, compileall, preflight, demo/pip/diff checks |
| C3H-G12 frozen identity | PASS; hashes, exact pip inventory, dataset and Git release identity |

Thirteen quick deterministic tests cover staged builders, common real inference/precomputed tracking, RP wiring equivalence, semantic tap scope, unchanged sampler and threshold-free adjacent-difference analysis. Full repository suite: **755 passed, 0 failed**. `compileall`, preflight, demo check, pip check and `git diff --check` passed; before/after `pip freeze` files were byte-identical. No commit, tag, push, reset or clean was performed. Existing working-tree changes and ignored raw artifacts were preserved.

**P9-C.3h PASS / P9-C OVERALL PARTIAL.** Phase 8 FINAL RELEASED and P9-A/B PASS remain unchanged. P9-C.4 and P9-D/E/F remain unauthorized.
