# P9-C.3b Inference and Tracker Contribution Isolation — 2026-09-26

## Changed

Added non-production M/N controls to the P9-C attribution harness. M uses
real inference on the 47 cached MP4 frames without downstream stages. N
uses the verified real Detection fixture and a separately generated real
Track fixture, then runs the formal MonitoringService downstream graph.
The diagnostic tracker injection defaults to the production adapter when
unused. Added five focused control tests and the C3b evidence report.

## Reason

K/L showed lower but persistent RSS growth after replacing repeated real
inference. Separating inference alone and tracker update/reset from the
same workload narrows the remaining resource attribution question.

## Validation

M completed 125 real-inference cycles in 20.125 minutes: 5,875 frames and
9,625 detections. Cycles 1, 75 and 125 matched the real detection fixture.
Its 2–20-minute RSS slope was +0.0470 MiB/min or +0.00736 MiB/cycle,
with a −0.00282 MiB/min slope at minutes 10–20. The CPU throughput
limited M below the target cycle count, so the rate is not a matched
throughput estimate.

The real ByteTrack fixture contains 47 frames and 66 tracks; an independent
second generation pass matched exactly. N's one-cycle output matched L
in all fields checked by the semantic comparator. Formal N completed
150 cycles/events, 150 SQLite rows, 150 snapshots and 300 alert deliveries
in 20 minutes. Its warm RSS slope was +0.1779 MiB/min or +0.0238
MiB/cycle/event, versus L +0.3211/+0.0430. Python traced slopes were
effectively equal. Five focused tests and all 698 repository tests passed.
Compileall, preflight, demo check, pip check and diff check passed; pip
freeze, frozen asset hashes, HEAD and historical tags were unchanged.

## Evidence

`docs/reports/phase-09/P9C3B_INFERENCE_TRACKER_ISOLATION_REPORT.md`;
ignored M/N diagnostic artifacts under `artifacts/p9c3/`.

## Risk

The memory observations come from separate processes, and RSS can reflect
native allocator reuse or retained capacity. They cannot by themselves
prove a production leak or indefinite boundedness. RISK-028 remains OPEN.

## Not Verified

Native allocation stack ownership and eventual full-graph RSS plateau are
not established by these 20-minute controls.

## Next Step

The smallest separately authorized next control is P9-C.3c tracker-native
attribution: compare real ByteTrack update-only with repeated construct/
reset on the verified detections, then test boundedness on the reproducing
path. P9-C overall remains PARTIAL;
P9-C.4 and P9-D/E/F remain unauthorized.
