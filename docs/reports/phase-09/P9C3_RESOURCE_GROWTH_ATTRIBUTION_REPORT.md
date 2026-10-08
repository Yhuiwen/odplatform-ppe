# P9-C.3 Resource Growth Attribution — 2026-09-25

> Latest continuation (2026-10-07): [P9-C.3h downstream boundary
> isolation](P9C3H_INFERENCE_DOWNSTREAM_BOUNDARY_REPORT.md) found
> RP-scale growth already in H0: real inference + precomputed Track
> inside formal MonitoringService, without real Association/Compliance/
> Event/SQLite/Snapshot/Alert. Fresh 20-minute H0/RP slopes were
> +0.10318/+0.10255 MiB/cycle. **FIRST MATERIAL DOWNSTREAM
> DIVERGENCE: NONE.** The P9-C.3g matrix remains valid measured
> evidence, but its suggested requirement for formal business
> downstream is superseded by this narrower control. P9-C.3h PASS
> as attribution, P9-C overall PARTIAL. Production retained owner and
> indefinite leak remain NOT CONFIRMED.

> Latest continuation (2026-10-04): [P9-C.3g unified lean interaction
> matrix](P9C3G_LEAN_INTERACTION_MATRIX_REPORT.md) supports real
> inference × formal downstream as the leading growth direction;
> cached-frame RP/RR grow without fresh source/decode. P9-C.3g PASS as
> attribution, P9-C overall PARTIAL, production retained owner and
> indefinite leak NOT CONFIRMED. Older sections preserve their
> at-the-time decisions.

> Latest continuation (2026-09-27): [P9-C.3f lean real full-graph
> report](P9C3F_FINAL_LEAN_FULL_GRAPH_STABILITY_REPORT.md) found
> SUSPICIOUS_CONTINUED_GROWTH over 60 minutes. P9-C.3f and P9-C overall
> remain PARTIAL; resource growth is reproduced with lean observation,
> while an unbounded retained owner is not confirmed. Earlier sections
> below retain their historical at-the-time decisions.

> Subsequent P9-C.3a continuation (2026-09-26): the precomputed-detection
> downstream control passed one-cycle semantic equivalence, completed 148
> paced cycles/events over 20 minutes, and reduced RSS slope from K's
> +0.9737 to +0.3211 MiB/min without eliminating it. This supports a
> **multi-contributor pattern**; the exact native owner remains unresolved.
> See [P9-C.3a control report](P9C3A_PRECOMPUTED_DETECTION_CONTROL_REPORT.md).
> P9-C overall remains PARTIAL; P9-C.4 and P9-D/E/F remain unauthorized.

## 1. PRE-READ and scope

The required governance files and P9-C.1/P9-C.2 reports were read before edits. No substantive governance conflict was found. Phase 8 is FINAL RELEASED; P9-A, P9-B and P9-C.1 remain PASS. P9-C.2 is PARTIAL because the MP4 10–60-minute RSS slope was +1.2478 MiB/min, with five rising warm-window means. P9-C.3 is authorized for attribution only. P9-B G1–G13 stay closed. P9-C.4 and P9-D/E/F are not authorized. No Charter acceptance is changed.

## 2. Git and runtime identity

Branch `main`; HEAD and `origin/main` both `6c38a4ea51eec9a62f433683a3447c073852cbbd` at entry. Existing P9-A/B/C.1/C.2 working-tree edits were preserved. The test runtime is `.venv-final-demo-verify`, Windows CPU, Python 3.12.1. Entry `git diff --check`, preflight, demo check and `pip check` passed. Frozen SHA256 values remain: `best.pt` `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`; `configs/inference.yaml` `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c`; `FINAL-DEMO-RUNTIME-001/requirements.txt` `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4`.

## 3. Static retention audit: production and diagnostic ownership

This table describes code ownership and bounds; it **does not by itself prove RSS attribution**. Cardinality measurements and controls follow below.

