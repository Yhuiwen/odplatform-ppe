# PHASE_7_5_RUNTIME_VALIDATION_REPORT

Date: 2026-09-23

Result: COMPLETE / HUMAN REVIEW PASS

Phase 7 release: AUDIT IN PROGRESS

## 1. Scope

Phase 7-5 validates the integrated runtime path:

```text
MP4
-> VideoSource
-> YOLO11 inference
-> person-only ByteTrack
-> Person-PPE association
-> compliance/event engine
-> Phase 6 JSONL
-> SQLite
-> evidence snapshot
-> dashboard query/pages
-> Console/Web alerts
```

This validation composes existing Phase 4 through Phase 7 boundaries. It does
not modify the dataset, model, training configuration, inference logic,
tracking, association, compliance engine or Phase 6 JSONL contract.

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
| NumPy | 2.2.6 |
| Streamlit | 1.64.0 |
| Pandas | 3.0.6 |
| lap | 0.5.12 |

The validation environment was isolated from the repository. Python 3.12.1
differs from the frozen `INF-RUNTIME-001` Python 3.10.4 baseline; this is a
release limitation rather than a silent runtime re-freeze.

## 3. Frozen Identity

| Asset | Identity |
| --- | --- |
| Checkpoint | `models/checkpoints/EXP-001/best.pt` |
| Checkpoint SHA256 | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| Inference config | `configs/inference.yaml` |
| Inference config SHA256 | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| Video | Git-ignored public-domain construction MP4 from P4C-2 |
| Video SHA256 | `b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852` |
| Processed dataset `data.yaml` SHA256 | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` |
| Training config SHA256 | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` |

The checkpoint, processed dataset, training configuration and frozen inference
configuration remained unchanged.

## 4. Runtime Smoke Test

Run ID: `20260923T131111Z`

| Measurement | Result |
| --- | --- |
| Input type | MP4 |
| Frames processed | 47 / 47 |
| Frames with detections | 47 |
| Total detections | 77 |
| Classes | `person=76`, `no_vest=1` |
| Track updates | 66 |
| Association updates | 1 |
| Unknown associations | 1 |
| Compliance findings | 66 |
| Generated events | 1 |
| Persisted events | 1 |
| Verified snapshots | 1 |
| Runtime errors | 0 |
| Processing time | 19.070 seconds |
| Processing rate | approximately 2.46 FPS |
| Source final state | `closed` |

The generated event was:

```text
event_id: EVT-630ed364e15a46919e58eb5080490cd1
type: PPE_UNKNOWN
track_id: 1
frame_id: 24
source_timestamp: 1.001
confidence: 0.0
```

The original Phase 6 JSONL wire record remains exactly:

```json
{"type":"PPE_UNKNOWN","track_id":1,"confidence":0.0,"timestamp":1.001}
```

## 5. Persistence And Evidence

| Output | Result |
| --- | --- |
| Phase 6 JSONL | 1 record |
| SQLite event | 1 persisted event |
| Snapshot metadata | 1 associated event |
| Snapshot file | verified, 1 file |
| Snapshot SHA256 | `92452ae640a19bab64bca4e194612eff72143f95c00cb9a10ef2731aa6721b40` |
| Dashboard source query | `mp4:construction-workers-public-domain.mp4` |
| Snapshot integrity check | PASS |

Runtime evidence is stored only below the Git-ignored
`artifacts/validation/P7-5/` tree. The primary machine-readable evidence is
`runtime_validation.json`; the run-specific directory also contains the JSONL
event, SQLite database and snapshot file.

## 6. Dashboard Runtime Validation

The four Streamlit page sources were executed with `AppTest` against the
P7-5 SQLite database and snapshot root:

| Page | Status |
| --- | --- |
| Overview | PASS |
| Event Explorer | PASS |
| Evidence Viewer | PASS |
| Statistics | PASS |

