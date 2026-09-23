# P5-1 ByteTrack Adapter Implementation Report

Status: COMPLETE FOR HUMAN REVIEW

## Scope

Phase 5-1 implements the person-only tracking leg:

```text
DetectionResult
-> PersonTrackingAdapter
-> ByteTrack backend
-> TrackResult
```

The implementation does not change `DetectionResult`, load the release
checkpoint, execute inference, modify the dataset, change the frozen mapping,
run Person-PPE association, or begin Phase 5-2.

## Implementation Architecture

- `core/tracking/bytetrack_adapter.py` provides
  `ByteTrackPersonTrackingAdapter`.
- `core/tracking/tracker.py` exposes the compatibility name `PersonTracker`
  bound to that adapter.
- The adapter accepts only project-owned `DetectionResult` values with
  `class_id=0` and `class_name=person`.
- Non-person detections are rejected before the backend receives the frame.
- Detections below the frozen `0.25` person-confidence threshold are removed
  before the backend update.
- Empty frames still call the backend so tracker state advances.
- Backend matches are converted to project-owned `TrackResult` values.
- Ultralytics `Results` objects, tracker rows and backend IDs do not cross the
  adapter boundary.

The real backend is lazy and private:

```text
ByteTrackPersonTrackingAdapter
-> optional injected test backend
-> _UltralyticsByteTrackBackend
-> ultralytics.trackers.byte_tracker.BYTETracker
```

The adapter fails closed for disabled execution, invalid class input,
inconsistent frame context, unavailable runtime, version mismatch and invalid
backend output.

## Frozen Runtime Boundary

`configs/tracker.yaml` now records the P5-1 runtime state while preserving the
P5-0 thresholds:

| Field | Value |
| --- | --- |
| Provider/API | Ultralytics `BYTETracker` |
| Frozen version | `8.4.157` |
| Dependency source | `locks/EVAL-001/requirements.txt` |
| Person class | `0` / `person` |
| Minimum confidence | `0.25` |
| `track_high_thresh` | `0.5` |
| `track_low_thresh` | `0.1` |
| `new_track_thresh` | `0.6` |
| `track_buffer` | `30` |
| `match_thresh` | `0.8` |
| `fuse_score` | `true` |
| Execution | enabled for P5-1 adapter use |

The adapter performs a strict package-version check before initializing the
real Ultralytics tracker. It does not download a model or dependency.

## Tests

`tests/test_bytetrack_adapter.py` uses an injected scripted backend and does not
load `best.pt` or require Torch/Ultralytics. Coverage includes:

- one person across continuous frames;
- multiple people in one frame;
- a person leaving and re-entering a stream;
- empty/missing frames still updating backend state;
- rejection of non-person detections before backend update;
- rejection of mismatched frame context;
- low-confidence person filtering;
- duplicate or invalid backend matches failing closed;
- disabled execution failing closed;
- `PersonTrackingAdapter` protocol conformance and reset delegation.

The focused suite passed `36` tests across the adapter, P5-0 interface tests
and placeholder/import checks.

## Validation

| Check | Result |
| --- | --- |
| `python -m pytest` | `286 passed, 1 skipped`; skip is the existing optional Torch evaluation test |
| `python -m compileall .` | PASS |
| `git diff --check` | PASS |
| `git diff -- docs/00_PROJECT_CHARTER.md` | EMPTY |

Frozen asset verification after implementation:

| Asset | SHA256 |
| --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` |
| Processed `data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` |
| Source `data.yaml` | `5c393e74086c366a2ef55a77a4ddbf26bde1e08887a16f292f30a69fb3d21b34` |

## Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P5-1-G1 | Person-only ByteTrack adapter implemented behind the frozen interface | PASS |
| P5-1-G2 | Only class ID `0` / `person` reaches the tracker | PASS |
| P5-1-G3 | `DetectionResult` and core schemas remain runtime-independent | PASS |
| P5-1-G4 | Required single/multiple/enter-leave/missing/invalid-class tests pass | PASS |
| P5-1-G5 | Checkpoint, dataset, mapping and training configuration remain unchanged | PASS |
| P5-1-G6 | No model load, inference, association, training or commit/push occurred | PASS |

## Limitations

The current workspace does not have `ultralytics` or `torch` installed, so the
real Ultralytics `BYTETracker` backend was not executed. The tests verify the
adapter contract and fail-closed behavior with an injected backend; they do
not prove real track-ID continuity, occlusion behavior or stream accuracy.

M-009 remains `待实现`. Real runtime acceptance belongs to a later authorized
verification step after human review.

## Next Step

Wait for human review of P5-1. Do not begin Phase 5-2 Person-PPE association
until that review is explicitly recorded as PASS.
