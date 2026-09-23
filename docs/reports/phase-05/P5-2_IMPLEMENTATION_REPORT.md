# P5-2 Person-PPE Association Implementation Report

Status: COMPLETE FOR HUMAN REVIEW

## Scope

Phase 5-2 implements the frame-level association leg:

```text
TrackResult
+ PPE DetectionResult
-> PPEPersonAssociationAdapter
-> AssociationResult
```

The implementation consumes only project-owned schemas. It does not load
`best.pt`, execute inference or ByteTrack, modify the dataset, change the
frozen mapping or training configuration, or begin Phase 5-3.

## Implementation Architecture

- `core/association/ppe_person_association.py` provides
  `PPEPersonAssociationAdapter`.
- The class implements the frozen `PPEAssociationAdapter` protocol from
  `core/association/interfaces.py`.
- `core/association/__init__.py` exports the adapter.
- Only `TrackResult` values can supply candidate person identities.
- Only PPE class IDs `1=hardhat`, `2=no_hardhat`, `3=vest` and `4=no_vest`
  are accepted as PPE detections.
- A person detection or unsupported class in the PPE input fails closed.
- PPE detections never enter the tracker and are never converted to
  `TrackResult`.

The adapter is stateless. One call produces one `AssociationResult` for one
frame and never mutates a person track or PPE detection.

## Frozen Association Policy

The adapter reads `configs/association.yaml` and preserves the P5-0 policy:

| Rule | Value |
| --- | --- |
| Minimum detection confidence | `0.25` for person tracks and PPE |
| Minimum containment ratio | `0.50` |
| Minimum IoU | `0.10` |
| Assignment priority | containment, then IoU |
| Ambiguity margin | `0.10` |
| Maximum assignments per PPE | `1` |
| Nearest-distance assignment | prohibited |
| No eligible candidate | `unknown` |
| Ambiguous leading candidates | `unknown` |

Containment is the intersection area divided by the PPE bbox area. IoU is the
intersection area divided by the union of the PPE and person bboxes.

Eligible candidates are ranked by:

1. containment method before IoU-only method;
2. the candidate method's primary geometric score;
3. containment ratio;
4. IoU;
5. person confidence;
6. track ID as a deterministic final tie-breaker.

If the leading candidates use the same method and their primary scores differ
by less than `0.10`, the result remains `unknown`. Deterministic tie-breakers
do not override ambiguity.

## Output Semantics

- Every accepted PPE detection gets one `PPEAssociation` record.
- An associated record contains the existing `track_id`, matching
  `TrackResult`, accepted geometric method and measured geometry.
- An unknown record carries no person, track ID or method.
- Missing PPE remains the absence of a PPE detection; the adapter does not
  synthesize a box or negative class.
- Empty input returns an empty, valid `AssociationResult`.
- Low-confidence PPE remains `unknown` rather than being assigned.

## Tests

`tests/test_person_ppe_association.py` covers:

- one person with a helmet;
- one person with a vest;
- multiple people with separate PPE assignments;
- rejection of a geometrically wrong candidate;
- ambiguity inside the frozen margin;
- missing PPE without synthetic output;
- empty detection;
- IoU-only association;
- low-confidence PPE and person boundaries;
- rejection of person/unsupported PPE classes;
- frame-context mismatch;
- disabled execution;
- protocol conformance.

The focused adapter/interface/placeholder suite passed `40` tests.

## Validation

| Check | Result |
| --- | --- |
| `python -m pytest` | `300 passed, 1 skipped`; skip is the existing optional Torch evaluation test |
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

Implementation hashes:

| Artifact | SHA256 |
| --- | --- |
| `core/association/ppe_person_association.py` | `2c021e4ad80ce906cca0acb916b7ccab8cbb6622af67b7c5287a7834f5c0b7d5` |
| `configs/association.yaml` | `be32af654ab76e4d1dd7e82c1a3fb0ffbbed2026e9711bea73fcacfc703073a6` |
| `tests/test_person_ppe_association.py` | `6739f601452813206cea07590cf9c31008822b99aa35c9c3a4b44d5dd01f058f` |

## Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P5-2-G1 | Association adapter implemented behind the frozen protocol | PASS |
| P5-2-G2 | Only existing person tracks are assignment targets | PASS |
| P5-2-G3 | Frozen confidence/containment/IoU thresholds are preserved | PASS |
| P5-2-G4 | Nearest-distance and forced assignment are excluded | PASS |
| P5-2-G5 | Required single/multiple/wrong/ambiguous/missing/empty tests pass | PASS |
| P5-2-G6 | Frozen checkpoint, dataset, mapping and training config remain unchanged | PASS |
| P5-2-G7 | No model load, inference, training, commit or push occurred | PASS |

## Limitations

The adapter is verified with deterministic synthetic `TrackResult` and
`DetectionResult` inputs. Real detector output, real ByteTrack tracks, video
integration, occlusion behavior and end-to-end association accuracy remain
unverified. Phase 5-1 real Ultralytics execution is also still unverified in
the current workspace.

M-010 remains `待实现`. Phase 5-3 must provide the integrated acceptance
evidence before the Charter status can change.

## Next Step

Wait for human review of P5-2. Do not begin Phase 5-3 until that review is
explicitly recorded as PASS.
