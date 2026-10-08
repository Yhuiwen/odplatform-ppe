# Phase 9 — Realtime CPU 24 FPS optimization

Date: 2026-10-07. Decision: **targeted MP4 speed gate PASS**; P9-C overall remains PARTIAL.

## Configuration and method

Machine: Intel Core i5-1340P, Windows, CPU-only `.venv-final-demo`; OpenVINO 2025.2.0, Ultralytics 8.4.157 and PyTorch 2.5.1+cpu. Source: `artifacts/validation/test/4afa6b121fe5db806c3ff416bafdf571.mp4`, 570 frames, 1280×720, source rate 30 FPS. Runtime profile: `configs/inference_cpu_fast.yaml`, 416-pixel export of frozen `models/checkpoints/EXP-001/best.pt`, four CPU threads, one OpenCV thread. The exporter and three output hashes are recorded in the profile and ADR-025.

`diagnostics/bench_cpu_full_chain.py --production` warms the detector and times the 570-frame monitoring service with video decode, inference, ByteTrack, association, compliance/event confirmation, SQLite/snapshot persistence and annotated JPEG preview. An alert dispatcher stub isolates the video processing time. Results are processed frames divided by wall-clock time; they are not the source video FPS or browser display cadence. The diagnostic script inserts the repository root into `sys.path` to avoid importing an older installed package.

The `--real-alerts` variant also keeps the configured Console, Web and TTS adapters active.

| Run | Time | Processed FPS | Detections | Events | State |
| --- | ---: | ---: | ---: | --- | --- |
| OpenVINO 416 with per-frame source hash | 24.589 s | 23.181 | 1774 | NO_HELMET 1, NO_VEST 1 | completed |
| Final production profile 1 | 19.767 s | 28.836 | 1774 | NO_HELMET 1, NO_VEST 1 | completed |
| Final production profile 2 | 19.379 s | 29.414 | 1774 | NO_HELMET 1, NO_VEST 1 | completed |
| Final production profile, real alerts | 21.923 s | 26.000 | 1774 | NO_HELMET 1, NO_VEST 1 | completed; 6 delivered, 0 failed |

The first apparent production run at 10.8 FPS used an older installed `web` module because the diagnostic entry point did not place the checkout first on `sys.path`; it is excluded from the final comparison. A direct PyTorch 320-pixel full-chain run reached 17.041 FPS and lost the helmet event, so it was rejected.

## Verification and limits

Targeted detector/monitoring tests: 15 passed. New profile and integrity tests: 3 passed. Full repository suite: 780 passed. `pip check` and `git diff --check` passed. The generated export is ignored by Git; another machine must install the pinned OpenVINO dependency and run `scripts/export_cpu_openvino.py` once. The Streamlit service was restarted on port 8502 and its health endpoint returned `ok`. No camera/RTSP throughput or browser-rendering 24 FPS claim is made. Broad-scene accuracy and long-run memory stability remain unverified; the prior P9-C resource gate remains PARTIAL.
