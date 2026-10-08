# P9-C.3e — N-Harness Bridge Attribution

## Scope and frozen identity

This authorized diagnostic increment tests whether historical N's
RSS residual can be reproduced by N's observation assembly while
holding the 47 cached real MP4 frames, verified Detection/Track
fixtures, formal downstream business components and 8-second pacing.
No production implementation, model, configuration, runtime or P9-B
acceptance is changed. P9-C.3f, P9-C.4 and P9-D/E/F are not started.

PRE-READ found no substantive governance conflict. At entry branch
`main`, HEAD and `origin/main` are
`6c38a4ea51eec9a62f433683a3447c073852cbbd`. `git diff --check`,
preflight, demo check and pip check passed. Frozen SHA256 values:

| Item | SHA256 |
| --- | --- |
| `best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| `configs/tracker.yaml` | `42ec753ee1511b9de652a750b2d67a384f4aea95d56b43a98d287c877121f10a` |
| FINAL-DEMO-RUNTIME-001 lock | `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |
| Detection fixture | `c8c53966fb1117a26f23df648f6e21179555e32f0cb6bd1a7a4f48addedd8f38` |
| Track fixture | `0e42709fab781ba79eb135da09789212ff932e7ee412c33c0b571919f8ec76c1` |

## Historical N and S4

N used the same verified precomputed Detection/Track outputs and full
downstream chain for 150 cycles/events over 20 minutes. Its warm RSS
was +0.1779 MiB/min, +0.0238 MiB/cycle. Lean S4 completed 75
cycles/events over 10 minutes, with 75 SQLite rows, 75 snapshots and
150 alerts. Its warm RSS was +0.00464 MiB/cycle, with a negative
5-minute-on slope. S4 did not reproduce N's residual.

## N-HARNESS WIRING DIFF — static audit before any bridge run

`N` is `scripts/run_p9c3_memory_attribution.py:run_full()` calling
the original `scripts/run_p9b_full_chain.py:run()` with `metrics=True`,
`bounded=True`, the cached source and precomputed inputs. `S4` is
`scripts/run_p9c3d_downstream_stages.py:run("S4", ...)`. The table
distinguishes observer state from business state; both use formal
MonitoringService logic, association, compliance, temporal processing,
SQLite, snapshot and Console/Web adapters.

| Wiring item | N | S4 | Memory behavior | Production-owned? |
| --- | --- | --- | --- | --- |
| 1. `ObservedMonitoringService` | enabled | disabled | forwards; metrics to rolling lists | NO |
| 2. inference `Observed` | enabled | disabled | forwards; count/timing to bounded recorder | NO |
| 3. tracker `Observed` | enabled | disabled | forwards; track dicts capped 200 | NO |
| 4. association `Observed` | enabled | disabled | forwards; JSONL + 200 recent | NO |
| 5. compliance `Observed` | enabled | disabled | finite counters, capped first-seen keys | NO |
| 6. `ObservedTemporalFilter` | enabled | disabled | forwards; confirmed keys capped 200 | NO |
| 7. event `Observed` | enabled | disabled | forwards; events capped 200 | NO |
| 8. `ObservedSource` | enabled | disabled | forwards; timeline/stages rolling 200 | NO |
| 9. `TimedAlertAdapter` | enabled | disabled | timing to rolling stages; formal adapter state still present | NO |
| 10. `BoundedRecorder` | enabled | disabled | primary lists/dicts 200; finite Counters | NO |
| 11. frame timing JSONL | enabled | disabled | streamed, recent 200 | NO |
| 12. tracking JSONL | no separate writer; capped dicts in final summary | disabled | capped 200 | NO |
| 13. association JSONL | enabled | disabled | streamed, recent 200 | NO |
| 14. event timeline JSONL | enabled | disabled | streamed, recent 200 | NO |
| 15. cycle summary records | enabled | disabled | streamed, recent 200 | NO |
| 16. console rolling history | enabled | disabled (no-op sink) | N streamed/recent 200 | NO |
| 17. resource probe/sampler | enabled, two paths | enabled, lean probe | both stream; N recorder resource recent 200 | NO |
| 18. `EventService` JSONEventStore | enabled | disabled (discard store) | N append/open/close per event; file grows, no retained list | YES service; NO path choice |
| 19. final summary construction | enabled | enabled, lean summary | N recent 200 plus query page max 1000; once at end | NO |
| 20. retained auxiliary containers | rolling recorder/cycles/console; fixed-mark probe snapshots; formal alert `_completed` | lean counters/status; formal alert `_completed` | recorder bounded; alert maps unbounded by event ID in both | mixed |

