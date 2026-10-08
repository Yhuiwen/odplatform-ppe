# P9-C.3a — Precomputed Detection Downstream Isolation

## 1. Scope

P9-C.3a is a diagnostic continuation of P9-C.3. Its only major experimental
variable relative to K is per-frame inference: K uses real YOLO; L returns
real, previously computed `DetectionResult` content while retaining the
predecoded 47 images and the complete formal downstream MonitoringService
graph. This is **not** a production model alternative, P9-B E2E acceptance,
or a performance baseline. P9-C.4 and P9-D/E/F remain unauthorized.

## 2. Frozen identity

At entry, branch `main`, HEAD and `origin/main` were
`6c38a4ea51eec9a62f433683a3447c073852cbbd`. The Phase 8 final tag
remains `phase-8-final-integration-complete`. Entry `git diff --check`,
preflight, demo check and `pip check` passed. The frozen SHA256 values are:

| Asset | SHA256 |
| --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| `locks/FINAL-DEMO-RUNTIME-001/requirements.txt` | `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |
| 47-frame source MP4 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |
| frozen source `data.yaml` | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |
| processed dataset checksum manifest | `dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c` |

The required governance files and P9-C.1/C.2/C.3 reports were read before
editing. No new substantive conflict was found. P9-A/B/C.1 remain PASS;
P9-C.2/C.3 and P9-C overall remain PARTIAL at entry. Charter and P9-B
acceptance are unchanged.

## 3. Detection fixture generation

`scripts/generate_p9c3a_fixture.py` decoded the frozen real MP4 once and ran
the formal `InferenceService` with the frozen model/config on all 47 frames.
It saved frame ordinals, class IDs/names, confidence and each bbox in
`artifacts/p9c3/p9c3a-real-detections.json`, along with source/model/config/
lock hashes, Python runtime and timestamp. It then loaded the fixture through
strict identity/count checks and independently ran another real detection
pass. Every frame's full detection template matched exactly.

The result was **47 frames, 77 detections**: 76 `person`, one `no_vest`.
Fixture SHA256:
`c8c53966fb1117a26f23df648f6e21179555e32f0cb6bd1a7a4f48addedd8f38`.
The fixture resides in ignored diagnostic artifacts and cannot replace
production inference. No detections, confidence values or boxes were edited.

## 4. Diagnostic adapter design

`diagnostics/p9c3a_precomputed.py` loads only the hash-checked 47-frame
fixture. Its `PrecomputedInferenceService.infer_frame(frame, source=...)`
reconstructs formal `DetectionResult` objects with current `FrameData`
`frame_id`/`timestamp` and current MonitoringService `source`; only class,
confidence and bbox come from the real detection template. Missing/invalid
ordinals fail closed. The adapter lives exclusively under `diagnostics/` and
is injected through an optional harness parameter. Production inference,
tracker, association, compliance, temporal/event, SQLite, snapshot and alert
implementations are untouched.

## 5. One-cycle semantic equivalence

The existing K smoke `20260925T180325Z-b68a834c` and new L smoke
`20260926T072401Z-f14ffa28` used the same frozen 47-image cached source.
`scripts/compare_p9c3a_semantics.py` compared frame-by-frame detection,
tracking and association counts; formal track IDs/details, association output
and candidates,
compliance findings; event type, track, frame and source timestamp; SQLite
row, snapshot SHA256 and alert delivery counts. Event UUIDs, wall-clock
timestamps and benchmark timing were excluded. **SEMANTIC PASS: no differing
fields.** Each run processed 47 frames and 77 detections, produced one
`PPE_UNKNOWN` event at frame 24, one SQLite row, one snapshot and two
successful Console/Web alerts. The comparison JSON is
`artifacts/p9c3/p9c3a-semantic-comparison.json`.

## 6. K control and L experiment

K (`20260925T180439Z-0bf77f71`) completed 150 cycles, 7,050 frames and
150 events in 20.10 minutes. Its 2–20-minute RSS slope was +0.9737 MiB/min,
+0.1291 MiB/cycle; traced-current slope was +0.0519 MiB/min. K retained
formal inference and the complete downstream graph.

L uses the same cached 47 images and graph, with diagnostic precomputed
detections. The bounded observer, five-second `MemoryProbe`, depth-1
tracemalloc and complete source-cycle semantics remain. L waits after each
cycle to target an approximately eight-second period, to match K's roughly
150 cycles/events in 20 minutes. Formal L run
`20260926T072559Z-ccec349d` completed **148 cycles, 6,956 frames, 148
events, 148 SQLite rows, 148 verified snapshots and 296 successful
Console/Web deliveries** in 20.00 minutes, with zero alert failures. Each
cycle generated one `PPE_UNKNOWN` event. The final frame/event probe sample
may precede final summary collection by a few seconds; the completed summary
and SQLite query are authoritative for totals. A short initial start was
stopped before measurement to add SQLite/snapshot/alert cardinality to every
probe row; it is excluded from analysis.

## 7. Cycle/event normalization and RSS comparison

All slopes below are least-squares regressions over five-second probe rows
from 2 minutes onward. Event and cycle slopes are both reported; one unique
event was produced per complete cycle in each run. Absolute RSS differs
because K holds the real YOLO model and L does not. That baseline difference
is not an allocated-byte attribution.

| Metric | K real inference | L precomputed detection | L − K |
| --- | ---: | ---: | ---: |
| Duration | 20.10 min | 20.00 min | −0.10 min |
| Complete cycles | 150 | 148 | −2 (−1.3%) |
| Frames | 7,050 | 6,956 | −94 |
| Unique events / SQLite rows / snapshots | 150 each | 148 each | −2 each |
| Alert deliveries | 300 | 296 | −4 |
| Mean RSS, 2–10 min | 600.004 MiB | 379.538 MiB | baseline differs |
| Mean RSS, 10–20 min | 608.644 MiB | 382.384 MiB | baseline differs |
| RSS mean-window increase | +8.640 MiB | +2.846 MiB | −5.794 MiB |
| RSS slope, 2–20 min | **+0.9737 MiB/min** | **+0.3211 MiB/min** | **−0.6526 MiB/min (−67%)** |
| RSS slope per cycle | +0.1291 MiB | +0.0430 MiB | −0.0861 MiB (−67%) |
| RSS slope per event | +0.1291 MiB | +0.0430 MiB | −0.0861 MiB (−67%) |
| Traced-current slope | +0.0519 MiB/min | +0.0561 MiB/min | +0.0042 MiB/min |

The similar cycle/event counts make the per-minute and per-cycle direction
consistent. L still has a positive RSS slope; its later path included a
roughly 2 MiB step near minute 17–18 and does **not** prove a permanent
plateau. K's 10–20-minute mean exceeded its 2–10 mean by 8.64 MiB; L's
increase was 2.85 MiB. The roughly 67% reduction is directional evidence
that variable-frame real inference or its interaction with the downstream
graph contributes to growth. The residual L growth points to an additional
downstream/diagnostic/native or allocator contribution. Regression slopes do
not uniquely decompose bytes by owner.

## 8. Python traced memory, resources and container cardinality

Traced-current window means were K 115.506→116.005 MiB and L
54.614→55.114 MiB across 2–10 and 10–20 minutes. Their **slopes are
nearly identical**, about +0.052 and +0.056 MiB/min, even though K's RSS
slope is three times L's. This places the major *difference* outside
tracemalloc's Python allocations. Windows psutil private/VMS represent
committed virtual memory and are not direct native-leak measurements.

Threads and handles were stable within each process: K 2–10 vs 10–20
mean threads 38.50→38.29, handles 594.61→593.80; L 17.35→17.32,
handles 479.40→479.22. Open files averaged about 10.2 in both windows for
both runs, with short 10–13 variation. The lower L baseline is expected
without a loaded Torch/YOLO model, not evidence of an accumulating thread
or handle leak.

Every five-second L row includes cycle/frame/event, SQLite/snapshot/alert
totals, RSS/VMS/private, threads/handles/files, GC counts, traced current/
peak and critical state cardinalities. At the last complete cycle, Console
and Web `_completed` were both 148, Web history 148 (below its 200 cap),
SQLite/snapshot totals 148 and alert deliveries 296. In sampled 10–20-minute
windows, Monitoring recent events and EventEngine active/recovery each stayed
within 0–1; temporal states stayed within 0–1; tracker active/lost each
remained at one. Harness detail collections stayed bounded at 200. The
formal alert maps grow by event ID in both K and L and were quantified as a
small contributor in P9-C.3; they cannot explain the 67% slope difference.

## 9. Attribution decision and narrowed suspect ranking

**P9-C.3a RESULT: PASS — MULTI-CONTRIBUTOR PATTERN.** L grows at roughly
one-third of K's time/cycle/event slope under closely matched business
workloads. Repeated real inference is **not required for all** observed
growth, but removing it substantially reduces growth. The leading suspect
for the K-minus-L difference is **variable-frame real inference or its
interaction with downstream tracking/event work**. I's fixed-frame 10,000
real inference calls approached a plateau, so these data do **not** prove a
standalone YOLO leak. The residual L rise keeps tracker/update/reset,
downstream native allocations, and allocator high-water behavior in scope.
The exact native allocation owner and unboundedness remain unknown.

Read-only tracker lifecycle audit: project `ByteTrackPersonTrackingAdapter`
keeps one backend; `_UltralyticsByteTrackBackend.reset()` calls the current
tracker's reset and then clears its reference, so the next cycle constructs
a fresh `BYTETracker`. The frozen Ultralytics implementation's `reset()`
replaces `tracked_stracks`, `lost_stracks` and `removed_stracks` with empty
lists, resets frame ID and constructs a Kalman filter. `STrack.shared_kalman`
is one class-level object, not a per-cycle list. The project adapter creates
new NumPy arrays per update, and the external tracker creates per-track
arrays. This is a plausible native allocator interaction but **not** proof
of retention; no tracker isolation experiment was run in P9-C.3a.

**Next minimal experiment:** two separately bounded controls designed
before any production edit: variable 47-frame inference only (without the
downstream graph), and the matching precomputed-track-output full downstream
control that removes real ByteTrack update/reset while preserving event
semantics. Compare each with K and L at matched cycles/events. This is a
proposal only; neither control is executed in this task. Do not enter
P9-C.4 or P9-D/E/F. P9-C overall remains **PARTIAL** because the real full
graph is not proven bounded.

## 8. Gates and regression

| Gate | Status |
| --- | --- |
| C3A-G1 real fixture and hash | PASS |
| C3A-G2 context-preserving diagnostic adapter | PASS: focused tests |
| C3A-G3 one-cycle K/L semantic equivalence | PASS |
| C3A-G4 20-minute paced L control | PASS: 20.00 min, 148 cycles |
| C3A-G5 comparable cycle/event workload | PASS: K 150/150, L 148/148 |
| C3A-G6 RSS time/cycle/event regressions | PASS: Section 7 |
| C3A-G7 Python traced memory | PASS: Section 8 |
| C3A-G8 inference versus downstream decision | PASS: multi-contributor pattern |
| C3A-G9 narrowed next suspect | PASS: Section 9 next controls designed |
| C3A-G10 regression/frozen identity | PASS: 693 tests, hashes and runtime unchanged |

The full suite passed **693/693**. `compileall -q core infra services utils web
scripts diagnostics`, preflight, `run_demo.py --check`, `pip check` and
`git diff --check` passed. `pip freeze` before/after had **NO DRIFT**. The
fixture SHA256 and frozen model/config/lock SHA256 values at exit match the
values in Sections 2–3. The dataset source `data.yaml` and processed
checksum-manifest hashes match their frozen dataset-card identities. HEAD,
`origin/main` and historical Phase 8 release tag are unchanged. No
production fix, commit, tag, push or reset was made. Existing P9-A/B/C.1/C.2/C.3
working-tree edits were preserved.
