# 2026-10-07 processed-frame stream handover

- **Changed:** MonitoringService can render a completed frame and publish it to a bounded latest-frame sink. Added a session-tokenized loopback MJPEG channel and moved the page preview outside the Streamlit statistics/event fragment.
- **Reason:** The previous page showed an unannotated frame and its 0.3-second rerun interval limited visible updates even if the worker produced more frames.
- **Validation:** 26 focused tests and 31 documentation governance tests passed; an isolated real 47-frame MP4 run processed 47 frames and 77 detections; the rendered final image differed from the raw frame. `compileall` and restarted-server health check passed.
- **Evidence:** `tests/unit/test_monitoring_preview.py`, `tests/integration/test_monitoring_service.py`, `tests/e2e/test_p9d_pages.py`, and `docs/reports/phase-09/P9D_PROCESSED_FRAME_STREAM_REPORT.md`.
- **Risk:** JPEG encoding/rendering adds per-frame CPU work. The local loopback endpoint uses one daemon HTTP listener and a latest-frame buffer per active session; remote-browser use has not been verified.
- **Not Verified:** Continuous playback in the in-app browser, because its control interface was unavailable. Long-run stream-client resource behavior was not remeasured.
- **Next Step:** Repeat the short-MP4 browser visual check when browser control is available, then measure preview encoding overhead and long-run connection lifecycle before P9-C closure.
