# PHASE_7_4_CAMERA_RTSP_REPORT

Date: 2026-09-23

Result: COMPLETE FOR HUMAN REVIEW

## 1. Scope

Phase 7-4 implements the unified `VideoSource` input layer for MP4, USB
Camera and RTSP. The adapters expose source metadata and lifecycle status,
handle open/read failures explicitly and release resources on close.

This slice does not modify the model, dataset, training, inference logic,
tracking, association, compliance engine or Phase 6 JSONL contract. It does
not open a real camera or RTSP stream during validation and does not claim
M-008 acceptance.

## 2. Changed Files

Contracts:

- `core/schemas/video.py`
- `core/video/video_source.py`

Adapters:

- `core/video/mp4_source.py`
- `core/video/usb_camera_source.py`
- `core/video/rtsp_source.py`
- `core/video/__init__.py`

Tests:

- `tests/unit/test_video_source.py`
- `tests/test_video_schema.py`
- `tests/unit/test_imports.py`
- `tests/unit/test_structure.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/08_RISK_REGISTER.md`
- `docs/phases/PHASE_07_WEB_ALERTS.md`
- `docs/reports/phase-07/PHASE_7_4_CAMERA_RTSP_REPORT.md`
- `docs/worklogs/2026/09/2026-09-23-13-phase7-p4-camera-rtsp.md`

## 3. VideoSource Contract

`VideoSource` defines one lifecycle:

```text
open() -> SourceMetadata
read() -> FrameData | None
status() -> SourceStatus
close() -> None
```

Shared state vocabulary:

```text
idle | opening | live | degraded | ended | failed | closed
```

`SourceStatus` records the last frame ID/time, stable error code/message and
reconnect count. Failed or degraded states require an error code.

## 4. Adapters

`MP4VideoSource` delegates to the existing sequential `VideoReader`, so the
released MP4 decoding path is reused rather than duplicated. It returns
ordered `FrameData` values and returns `None` at EOF.

`USBCameraSource` accepts a non-negative device index, owns capture creation
and release, derives optional width/height/FPS metadata and raises
`SOURCE_OPEN_FAILED` or `SOURCE_DISCONNECTED` with an observable failed
status.

`RTSPVideoSource` accepts only `rtsp://` or `rtsps://`, applies open/read
timeout properties, rejects invalid URIs and redacts credentials and query
strings from status, errors and metadata. A stream that stops returning
frames fails with `SOURCE_DISCONNECTED`.

## 5. Boundary Enforcement

`cv2.VideoCapture` is confined to the video source modules. A static test
scans `services/`, `web/`, `scripts/` and non-video `core/` modules and fails
if a direct capture call appears.

No synthetic frame or fallback source is created. Invalid input and
connection failure remain observable.

## 6. Tests

Commands:

```text
python -m pytest
python -m compileall .
git diff --check
git diff HEAD -- docs/00_PROJECT_CHARTER.md
```

Results:

- `python -m pytest`: `390 passed, 1 skipped`.
- `python -m compileall .`: PASS.
- `git diff --check`: PASS.
- Charter diff: PASS, empty.
- Skip: the existing optional Torch evaluation test because Torch is not
  installed on this governance host.

Coverage includes mock protocol implementation, MP4 order/EOF/release, USB
open/read/disconnect/release, RTSP redaction/timeout/read, invalid source
input, idempotent release and the direct-capture boundary.

## 7. Limitations

- No real USB Camera or RTSP endpoint was opened; validation used injected
  capture doubles.
- Reconnect/backoff orchestration and stale-frame detection remain pending.
- The existing offline `VideoInferenceService` still uses `VideoReader`
  directly. Monitoring-service integration with `VideoSource` belongs to the
  next subphase and was intentionally not changed here.
- M-008 Camera/RTSP acceptance remains `待实现`.
- Annotated video rendering, TTS and runtime acceptance remain pending.

## 8. Final Decision

Phase 7-4 is `COMPLETE FOR HUMAN REVIEW`.

Next allowed step:

```text
WAIT FOR PHASE 7-4 HUMAN REVIEW
```

Commit, push and tag: `NO`.
