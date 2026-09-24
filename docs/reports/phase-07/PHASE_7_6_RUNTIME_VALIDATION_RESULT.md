# PHASE_7_6_RUNTIME_VALIDATION_RESULT

Date: 2026-09-23

Result: PASS / HUMAN REVIEW PENDING

Publication: NOT AUTHORIZED

## 1. Scope

This report records actual runtime validation for the requested Phase 7-6
targets in this order:

1. MP4 regression
2. USB Camera
3. native TTS backend
4. Streamlit browser runtime
5. RTSP runtime

The validation reused the frozen checkpoint, inference configuration,
tracking, association, compliance, persistence and monitoring boundaries. It
did not modify the model, dataset, training configuration, class mapping or
core pipeline.

## 2. Runtime Environment

| Component | Observed |
| --- | --- |
| OS | Windows 11, AMD64 |
| Python | 3.12.1 |
| PyTorch | 2.5.1+cpu |
| torchvision | 0.20.1+cpu |
| CUDA | unavailable |
| Device policy | CPU only |
| Ultralytics | 8.4.157 |
| OpenCV | 5.0.0 |
| Streamlit | 1.64.0 |
| Pandas | 3.0.6 |
| pyttsx3 | 2.99 |
| Frozen checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |

Python 3.12.1 differs from the frozen `INF-RUNTIME-001` Python 3.10.4
baseline. This remains a recorded release limitation and is not presented as
a runtime re-freeze.

## 3. Runtime Validation Order

### MP4 Regression

Status: PASS

| Field | Result |
| --- | --- |
| Input | `artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4` |
| Input SHA256 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |
| Output | 47/47 frames, 77 detections, 66 track updates, 1 association/unknown, 66 compliance findings, 1 event |
| FPS | `3.1999` processing FPS |
| Latency | `14.6882 s` pipeline processing, approximately `312.5 ms/frame`; model/setup wrapper total `19.4168 s` |
| Resources | peak RSS `433.16 MB`, `32.11%` of one CPU core over the measured process lifetime |
| Screenshot/log path | no MP4 screenshot; `artifacts/validation/P7-6/runtime_validation.json`; `artifacts/validation/P7-6/mp4_resource_validation.json`; run artifacts under `artifacts/validation/P7-6/20260923T140819Z/` |

The generated event was `EVT-0c1e8966a29042e6b7e4732dca4bd0e7`, type
`PPE_UNKNOWN`, and its snapshot/query/alert integrity checks passed.

### USB Camera

Status: PASS

| Field | Result |
| --- | --- |
| Input | USB Camera device index `0` |
| Output | 640x480 at 30 FPS; 60 frames read; clean `closed` state |
| FPS | `27.5875` read FPS |
| Latency | open `4513.71 ms`; read mean `36.24 ms`, p95 `47.06 ms`, max `280.54 ms` |
| Resources | RSS `161.70 MB`; sampled CPU `0.0%` |
| Screenshot/log path | `artifacts/validation/P7-6/usb_camera/usb_camera_frame.jpg`; `artifacts/validation/P7-6/usb_camera/usb_camera_validation.json` |
| Screenshot SHA256 | `3af8dbefaa5b7318c8955270fe6e55e47693180b48764391041324a3dd9558ea` |

The screenshot was visually inspected and contained a valid camera frame.

### Native TTS Backend

Status: PASS

| Field | Result |
| --- | --- |
| Input | `安全帽佩戴检测告警测试` through Windows SAPI |
| Output | `pyttsx3` backend returned success; no structured backend error |
| FPS | not applicable |
| Latency | `5480.51 ms` speak call |
| Resources | RSS `52.75 MB`; sampled CPU `0.0%` |
| Screenshot/log path | `artifacts/validation/P7-6/tts/tts_native_validation.json` |

This verifies the native backend call path only. Audio quality and
long-running speech behavior are not acceptance claims.

### Streamlit Browser Runtime

Status: PASS

| Field | Result |
| --- | --- |
| Input | local Streamlit app and MP4 path entered through the realtime page |
| Output | Overview, Event Explorer, Evidence Viewer and Statistics passed; browser-driven MP4 session reached `COMPLETED` |
| FPS | approximately `2.0` session FPS from 47 frames over the recorded `23 s` browser session; not a production performance claim |
| Latency | browser page-load timing was not separately instrumented |
| Resources | browser process resources were not sampled; no resource claim is made |
| Screenshot/log path | `artifacts/validation/P7-6/streamlit/home_overview_loaded.png`; `artifacts/validation/P7-6/streamlit/realtime_monitoring_mp4_completed.png`; the three JSON evidence files in `artifacts/validation/P7-6/streamlit/` |

