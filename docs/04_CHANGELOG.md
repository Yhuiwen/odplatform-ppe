# Changelog

All notable project changes are recorded here. This project follows a
phase-based log rather than claiming semantic-release completeness.

## 2026-09-21

### Phase 0 Foundation initialized

- Created the complete engineering directory and Python package skeleton.
- Added six YAML configuration files with future-phase status markers.
- Added path, YAML loading, logging, timing, system information, and detection
  schema foundations.
- Added explicit `NotImplementedError` boundaries for Phase 1 through Phase 9
  business modules.
- Added the locked project charter, master plan, ten phase documents, ADR log,
  dataset card, open-source usage record, risk register, and test gate system.
- Added Phase 0 unit tests and repository retention files.
- Initialized the Git repository without committing or pushing.

### Phase 0 Gate verified

- `python -m pytest`: 92 passed.
- `python -m compileall .`: passed.
- `git diff --check`: passed with all project files in intent-to-add state,
  then the intent-to-add index state was removed.
- G0-1 through G0-13: PASS.
- Phase status updated to `已经实现`; all MUST and Extension business statuses
  remain `待实现`.

### Pre-Phase 1 Reference Intake

- Added `docs/09_REFERENCE_ASSETS.md`.
- Added ADR-007 and ADR-008.
- Added RISK-011 and RISK-012.
- Updated AGENTS mandatory reading order.
- No business implementation.
- No teacher asset copied.
- Validation: pytest 99 passed; compileall passed.
