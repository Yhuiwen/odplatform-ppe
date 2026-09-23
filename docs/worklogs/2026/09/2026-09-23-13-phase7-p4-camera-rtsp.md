# Worklog: Phase 7-4 Camera / RTSP Input

Date: 2026-09-23

## Objective

Implement a unified `VideoSource` input layer for MP4, USB Camera and RTSP
without changing the frozen inference, tracking, association, compliance or
Phase 6 wire contracts.

## Changes

- Added source metadata/status schemas and the shared lifecycle protocol.
- Added MP4, USB Camera and RTSP adapters with explicit failure handling and
  release cleanup.
- Redacted RTSP credentials and query strings from observable status/errors.
- Added lifecycle, mock source and invalid-input tests.
- Added a static boundary test preventing direct `cv2.VideoCapture` calls from
  business, dashboard and script layers.

## Validation

```text
python -m pytest
390 passed, 1 skipped

python -m compileall .
PASS

git diff --check
PASS

git diff HEAD -- docs/00_PROJECT_CHARTER.md
EMPTY
```

The skipped test is the existing optional Torch evaluation test.

## Boundary Statement

No model, dataset, mapping, training, inference, tracking, association,
compliance-engine or Phase 6 JSONL contract file was modified. No real USB
Camera or RTSP stream was opened. No commit, push or tag was created.

## Handover

Phase 7-4 is `COMPLETE FOR HUMAN REVIEW`. Real-device/stream validation,
reconnect orchestration, monitoring integration, annotated rendering and
M-008 acceptance remain pending.

Next allowed step:

```text
WAIT FOR PHASE 7-4 HUMAN REVIEW
```
