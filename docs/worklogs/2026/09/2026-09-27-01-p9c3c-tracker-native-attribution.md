# P9-C.3c ByteTrack Native Lifecycle Attribution — 2026-09-27

## Changed

Added diagnostic-only P/Q/R tracker drivers and a five-second resource
probe/analysis script, eight quick deterministic tests, the C3c report
and current governance records. No production tracker, configuration,
model, downstream service or frozen dependency was modified.

## Reason

P9-C.3b found a directional L−N RSS reduction when real ByteTrack was
replaced by verified real Track outputs, but did not distinguish update
from reset/reconstruct or establish standalone tracker growth.

## Validation

Read-only audit confirmed that project backend reset invokes frozen
Ultralytics reset, then clears its BYTETracker reference. Each of P/Q/R
completed 149 paced cycles in 20 minutes using the hash-checked real
47-frame Detection fixture. P ran 7,003 updates on one tracker, Q ran
149 construct/reset cycles without updates, and R ran 7,003 updates
across 149 reconstructed sessions. Warm RSS slopes were P +0.00155,
Q +0.00080 and R +0.00168 MiB/cycle, much smaller than the directional
L−N +0.0192 MiB/cycle. Late windows approached plateau; no 60-minute
extension was triggered. Eight focused tests and the full 706-test
repository suite passed. Compileall, preflight, demo check, pip check
and diff check passed. Frozen hashes, dataset identity, pip freeze,
HEAD/origin/main and historical tags were unchanged.

## Evidence

`docs/reports/phase-09/P9C3C_TRACKER_NATIVE_ATTRIBUTION_REPORT.md`;
ignored probe, analysis and summary artifacts under `artifacts/p9c3/`.

## Risk

P/Q/R are tracker-only independent processes. They weaken a standalone
tracker leak hypothesis but do not cancel the full-downstream L/N
difference or prove full-graph boundedness. RISK-028 remains OPEN.

## Not Verified

No native allocation stack or exact cross-component owner was identified.
Real full-graph eventual plateau is not established. No production fix
was attempted.

## Next Step

Seek separate authorization for one matched-load tracker/downstream
interaction control. P9-C overall remains PARTIAL; P9-C.4 and
P9-D/E/F remain unauthorized.
