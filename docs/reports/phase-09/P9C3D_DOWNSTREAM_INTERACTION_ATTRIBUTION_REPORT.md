# P9-C.3d — Monitoring Lifecycle & Downstream Interaction Isolation

## Scope and frozen identity

This authorized attribution increment first isolates the real
`MonitoringService.start()`/worker/source/status/EOF lifecycle as S0.
Only if S0 is near plateau may it screen S1–S4 downstream stages using
precomputed real Detection and Track fixtures. It does not modify
production services, model, tracker/config, frozen runtime or P9-B
acceptance. P9-C.4 and P9-D/E/F remain unauthorized.

PRE-READ found no substantive governance conflict. At entry branch
`main`, HEAD and `origin/main` were
`6c38a4ea51eec9a62f433683a3447c073852cbbd`. `git diff --check`,
preflight, demo check and pip check passed in `.venv-final-demo-verify`.

| Frozen item | SHA256 at entry |
| --- | --- |
| Model `best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Inference config | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| Tracker config | `42ec753ee1511b9de652a750b2d67a384f4aea95d56b43a98d287c877121f10a` |
| FINAL-DEMO-RUNTIME-001 lock | `56944614bacdf861d0ad8526e7b9b7b7318039d94644a6f0aa0c51ac59233bc4` |
| Real Detection fixture | `c8c53966fb1117a26f23df648f6e21179555e32f0cb6bd1a7a4f48addedd8f38` |
| Real Track fixture | `0e42709fab781ba79eb135da09789212ff932e7ee412c33c0b571919f8ec76c1` |

## Existing evidence and why S0 comes first

Historical N retained +0.0238 MiB/cycle with precomputed detections
and tracks, but includes real MonitoringService worker/session lifecycle,
status construction and cached-source open/read/close. P9-C.3c
tracker-only P/Q/R reached late plateaus and did not reproduce the
directional L−N +0.0192 MiB/cycle difference. N cannot be labeled a
pure downstream slope. S0 isolates its MonitoringService component
before adding business stages.

## S0 design and lifecycle audit

S0 uses the same 47 cached decoded real MP4 `FrameData` objects per
cycle. Every cycle calls formal `MonitoringService.start()`, creates
its real worker Thread and a new diagnostic cached source, executes
47 real source reads and `_process_frame()` calls, reaches EOF,
closes the source and joins the worker. Its diagnostic inference,
tracker, association, compliance and event boundaries return minimal
formal empty outputs; no event or downstream side effect occurs.
The latest frame image remains held by MonitoringStatus, as in
production, and is replaced each frame. The source factory uses only
weak references for live-source counting. A five-second probe records
RSS/VMS/private, traced bytes, GC, process and GC-visible Thread counts,
MonitoringStatus count, source/worker counters, recent events and
latest-frame identity. It does not retain a frame/status history.

One-cycle smoke passed: 47 frames, zero events, one worker created and
exited, source created/opened/closed once and no source live at exit.

## S0 and staged results

S0 ran in a fresh process for 1200.23 seconds, reaching exactly 150
cycles and 7050 frames. All 150 workers exited; all 150 newly created
sources opened and closed; zero sources remained live at exit. No events
were emitted. The final state was `completed` with a preview and one
`MonitoringStatus` object. The 2-minute-on RSS slope was +0.00261
MiB/min or **+0.000344 MiB/cycle**, versus historical N's +0.0238
MiB/cycle. Mean RSS was 174.20 MiB at 2–5 min, 174.01 MiB at 5–10
min, and 174.08 MiB at 10–20 min. Traced memory slope was +0.000136
MiB/min. Warm ranges: process threads 16–19, handles 356–360, open
files exactly 2, live sources 0, GC-visible `MonitoringStatus` 1–2
and `Thread` exactly 2. This is a near plateau; the lifecycle alone
does not reproduce N's slope. The stage probe and analysis are under
`artifacts/p9c3d/20260927T085534Z-757a46d1/attribution/`.

S1–S4 screening was authorized by the S0 decision. S1 ran in a fresh
process for 600.27 seconds: 75 cycles, 3525 frames, zero events. The
2-minute-on RSS slope was −0.0224 MiB/min or **−0.00302 MiB/cycle**;
traced slope was −0.000008 MiB/min. Mean RSS was 174.52 MiB at 2–5
min and 174.70 MiB at 5–10 min, with transient sawtooth samples and
no sustained positive trend. Warm process threads 17–19, handles
356–360, open files 2, live sources 0; GC-visible status 1–2 and
Thread 2. All 75 workers and sources completed/closed. The S1 probe
is under `artifacts/p9c3d/20260927T091736Z-e4931647/attribution/`.
S1 does not create a first material divergence. S2 ran in its own
process for 600.33 seconds: 75 cycles, 3525 frames, and exactly 75
confirmed `PPE_UNKNOWN` events (one per cycle) through real
`EventService`/`EventEngine`/temporal processing. Its isolated discard
store held no event history and the boundary returned no events to
MonitoringService, so SQLite/snapshot/alert remained absent. The
2-minute-on RSS slope was +0.00619 MiB/min or **+0.000827 MiB/cycle**;
traced slope was +0.00104 MiB/min. Mean RSS was 174.24 MiB at 2–5
min and 174.34 MiB at 5–10 min. Warm event active/recovery/temporal
cardinalities were each exactly 1; status count 1–3, Thread exactly 2,
files exactly 2, handles 356–360. All workers and sources closed.
Probe: `artifacts/p9c3d/20260927T092823Z-84a09b13/attribution/`.
S2 does not create a material divergence. S3 ran in its own process
for 600.27 seconds: 75 cycles, 3525 frames, 75 confirmed events,
75 MonitoringService events and 75 rows in the isolated SQLite DB.
Snapshot and alert used bounded diagnostic replacements; the
`diagnostic/no-snapshot` value explicitly denotes no image file. Its
2-minute-on RSS slope was +0.0148 MiB/min or **+0.00197 MiB/cycle**;
from 5 min it was −0.0197 MiB/min. Traced slope was +0.00119 MiB/min.
Mean RSS was 175.68 MiB at 2–5 min and 175.80 MiB at 5–10 min.
Warm files stayed at 2, handles 356–360, recent events exactly 1,
active/temporal states exactly 1, status count 1–2 and Thread exactly
2. All workers/sources closed. Probe:
`artifacts/p9c3d/20260927T093855Z-9c2f5553/attribution/`.
S3's small slope increase over S2 is not a material reproducible
divergence in a 10-minute screen.

S4 ran in a fresh process for 600.26 seconds: 75 cycles, 3525 frames,
75 confirmed events, 75 SQLite rows, 75 real JPEG snapshots and two
successful Console/Web alerts per cycle. Mean RSS was 181.50 MiB at
2–5 min and 181.76 MiB at 5–10 min; its 2-minute-on slope was +0.0350
MiB/min or **+0.00464 MiB/cycle**, and its 5-minute-on slope was
−0.00523 MiB/min. Traced slope was +0.00886 MiB/min. Warm threads
17–19, handles 361–367, open files 2–5 (the high values were transient
in-cycle), live source 0–1, recent event 0–1, status 1–2 and GC-visible
Thread exactly 2. All workers/sources closed. The final status was
`completed`, with one event, a real snapshot path and two delivered
alerts. Probe: `artifacts/p9c3d/20260927T095000Z-69619418/attribution/`.
S4 incurred a higher initial RSS allocation than S3, but the screened
growth was much smaller than historical N's +0.0238 MiB/cycle and
flattened after 5 min. It does not reproduce N's trend at matched
event/cycle cardinality.

## First divergence, confirmation and interaction

**FIRST DOWNSTREAM DIVERGENCE: NONE. N RESIDUAL NOT REPRODUCED.**
The 2-minute-on RSS slopes (MiB/cycle) were S0 +0.000344, S1
−0.00302, S2 +0.000827, S3 +0.00197, S4 +0.00464, versus N +0.0238.
S4's incremental +0.00266 over S3 is a screening observation, not a
repeated material positive slope. Its 5-minute-on slope turned slightly
negative. The traced slopes (MiB/min) were S0 +0.000136, S1
−0.000008, S2 +0.00104, S3 +0.00119 and S4 +0.00886, versus
historical N +0.0566. The Python/native split remains unresolved:
S4's traced increase is small in absolute size and the different
harnesses prevent assigning the N gap to a native owner.

The conditional matched 20-minute adjacent-stage pair, real versus
precomputed tracker pair, and S4 alert/snapshot split were not
triggered. Thus **tracker × downstream interaction is NOT TESTED** in
this increment. The historical L−N directional difference still
supports investigating interaction, but does not prove it.

Historical N ran `scripts/run_p9b_full_chain.py:run()` with
`ObservedMonitoringService`, `Observed` wrappers on every business
boundary, `ObservedSource`, `ObservedTemporalFilter`, `TimedAlertAdapter`,
`BoundedRecorder`, rolling cycle/console logs, JSONL `EventService`
storage, and a resource sampler. S4 calls the formal
`MonitoringService` directly with lean counters, a discard
`EventService` store, and a no-op console sink; its 5-second probe
samples different object cardinalities. The source, frame, Detection,
Track and one-event/cycle business semantics match, but the harness
and observation/writing paths do not. These concrete differences are
the smallest remaining reproduction boundary; the 10-minute screen
also cannot establish a 20-minute late behavior. They explain why S4
cannot be treated as an exact N rerun; they are not yet shown to cause
N's growth.

Static `MonitoringService` inspection confirms each frame replaces
`latest_frame` in a fresh immutable status. S0's GC-visible status
count stayed 1–2, Thread exactly 2, with no old cached source live
after cycles. It gives no evidence of accumulating old status or
worker references. GC does not track NumPy array buffers; the source
weakset and process RSS are the stronger bounds available here.
S2/S3/S4 active and temporal cardinalities stayed at 1, while recent
events stayed at 0–1. The real alert adapters still retain unique IDs
in `_completed` maps; prior E micro quantified that separate known
retention risk. This stage did not measure their per-cycle cardinality,
so the S4 result does not resolve that risk or attribute its RSS.

Updated suspect order: (1) historical N harness/observer/logging
interaction or run-to-run allocator variance; (2) cross-component
allocator effects over a longer window; (3) tracker × downstream
interaction for the separate L−N gap. MonitoringService lifecycle
alone, association/compliance alone and the isolated temporal path
are weakened by these controls. No production leak owner is identified.

**Unique next minimal action, requiring separate authorization:**
run one N-harness bridge control with the frozen precomputed Detection
and Track fixtures, same 47 frames/8-second pacing, adding N's
observer/recorder/JSONL/rolling-log wiring to S4 in a single fresh
20-minute process, with the same bounded probe and a matched lean S4
20-minute control only if needed to separate late-window variance.
Compare identical 2–5, 5–10 and 10–20-minute windows before any
component attribution. No such run or production change is started
here.

## Gates and final decision

The staged experiment decision is **P9-C.3d PASS for completed
attribution controls, P9-C overall PARTIAL**. S0 and all four screens
completed, no first material divergence was evidenced, and the
conditional confirmation/interaction experiments were correctly
withheld. The full production graph remains neither proven bounded
nor proven to have an unbounded leak.

| Gate | Decision |
| --- | --- |
| C3D-G1/G2 S0 lifecycle and attribution | PASS: 150 cycles, 7050 frames, near plateau, balanced worker/source lifecycle |
| C3D-G3/G4 screens and first divergence | PASS: S1–S4 each 75 cycles; NONE, N RESIDUAL NOT REPRODUCED |
| C3D-G5/G6 conditional pairs | NOT REQUIRED: no material first divergence; tracker interaction NOT TESTED |
| C3D-G7/G8/G9 domain, ranking, next action | PASS: RSS/traced/container evidence and N-harness bridge proposed |
| C3D-G10 regression | PASS: 715 tests, compileall, preflight, demo check, pip check |
| C3D-G11 frozen identity | PASS: hashes, dataset, pip freeze, HEAD/origin/main and historical tag unchanged |

The complete repository suite passed **715/715**. `compileall -q core
infra services utils web scripts diagnostics`, preflight,
`run_demo.py --check`, `pip check` and final `git diff --check` passed.
`pip freeze` snapshots were identical. Exit hashes of the model,
inference and tracker configs, runtime lock, Detection and Track
fixtures matched the entry table. Frozen source `data.yaml` SHA256
remained `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34`;
processed checksum manifest SHA256 remained
`dbfe43c43d45e65951abec1bd112e07342b66651d799a05d79b6d749f2831c2c`.
Dataset files and P9-B code/evidence were not edited. Branch `main`,
HEAD, `origin/main` and final Phase 8 tag target remained
`6c38a4ea51eec9a62f433683a3447c073852cbbd`. No historical tag,
production service, config, dependency, commit or remote was changed.
