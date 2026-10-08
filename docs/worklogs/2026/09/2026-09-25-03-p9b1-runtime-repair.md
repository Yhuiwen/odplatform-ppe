# P9-B.1 Runtime Drift Repair Handover — 2026-09-25

Changed: Revised the unpublished `FINAL-DEMO-RUNTIME-001` lock and root requirements with `lap==0.5.13`; strengthened preflight and tests; added deterministic full-service E2E and 30-second temporal test; made Event Explorer fail closed on invalid Track ID. Added isolated P9-B.1 validation reports and synchronized Phase 9 status.

Reason: Ultralytics 8.4.157 lazily installs `lap` when ByteTrack matching is first imported, causing package drift after the original final-demo freeze. P9-B also lacked default E2E, duplicate, Camera and recovery/cooldown evidence.

Validation: Independent Python 3.12.1 clean installation, `pip check` and enhanced preflight PASS; real 47-frame MP4 full chain repeated with unchanged before/after package inventory; real 30-second USB full chain processed 143 frames and produced NO_HELMET/NO_VEST events; invalid camera index failed with zero fabricated frames. Clean default pytest: 681 passed. Compileall and demo preflight passed.

Evidence: `artifacts/p9b/p9b1-clean-install.log`, `p9b1-clean-mp4.log`, before/after freeze and inventory files, runs `20260925T093935Z-c9530763` and `20260925T094052Z-24a066b4`, `docs/reports/phase-09/P9B_RUNTIME_DRIFT_REPAIR_REPORT.md`, `P9B_USB_FULL_CHAIN_REPORT.md` and updated `P9B_FULL_CHAIN_VALIDATION_REPORT.md`.

Risk: Short cold-start USB stop calls can report `MONITORING_STOP_TIMEOUT` before the worker eventually stops. Controlled crossing, occlusion, re-entry and ambiguous PPE scenes remain unvalidated. Actual live Streamlit display was not visually reviewed. A sustained construction-site violation MP4 is unavailable.

Not Verified: P9-C, full Phase 9 Charter Gate, remote RTSP reliability, physical camera unplug, long-run performance and all complex real tracking/association scenes.

Next Step: Human review of P9-B.1 evidence and the remaining G8/G10 gaps. P9-B remains PARTIAL; P9-C is not ready. No commit, tag, push or history rewrite was performed.