| Owner | State | Growth key / bound | MP4-cycle behavior |
| --- | --- | --- | --- |
| `MonitoringService` | immutable status, `recent_events`, latest frame | recent events capped by `max_recent_events=20`; one latest frame | status reset at start; one live image retained |
| `AlertService` | adapter tuple, per-dispatch result list | fixed adapters; result list local to dispatch | adapters persist across cycles |
| `BaseAlertAdapter` (Console, Web, TTS) | `_completed: dict[event_id, AlertResult]` | no eviction; unique delivered event ID | persists across cycles; production-owned |
| `WebAlertAdapter` | `_history` | deque `maxlen=200` | persists but bounded |
| `ConsoleAlertAdapter` | sink | no internal message history beyond base completion dict | persists |
| `TTSAlertAdapter` | `_last_spoken`, `_completed` | by track/type and delivered event ID | not registered in P9-C.2/C.3 full-chain headless graph; not a cause of these runs |
| `EventService` / `JSONEventStore` | engine and output path | JSONL append uses local tuple/file context; `read_all` allocates only on explicit query | engine reset at source start |
| `EventEngine` | `_active`, `_recovery_counts`, `_last_recovered` | keyed by track/type, reset; active/recovery entries removed on recovery | reset each cycle through service |
| `TemporalViolationFilter` | `_states`, each `confidences` list | confidence list can grow for a continuing candidate within a session | reset each cycle; MP4 maximum 47 frames per cycle |
| ByteTrack adapter / backend | active/lost/removed track state | Ultralytics tracker owns in-session lists; adapter reset creates new tracker | reset each cycle; measured dynamically |
| Association adapter / `ComplianceService` | settings; local candidates/findings | no retained per-frame result collection | settings persist, locals released |
| `InferenceService` / `YOLODetector` | loaded YOLO model and predictor | model intentionally reused; third-party predictor/native caches not statically bounded here | persists across cycles; needs dynamic evidence |
| `SnapshotService`, `EventRepository`, SQLite `Database` | references/configuration | no per-event in-memory list; file-backed DB connections close on context exit | persistent service objects, transient operations |
| `MP4VideoSource` / `VideoReader` | reader, iterator, capture | one source object per cycle; `close()` releases capture and clears reader/iterator | rebuilt per cycle; native allocator behavior unproven statically |
| P9-C.2 bounded recorder | rolling detail lists/dicts, fixed category counters | detail state capped at 200; JSONL streams all records | persists across cycles, bounded except fixed-category counts |
| P9-C.2 harness | rolling cycle summaries, Console log stream, final query/summary | cycle list capped at 200; final query at most 1,000 rows, executed after loop | summary can allocate at end, not during long-run slope |
| P9-C.3 probe | sample JSONL, tracemalloc aggregates | JSONL stream; snapshots summarized and raw objects released after capture | diagnostic-only; its perturbation measured and disclosed |

Dashboard/report/Agent caches are not invoked by the P9-C.2 or P9-C.3 headless long-run loops. The static audit finds an unbounded production-owned alert completion map. Whether its retained bytes are material relative to the observed ~50 MiB warm MP4 RSS rise requires measurements. A separate TTS idempotency map exists but is outside this chain.

## 4. Method, controls and probe limitations

The attribution script uses the same frozen MP4, real model/config and bounded full-chain harness for A/D. Every five seconds it streams elapsed time, cycles/frames/events, RSS/VMS/private bytes, threads/handles/open files, GC tracked-object/generation counts, tracemalloc current/peak and critical container cardinalities. Inaccessible tracker fields are `UNSUPPORTED`. Tracemalloc depth 1 captures current/peak continuously in A/D; selected object-type counts are sampled at warm start and 30 minutes. A separate T run takes full snapshots at warm/5/10 minutes and reports filename/line/traceback deltas. Depth 1 limits traceback specificity. The baseline does not call `gc.collect()`; a separate short G run does. Source-only B uses the production `MP4VideoSource` and `VideoReader` without business processing. D substitutes a **NON-PRODUCTION ATTRIBUTION ADAPTER** that returns valid delivered `AlertResult` values without retaining event IDs. E invokes the formal Console/Web adapters with 10,000 deterministic IDs and a no-op Console sink.

Runs were invoked in `.venv-final-demo-verify` with `python scripts/run_p9c3_memory_attribution.py --mode {A|B|C0|D|E|F|G|I|T|K}`. A used `--seconds 1800`, B `--seconds 1200` and then a separate `--seconds 3600` extension, C0/D/K `--seconds 1200`, and T `--seconds 600`; E/F/G/I use fixed work counts. Each run's `artifacts/p9c3/<run-id>/attribution/probe.jsonl`, summary and `analysis.json` are the machine-readable evidence. Analysis used `python scripts/analyze_p9c3_attribution.py <probe.jsonl>`. The frozen asset is `artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4` (47 frames). The probe itself and tracemalloc can alter throughput and allocator behavior; comparisons therefore include both time and cycle normalization.

An initial one-cycle smoke proved the probe path. Two early A attempts were interrupted after full tracemalloc snapshots caused large RSS steps: the first retained a raw snapshot; the second released it but still raised process RSS through allocator high-water. Both attempts are excluded from attribution. The formal A/D controls avoid full snapshots, and T isolates their perturbation in a separate process. An initial B source-only run was also stopped after it revealed a much faster source-cycle rate than A; the formal B control pauses between cycles to match A's approximately 7.7-second period. These interrupted probes are retained as diagnostic artifacts and not used for slopes. Continuous tracing itself changes throughput, so source/event rates and Python-heap deltas are reported alongside process RSS. P9-C.2 remains the independent untraced 60-minute observation.