The static check found no recorder-owned unbounded frame/image history.
`Observed` closures are per-call and return their outputs; callbacks
copy schema dictionaries into rolling containers, not NumPy images.
`BoundedRecorder` retains at most 200 rows per rolling list/dict.
`Recorder` counters have finite detection/finding categories;
`first_seen`, `confirmed`, `events`, tracking and association
containers are rolling. `JSONEventStore.append_many()` opens and
closes the file per append without an in-memory record list. Disk
growth alone is not RSS growth. Formal alert `_completed` maps are
known unbounded by unique IDs in both N and S4; they are not an
N-only harness difference.

This completes the required static wiring diff before experiment H.

## Experiment H and one-cycle semantic gate

H directly reuses `scripts/run_p9b_full_chain.py:run()` with
`metrics=True`, `bounded=True`, the historical N diagnostic source
and the same precomputed inference/tracker adapters. The additional
`BridgeProbe` writes a companion cardinality JSONL, leaving the
historical five-second `MemoryProbe` intact. It records rolling
container sizes/caps/line counts, file sizes, GC-visible FrameData
and ndarray wrapper counts, and alert map sizes. It never collects
historical frames or all JSONL records in memory.

One-cycle S4/H runs used 47 cached frames. The S4 semantic gate used
a one-cycle-only compliance tap; formal S4 screening from P9-C.3d
was untouched. SQLite row and snapshot metadata comparison passed:
47 frames, 77 detections, 66 tracks, one association and one unknown
association, 66 `PPE_UNKNOWN:unknown` findings and candidates,
one `PPE_UNKNOWN` event for track 1 at frame 24/source timestamp
1.001, equal bbox/confidence, one SQLite row, equal JPEG SHA256
`92452ae640a19bab64bca4e194612eff72143f95c00cb9a10ef2731aa6721b40`
at 1280×720, and two delivered/zero failed alerts. Event UUID,
wall-clock and timing values were excluded. The semantic comparator
reported zero differences. S4 evidence:
`artifacts/p9c3d/20260927T102533Z-bb242a67/`; H evidence:
`artifacts/p9c3/20260927T102551Z-b50aff6a/`.

H completed in a fresh process for 1200.00 seconds: 150 cycles,
7050 frames, 150 events/SQLite rows/snapshots and 300 successful
alerts. Probe/summary:
`artifacts/p9c3/20260927T102628Z-bc550e38/`. The 2-minute-on
RSS slope was **+0.2340 MiB/min, +0.03127 MiB/cycle and
+0.03127 MiB/event**. The 5-minute-on and 10-minute-on slopes were
+0.2406 and +0.2238 MiB/min; growth continued throughout the second
half. Traced-current slope was +0.05637 MiB/min. Mean RSS was
182.669 MiB at 2–5 min, 183.438 MiB at 5–10 min and 185.320 MiB
at 10–20 min. Absolute baseline is not compared with historical N.

Historical N completed the same 150 cycles/events at +0.1779
MiB/min and +0.0238 MiB/cycle; its traced-current slope was
+0.0566 MiB/min. H reproduces the same direction and order of
magnitude, and almost exactly the traced slope. The warm process
ranges were 17–19 threads, 389–393 handles and 11–14 open files.
Those counts were bounded despite RSS growth.

The harness cardinality stream observed caps of 200 for every
`BoundedRecorder` rolling list/dict. At H end, track IDs/details
held 47 entries, associations/candidates/events 150 each,
first-seen 2, confirmed 1, and timeline/stage/resource/frame lists
exactly 200. `FrameData` GC-visible count remained fixed at 47;
GC-visible ndarray wrapper count was 0 (NumPy buffers are not
fully described by GC). Console/Web `_completed` maps grew from
16 to 150; Web history grew from 16 to 150, below its cap of 200.
Recent MonitoringStatus events stayed at 0–1. No observer list or
wrapper retained all 7050 frame/image objects.

JSONL files grew on disk while recent in-memory rows stayed bounded:
frame timings 7050 lines/719,105 bytes; stages 50,550/3,408,373;
timeline 86,700/4,568,250; associations 150/55,200;
association candidates 150/60,000; cycles 150/196,591;
resources 211/56,906; console 150/44,700; and event evidence
150/10,650. The companion probe counted only newly flushed bytes;
the final audit streamed file lines and did not load JSONL history
into an in-memory list. Disk growth itself is not classified as an
RSS leak.

## Conditional J and attribution decision

**H Case A triggered.** Its continued 10–20-minute rise and
N-scale 2–20-minute RSS/cycle slope required a matched 20-minute
lean S4 J control. J ran in a separate fresh process for 1200.26
seconds and completed exactly 150 cycles, 7050 frames, 150
events/SQLite rows/real snapshots and 300 delivered alerts, matching
H's workload cardinality. Its final worker/source creation and
closure counts were each 150, with zero live sources. Evidence:
`artifacts/p9c3d/20260927T104810Z-69ae6418/`.

