# P9-C.3g Lean Interaction Matrix Handover — 2026-10-04

Changed: Added `diagnostics/p9c3g_cached_source.py`, `scripts/run_p9c3g_lean_matrix.py`, `scripts/validate_p9c3g_matrix.py`, `scripts/compare_p9c3g_smokes.py`, `scripts/analyze_p9c3g_matrix.py`, `tests/test_p9c3g_lean_matrix.py` and the [final report](../../../reports/phase-09/P9C3G_LEAN_INTERACTION_MATRIX_REPORT.md). Updated the P9-C.3 aggregate report, Phase 9 plan, Current Status, Changelog, Test Gates and Risk Register.

Reason: P9-C.3f reproduced RSS growth under lean real full-graph observation without identifying an owner. K/L/N were differently instrumented, so a unified PP/PR/RP/RR matrix was required. Historical J was not reused as PP because its discard event store and in-process diagnostic probe differ from the new formal lean harness.

Validation: Four one-cycle smokes had identical 47-frame, 77-detection, 66-track, compliance-event, SQLite, snapshot-SHA256 and two-alert signatures. Fresh 20-minute PP/PR/RP/RR controls completed 150/150/149/148 cycles; all 597 event IDs, SQLite rows and snapshot files/hashes/dimensions verified; 1,194 alerts delivered, zero failed. Eleven new quick tests and full suite 742/742 passed; compileall, preflight, demo check, pip check, diff check and exact before/after pip freeze matched.

Evidence: `artifacts/p9c3g/semantic-gate.json`, `artifacts/p9c3g/matrix-analysis.json`, and ignored per-cell roots `pp-20261003T142047Z-cb6d1b94`, `pr-20261003T144200Z-46510543`, `rp-20261003T150306Z-4e483e67`, `rr-20261003T152426Z-66c54569` under `artifacts/p9c3g/`. The linked report includes all windows, normalized contrasts and Gate decisions. Frozen model/config/MP4/fixture/dataset/lock hashes and HEAD/origin/main/Phase 8 release tag matched entry values.

Risk: 2–20-minute RSS slopes were +0.01245/+0.00156/+0.10231/+0.10512 MiB/cycle. Real inference × formal downstream is the leading supported direction. A weak positive factorial term is insufficient to assign a ByteTrack interaction or a precise byte owner. Source/decode is not required for 20-minute growth. Production unbounded leak remains NOT CONFIRMED. P9-C overall remains PARTIAL.

Not Verified: Which formal downstream stage drives the interaction, a production-owned retained object, allocator high-water versus indefinite growth, TTS/RTSP in these cached-frame controls, P9-D/E/F or Phase 9 final Charter acceptance. No production change was attempted.

Next Step: Seek separate authorization for one matched lean RP control ending after association/compliance, then narrow only the block shown necessary. P9-C.4 and P9-D/E/F remain unauthorized; preserve all existing working-tree changes and ignored raw artifacts.
