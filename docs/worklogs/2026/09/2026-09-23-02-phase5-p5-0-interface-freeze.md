# Phase 5-0 Interface Freeze Worklog

## Changed

- Added model-independent tracking and association output schemas.
- Added person-only tracking and PPE-association adapter protocols.
- Froze `configs/tracker.yaml` and added `configs/association.yaml`.
- Added ADR-020, the Phase 5-0 design, report and focused tests.
- Recorded Phase 5 as in progress while leaving M-009 and M-010 `待实现`.

## Reason

Freeze interfaces and acceptance boundaries before implementing ByteTrack or
Person-PPE association, preventing runtime objects, nearest-distance matching
or ambiguous assignments from leaking into later phases.

## Validation

- `python -m pytest`: `276 passed, 1 skipped` (existing optional Torch test).
- `python -m compileall .`: PASS.
- `git diff --check`: PASS.
- `git diff -- docs/00_PROJECT_CHARTER.md`: EMPTY.

## Evidence

- `docs/designs/phase-05/P5-0_INTERFACE_FREEZE.md`
- `docs/reports/phase-05/P5-0_INTERFACE_FREEZE_REPORT.md`
- `configs/tracker.yaml`
- `configs/association.yaml`
- `core/schemas/tracking.py`
- `core/schemas/association.py`

## Risk

RISK-005 remains open. The frozen ambiguity rule prevents forced assignment but
still requires overlap and occlusion testing in Phase 5-2 and Phase 5-3.

## Not Verified

No ByteTrack run, association execution, model load, inference, video input,
track ID continuity or association accuracy was tested.

## Next Step

Wait for human review of P5-0, then authorize Phase 5-1.
