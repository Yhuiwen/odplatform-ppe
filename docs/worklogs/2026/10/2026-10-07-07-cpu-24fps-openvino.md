# 2026-10-07 — Realtime CPU 24 FPS profile

Changed: Added the 416-pixel OpenVINO monitoring profile, verified derived export, pinned dependency, export script, focused tests and benchmark diagnostics. Original 640-pixel offline profile remains available.

Reason: The user requested at least 24 processed FPS on CPU and explicitly authorized a frozen CPU configuration change.

Validation: Two corrected 570-frame production-path runs reached 28.836 and 29.414 FPS, completed without error and produced one `NO_HELMET` and one `NO_VEST` event each. Full pytest: 780 passed. `pip check` and `git diff --check` passed.

Real alert validation: A third full-video run with active Console/Web/TTS adapters reached 26.000 FPS, with the same two events, six delivered alerts and zero failures. Streamlit was restarted on port 8502; its health endpoint returned `ok`.

Evidence: `docs/reports/phase-09/P9_CPU_24FPS_REPORT.md`, `configs/inference_cpu_fast.yaml`, `diagnostics/bench_cpu_full_chain.py`, `tests/test_cpu_fast_profile.py`, ADR-025.

Risk: Smaller images can change detections on other scenes. The OpenVINO export is local and ignored by Git; new environments must regenerate it. Existing P9-C memory-growth findings are unresolved.

Not Verified: Camera/RTSP throughput, browser-rendered 24 FPS, sustained resource stability and broad-scene precision/recall.

Next Step: Review the local video result in the live UI, then perform camera/RTSP and long-run checks before broad performance claims.
