# P9-C.3 Resource Growth Attribution — 2026-09-26

## Changed

Added isolated P9-C.3 memory probes, an analyzer, diagnostic source and alert
controls, focused unit tests, the attribution report and current governance
updates. The full-chain harness accepts optional diagnostic injection; its
default production graph is unchanged. No production source, inference,
tracking, association, temporal, event, persistence or alert implementation
was modified.

## Reason

P9-C.2's 675-cycle MP4 run preserved correctness but showed +1.2478 MiB/min
warm RSS growth without an identified owner. P9-C.3 was authorized to
distinguish retained Python state, source lifecycle, native allocation,
business side effects and diagnostic observer effects before any fix.

## Validation and evidence

The 30-minute full-chain baseline reproduced RSS growth; source-only 20-minute
and 60-minute controls, source-only persistent rewind, stateless-alert
full-chain control, 10,000-event formal alert micro, 1,000-event/snapshot
micro, separate tracemalloc snapshot and GC controls, and 10,000 fixed-frame
real inferences were run in isolated processes. The source-only 60-minute
extension reached a near-plateau in the final 30 minutes. A diagnostic
predecoded-frame full-chain control and final regression are underway.
The predecoded-frame full-chain control then completed 150 cycles, 7,050
frames and 150 events; RSS still rose +0.9737 MiB/min after warm-up while
traced Python memory rose only +0.0519 MiB/min. The final full regression
passed 689 tests. Preflight, demo check, pip check, compileall and diff check
passed; `pip freeze` matched the entry snapshot. Evidence:
`docs/reports/phase-09/P9C3_RESOURCE_GROWTH_ATTRIBUTION_REPORT.md`
and ignored `artifacts/p9c3/` run directories.

## Risk and unverified

Source-only boundedness does not establish full-chain boundedness. Alert
completion dictionaries retain event IDs without eviction, but the measured
bytes are far smaller than the full-chain RSS trend. Native allocation stacks
and the full-chain retained owner remain unconfirmed. No production bug fix
is made; P9-C.3 is PARTIAL / ATTRIBUTION INCONCLUSIVE, P9-C stays PARTIAL,
and P9-D/E/F remain unauthorized.

## Next step

Use a 20-minute precomputed-detection full-chain control to isolate repeated
model inference from the remaining tracker/event path. Then instrument the
native tracker boundary if growth remains. This is the smallest justified
next attribution step before proposing a production fix.