## 5. Experiment results

### A — full-pipeline attribution baseline

Formal run `20260925T144206Z-afa46085` completed 30.15 minutes, 234 full MP4 cycles, 10,998 frames and 234 events. It used the same real MonitoringService graph as P9-C.2, bounded diagnostics and continuous depth-1 tracemalloc, without full snapshot capture or explicit GC. Of 309 five-second samples, the 2–30-minute RSS slope was **+1.4358 MiB/min** while traced-current slope was only **+0.0940 MiB/min**. RSS means were 560.74 MiB (2–10), 573.12 MiB (10–20) and 588.35 MiB (20–30); traced means were 127.03, 127.95 and 128.93 MiB. This independently **REPRODUCED** the P9-C.2 RSS trend, with a smaller Python-traced contribution. At end, Console/Web `_completed` counts were each 234, Web history was capped at 200, threads 69, handles 625 and open files 11. Object snapshots at warm start and 30 minutes showed `AlertResult` count 22 → 468 and `AlertMessage` count 11 → 200; ByteTrack/FrameData counts did not grow correspondingly. These are counts, not retained byte attribution.

Critical A cardinalities at sampled event milestones:

| Events | Console/Web completed each | Web history | Monitoring recent events | Event active/recovery | Temporal states/confidences | Tracker active/lost/removed | Harness event/timeline detail |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 0/0 | 0/0 | `UNSUPPORTED` at start | 0/2 |
| 100 | 100 | 100 | 0 | 0/0 | 1/2 | 1/0/0 | 100/200 |
| 200 | 200 | 200 | 0 | 0/0 | 2/11 | 2/0/0 | 200/200 |
| 234 | 234 | 200 | 1 | 1/1 | 1/43 | 1/1/0 | 200/200 |

The probe only reads private implementation fields; some fields are transient during a frame and should not be interpreted as complete lifecycle maxima. The only measured container growing linearly across these full cycles is each formal alert adapter's completion map; the separate E control quantifies its small memory contribution.

### B — source lifecycle only

Formal run `20260925T151525Z-577267a8` completed 20 minutes, 156 real `MP4VideoSource` open/read-47/EOF/close cycles and 7,332 decoded frames, paced to A's ~7.7-second cycle period. No model, tracker, event, SQLite, snapshot or alert was present. The 2–20-minute RSS slope was **+4.2597 MiB/min**; 10–20-minute slope **+2.1311 MiB/min**. Traced-current slopes were +0.00065 and approximately zero MiB/min. RSS means were 55.62 MiB (0–2), 71.15 MiB (2–10) and 111.34 MiB (10–20). This established early source-only RSS growth, despite a flat traced Python heap and stable handles/files. It includes OpenCV decoder and repeated capture lifecycle, so it does not by itself distinguish decoding allocations from open/close allocation behavior. Absolute A/B RSS is not compared: B excludes the model and business graph.

The boundedness question justified one 60-minute B extension, run `20260925T170228Z-4bb42cfe`: **468 cycles, 21,996 frames**, paced identically. Its 10-minute RSS means were 56.12, 72.17, 116.21, 123.43, 125.56, 127.26 and 125.57 MiB from 0–2 through 50–60 minutes. The 20–60-minute slope was **+0.1301 MiB/min**, and 30–60-minute slope **+0.0406 MiB/min**. Repeated transient drops to about 57–58 MiB occurred while the upper envelope stabilized near 130–132 MiB; traced-current stayed essentially flat (+0.00012 MiB/min after 2 minutes). This supports a **bounded source-only native/working-set high-water or cache pattern over 60 minutes**, rather than an indefinitely rising source-only curve. It does not prove that the *full pipeline* has the same bound; P9-C.2 full-chain warm windows continued rising across its separate 60-minute run. Windows RSS `private` in psutil is committed virtual memory, not proof of uniquely resident physical pages.

The 20-minute B window is an early-window observation only. A separately authorized 60-minute B extension checks whether the source-only trajectory continues or returns to a bounded working set; its final measurements are recorded below. Absolute RSS values across isolated processes are not directly comparable.

### C and supplemental C0 — persistent rewind

