# P9-C.3a Precomputed Detection Downstream Isolation — 2026-09-26

## Changed

Added a hash-checked real 47-frame detection fixture, a non-production
`PrecomputedInferenceService`, a single-cycle K/L semantic comparator,
diagnostic inference injection and eight-second cycle pacing in the existing
P9-C.3 harness, fast deterministic tests, and attribution documentation.
No production model, tracking, association, compliance, temporal/event,
snapshot, persistence or alert behavior was changed.

## Reason

P9-C.3 found that source-only RSS approaches a high-water plateau while
the full cached-frame pipeline still grows. P9-C.3a isolated repeated
real inference from the unchanged downstream graph at matching workloads.

## Validation

The fixture came from a real 47-frame pass through the frozen model/config:
77 detections, 76 person and one no_vest. A second independent real pass
matched every class, confidence and box exactly; fixture SHA256 is
`c8c53966fb1117a26f23df648f6e21179555e32f0cb6bd1a7a4f48addedd8f38`.
K/L one-cycle semantic comparison passed for detection, tracking,
association, compliance, frame-24 PPE_UNKNOWN event, SQLite, snapshot and
alerts. L completed 20.00 minutes, 148 cycles/events, 148 verified
snapshots and 296 alerts. Its RSS slope was +0.3211 MiB/min and +0.0430
MiB/cycle, versus K's +0.9737 and +0.1291; Python traced slopes were
near equal. Focused tests passed 8/8 and the final full regression passed
693/693. Compileall, preflight, demo check, pip check and diff check passed;
`pip freeze` had no drift. Frozen assets and dataset identity matched.

## Evidence

`docs/reports/phase-09/P9C3A_PRECOMPUTED_DETECTION_CONTROL_REPORT.md`;
ignored diagnostic artifacts under `artifacts/p9c3/` for fixture,
semantic comparison and K/L probe JSONL.

## Risk

The lower but positive L slope suggests multiple contributors; it does not
prove a YOLO leak or full-graph boundedness. RISK-028 remains OPEN; RISK-029
alert completion retention remains separate and unchanged.

## Not Verified

Native allocation stacks, independent tracker isolation, variable-frame
inference-only behavior and eventual real full-graph plateau were not
measured in this subtask.

## Next Step

Design separately bounded variable-frame inference-only and
precomputed-track-output downstream controls at matched workloads before
any production fix. P9-C overall remains PARTIAL; P9-C.4 and P9-D/E/F
remain unauthorized.