Browser-run counters were 47 frames, 77 detections, 66 tracks, 1 event,
3 delivered alerts, 0 failed alerts and 1 unknown association. No browser
exceptions or console errors were recorded.

### RTSP Runtime

Status: PASS

| Field | Result |
| --- | --- |
| Input | `rtsp://127.0.0.1:8554/live`, MediaMTX v1.9.3, TCP transport |
| Output | 60 frames read; 1280x720 at 23.976 FPS; final state `closed`; release PASS |
| FPS | `30.3053` read FPS |
| Latency | open `1931.68 ms`; read mean `32.97 ms`, p95 `50.68 ms`, max `627.17 ms`; close `12.33 ms` |
| Resources | RSS `49.37 MB`; `1.98%` of one CPU core over the measured process lifetime |
| Screenshot/log path | `artifacts/validation/P7-6/rtsp/rtsp_frame.jpg`; `artifacts/validation/P7-6/rtsp/rtsp_validation.json`; `artifacts/validation/P7-6/rtsp/rtsp_ffprobe.json` |
| Screenshot SHA256 | `6fb484b64939de73c76ad23151ae66e47052f10724f4de581046b3acba162bd0` |

The previous failed local-listener attempt is preserved at
`artifacts/validation/P7-6/rtsp/rtsp_validation_initial_failure.json`. The
successful result uses a real local RTSP server and the project
`RTSPVideoSource` boundary.

## 4. Gate Decision

| Gate | Requirement | Result |
| --- | --- | --- |
| P7-6-G1 | TTS alert adapter implemented with cooldown and failure isolation | PASS; native backend call also executed |
| P7-6-G2 | Service-owned MP4/USB/RTSP monitoring loop implemented | PASS; MP4, USB Camera and RTSP were exercised through runtime boundaries |
| P7-6-G3 | Streamlit realtime page uses service boundaries only | PASS; all pages and the MP4 realtime path executed in a real browser |
| P7-6-G4 | Real Camera/RTSP validation design and evidence policy documented | PASS; design was executed with real USB and RTSP sources |
| P7-6-G5 | Full repository tests, compileall and diff checks pass | PASS; see section 6 |
| P7-6-G6 | Frozen model, dataset, training and upstream core modules unchanged | PASS; no core/model/dataset/training diff was introduced by this task |
| P7-6-G7 | No commit, new tag or push performed by this task | PASS |
| P7-6-G8 | Real RTSP runtime evidence recorded | PASS; local RTSP lifecycle and read/close evidence recorded |

## 5. Evidence Boundary

All runtime evidence remains below the Git-ignored
`artifacts/validation/P7-6/` tree. Media, database, browser-profile, model and
training artifacts were not added to Git.

The validation used an isolated runtime environment. No source model, dataset,
mapping or training configuration was modified.

## 6. Tests

Executed on the repository test environment:

```text
python -m pytest
python -m compileall -q .
git diff --check
```

Results:

```text
407 passed, 1 skipped
compileall: PASS
git diff --check: PASS
Charter diff: EMPTY
```

The skipped test is the existing optional Torch evaluation test; the
validation runtime is CPU-only and does not include the optional test runtime.

## 7. Known Limitations

- RTSP validation used a controlled local MediaMTX server, not a remote or
  production RTSP deployment.
- Reconnect/backoff, stale-frame detection and long-running RTSP recovery
  remain unverified.
- Browser page-load latency and browser process resource usage were not
  separately instrumented.
- Native TTS verifies backend invocation, not audio quality or long-running
  speech delivery.
- Python 3.12.1 differs from frozen `INF-RUNTIME-001` Python 3.10.4.
- M-007 annotated video rendering and M-008 final Charter acceptance remain
  pending.

## 8. Final Status

```text
Phase 7-6 runtime validation: PASS
Human review: PENDING
Training: NOT STARTED
Dataset: UNCHANGED
Frozen checkpoint: UNCHANGED
Commit: NO
Tag: NO
Push: NO
```
