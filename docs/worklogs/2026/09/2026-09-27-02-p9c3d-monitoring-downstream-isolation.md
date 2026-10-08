# P9-C.3d Monitoring Lifecycle and Downstream Isolation — 2026-09-27

## Changed

Added diagnostic-only S0–S4 stage adapters, a formal MonitoringService
driver, analysis script, nine quick tests and the P9-C.3d attribution
report. Updated the aggregate report and current phase, status,
changelog, gate and risk records. Added one `.gitignore` entry for
the required `artifacts/p9c3d/` diagnostic evidence directory.
Production services, model,
configuration and frozen dependencies were unchanged.

## Reason

Historical N's +0.0238 MiB/cycle included repeated MonitoringService
lifecycle and downstream processing. The prior tracker-only P/Q/R
controls did not explain the L−N directional difference.

## Validation

S0 completed 150 formal cycles/7050 cached real frames in 20 minutes
with balanced worker and source lifecycle and +0.000344 MiB/cycle warm
RSS. S1–S4 ran separately for 75 cycles each, yielding warm RSS
−0.00302, +0.000827, +0.00197 and +0.00464 MiB/cycle. S2 confirmed
75 temporal events, S3 persisted 75 SQLite rows, and S4 persisted
75 rows and JPEGs with 150 delivered alerts. No material first
downstream divergence reproduced N. Conditional matched stage and
tracker pairs were not triggered. Nine focused tests and full
715-test suite passed; compileall, preflight, demo check, pip check,
diff check and frozen identity checks passed.

## Evidence

`docs/reports/phase-09/P9C3D_DOWNSTREAM_INTERACTION_ATTRIBUTION_REPORT.md`;
ignored stage probes, analyses and snapshots under `artifacts/p9c3d/`.

## Risk

S4's lean harness differs from historical N's observed/recorded
pipeline, JSONL event storage and rolling logs. N residual and the
separate tracker × downstream interaction remain unresolved. P9-C
overall stays PARTIAL and RISK-028 stays OPEN.

## Not Verified

No first material stage owner, N-harness equivalence, tracker
interaction, native allocation stack or production full-graph
boundedness was established. An unbounded production leak is not
confirmed. P9-C.4 and P9-D/E/F remain unauthorized.

## Next Step

Only with separate authorization, run one 20-minute N-harness bridge
control with the frozen fixtures and observer/recorder/JSONL/log wiring;
add a matched 20-minute lean S4 control only if late-window variance
requires it. Do not begin production changes from this attribution.
