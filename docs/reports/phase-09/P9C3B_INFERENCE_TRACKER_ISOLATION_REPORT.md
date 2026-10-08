# P9-C.3b — Inference and Tracker Contribution Isolation

## 1. Scope

This authorized attribution increment runs only M (47 variable cached MP4
frames through formal real inference, without downstream work) and N
(precomputed real detections and precomputed formal tracks through the real
MonitoringService downstream graph). It does not change production services,
frozen configuration or Phase 9 acceptance. P9-C.4 and P9-D/E/F remain
unauthorized.

## 2. Frozen identity and PRE-READ

The required governance sources and P9-C.1/C.2/C.3/C.3a reports were read
before editing. No new substantive conflict was found. Phase 8 remains
FINAL RELEASED, P9-A/B/C.1 PASS, P9-C.2/C.3 PARTIAL, P9-C.3a PASS, and
P9-C overall PARTIAL. Branch `main`, HEAD and `origin/main` were
`6c38a4ea51eec9a62f433683a3447c073852cbbd`. Entry diff check,
preflight, demo check and pip check passed in `.venv-final-demo-verify`.

| Frozen asset | Entry SHA256 |
| --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| `locks/FINAL-DEMO-RUNTIME-001/requirements.txt` | `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |
| 47-frame MP4 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |
| P9-C.3a real-detection fixture | `c8c53966fb1117a26f23df648f6e21179555e32f0cb6bd1a7a4f48addedd8f38` |

## 3. Existing A/B/I/K/L evidence

| Control | Relevant observation |
| --- | --- |
| A full chain | +1.4358 MiB/min RSS, +0.0940 MiB/min traced over 30 minutes |
| B source only | 60-minute 30–60 RSS slope +0.0406 MiB/min; high-water behavior |
| I fixed-frame real inference | 10,000 calls; warm RSS +0.0563 MiB/min, near plateau |
| K cached 47 frames + real inference/downstream | 150 cycles/events, +0.9737 MiB/min, +0.1291 MiB/cycle, traced +0.0519 MiB/min |
| L cached 47 frames + precomputed detection/real tracking/downstream | 148 cycles/events, +0.3211 MiB/min, +0.0430 MiB/cycle, traced +0.0561 MiB/min |

These are separate processes. Slopes and workload counts, rather than
absolute RSS baselines, inform direction. K−L is about +0.0861 MiB/cycle,
but these controls do not yield an exact additive byte decomposition.

## 4. Experiment M design and semantics

M decodes the same frozen MP4 once into 47 cached frames, then repeatedly
calls formal `InferenceService.infer_frame()` on those frames in order.
No source reopen/decode, tracking, association, compliance, event, SQLite,
snapshot or alert work occurs in its measured loop. Pacing only waits after
a complete 47-frame cycle to target eight seconds. The same depth-1
tracemalloc and five-second `MemoryProbe` strategy captures RSS/VMS/private,
threads/handles/files, GC and traced bytes plus frame/detection counters.

M verifies all frame detection counts, classes, confidence and boxes against
the independently checked P9-C.3a real fixture on the first, middle and
last complete cycle. A one-cycle smoke completed 47 frames/77 detections
and passed semantics. Formal M completed in
`artifacts/p9c3/20260926T080904Z-077dd19c`: 20.125 minutes, 125 cycles,
5,875 frames and 9,625 detections. The 1st, 75th and 125th cycles all
matched the fixture exactly. Real CPU inference exceeded the eight-second
cycle target, so M achieved 125 rather than roughly 145–155 cycles. Its
per-cycle and per-frame slopes therefore matter more than a raw time-only
comparison.

## 5. Experiment N design

N will retain L's cached frames and hash-checked real detection fixture.
It replaces only real `ByteTrackPersonTrackingAdapter.update/reset` with a
non-production adapter using one independently generated and reverified
real Track fixture. The adapter reconstructs formal `TrackResult` objects
from the **current** `DetectionResult` context, validates track template
ID/class/confidence/box and fails closed on a wrong ordinal. It resets its
bounded cursor per MonitoringService cycle. The real association,
compliance, temporal/event, SQLite, snapshot, alert and bounded observer
remain in the formal MonitoringService graph. N will be paced to roughly
eight seconds per 47-frame cycle.

The fixture was generated from formal ByteTrack twice independently and
matched exactly: 47 frames, 66 tracks,
`artifacts/p9c3/p9c3b-real-tracks.json`, SHA256
`0e42709fab781ba79eb135da09789212ff932e7ee412c33c0b571919f8ec76c1`.
It records the detection fixture and tracker configuration hashes plus
Ultralytics/lap versions. The one-cycle N smoke
`artifacts/p9c3/20260926T083205Z-628bd259` matched the earlier L smoke
`artifacts/p9c3/20260926T072401Z-f14ffa28` in the complete semantic
comparator (`different_fields=[]`), including per-frame detections/tracks,
association, event, SQLite, snapshot hash and alert delivery. Formal N was
started only after this PASS.

## 6. Results, comparison and interpretation

M warm (minutes 2–20) RSS slope was +0.0470 MiB/min,
+0.00736 MiB/cycle, +0.000156 MiB/frame; traced-current slope was
+0.00566 MiB/min. Minute 10–20 RSS slope was −0.00282 MiB/min. RSS
window means were 568.192 MiB at minutes 2–10 and 568.784 MiB at
10–20, with overlapping oscillatory ranges. Variable-frame real inference
alone therefore shows a weak contribution compared with K−L's roughly
+0.0861 MiB/cycle gap; an inference/downstream interaction remains possible.
N completed in `artifacts/p9c3/20260926T083238Z-2323fd93` in 20.000
minutes: 150 cycles, 7,050 frames, 150 events, 150 SQLite rows,
150 snapshots and 300 alert deliveries. All 211 probe samples were
captured at about five-second intervals. The diagnostic tracker reset
once per cycle (`_session_count=150`), and its cursor ended at 47;
it held only the 47-frame fixture. The final formal output and probe
counts agreed.

| Control | Cycles/events | Warm RSS MiB/min | Warm RSS MiB/cycle | Warm traced MiB/min | 2–10 RSS mean MiB | 10–20 RSS mean MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| I fixed-frame real inference | 10,000 calls / 0 events | +0.0563 | not comparable | +0.0011 | 447.46 | 447.86 |
| M variable-frame real inference only | 125 / 0 | +0.0470 | +0.00736 | +0.00566 | 568.19 | 568.78 |
| K real inference + real full downstream | 150 / 150 | +0.9737 | +0.1291 | +0.0519 | 600.00 | 608.64 |
| L precomputed detections + real tracker/downstream | 148 / 148 | +0.3211 | +0.0430 | +0.0561 | 379.54 | 382.38 |
| N precomputed detections/tracks + real downstream | 150 / 150 | +0.1779 | +0.0238 | +0.0566 | 184.05 | 185.58 |

Absolute RSS values differ because each control starts a separate process
with different resident components. They are not an additive comparison.
N's event-normalized RSS slope was +0.02377 MiB/event versus L's
+0.04300 MiB/event. N's 2–20-minute RSS time/cycle slopes were about
45% lower than L; the traced-current slopes were effectively equal.
N's 10–20-minute RSS slope remained +0.2121 MiB/min, versus L's
+0.3193 MiB/min. Its 10–20 RSS mean exceeded the 2–10 mean by
1.52 MiB. Thus removing real ByteTrack reduced but did not eliminate
growth over this window. A step around minute 14 and subsequent rise
are compatible with allocator capacity changes; neither a persistent
native leak nor eventual high-water plateau is established.

N's warm resource ranges were 17–20 threads, 388–395 handles and
10–14 open files. `monitor_recent_events` stayed at 1, event active at
most 1 and temporal states at most 2. Web history and both alert
completion maps reached 150 entries, as expected for 150 unique events;
the existing RISK-029 remains separate. Diagnostic tracker cursor was
between 0 and 47 within cycles, never accumulating across sessions.

### Contribution decision matrix

| Path | Evidence and judgment |
| --- | --- |
| Variable-frame real inference alone | M +0.00736 MiB/cycle, near I's low time slope and far below K−L ≈+0.0861; **WEAK** standalone explanation. Inference/downstream interaction remains possible. |
| Real ByteTrack update/reset | L→N reduced RSS slope from +0.0430 to +0.0238 MiB/cycle at nearly matched cycle/event counts; **SUPPORTED contributor**, not proven exact allocation owner. |
| Other downstream / interaction | N still rose +0.1779 MiB/min and +0.0238 MiB/event; **SUPPORTED residual**, exact stage unknown. |
| Repeated MP4 source lifecycle | Prior B60 late near-plateau and K growth without cycle decoding; warm-up contributor, insufficient sole explanation. |
| Alert completion retention | Production maps grow with unique event IDs, but 10,000-event micro measured a small fraction of P9-C.2 RSS; real boundedness risk, weak main RSS explanation. |
| Event/SQLite/snapshot | Prior F reached early plateau; these paths run in N, so they are possible contributors or interactions but lack a single-owner result. |
| Python heap versus native/allocator | L/N traced slopes ~+0.056 MiB/min while their RSS slopes differ by ~+0.143 MiB/min; untraced/native allocator or working-set behavior is a stronger domain hypothesis. No native allocation stack exists. |

Updated suspect ranking: (1) real tracker update/reset native allocator
or interaction, (2) non-tracker downstream interaction retained in N,
(3) inference plus downstream interaction for K−L, (4) source lifecycle
warm-up, (5) small measured alert retention. This is directional evidence,
not an exact additive decomposition. No standalone YOLO memory leak or
unbounded real full-graph leak has been confirmed.

The smallest next separately authorized test is **P9-C.3c tracker-native
attribution**: isolate real ByteTrack update-only versus repeated
construct/reset on the same verified Detection sequence, then inspect
native RSS/allocator behavior and a longer boundedness window only for
the path that reproduces L−N. Do not start that experiment or a
production fix under P9-C.3b.

## 7. C3B Gates and regression

| Gate | Status |
| --- | --- |
| C3B-G1 M 20-minute variable-frame inference | PASS; 125 cycles (CPU throughput below target) |
| C3B-G2 M detection semantics stable | PASS; cycles 1/75/125 |
| C3B-G3 M RSS/traced/cycle metrics | PASS |
| C3B-G4 real Track fixture generated and verified | PASS; independent repeat |
| C3B-G5 diagnostic tracker context semantics | PASS; five focused tests and smoke |
| C3B-G6 L/N one-cycle semantic equivalence | PASS; no different fields |
| C3B-G7 paced N 20-minute control | PASS; 150 cycles/events |
| C3B-G8 L/N time/cycle/event comparison | PASS; time, cycle and event slopes above |
| C3B-G9 inference/tracker contribution decisions | PASS; matrix above |
| C3B-G10 suspect ranking | PASS; ranking above |
| C3B-G11 full regression | PASS; 698/698 |
| C3B-G12 frozen identity/dependencies | PASS; hashes and pip freeze unchanged |

## 8. Regression, frozen verification, changed files and final result

Focused diagnostic tests passed 5/5; full regression passed **698/698**.
`compileall -q core infra services utils web scripts diagnostics`,
`scripts/preflight.py`, `scripts/run_demo.py --check`, `pip check` and
`git diff --check` passed. Entry and exit `pip freeze` are identical.
Exit SHA256 values for the checkpoint, inference configuration, runtime
lock, 47-frame MP4 and Detection fixture match the values in Section 2.
The new Track fixture SHA256 is the value in Section 5. Branch `main`,
HEAD and `origin/main` remain
`6c38a4ea51eec9a62f433683a3447c073852cbbd`; the historical Phase 8
release tag was not changed. The P9-B production path and dataset were
not edited. Existing uncommitted P9-A/B/C work was preserved.

This increment changed only diagnostic harness/analysis scripts,
`diagnostics/p9c3b_precomputed_tracking.py`, focused tests, this and the
aggregate C3 report, status/gate/risk/phase/changelog records and its
worklog. Generated fixtures and runs remain in ignored `artifacts/p9c3/`.
No production service, tracker config, model, lock or business threshold
was changed.

**P9-C.3b RESULT: PASS. INFERENCE CONTRIBUTION: WEAK as a standalone
cause of K−L. TRACKER CONTRIBUTION: SUPPORTED directionally. FULL-GRAPH
UNBOUNDED LEAK: NOT CONFIRMED. P9-C OVERALL: PARTIAL.** P9-C.4 and
P9-D/E/F remain unauthorized. No commit, tag, push, reset or production
fix was made.
