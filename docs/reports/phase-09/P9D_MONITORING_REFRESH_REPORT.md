# P9-D realtime monitoring refresh report — 2026-10-07

## Scope and decision

The user requested a smoother realtime monitoring picture and allowed consulting the course-provided `odplatform.zip` and open-source projects. The course archive was read as a reference without copying code; its identity and usage boundary are recorded as REF-003 in `docs/09_REFERENCE_ASSETS.md`. Official Streamlit fragment and Ultralytics prediction documentation were also reviewed. The chosen change keeps the frozen sequential analysis path and makes Streamlit request a new preview more often.

## Measurement and change

On this Windows host (16 logical CPU cores, CPU-only frozen YOLO runtime), the supplied 1280×720, 30 FPS, 570-frame MP4 delivered approximately 7.3 FPS in a warm direct-inference sample. Frame reads took about 4 ms and inference about 137 ms per frame on average. The checkpoint SHA-256 check alone cost about 14.7 ms per frame; it was left in place to preserve the frozen integrity behavior. The old UI fragment updated once per second, limiting visible changes to 1 FPS even when the pipeline produced more frames.

`web/pages/1_实时监控.py` now uses `run_every=0.3`, giving a maximum preview refresh cadence of approximately 3.3 FPS, and avoids redundant full-page `st.rerun()` calls after start and stop. It still displays the latest frame from the same `MonitoringService` status. No frame skipping, model, image size, tracker, event, snapshot, alert, schema or monitoring configuration changed. This improves visible continuity but does not raise the measured CPU inference throughput or match a 30 FPS source in real time.

## Verification

- Fresh Streamlit process on localhost:8502; browser started `artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4`.
- During processing, the UI displayed an image while showing frame 23 and 24; the run completed at frame 46 with 47 frames processed and one confirmed PPE_UNKNOWN event.
- Focused command: `.venv-final-demo/Scripts/python.exe -m pytest -q tests/e2e/test_p9d_pages.py tests/integration/test_monitoring_service.py tests/test_image_inference.py` → **22 passed**.
- Reference and documentation command: `.venv-final-demo/Scripts/python.exe -m pytest -q tests/unit/test_reference_assets.py tests/unit/test_documentation_governance.py` → **38 passed**.
- A hot-reloaded browser session previously produced a stale `MonitoringRuntime` class-instance error after code edits; a clean server restart cleared it. The final browser smoke used the clean process.

## Status and limits

This targeted display-cadence improvement is implemented and smoke-tested. P9-D overall still awaits its broader UI review. P9-C resource-growth attribution remains PARTIAL; the fixed CPU inference policy is the dominant limit for source-rate playback. Further throughput work requires a separate measured design that preserves event temporal evidence and long-run resource bounds.
