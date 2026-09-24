# PHASE_7_6_RUNTIME_VALIDATION_REPORT

Date: 2026-09-23

Result: FINALIZATION CANDIDATE / HUMAN REVIEW PENDING

Base Phase 7 release: RELEASED

## 1. Scope

This report records the Phase 7 release-finalization work requested after the
base release tag existed:

- audit the current Phase 7 implementation and documentation state;
- implement the TTS alert adapter;
- expose a service-owned realtime monitoring loop through Streamlit;
- define real Camera or RTSP runtime validation;
- add focused tests and gates without modifying Detection, Tracking,
  Association or Compliance implementations.

The frozen model, dataset, `best.pt`, training configuration and Phase 5/6
contracts remain unchanged.

## 2. Release Baseline

| Item | Value |
| --- | --- |
| Branch | `main` |
| Base release commit | `a30b73c080c18d010fbaa08642868e86acb68022` |
| Base release tag | `phase-7-web-alert-platform-complete` |
| Tag object | `d97c8249c756dec33a9bb149bf837871b59b3503` |
| Remote `origin/main` | `a30b73c080c18d010fbaa08642868e86acb68022` |
| Finalization change set | uncommitted, human review pending |

The existing tag and remote state are historical facts and were not changed
by this task.

## 3. Pre-Read And Conflict Check

The root `AGENTS.md` is authoritative. `docs/AGENTS.md` does not exist. The
requested Phase 7 status files were read together with the phase document,
test gates, target architecture and latest Phase 7 reports.

The repository contained documentation drift: the Phase 7 tag and remote
publication already existed while several status documents still said
"not published." This is a status synchronization issue, not a conflict with
the locked Phase 7 goal. The locked goal remains:

```text
SQLite + Snapshot + TTS + Streamlit
```

No requirement, MUST definition or phase goal was changed.

## 4. Implementation Summary

### 4.1 TTS Alert Adapter

Added:

- `infra/tts/tts_service.py`
- `infra/alerts/tts.py`
- exports from `infra/tts/__init__.py` and `infra/alerts/__init__.py`

Behavior:

- lazy optional `pyttsx3` backend;
- injectable speaker for tests and non-native delivery;
- stable `TTS_UNAVAILABLE` and `TTS_BACKEND_FAILED` error codes;
- event-id idempotency through the existing alert base contract;
- per `(track_id, event_type)` cooldown;
- backend failure is returned as a structured failed alert and does not
  escape into the event-ingest path.

The governance host does not have `pyttsx3` installed, so native audio output
was not executed. The adapter and failure isolation are verified with an
injected speaker.

### 4.2 Service-Owned Monitoring

Added:

- `services/monitoring_service.py`
- `web/monitoring_support.py`
- `web/pages/1_实时监控.py`
- `configs/monitoring.yaml`

The service owns one background worker and exposes an immutable serializable
status projection. It reuses the existing source, inference, tracking,
association, compliance, event, ingest, snapshot and alert boundaries.
Streamlit starts and stops the service but does not own the processing loop.

The page provides:

- MP4, USB Camera and RTSP source selection;
- start and stop controls;
- periodic status refresh;
- frame, detection, track, event and alert counters;
- latest processed-frame preview;
- recent-event and alert-result display.

The page source does not call `cv2.VideoCapture`, `YOLODetector`,
`InferenceService`, `ComplianceEngine` or `EventEngine` directly.

### 4.3 Persistence And Alert Ordering

The monitoring loop follows the frozen order:

```text
source frame
-> inference
-> person-only tracking
-> Person-PPE association
-> compliance
-> Phase 6 event creation and JSONL
-> SQLite ingest
-> snapshot evidence
-> alert fan-out
```

The monitoring service reloads the persisted event through an injected
`event_loader` before alert dispatch. This preserves the snapshot reference
without assuming a concrete repository inside the service.

## 5. Real Camera Or RTSP Validation Design

Validation configuration:

```text
configs/p7_6_validation.yaml
```

The config is `execution_enabled: false`. It records the frozen checkpoint
identity, CPU-only policy, accepted live source kinds, bounded frame count,
timeouts and evidence output path.

### 5.1 Execution Preconditions

