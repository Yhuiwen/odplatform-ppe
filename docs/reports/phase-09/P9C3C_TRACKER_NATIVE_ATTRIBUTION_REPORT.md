# P9-C.3c — ByteTrack Native Lifecycle Attribution

## Scope and frozen identity

This authorized diagnostic isolates tracker updates (P), tracker
construct/reset lifecycle without updates (Q), and the real per-cycle
tracker-only path (R). It uses the hash-checked P9-C.3a Detection fixture
and no YOLO, video decoding, association, event, persistence, snapshot or
alert work. Production tracker, configuration and downstream services are
unchanged. P9-C.4 and P9-D/E/F remain unauthorized.

At entry, branch `main`, HEAD and `origin/main` were
`6c38a4ea51eec9a62f433683a3447c073852cbbd`. `git diff --check`,
runtime preflight, demo check and pip check passed in
`.venv-final-demo-verify`. Entry hashes:

| Frozen asset | SHA256 |
| --- | --- |
| Model checkpoint | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Inference config | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| Tracker config | `42ec753ee1511b9de652a750b2d67a384f4aea95d56b43a98d287c877121f10a` |
| FINAL-DEMO-RUNTIME-001 lock | `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |
| Real Detection fixture | `c8c53966fb1117a26f23df648f6e21179555e32f0cb6bd1a7a4f48addedd8f38` |
| Real Track fixture | `0e42709fab781ba79eb135da09789212ff932e7ee412c33c0b571919f8ec76c1` |

## Existing L/N evidence

L ran 148 complete cycles/events with real ByteTrack and precomputed
detections, at +0.3211 MiB/min and +0.0430 MiB/cycle RSS. N ran 150
cycles/events with independently verified precomputed tracks and the same
formal downstream path, at +0.1779 MiB/min and +0.0238 MiB/cycle RSS.
The directional L−N gap is about +0.0192 MiB/cycle; it is not an exact
byte accounting. Both had near-equal Python traced-current slopes.

## Read-only ByteTrack lifecycle audit

`ByteTrackPersonTrackingAdapter.reset()` calls its active backend reset.
`_UltralyticsByteTrackBackend.reset()` calls `BYTETracker.reset()` and
sets its `_tracker` reference to `None`; the next update calls the same
project backend factory and constructs a new `BYTETracker`. In frozen
Ultralytics 8.4.157, `BYTETracker.reset()` replaces `tracked_stracks`,
`lost_stracks` and `removed_stracks` with empty lists, zeroes `frame_id`,
constructs a new `KalmanFilterXYAH` and resets `BaseTrack._count`.
`STrack.shared_kalman` is one class-level Kalman filter. Track instances
hold NumPy `_tlwh`, mean and covariance arrays and a Kalman filter
reference; update builds new result arrays and temporary association
arrays. The static ID counter and shared Kalman object are not per-cycle
lists. This audit identifies plausible allocator work, not retained native
allocation ownership.

## P/Q/R design and correctness

P holds one production adapter/backend/BYTETracker and repeats 47 real
person Detection templates with monotonically increasing diagnostic
`frame_id` and timestamp. It never resets. Its Track IDs need not match
L because session semantics intentionally differ. Q uses the project's
existing `_get_backend()._get_tracker()` factory path, then reset and
release, without any update. R uses one production adapter, resets at
the cycle boundary, updates all 47 real person Detection templates and
resets again; it retains no downstream graph. Each mode runs in a
separate process, targets eight seconds per cycle, uses 5-second RSS,
VMS/private, thread, handle, file, tracemalloc and GC samples, and records
tracker instance, tracked/lost/removed and native frame counts. No
`gc.collect()` is injected.

Eight focused tests passed, covering fixture identity, monotonic context,
P/Q/R drivers, pacing, state probing and production-default isolation.
P one-cycle smoke produced 47 updates and 66 Track outputs; tracker
frame count reached 47 with tracked/lost/removed = 1/1/0.

## P/Q/R results and normalized comparison

P completed in `artifacts/p9c3/20260927T073321Z-e0c9ce8e`:
20.006 minutes, 149 cycles, 7,003 real ByteTrack updates, 10,574
Track outputs and one BYTETracker instance. The native frame counter
reached 7,003. At exit tracked/lost/removed = 1/1/0 and GC-visible
STrack/BYTETracker/KalmanFilterXYAH counts = 2/1/2.

P's 2–20-minute RSS slope was **+0.01163 MiB/min**,
**+0.00155 MiB/47-frame cycle** and **+0.0000331 MiB/update**.
The 10–20-minute slope was +0.00215 MiB/min. Python traced-current
slope was +0.00890 MiB/min. Warm resource ranges: threads 1–5,
handles 425–435, files 2; tracked 1–2, lost 0–1, removed 0.
The track containers and GC-visible object count remained bounded in
this 20-minute persistent-update workload. P's per-cycle RSS slope is
far below the L−N directional difference of about +0.0192 MiB/cycle.

Q completed in `artifacts/p9c3/20260927T075444Z-64003299`:
20.006 minutes, 149 real project-factory BYTETracker instantiations and
resets, zero updates. Its 2–20-minute RSS slope was **+0.00600 MiB/min**
or **+0.000801 MiB/construct-reset cycle**; 10–20 slope was
+0.000839 MiB/min. Python traced-current slope was +0.000979 MiB/min.
Warm resource ranges were threads 1–5, handles 425–435 and files 2–3.
At exit, GC-visible BYTETracker/STrack/KalmanFilterXYAH counts were
0/0/1, the remaining Kalman instance being `STrack.shared_kalman`.
Ordinary automatic GC ran; the diagnostic did not explicitly collect.
Q did not reproduce the L−N magnitude.

R completed in `artifacts/p9c3/20260927T081539Z-b76ef1c2`:
20.007 minutes, 149 full 47-frame tracker-only cycles, 7,003 real
updates, 9,834 Track outputs and 149 BYTETracker instances. At exit,
the backend tracker reference was cleared and GC-visible
BYTETracker/STrack/KalmanFilterXYAH counts were 0/0/1. R's 2–20-minute
RSS slope was **+0.01257 MiB/min**, **+0.001678 MiB/cycle** and
**+0.0000357 MiB/update**. The 10–20-minute slope was +0.00446
MiB/min. Python traced-current slope was +0.00961 MiB/min. Warm ranges:
threads 1–5, handles 425–435, files 2; sampled tracked at most 2,
lost/removed zero. The sampler often observed the reset interval;
driver counters prove the complete 47-update workloads occurred.

| Control | Cycles | Updates | RSS MiB/min, 2–20 | RSS MiB/cycle | RSS MiB/update | Traced MiB/min | RSS mean 2–10 → 10–20 MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P persistent update | 149 | 7,003 | +0.01163 | +0.001553 | +0.0000331 | +0.00890 | 245.822 → 245.937 |
| Q construct/reset only | 149 | 0 | +0.00600 | +0.000801 | N/A | +0.000979 | 245.811 → 245.870 |
| R real per-cycle tracker path | 149 | 7,003 | +0.01257 | +0.001678 | +0.0000357 | +0.00961 | 245.093 → 245.216 |
| L real tracker + downstream | 148 | 6,956 | +0.3211 | +0.0430 | N/A | +0.0561 | 379.538 → 382.384 |
| N precomputed tracks + downstream | 150 | 0 | +0.1779 | +0.0238 | N/A | +0.0566 | 184.053 → 185.577 |

P/Q/R were independent processes and absolute RSS baselines are not
additive. All use least-squares warm slopes after two minutes. R's
+0.001678 MiB/cycle is about one-tenth of the directional L−N gap,
and its 10–20-minute RSS mean exceeded its 2–10 mean by only 0.123 MiB.
The 10–20-minute ranges were narrow: P 245.922–245.945 MiB, Q
245.859–245.875, R 245.195–245.238. These paths show observed
high-water/plateau behavior over 20 minutes, not a reproduced continuing
tracker-only rise of L−N magnitude.

## Boundedness, update-vs-reset decision and next action

Neither P nor Q showed material continuing growth; R also approached a
late plateau and did not reproduce L−N at comparable cycle cardinality.
Therefore no path met the authorized trigger for a 60-minute extension.
The extended-run gate is **NOT REQUIRED / NO REPRODUCING PATH**, rather
than a failed or silently skipped test. The observed isolated tracker
behavior is **STABLE_PLATEAU** over this 20-minute workload, with a small
early high-water rise. This does not establish a bound for a real full
MonitoringService graph or future inputs.

**Update-vs-reset decision: NEITHER CLEARLY** reproduces L−N alone.
P's persistent updates were weak; Q's bare lifecycle was weaker; R's
combination remained weak. The earlier L/N difference remains valid
directional evidence that including real ByteTrack changes the full
downstream process RSS slope, but C3c does not support assigning it to a
standalone tracker leak. A tracker ↔ downstream interaction or allocator
behavior across components is now the leading hypothesis. N's independent
+0.0238 MiB/cycle residual remains unexplained; Alert completion maps
remain a separately measured small contributor, while event/snapshot
micro-controls previously reached early plateaus. No native allocation
stack or exact owner was obtained.

Updated suspect ranking: (1) tracker × downstream full-graph interaction,
(2) non-tracker downstream residual in N, (3) inference × downstream
interaction for K−L, (4) source lifecycle warm-up, (5) small alert state
retention. The smallest next separately authorized experiment is a
matched-workload interaction control that incrementally restores the
formal downstream stages to R, preserving the same 47-frame Detection
fixture and 8-second cycle period. Begin with association/compliance
and event state, then persistence/snapshot/alerts only if the preceding
step reproduces L−N. A longer real full-graph boundedness confirmation
would still be needed before P9-C PASS. No production tracker fix is
justified by these isolated measurements.

## Gates, regression and final decision

| Gate | Result |
| --- | --- |
| C3C-G1 ByteTrack lifecycle audit | PASS; project and frozen Ultralytics reset paths inspected |
| C3C-G2 P persistent update | PASS; 149 cycles, 7,003 updates |
| C3C-G3 Q lifecycle only | PASS; 149 constructs/resets, zero updates |
| C3C-G4 R real tracker-only sessions | PASS; 149 sessions, 7,003 updates |
| C3C-G5 normalized RSS/traced metrics | PASS; table above and 5-second probes |
| C3C-G6 update-vs-reset decision | PASS; NEITHER CLEARLY reproduces L−N |
| C3C-G7 conditional boundedness | NOT REQUIRED; no isolated path reproduced material continued growth |
| C3C-G8 native high-water vs growth | PASS; observed tracker-only late STABLE_PLATEAU; no native stack attribution |
| C3C-G9 downstream residual | PASS; N +0.0238 MiB/cycle remains unexplained |
| C3C-G10 full regression | PASS; 706/706 |
| C3C-G11 frozen identity | PASS; hashes, dependencies and Git history unchanged |

Eight focused tests and the full repository suite (**706 passed**) passed.
`compileall -q core infra services utils web scripts diagnostics`,
preflight, `run_demo.py --check`, `pip check` and `git diff --check`
passed. `pip freeze` before/after was identical. Exit SHA256 values for
the model, inference and tracker configs, runtime lock, Detection and
Track fixtures matched entry values above. Dataset source `data.yaml`
and source/processed manifest SHA256 values matched the frozen dataset
card. Branch `main`, HEAD and `origin/main` remained
`6c38a4ea51eec9a62f433683a3447c073852cbbd`; historical Phase 8
tags were untouched. Existing uncommitted P9-A/B/C work was preserved.

This increment added `scripts/run_p9c3c_tracker_attribution.py`,
`scripts/analyze_p9c3c_tracker_attribution.py`,
`tests/unit/test_p9c3c_tracker_attribution.py`, this report and a
worklog. It appended current status, phase, gate, risk, changelog and
aggregate P9-C.3 report entries. The ignored P/Q/R artifacts are under
`artifacts/p9c3/`. No production service, tracker/config threshold,
model, dataset, lock or P9-B acceptance was edited.

**P9-C.3c RESULT: PASS. TRACKER UPDATE CONTRIBUTION: WEAK as a standalone
cause. TRACKER RESET/RECONSTRUCT CONTRIBUTION: WEAK as a standalone
cause. TRACKER RESOURCE BEHAVIOR: STABLE_PLATEAU in P/Q/R's observed
20-minute windows. PRODUCTION TRACKER LEAK: NOT CONFIRMED. P9-C OVERALL:
PARTIAL.** The next minimal experiment is a separately authorized
matched-workload tracker/downstream interaction control. P9-C.4 and
P9-D/E/F were not started; no commit, tag, push or reset was performed.