A real local Streamlit server was also started for validation. The health
endpoint returned HTTP 200 with `ok`, and the root page returned HTTP 200 with
Streamlit HTML. The server was stopped after the check.

The only observed warning was Streamlit's deprecation notice for
`use_container_width`; it did not affect page execution.

## 7. Camera Validation

Real USB Camera device index `0` was opened:

| Operation | Result |
| --- | --- |
| Open | PASS |
| Metadata | 640x480, 30 FPS |
| First read | PASS |
| Close | PASS |
| Final state | `closed` |

A deterministic injected capture also verified that a disconnect produces the
observable `SOURCE_DISCONNECTED` state and that `close()` releases the capture.

No real RTSP endpoint was opened. RTSP remains covered by adapter-level tests
only and is not claimed as runtime-validated.

## 8. Alert Validation

| Adapter | Runtime result |
| --- | --- |
| ConsoleAlertAdapter | 1 delivered record |
| WebAlertAdapter | 1 delivered in-process publication |

Both deliveries preserved the Phase 6 `event_id`
`EVT-630ed364e15a46919e58eb5080490cd1`. The Web adapter is an in-process
publication boundary, not an external network notification service. TTS is
not implemented or validated in this subphase.

## 9. Test Cases

The Phase 7-5 smoke evidence covers:

- MP4 source open, ordered read and close.
- Real CPU YOLO11 checkpoint loading and frame inference.
- Person-only tracking input.
- Conservative association and explicit unknown output.
- Compliance finding generation without single-frame forced output.
- Phase 6 event generation and JSONL compatibility.
- SQLite idempotent ingestion and restart-persistent query projection.
- Snapshot capture, file association and integrity verification.
- Dashboard queries, filtering, evidence access and statistics.
- Console and in-process Web alert delivery.
- USB Camera open/read/close and observable injected disconnect handling.

## 10. Known Limitations

- Python 3.12.1 differs from the frozen `INF-RUNTIME-001` Python 3.10.4.
- Real RTSP was not tested; only MP4 and real USB Camera input were exercised.
- Reconnect/backoff orchestration and stale-frame detection remain incomplete.
- TTS remains unimplemented; Console and in-process Web alerts are the only
  validated V1 adapters in this run.
- M-007 annotated video rendering remains pending.
- M-008 final Camera/RTSP acceptance remains pending because RTSP runtime and
  production monitoring behavior were not validated.
- The dashboard validation used a short MP4 smoke run with one event, so it
  does not establish large-history performance, retention behavior or
  long-running stability.
- The Ubuntu/domain boundary was not changed; the validation host is Windows.

## 11. Release Checklist

| Check | Status |
| --- | --- |
| Frozen checkpoint identity verified | PASS |
| Dataset identity unchanged | PASS |
| Training configuration unchanged | PASS |
| Inference configuration unchanged | PASS |
| MP4-to-event-to-SQLite-to-snapshot closed loop verified | PASS |
| Dashboard pages executed against runtime evidence | PASS |
| Real USB Camera lifecycle verified | PASS |
| Console and Web alert adapters verified | PASS |
| Real RTSP runtime verified | NOT RUN |
| TTS implemented and verified | NOT IMPLEMENTED |
| M-007 annotated rendering accepted | PENDING |
| M-008 final acceptance | PENDING |
| Full repository tests | PASS: `390 passed, 1 skipped` |
| compileall and diff checks | PASS |
| Charter diff | PASS, empty |
| Commit, push or tag | NO |

## 12. Final Decision

Phase 7-5 runtime integration is `COMPLETE / HUMAN REVIEW PASS`.

The runtime evidence supports the implemented offline/input-adapter path and
the dashboard/alert boundaries for the tested MP4 and USB Camera cases. It
does not complete the locked Phase 7 goal because TTS, real RTSP validation,
annotated rendering and M-008 acceptance remain outstanding.

Phase 7 publication remains:

```text
AUDIT COMPLETE FOR HUMAN REVIEW / NOT PUBLISHED
```

No commit, push or tag was created.
