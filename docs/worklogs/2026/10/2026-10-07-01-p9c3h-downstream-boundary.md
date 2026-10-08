# P9-C.3h Downstream Boundary Handover — 2026-10-07

Changed: Added `scripts/run_p9c3h_boundaries.py`, `scripts/analyze_p9c3h_boundaries.py`, `scripts/validate_p9c3h_boundaries.py`, `tests/test_p9c3h_boundaries.py` and the [P9-C.3h report](../../../reports/phase-09/P9C3H_INFERENCE_DOWNSTREAM_BOUNDARY_REPORT.md). Updated the P9-C.3 aggregate report, Phase 9 plan, Current Status, Changelog, Test Gates and Risk Register.

Reason: P9-C.3g associated RSS growth with real inference in a full downstream graph but did not identify the first necessary boundary. P9-C.3h staged H0/H1/H2 with the same real inference, precomputed Track, cached source, MonitoringService lifecycle, pacing and external sampler, then compared fresh H0 with full RP.

Validation: H0/H1/H2 one-cycle semantics passed. Fresh 10-minute screens completed 72/68/69 correct cycles with +0.10190/+0.10508/+0.10653 MiB/cycle. Fresh 20-minute H0/RP completed 142/150 cycles with +0.10318/+0.10255 MiB/cycle; RP had 150 JSON events, SQLite rows and snapshots plus 300 delivered alerts, zero failed. Post-run integrity checks, 13 new quick tests and full suite 755/755 passed. `compileall`, preflight, demo check, pip check, diff check and before/after pip-freeze byte comparison passed.

Evidence: `artifacts/p9c3h/` contains the smoke roots `h0-20261007T011246Z-a14138c0`, `h1-20261007T011327Z-17366d59`, `h2-20261007T011327Z-b3f111cf`; 10-minute roots `h0-20261007T011356Z-85418e5c`, `h1-20261007T012427Z-204797de`, `h2-20261007T013519Z-ce671445`; and 20-minute roots `h0-20261007T014609Z-b1012447`, `rp-20261007T020647Z-7ad12953`. Per-root `outputs/summary.json`, `validation.json`, `resource-analysis.json`, `cycles.jsonl` and `resources/external.csv` are retained. Frozen model/config/MP4/fixture/dataset/lock hashes and Git release identity matched entry values.

Risk: H0 alone reproduced RP-scale continuing growth. No material positive business-downstream increment was found; P9-C.3g's narrower causal phrase is superseded while its matrix measurements remain historical. A production-owned retained object, native allocator behavior, indefinite leak and 60-minute bound are unproven. P9-C overall remains PARTIAL.

Not Verified: Which object or native allocation retains resources in the real-inference/MonitoringService frame/session context; standalone YOLO defect; TTS/RTSP and complex-scene behavior under these controls; Phase 9 final Charter acceptance. No production repair was attempted.

Next Step: Seek separate authorization for a wiring-matched H0 inference-output/session-lifecycle attribution experiment. P9-C.4 and P9-D/E/F remain unauthorized. Preserve working-tree changes and raw artifacts.
