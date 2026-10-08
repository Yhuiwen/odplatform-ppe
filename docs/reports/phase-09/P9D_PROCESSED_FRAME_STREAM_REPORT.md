# P9-D processed-frame live preview — 2026-10-07

## Goal

Display the actual processed detection frame as soon as the monitoring worker completes it, without tying later preview throughput improvements to the Streamlit status refresh interval.

## Implementation

- `MonitoringService._process_frame` completes inference, tracking, association, compliance, event persistence, evidence and alerts before rendering the latest preview. The existing `AnnotatedFrameRenderer` draws frozen-class bounding boxes and labels on a copy. Snapshot capture continues to use the source frame.
- A display exception falls back to the source image and never cancels confirmed events. A preview transport exception also does not interrupt the event pipeline.
- `PreviewChannel` encodes the newest BGR image as JPEG and retains only that image. A per-process HTTP listener bound to `127.0.0.1` streams `multipart/x-mixed-replace` to a high-entropy, session-specific URL. Slow clients see the latest frame; no unbounded frame queue is created. The connection sends its current image periodically so closed clients can be released.
- The page mounts one static `<img>` outside the 0.3-second Streamlit statistics/event fragment. The browser receives frame updates on the same HTTP connection without rerendering that element. The stats and event list still use the existing fragment cadence.

The design follows the documented Streamlit [fragment execution model](https://docs.streamlit.io/develop/concepts/architecture/fragments). No model, inference configuration, temporal rule, event schema or third-party source code was changed.

## Verification

- `pytest -q tests/unit/test_monitoring_preview.py tests/integration/test_monitoring_service.py tests/e2e/test_p9d_pages.py tests/e2e/test_full_ppe_pipeline.py tests/unit/test_annotated_demo_video.py`: **26 passed** in the frozen demo environment.
- The stream test read two different JPEGs from one HTTP response and confirmed an invalid token returns 404. AppTest confirmed the page emits the session-specific preview image URL.
- An isolated real-MP4 run of `build_monitoring_runtime` completed all 47 frames with 77 detections. The last preview frame differed from the source frame (absolute pixel difference sum 3,863,910), confirming that annotations were present. The run used a temporary validation root and a no-op alert dispatcher.
- `compileall` succeeded for the changed service and Web modules.
- Documentation governance tests: **31 passed**. The restarted Streamlit server returned HTTP 200 `ok` from `/_stcore/health`.

## Limits and gate

The browser control interface was unavailable during this turn, so live playback was not visually confirmed in the browser. The preview server binds to loopback; access from a different machine is not verified and may require a same-origin transport later. The new JPEG encoding and rendering add some per-frame work; no new throughput gain is claimed. The targeted code/protocol gate is **PASS**, while browser visual acceptance and overall P9-D/P9-C remain open.