Real validation may run only after an explicit human authorization that:

1. selects `usb_camera` or `rtsp`;
2. supplies the authorized device index or RTSP endpoint outside Git;
3. confirms the source is allowed for the validation environment;
4. confirms the frozen `best.pt` SHA256 matches
   `configs/inference.yaml`;
5. explicitly changes a validation-only copy or command flag from disabled
   to enabled.

The frozen application configuration is not changed.

### 5.2 Evidence Procedure

For the authorized source:

1. record the runtime fingerprint, OS, Python, OpenCV and GPU/CPU policy;
2. record the source kind and redacted source identity;
3. open the source and record metadata and status;
4. read a bounded number of sequential frames;
5. record frame IDs, timestamps, read latency and source state;
6. exercise the service start, status and stop lifecycle;
7. confirm event, SQLite, snapshot and alert identity when an event occurs;
8. close the source and record final source state and release result;
9. write JSON evidence below the Git-ignored
   `artifacts/validation/P7-6/` tree.

### 5.3 Failure Handling

The validation must fail closed:

- no synthetic frame on disconnect;
- no silent RTSP reconnect or fallback to local video;
- no successful status when source open or read fails;
- no alert dispatch before persistence and snapshot association;
- credential and query strings must be absent from source status and errors;
- a failed source must still release its capture.

### 5.4 Validation Status

| Check | Status |
| --- | --- |
| USB Camera adapter lifecycle unit/integration tests | PASS |
| RTSP adapter lifecycle, redaction and timeout tests | PASS |
| Real USB Camera lifecycle from Phase 7-5 | PASS |
| Real RTSP runtime | NOT RUN |
| P7-6 real source evidence | NOT RUN / WAITING FOR HUMAN AUTHORIZATION |

The P7-6 design is complete. Real RTSP is not claimed as validated, and
M-008 final acceptance remains pending.

## 6. Tests

Executed:

```text
python -m pytest -q
python -m compileall .
git diff --check
```

Result:

```text
407 passed, 1 skipped
```

The skipped test is the existing optional Torch evaluation test because the
governance host does not have Torch installed.

Added or updated coverage includes:

- TTS successful delivery, duplicate suppression, cooldown and failure
  isolation;
- monitoring start, ordered frames, completion, source failure and release;
- SQLite event ingestion followed by snapshot association before alert
  delivery;
- page/service import boundaries;
- monitoring and P7-6 configuration integrity;
- frozen checkpoint identity in the validation config.

Streamlit and `pyttsx3` are not installed on this host. The page source and
boundary tests pass, but this finalization task did not execute a browser
render or native audio output.

## 7. Gate Decision

| Gate | Requirement | Status |
| --- | --- | --- |
| P7-6-G1 | TTS adapter implemented with cooldown and failure isolation | PASS |
| P7-6-G2 | Service-owned MP4/USB/RTSP monitoring loop implemented | PASS |
| P7-6-G3 | Streamlit realtime page uses service boundaries only | PASS |
| P7-6-G4 | Real Camera/RTSP validation design and evidence policy documented | PASS |
| P7-6-G5 | Full repository test gate passes | PASS |
| P7-6-G6 | No frozen model, dataset, training asset or upstream core module changed | PASS |
| P7-6-G7 | No commit, new tag or push performed by this task | PASS |
| P7-6-G8 | Real RTSP runtime evidence recorded | NOT RUN |

## 8. Limitations

- Native TTS audio was not executed because `pyttsx3` is not installed.
- Streamlit browser runtime was not executed in this task because Streamlit
  is not installed on the governance host.
- Real RTSP was not opened; only adapter-level tests and the earlier real USB
  Camera lifecycle are available.
- Reconnect/backoff, stale-frame detection and long-running session recovery
  remain pending.
- Annotated video rendering and M-007/M-008 final acceptance remain pending.
- The uncommitted finalization change set requires human review before any
  commit or publication action.

## 9. Final Status

```text
Phase 7 base release: RELEASED
Phase 7-6 finalization: FINALIZATION CANDIDATE / HUMAN REVIEW PENDING
Real RTSP validation: NOT RUN
Commit: NO
New tag: NO
Push: NO
```