Full-pipeline C was **NOT RUN / UNSAFE DIAGNOSTIC**: keeping one capture alive across official MonitoringService cycles would require a custom source that defeats the production source `close()` lifecycle, while one uninterrupted rewinding session would change frame timestamps, tracker/event reset and event generation. It would therefore cease to be a one-variable full-pipeline comparison. Instead, supplemental source-only C0 held a single OpenCV `VideoCapture` open and used frame-position seek after each real 47-frame EOF, at the same 7.7-second cycle period as B. Run `20260925T153647Z-93bf2ba0` completed 20 minutes, 156 rewinds and 7,332 decoded frames. RSS means were 105.55 MiB (0–2), 106.25 MiB (2–10), and 121.63 MiB (10–20); a native RSS step occurred around minute 11–12, then stayed near 128 MiB through the end. The 2–20-minute slope was +1.3965 MiB/min and 10–20-minute slope +0.7302 MiB/min, versus B's +4.2597 and +2.1311. Traced heap remained essentially flat. This supports a source/native contribution even without repeated open/close, while the larger B growth is consistent with additional lifecycle contribution. It does not prove indefinite growth or identify the exact OpenCV allocator site. C0 imports cv2 before tracemalloc starts, so its traced absolute baseline is not comparable to B; RSS slopes and cycle counts are the useful comparison.

### D — full pipeline with stateless attribution alerts

Run `20260925T155758Z-bfd4b9f2` completed 20.12 minutes, 98 real 47-frame cycles/events, with normal event creation, SQLite and snapshot flow. Its two **NON-PRODUCTION ATTRIBUTION ADAPTERS** returned delivered `AlertResult` values but had no `_completed` or Web history. The 2–20-minute RSS slope was +0.8753 MiB/min, traced-current slope +0.0602 MiB/min; RSS means were 560.18 MiB (2–10) and 568.17 MiB (10–20). D's throughput was 98/20 minutes versus A's approximately 154/20 minutes, so the lower per-minute slope is not a clean memory improvement. Normalizing by cycle gives **D +0.1905 MiB/cycle versus A +0.1807 MiB/cycle**. Removing the alert retention state did **not** remove the RSS growth. The precise adapter delivery side effects also differ, so this is a directional attribution control rather than a production acceptance run.

### E — formal alert state micro attribution

Run `20260925T161921Z-433e6248` delivered 10,000 deterministic unique event IDs through the production Console/Web adapters, with a no-op Console sink. Both `_completed` maps grew exactly 0 → 100 → 300 → 600 → 1,000 → 10,000. Web `_history` reached its 200-message cap by 300 and stayed at 200. Across 10,000 events, traced-current memory increased by 4,067,489 bytes, about **407 bytes/event**; process RSS increased by 9,535,488 bytes, about **954 bytes/event** in this micro-process. Linear extrapolation to 675 MP4 events suggests roughly **0.26 MiB traced** or **0.61 MiB RSS** contribution, far below P9-C.2's ~50 MiB warm-window mean rise. This is an estimate from a distinct micro workload, not a full-pipeline byte accounting. The maps are production-owned and unbounded by event count, but the measurements do **not** support them as the main cause of the observed 60-minute RSS trend.

### F — event and snapshot side effects

Run `20260925T163538Z-ab54c467` used the formal `EventIngestService`/SQLite and `SnapshotService`/JPEG storage with a single decoded image, without a repeated source or model. One thousand event inserts took 19.3 seconds; RSS moved from 50.82 to 52.78 MiB and traced heap from about 0 to 0.027 MiB, with most RSS rise in the first 100 writes. A following 1,000 verified snapshot writes took the total runtime to 96 seconds; RSS moved from 52.78 to 59.41 MiB and traced heap to 3.162 MiB, with nearly all of the increase by the first 100 snapshots and a later plateau. Handles stayed 349–352 and open files at one. This micro test does not support a continuing per-event SQLite or JPEG storage RSS rise of the magnitude seen in A/B. Its repeated identical image and short duration limit extrapolation.

### T — independent tracemalloc snapshots

Run `20260925T162402Z-6c550f02` completed 59 full cycles over ten minutes, taking depth-1 snapshots at about 2, 5 and 9 minutes. Full snapshot capture raised this diagnostic process's RSS, so its RSS is **not** attribution evidence; continuous A/D curves are used for that. The 2→5-minute top filename difference included `core/inference/detector.py` +2,114,054 bytes, traced mainly to line 244 where per-frame checkpoint SHA256 reads transient 1 MiB chunks; snapshot timing during a worker read makes this a poor retained-leak signal. Other top increases were `tracemalloc.py` +636,579 bytes, the diagnostic script +125,628 bytes, `core/schemas/alerts.py` +31,552 bytes and bounded harness code +30,191 bytes. The 5→9-minute top increases were `tracemalloc.py` +414,097 bytes, diagnostic script +131,376 bytes, harness +47,488 bytes, monitoring status +33,216 bytes and alert schema +28,288 bytes. No project Python allocation category approached the untraced MP4 RSS rise. Raw top filename/line/traceback differences are in `attribution/tracemalloc-120-to-300.json` and `tracemalloc-300-to-540.json`.

