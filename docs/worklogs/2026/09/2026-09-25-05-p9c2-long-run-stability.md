# P9-C.2 Long-Run Stability — 2026-09-25

## Changed

Added optional bounded JSONL diagnostics, isolated USB/MP4 long-run and post-run analyzers, a synthetic observer cap test, Phase 9 reports and current governance updates. Production code, runtime lock, model and dataset were unchanged.

## Reason

P9-C.1 diagnostics retained per-frame records, preventing a reliable long-run process-memory conclusion. P9-C.2 was authorized to remeasure with a bounded observer and check 60-minute lifecycle and correctness.

## Validation and evidence

USB main cycle ran 60 minutes and processed 31,965 frames; 40-second restart added 394. Fifteen events, snapshots and SQLite rows were consistent; 30 alerts delivered. Warm Stop and restart Stop returned in 375 and 335 ms. MP4 completed 675 × 47 = 31,725 frames; 675 events/evidence rows/files and 1,350 alerts were consistent. Post-run four-page Dashboard smoke passed for both databases. Five-second resource samples and complete source-cycle/timeline JSONL reside in ignored `artifacts/p9c2/` runs; report: `docs/reports/phase-09/P9C2_LONG_RUN_STABILITY_REPORT.md`.

## Risk and unverified

USB warm RSS reached a plateau (+0.0484 MiB/min); MP4 warm RSS rose monotonically (+1.2478 MiB/min). The owner is unverified. Long-run TTS, RTSP, browser visual interaction and indefinite memory behavior were not tested. P9-C.2 PARTIAL; P9-C.3 attribution required. P9-D/E/F remain unauthorized.

## Next step

Analyze Python and native memory separately under controlled repeated-source and event-producing scenarios without changing the frozen production behavior. Review the P9-C.2 reports and regression evidence before authorizing P9-C.3.
