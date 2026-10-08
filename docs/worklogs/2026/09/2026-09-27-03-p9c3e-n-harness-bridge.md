# P9-C.3e N-Harness Bridge Attribution — 2026-09-27

## Changed

Added a diagnostic bridge reusing the historical N full-chain runner,
a boundedness companion probe, semantic comparator/window analyzer,
eight quick tests and the P9-C.3e report. Updated the aggregate
resource report and Phase 9 status, changelog, gates and risk record.
No production service, model, config, dataset, runtime or P9-B
implementation was edited.

## Reason

P9-C.3d lean S0–S4 did not reproduce historical N's RSS residual.
N included observation wrappers, BoundedRecorder, JSONL and rolling
logs absent from lean S4.

## Validation

The static N/S4 wiring diff audited 20 specified items. A one-cycle
S4/H comparison matched 47 frames, 77 detections, 66 tracks,
compliance findings, event identity apart from UUID/time, SQLite,
snapshot SHA256 and alerts. H ran 150 cycles/events over 20 minutes
at +0.03127 MiB/cycle RSS, +0.22384 MiB/min in the 10–20-minute
window and +0.05637 MiB/min traced. Matched fresh-process lean J
ran 150 cycles/events at +0.00408 MiB/cycle, +0.02986 MiB/min late
and +0.00932 MiB/min traced. Recorder lists/dicts never exceeded
their 200-row caps; fixed FrameData count stayed 47. Eight focused
tests and the full 723-test suite passed; compileall, preflight,
demo check, pip check, diff check and frozen verification passed.

## Evidence

`docs/reports/phase-09/P9C3E_N_HARNESS_BRIDGE_REPORT.md`;
ignored H probe/JSONL/summary under
`artifacts/p9c3/20260927T102628Z-bc550e38/` and J probe/summary
under `artifacts/p9c3d/20260927T104810Z-69ae6418/`.

## Risk

The matched result supports a diagnostic harness/observation effect
but does not assign it to one wrapper, recorder or allocator path.
Formal alert idempotency maps grow in both H/J. The 60-minute
instrumented real full-graph rise remains historical evidence;
lean production full-graph boundedness is unverified. RISK-028 stays
OPEN and P9-C overall PARTIAL.

## Not Verified

No production downstream leak was confirmed, and no eventual bound
for the lean real full graph was established. P9-C.3f, P9-C.4 and
P9-D/E/F were not started.

## Next Step

Only on separate authorization, P9-C.3f FINAL LEAN REAL FULL-GRAPH
BOUNDEDNESS CONFIRMATION: real production graph with a minimal
external resource sampler and no heavy per-frame diagnostic
observer/recorder.