### G — separate GC diagnostic

Run `20260925T163807Z-f02e5f4e` completed one full MP4 cycle, then took a before/after sample around an explicit `gc.collect()` **only in this independent diagnostic process**. GC reported 43 collected objects; traced current decreased 54,351 bytes; tracked objects decreased from 262,431 to 262,048; RSS changed from 480,346,112 to 480,362,496 bytes (effectively unchanged). This provides no evidence of a large backlog of unreachable Python objects. Windows RSS remaining high after GC does not itself establish a native leak.

### I — fixed decoded frame, real model inference

Run `20260925T163935Z-4cae1059` decoded one frozen MP4 frame once, then called the formal `InferenceService.infer_frame()` **10,000 times** with the same model/config on CPU. It did not reopen a source, track, generate events, write SQLite or encode snapshots. Runtime was 1,296.5 seconds. After warm-up, RSS means were 447.46 MiB (2–10), 447.86 MiB (10–20) and 448.29 MiB (20–21.6); 2-minute-onward RSS slope was **+0.0563 MiB/min**, traced-current slope **+0.0011 MiB/min**. This is a near-plateau, strongly weakening the inference path as the main source of P9-C.2's repeated-MP4 RSS growth. One fixed image does not cover every possible input-dependent model allocation pattern.

### K — diagnostic predecoded-frame full-chain control

This additional, narrow control uses 47 frames decoded once before tracing and then runs the ordinary MonitoringService, real model, tracker, association, event, SQLite, snapshot and formal alerts through complete source cycles. Only the per-cycle OpenCV decode/open/close path is removed. It is a **NON-PRODUCTION diagnostic source**, not a replacement product adapter or Phase 9 acceptance run. A one-cycle smoke completed 47 frames, one event and one SQLite row. Formal run `20260925T180439Z-0bf77f71` completed **150 cycles, 7,050 frames, 150 events and 150 SQLite rows in 20.10 minutes**. Its 2–20-minute RSS slope was **+0.9737 MiB/min**, or **+0.1291 MiB/cycle**, while traced-current slope was **+0.0519 MiB/min**. RSS means were 600.00 MiB (2–10) and 608.64 MiB (10–20); traced means 115.51 and 116.01 MiB. A's corresponding full-source slopes were +1.4358 MiB/min and +0.1807 MiB/cycle, with different throughput and baseline. Growth **persists without per-cycle decode/open/close**, so source lifecycle is not the sole full-chain owner. Its removal reduced the observed per-cycle slope directionally, but the short, differently paced control cannot assign an exact percentage to source allocations. Absolute memory starts higher because 47 decoded images stay resident; compare slopes and per-cycle rates only. The 5-second probe's final row precedes final summary collection, explaining its 149-event count versus the verified 150-event final run.

## 6. Attribution and suspect ranking

Measured evidence before K completion:

| Rank | Candidate | Evidence for | Evidence against / limit | Current judgment |
| --- | --- | --- | --- | --- |
| 1 | Native allocation/working set within the full monitoring graph beyond per-cycle source decoding | A reproduced sustained growth; K retained +0.9737 MiB/min with predecoded frames and only +0.0519 MiB/min traced; B60 source-only plateaued | No native allocation stack trace or one-owner control; interaction among model, tracking and downstream work remains possible | **Highest priority, exact owner unconfirmed** |
| 2 | Native allocation associated with repeated MP4 decoding and source lifecycle | B20 reproduced steep untraced early rise; C0 rewind also showed native RSS step; K per-cycle slope was directionally lower than A | B60 30–60-minute slope only +0.0406 MiB/min; K still rose without this path | **Contributor to warm-up; not sufficient as sole continuing owner** |
| 3 | Model/predictor native allocator by itself | Model stays alive across cycles; native allocation is outside tracemalloc | 10,000 fixed-frame real inferences reached near plateau (+0.0563 MiB/min) | **Weakened** |
| 4 | Formal alert event-id completion maps | Two production maps are unbounded by event count; cardinality grew linearly | 10k-event micro estimates only ~0.61 MiB RSS at 675 events; D stateless control retained ~same RSS per cycle | **Real unbounded state, not material main cause of observed 60-minute RSS** |
| 5 | Event/SQLite/snapshot, tracker/temporal state, harness Python retention | Event count tracks cycle count; snapshots encode each event; tracker reset may still interact with third-party native arrays | F plateaued after initial work; tracker/temporal project state resets each cycle; bounded harness; Python traced slope far below RSS | **Project Python retention low support; native tracker interaction unresolved** |

