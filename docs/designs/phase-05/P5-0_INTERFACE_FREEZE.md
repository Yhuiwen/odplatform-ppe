# Phase 5-0 — Tracking & Association Interface Freeze

Status: FROZEN FOR PHASE 5 IMPLEMENTATION

This document freezes interfaces only. It does not claim that ByteTrack or
Person-PPE association has been implemented.

## 1. Entry Boundary

The implementation sequence is:

```text
DetectionResult
-> ByteTrack adapter
-> TrackResult
-> Person-PPE association
-> AssociationResult
```

The contracts consume the Phase 4 `DetectionResult` without changing detector
behavior, dataset identity, class mapping, training configuration or the
release checkpoint.

The frozen runtime is the existing `INF-RUNTIME-001`, with Ultralytics
`8.4.157` from `locks/EVAL-001/requirements.txt`. Tracking uses the mature
Ultralytics ByteTrack integration; no ByteTrack source is copied into this
repository.

## 2. Tracking Contract

`core/schemas/tracking.py` defines `TrackResult`.

- Tracking is person only.
- Only class ID `0` / `person` may be wrapped by `TrackResult`.
- `track_id` is a non-negative stable integer within one tracking stream.
- The source remains an ordered local video stream; camera and RTSP are not
  part of this phase.
- Empty frames still update tracker state but produce no tracks.

`core/tracking/interfaces.py` defines `PersonTrackingAdapter.update()`:

```text
detections + frame_id + timestamp + source
-> tuple[TrackResult, ...]
```

The adapter must preserve frame order. It must not download a model, remap
classes or emit non-person tracks.

## 3. Tracker Configuration Freeze

`configs/tracker.yaml` freezes:

| Field | Value |
| --- | --- |
| Tracker API | Ultralytics `BYTETracker` |
| Ultralytics | `8.4.157` |
| `track_high_thresh` | `0.5` |
| `track_low_thresh` | `0.1` |
| `new_track_thresh` | `0.6` |
| `track_buffer` | `30` |
| `match_thresh` | `0.8` |
| Person class | `0` / `person` |
| Minimum person confidence | `0.25` |
| Execution | Disabled until Phase 5-1 |

Changing these values requires new evidence and a reviewed configuration
change. They must not be tuned silently during implementation.

## 4. Association Contract

`core/schemas/association.py` defines:

- `AssociationStatus`: `associated` or `unknown`.
- `AssociationMethod`: `containment` or `iou`.
- `PPEAssociation`: one PPE detection with either a defensible track assignment
  or an explicit unknown result.
- `AssociationResult`: one frame with all person tracks and one association
  record for every PPE detection.

An associated record requires:

- a valid `track_id`;
- the matching `TrackResult`;
- the accepted geometric method;
- matching frame, timestamp and source.

An unknown record cannot carry a `track_id`, person track or method. It may
retain measured containment and IoU values for audit, but those values do not
create an assignment.

`core/association/interfaces.py` defines `PPEAssociationAdapter.associate()`:

```text
tracks + ppe_detections + frame context
-> AssociationResult
```

The contract is frame-based and returns project schemas only. Ultralytics or
tracker objects must not cross this boundary.

## 5. Association Policy Freeze

`configs/association.yaml` freezes the following candidate policy:

| Rule | Frozen value |
| --- | --- |
| PPE classes | `hardhat=1`, `no_hardhat=2`, `vest=3`, `no_vest=4` |
| Minimum detection confidence | `0.25` for both person and PPE |
| Minimum containment | PPE covered fraction `>= 0.50` |
| Minimum IoU | `IoU >= 0.10` |
| Assignment priority | containment, then IoU |
| Ambiguity margin | `0.10` |
| Maximum assignments per PPE | `1` |
| nearest-distance assignment | prohibited |
| Uncertain outcome | `unknown` |

For each PPE detection, implementation must:

1. reject person or PPE detections below the confidence threshold;
2. calculate bbox containment and IoU against candidate person tracks;
3. keep only candidates satisfying at least one frozen geometric threshold;
4. rank candidates by containment, then IoU, then person confidence and
   track ID as deterministic tie-breakers;
5. return `unknown` when no candidate exists; and
6. return `unknown` when the top two candidates are separated by less than
   the ambiguity margin.

The algorithm must never use nearest bbox centre, nearest distance or a
forced best-effort assignment.

## 6. Missing and Unknown Semantics

Missing PPE is represented by the absence of a PPE detection. Association must
not synthesize a PPE box or a negative class. Compliance interpretation of
that absence belongs to Phase 6.

Uncertain ownership is represented by `AssociationStatus.UNKNOWN`. This is a
successful, auditable output, not an error and not an assignment.

## 7. Test Contract

Phase 5-3 must cover at minimum:

- single person with one or more PPE detections;
- multiple non-overlapping people;
- overlapping or nested person boxes;
- missing PPE with no synthetic assignment;
- uncertain association retained as `unknown`;
- person-only tracker input and non-person rejection.

Phase 5-1 and Phase 5-2 may add focused tests before the integrated Phase 5-3
suite, but they must preserve these frozen contracts.

## 8. Implementation Sequence

Phase 5-1 implements the `PersonTrackingAdapter` through Ultralytics ByteTrack
and tracks person only.

Phase 5-2 implements `PPEAssociationAdapter` using containment, IoU and the
frozen confidence rule. Unknown remains explicit.

Phase 5-3 executes the required single-person, multi-person, overlap, missing
PPE and uncertain-association tests.

## 9. Non-Goals

Phase 5-0 does not implement:

- ByteTrack execution;
- association execution;
- RTSP or camera input;
- compliance or violation rules;
- temporal confirmation;
- event generation, persistence or alerts;
- Web, LLM or Agent behavior;
- model loading, inference, retraining or checkpoint modification.
