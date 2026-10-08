# P9-C.3f Final Lean Real Full-Graph Handover — 2026-09-27

Changed: Added `scripts/run_p9c3f_lean_full_graph.py`, `scripts/sample_p9c3f_process.py`, `scripts/validate_p9c3f_lean_full_graph.py`, `scripts/analyze_p9c3f_lean_resources.py`, `tests/test_p9c3f_lean_confirmation.py` and the [final report](../../../reports/phase-09/P9C3F_FINAL_LEAN_FULL_GRAPH_STABILITY_REPORT.md). Updated Phase 9 plan, Current Status, Changelog, Test Gates, Risk Register and the P9-C.3 aggregate report.

Reason: Resolve whether the real full MonitoringService graph shows a resource plateau when heavy diagnostics are removed. H/J previously supported an observer contribution but had not tested the real full graph's 60-minute bound.

Validation: Two-cycle real-MP4 sampler smoke passed. Formal fresh-process run completed 3602.625 s, 692 × 47 = 32,524 frames, 692 unique SQLite events and fully verified snapshots, 1,384 alerts, zero failures, clean worker/source lifecycle and sampler exit. Four Dashboard pages had zero exceptions with correct totals/evidence. Eight new quick tests and full suite 731/731 passed; compileall, preflight, demo check, pip check, diff check and exact pip freeze match passed.

Evidence: `artifacts/p9c3/p9c3f-20260927T113352Z-9a920840/` (smoke), `artifacts/p9c3/p9c3f-20260927T113427Z-442f873b/` (formal raw CSV, cycle summaries, business store, validation, analysis and Dashboard output), and the linked final report. Frozen model/config/MP4/dataset/lock hashes, HEAD/origin/main and historical release tag matched entry identity.

Risk: The lean real graph's RSS warm means increased 469.88 → 483.40 → 496.78 → 510.16 → 521.17 MiB; 30–60 slope +1.2200 MiB/min. Classified SUSPICIOUS_CONTINUED_GROWTH. P9-C.3f and P9-C overall remain PARTIAL. Alert `_completed` event-ID retention is a separate known long-horizon risk.

Not Verified: A specific retained allocation owner or indefinite production leak; TTS/RTSP in this headless run; P9-D/E/F; Phase 9 final Charter acceptance. No production repair was authorized or attempted.

Next Step: Human decision on further focused resource attribution or acceptance. P9-C.4 and P9-D/E/F remain unauthorized. Preserve all existing working-tree changes and ignored raw run artifacts.