The distinct interpretations must stay separate: a production-owned unbounded alert dictionary exists, but measured bytes do not explain the observed trend; source-only RSS is compatible with native allocator/cache high-water across 60 minutes; K shows a separate full-graph growth path with no per-cycle decode; full-chain RSS ownership and its eventual bound remain unproven. No production bug fix is authorized or made.

## 7. Decision and gate matrix

**P9-C.3 RESULT: PARTIAL / ATTRIBUTION: INCONCLUSIVE.** The domain is primarily untraced process memory during real full-graph MP4 processing, and the repeated-source lifecycle is not sufficient to explain it. The precise allocation owner and whether the full graph eventually plateaus have not been proven. It would be incorrect to label the main RSS trend a confirmed production leak or a proven bounded cache. The alert completion maps are a separate confirmed production-owned event-count retention risk with small measured contribution to this run; no fix is made under P9-C.3. **P9-C OVERALL: PARTIAL.** P9-A/B/C.1 statuses and Charter acceptance remain unchanged. P9-D/E/F and P9-C.4 are not started.

The **smallest next attribution experiment** is a 20-minute full-graph control using the same 47 cached frames and precomputed detections from one verified pass, with real tracker, association, temporal/event logic, SQLite, snapshots and alerts. Compare its per-cycle slope with K; this changes only repeated model inference while preserving downstream semantics. If growth persists, instrument the tracker/native update and reset boundary next. This targets the remaining owner without another blind 60-minute run. Any production fix requires separate P9-C.4 authorization after a defect is identified.

| Gate | Required evidence | Status |
| --- | --- | --- |
| C3-G1 | Reproduce or explicitly disconfirm P9-C.2 growth | PASS: A reproduced growth |
| C3-G2 | Production and harness static retention audit | PASS: Section 3 |
| C3-G3 | Python heap and tracemalloc evidence | PASS: A/D/T/E/F/I controls |
| C3-G4 | Critical container cardinality | PASS: A milestones and E 10,000-event micro |
| C3-G5 | Source lifecycle control | PASS: B20/B60 and supplemental C0; full C marked unsafe |
| C3-G6 | Event/alert retention control | PASS: D/E/F |
| C3-G7 | Native versus Python classification supported | PASS at memory-domain level; exact native owner unresolved |
| C3-G8 | Suspect ranking based on measurements | PASS: Section 6 includes K |
| C3-G9 | Production bug, non-production or inconclusive classification | PASS: main trend INCONCLUSIVE; separate alert retention risk recorded |
| C3-G10 | Full regression | PASS: 689 tests |

## 8. Regression, frozen identity and changed files

Focused architecture and probe tests passed after moving direct diagnostic
capture creation out of `scripts/`. The first full run recorded **688 pass,
one fail**: the architecture check correctly rejected direct `VideoCapture`
construction in a diagnostic script. That diagnostic-only helper was moved to
`diagnostics/p9c3_capture.py`; the affected focused suite then passed 10/10.
The final full suite passed **689/689** after K. `compileall`, preflight,
`run_demo.py --check`, `pip check` and `git diff --check` passed. `pip freeze`
matches the entry snapshot with **NO DRIFT**. The model, inference config and
runtime lock SHA256 values remain the entry hashes in Section 2; HEAD and
origin/main remain `6c38a4ea51eec9a62f433683a3447c073852cbbd`, and the
Phase 8 release tag `phase-8-final-integration-complete` was untouched. No
commit, tag, push, reset or production fix was made.

P9-C.3 changes are limited to diagnostic support in
`scripts/run_p9b_full_chain.py`, `scripts/run_p9c3_memory_attribution.py`,
`scripts/analyze_p9c3_attribution.py`, `diagnostics/p9c3_capture.py`,
`tests/unit/test_p9c3_memory_probe.py`, `.gitignore`, this report and the
current status, gate, risk, phase, master plan, README, changelog and worklog
records. Existing uncommitted P9-A/B/C.1/C.2 changes were preserved.

## 9. P9-C.3b follow-up — inference and tracker contribution isolation

The separately authorized P9-C.3b control is documented in
`P9C3B_INFERENCE_TRACKER_ISOLATION_REPORT.md`. It supersedes the narrow
"next experiment" proposal above as completed evidence, without changing
this historical P9-C.3 result. M ran real inference on all 47 cached
frames for 125 cycles/20.125 minutes; its warm RSS slope was +0.0470
MiB/min and +0.00736 MiB/cycle, with cycles 1/75/125 matching the
independently verified Detection fixture. This is weak evidence for
inference alone explaining K−L's +0.0861 MiB/cycle gap.