| Normalized metric | Historical N | H N-harness bridge | J lean S4 |
| --- | ---: | ---: | ---: |
| Duration / cycles / events | 20 min / 150 / 150 | 20 min / 150 / 150 | 20 min / 150 / 150 |
| RSS MiB/min, 2 min on | +0.1779 | +0.2340 | +0.03044 |
| RSS MiB/cycle, 2 min on | +0.0238 | +0.03127 | +0.00408 |
| RSS MiB/event, 2 min on | +0.0238 | +0.03127 | +0.00408 |
| RSS MiB/min, 10 min on | historical late window not established here | +0.22384 | +0.02986 |
| traced MiB/min, 2 min on | +0.0566 | +0.05637 | +0.00932 |

J mean RSS was 181.464 MiB at 2–5 min, 181.547 at 5–10 min and
181.801 at 10–20 min. Its warm process range was 16–19 threads,
361–367 handles and 2–5 open files. H's absolute RSS baseline is
intentionally not compared with J's. The H/J normalized RSS slope
ratio is about 7.7× per cycle and about 7.5× in the 10–20-minute
window; traced slope ratio is about 6.0×. This paired separation
persists after matching run duration, cycle/event counts, cached
images, Detection/Track fixtures and downstream business components.

**DIAGNOSTIC HARNESS CONTRIBUTION: SUPPORTED.** H reproduced N's
continued direction and order of magnitude, while J remained much
lower in a matched 20-minute run. This supports classifying the
historical N residual as a diagnostic harness/observation effect,
without claiming which individual observer, recorder, JSONL stream
or allocator interaction caused it. No diagnostic-only unbounded
frame/history container was found, so no diagnostic fix was made.
The growing JSONL files are disk evidence, not themselves an RSS
leak. Formal alert `_completed` maps grow in both H and J and are a
separate known risk; they do not explain the H/J difference alone.

**HISTORICAL N STATUS: REPRODUCIBLE as an instrumented N-harness
observation.** Its original artifacts remain valid and untouched;
their RSS slope is no longer evidence that a production downstream
component is leaking by itself. **PRODUCTION DOWNSTREAM LEAK: NOT
CONFIRMED.** P9-C.2's real full-graph 60-minute run also used heavy
diagnostic instrumentation, so the production full graph is still
not proven bounded. This increment does not reopen P9-B or mark
P9-C overall PASS.

The unique next action, requiring separate authorization, is
**P9-C.3f FINAL LEAN REAL FULL-GRAPH BOUNDEDNESS CONFIRMATION**:
run the real production graph with only a minimal external resource
sampler and no heavy per-frame Observed wrapper/recorder. P9-C.3f is
not started here. P9-C.4 is reserved for a confirmed production fix;
there is no confirmed production defect to fix in this increment.

## Gates, regression and frozen verification

| Gate | Decision |
| --- | --- |
| C3E-G1 wiring diff | PASS: all 20 specified wiring items audited above |
| C3E-G2 container bounds | PASS: recorder caps, auxiliary cycle/console limits, JSONL lines and frame objects audited |
| C3E-G3 semantic gate | PASS: one-cycle S4/H comparator found zero differences |
| C3E-G4/G5 H and historical N | PASS: H 150 cycles, N-scale sustained RSS and nearly identical traced slope |
| C3E-G6 conditional J | PASS: Case A triggered, matched fresh 150-cycle J completed |
| C3E-G7/G8/G9 interpretation | PASS: diagnostic harness contribution SUPPORTED, production leak NOT CONFIRMED, P9-C.3f next action identified |
| C3E-G10 regression | PASS: 723 tests, compileall, preflight, demo check, pip check |
| C3E-G11 frozen identity | PASS: pip freeze, hashes, dataset, HEAD/origin/main and historical tag unchanged |

Eight new fast deterministic tests cover the bridge builder, precomputed
business components, rolling caps/streaming, image-history absence,
semantic difference detection and cycle/event-normalized analysis.
The complete suite passed **723/723**. `compileall -q core infra
services utils web scripts diagnostics`, preflight,
`run_demo.py --check`, `pip check` and final `git diff --check` passed.
`pip freeze` before/after matched byte-for-byte.

Model, inference config, tracker config, runtime lock, Detection and
Track fixture SHA256 values matched the entry table. Frozen source
`data.yaml` SHA256 remained
`5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`;
processed checksum manifest SHA256 remained
`dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c`.
No dataset or P9-B file was edited. Branch `main`, HEAD, `origin/main`
and the `phase-8-final-integration-complete` tag target remained
`6c38a4ea51eec9a62f433683a3447c073852cbbd`. Existing
uncommitted work was preserved. No production code change, dependency
change, commit, tag, push or reset was made.

**P9-C.3e RESULT: PASS. N RESIDUAL: REPRODUCED. DIAGNOSTIC HARNESS
CONTRIBUTION: SUPPORTED. PRODUCTION DOWNSTREAM LEAK: NOT CONFIRMED.
HISTORICAL N STATUS: REPRODUCIBLE as an instrumented historical
observation. P9-C OVERALL: PARTIAL.**
