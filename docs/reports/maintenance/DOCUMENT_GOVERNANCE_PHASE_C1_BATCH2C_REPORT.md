# Documentation Governance Phase C-1 Batch-2C Report

Date: 2026-09-23
Base HEAD: `fe4d8de9fa5157b7f69ef1bc746271fa8b2a6049`
Status: design migration complete for human review; no commit or push.

## Moved Files

| Original | Destination |
| --- | --- |
| `docs/reports/P2-0_DEPENDENCY_STRATEGY.md` | `docs/designs/phase-02/P2-0_DEPENDENCY_STRATEGY.md` |
| `docs/reports/P2-0_VERSION_MATRIX.md` | `docs/designs/phase-02/P2-0_VERSION_MATRIX.md` |
| `docs/reports/P2-1_DEPENDENCY_SPECIFICATION.md` | `docs/designs/phase-02/P2-1_DEPENDENCY_SPECIFICATION.md` |
| `docs/reports/P2-1_ENVIRONMENT_DECISION.md` | `docs/designs/phase-02/P2-1_ENVIRONMENT_DECISION.md` |
| `docs/reports/P2-1_SETUP_PLAN.md` | `docs/designs/phase-02/P2-1_SETUP_PLAN.md` |

The earlier untracked Batch-2C audit report was deleted at the user's explicit direction to restore a clean baseline. The five designs were moved with `git mv` after that pre-check passed.

## Rename Status and Hash Verification

All five staged moves are `R100`. Each new path has the same Git blob ID and working-tree SHA256 as its pre-move source; design bodies were not edited.

| File | Git blob ID before/after | SHA256 before/after |
| --- | --- | --- |
| `P2-0_DEPENDENCY_STRATEGY.md` | `2f2974cfadb200eab22df8f8f90a55c002526535` | `eed6eaa2a8680df663c41c01de74569cbdaf398c2755be7e28cd4b1aa22d43d2` |
| `P2-0_VERSION_MATRIX.md` | `40e1c05c53f1a2d3c279b22a581eb437eeaeb098` | `d8ce6c17a8e13fcb8ad0948e40fd43c9ebefc8548ab35486e0971c34951347b5` |
| `P2-1_DEPENDENCY_SPECIFICATION.md` | `a3d9cf8b7e4999be6396b03a316ed3bceb6321d6` | `18017974b1e7bb1b6fe9908431ec1c435c9f85b799553d1f86073e56c55ce521` |
| `P2-1_ENVIRONMENT_DECISION.md` | `33455f7a7fd9815155a99adfbd4635e15ec17a36` | `4a7afc7921baa4e501c4eb14d564674ddd149c0c31c1f3b325c7fbb1ec1dcba6` |
| `P2-1_SETUP_PLAN.md` | `86e8ba3a0b3605fd649714d23553633b3cb6b26a` | `48a0740449e3d0ba1633f282e325009ba59abbd3e8c5c61fc3540dd7b62449d3` |

## Reference Updates

- `docs/04_CHANGELOG.md`: five active design paths updated to `docs/designs/phase-02/`.
- `docs/05_TEST_GATES.md`: five corresponding evidence paths updated; Gate statuses unchanged.
- `P2-1_ENVIRONMENT_DECISION.md` refers to `P2-1_DEPENDENCY_SPECIFICATION.md` by filename. Both now share the same destination directory, so that reference remains valid without changing either design.
- `docs/reports/phase-02/P2-0_TRAINING_READINESS.md` retains its three dated old-path statements. It is a historical report and was not modified. The previously deleted Batch-2C audit is not part of this migration.
- No other historical report, test, script, configuration, model, data or experiment asset was changed.

## Tests

- `python -m pytest tests/unit/test_documentation_governance.py`: **31 passed**.
- All 13 local Markdown links resolve.
- `git diff --check` and `git diff --cached --check`: PASS before this report was written.
- Blob identity, SHA256 and `R100` rename status were verified for all five moves.

## Remaining Risks

- Older dated report prose still names former paths. Current Changelog and Test Gates references point to the new design paths; historical text remains intentionally unchanged.
- The full test suite was not run for this design-only migration.

Next step: human review of this Batch-2C diff. Do not commit or push as part of this task.