The real ByteTrack Track fixture was reproduced independently (47 frames,
66 tracks), and the L/N one-cycle semantic comparator found no difference.
N removed real ByteTrack update/reset while keeping the formal downstream
graph; it completed 150 paced cycles/events in 20 minutes. N warm RSS was
+0.1779 MiB/min and +0.0238 MiB/cycle, below L's +0.3211 and +0.0430,
while traced-current slopes were effectively equal. This supports a
tracker-path contribution plus additional downstream/interaction growth,
without identifying native allocation stacks or proving an unbounded
full-graph leak. **P9-C.3b PASS; P9-C overall PARTIAL.** No production
fix or subsequent phase was started.

## 10. P9-C.3c follow-up — tracker native lifecycle attribution

The separately authorized P9-C.3c result is in
`P9C3C_TRACKER_NATIVE_ATTRIBUTION_REPORT.md`. P, Q and R each completed
149 paced tracker-only cycles using the verified real Detection fixture.
P held one BYTETracker and made 7,003 updates; Q constructed/reset 149
real project-factory trackers without updates; R performed 7,003
updates across 149 reset/reconstructed tracker sessions. Their warm RSS
slopes were respectively +0.00155, +0.00080 and +0.00168 MiB/cycle,
all far below the directional L−N +0.0192 MiB/cycle difference. Their
10–20-minute windows approached plateau; no isolated path met the
conditional trigger for a 60-minute extension. The L/N reduction remains
valid directional full-downstream evidence, but standalone tracker
update or reset/reconstruct does not explain it. A tracker/downstream
interaction or cross-component allocator behavior remains open. No
production tracker leak is confirmed, and the full graph is not proven
bounded. **P9-C.3c PASS; P9-C overall PARTIAL.**

## 11. P9-C.3d follow-up — Monitoring lifecycle and downstream stages

The separately authorized P9-C.3d result is documented in
`P9C3D_DOWNSTREAM_INTERACTION_ATTRIBUTION_REPORT.md`. Formal
MonitoringService S0 ran 150 repeated sessions and 7050 cached real
frames over 20 minutes; all workers and sources completed/closed,
and warm RSS was +0.000344 MiB/cycle. Four fresh-process 10-minute
stages each ran 75 cycles, adding real association/compliance (S1),
EventService/EventEngine/temporal processing (S2), isolated SQLite
(S3), then real snapshot and Console/Web alerts (S4). Their warm RSS
slopes were −0.00302, +0.000827, +0.00197 and +0.00464 MiB/cycle.
S4 produced 75 events/SQLite rows/snapshots and 150 alert deliveries,
but its late slope flattened and did not reproduce N +0.0238
MiB/cycle. No material first downstream divergence was evidenced;
therefore conditional matched 20-minute and tracker-interaction pairs
were not run. N's observer/recorder/JSONL and rolling-log wiring
differs materially from lean S4, leaving the N residual unassigned.
The next minimal proposed experiment is one separately authorized
N-harness bridge control. No production leak owner or full-graph
boundedness is established. **P9-C.3d PASS; P9-C overall PARTIAL.**

## 12. P9-C.3e follow-up — N diagnostic harness bridge

The separately authorized P9-C.3e result is in
`P9C3E_N_HARNESS_BRIDGE_REPORT.md`. A one-cycle S4/H business
semantic gate matched detections, tracks, compliance, event frame,
SQLite, snapshot SHA256 and alerts. H reused the original N
observer/recorder/JSONL/rolling-log harness with frozen precomputed
Detection/Track inputs for 150 cycles/events over 20 minutes. It
rose +0.2340 MiB/min or +0.03127 MiB/cycle after 2 minutes, with
+0.22384 MiB/min still in the 10–20-minute window. Its traced slope
of +0.05637 MiB/min nearly matched historical N's +0.0566. Matched
20-minute lean S4 J completed the same 150 cycles/events at only
+0.03044 MiB/min or +0.00408 MiB/cycle, with +0.02986 MiB/min in
the late window. All recorder rolling containers stayed within
their 200-row caps; JSONL growth was streamed to disk, and fixed
`FrameData` count stayed 47. No individual unbounded diagnostic
container was identified. The paired result supports a substantial
diagnostic harness/observation contribution to N's residual without
confirming a production downstream leak. Historical N remains a
reproducible instrumented observation. The real production graph's
eventual bound is still unverified; the sole next separately
authorized action is P9-C.3f lean real full-graph confirmation.
**P9-C.3e PASS; P9-C overall PARTIAL.**

## 13. P9-C.3f follow-up — final lean real full-graph confirmation

The separately authorized final confirmation is documented in
`P9C3F_FINAL_LEAN_FULL_GRAPH_STABILITY_REPORT.md`. A fresh process ran
the real frozen 47-frame MP4 through unwrapped MonitoringService,
YOLO, ByteTrack, association, compliance/event, SQLite, snapshot and
Console/Web delivery for 3602.625 seconds. A separate psutil process
streamed resource samples; no H/N heavy observer, fixture, per-frame
diagnostic recorder, tracemalloc or GC scan was active. All 692 cycles
completed 47 frames, yielding 692 unique and verified event/evidence
pairs and 1,384 delivered alerts. Final worker/source lifecycle and
four post-run Dashboard pages passed.

The lean real full graph did **not** reach an observed RSS plateau:
10–20 through 50–60-minute means were 469.88, 483.40, 496.78,
510.16 and 521.17 MiB. The 10–60, 20–60 and 30–60 slopes were
+1.2935, +1.2710 and +1.2200 MiB/min. Classification is
**SUSPICIOUS_CONTINUED_GROWTH**. This independently reproduces
resource growth under production-like lean observation. H/J still
supports a diagnostic-harness contribution in its matched workload;
it did not establish full-graph boundedness. P9-C.2 remains a valid
instrumented historical observation, not an isolated proof of a
production leak. The specific retained owner and indefinite growth
remain unconfirmed. **P9-C.3f PARTIAL; P9-C overall PARTIAL.**
P9-C.4 and P9-D/E/F remain unauthorized pending further human decision.

## 14. P9-C.3g follow-up — unified lean inference × tracker matrix

The authorized result is documented in
`P9C3G_LEAN_INTERACTION_MATRIX_REPORT.md`. Historical J could not be
reused as PP because it used a discard event store and in-process
diagnostic probe; a fresh PP was run under the same new lean harness
as PR/RP/RR. Four one-cycle signatures matched across 47 frames,
77 detections, 66 tracks, the frame-24 `PPE_UNKNOWN` event, SQLite,
snapshot SHA256 and two alert deliveries. Fresh, externally sampled
20-minute PP/PR/RP/RR controls completed 150/150/149/148 cycles
with 597 validated event/evidence pairs and 1,194 delivered alerts.

The 2–20-minute RSS slopes were **+0.01245/+0.00156/+0.10231/
+0.10512 MiB/cycle** for PP/PR/RP/RR. Real inference adds a strong
positive effect with either tracker, while real ByteTrack adds no
comparable effect in this matrix. Directional inference × downstream
interaction is supported; tracker × downstream is not supported as a
material positive effect; inference × tracker is weak. RP and RR
grow with 47 cached decoded frames, so fresh source/decode is **not
required** for this 20-minute growth. No exact production retained
owner or indefinite leak is confirmed. A matched lean RP control
ending after association/compliance is the next smallest proposed
attribution experiment, requiring authorization. **P9-C.3g PASS as
attribution; P9-C overall PARTIAL; P9-C.4 and P9-D/E/F unauthorized.**

## 15. P9-C.3h follow-up — real-inference downstream boundary

The separately authorized [P9-C.3h report](P9C3H_INFERENCE_DOWNSTREAM_BOUNDARY_REPORT.md) found H0, with real inference and precomputed Track but empty formal downstream, already grew at RP scale. A fresh matched 20-minute H0/RP pair measured +0.10318/+0.10255 MiB/cycle. Association/Compliance/Event/SQLite/Snapshot/Alert are not required for this 20-minute cached-frame growth. The narrower P9-C.3g suggestion that formal business downstream was required is superseded; no retained owner or indefinite leak was identified. **P9-C.3h PASS as attribution; P9-C overall PARTIAL.**

## 16. P9-C.3i follow-up — inference worker/session lifecycle

The separately authorized [P9-C.3i report](P9C3I_INFERENCE_WORKER_LIFECYCLE_REPORT.md) compares five fresh-process, 20-minute controls on the same 47 cached real MP4 frames. T0 direct main-thread inference and T1 one persistent worker were near stable at +0.00144/+0.00231 MiB/cycle. T2 fresh inference thread per cycle, without `MonitoringService` or tracking, rose +0.10446 MiB/cycle. Fresh formal H0 T3 rose +0.10432 MiB/cycle. The conditionally authorized T4 kept H0 worker/session churn but sent real inference synchronously to a single persistent diagnostic thread; it fell to +0.00331 MiB/cycle with a −0.00504 MiB/min late slope. All semantic, model-reuse and post-exit thread gates passed. This strongly supports real inference × fresh worker-thread lifecycle as the observed 20-minute growth mechanism, while a material `MonitoringService`-specific contribution is not supported by this comparison. Native retained owner and indefinite production leak remain unconfirmed. **P9-C.3i PASS as attribution; P9-C overall PARTIAL.** P9-C.4 and P9-D/E/F remain unauthorized.
