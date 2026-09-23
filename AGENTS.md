# ODPlatform-PPE Development Protocol

This file is the mandatory development protocol for Codex and all contributors.
It does not replace the locked project documents.

## Mandatory Reading Order

Before any development work, read these files in order:

1. `AGENTS.md`
2. `docs/00_PROJECT_CHARTER.md`
3. `docs/01_MASTER_PLAN.md`
4. `docs/02_CURRENT_STATUS.md`
5. `docs/03_TECHNICAL_DECISIONS.md`
6. `docs/04_CHANGELOG.md`
7. `docs/05_TEST_GATES.md`
8. `docs/08_RISK_REGISTER.md`
9. The most recent worklog under `docs/worklogs/`, if one exists; otherwise use
   the latest entry in `docs/04_CHANGELOG.md` as the handover summary.
10. The current phase document under `docs/phases/`
11. `docs/06_DATASET_CARD.md`
12. `docs/07_OPEN_SOURCE_USAGE.md`
13. `docs/09_REFERENCE_ASSETS.md`

After reading, output a PRE-READ REPORT before editing:

```text
PRE-READ REPORT
Current Phase:
Current Goal:
Current Status:
Relevant MUST IDs:
Known Risks:
Conflicts Found: YES / NO
Planned Changes:
```

If `Conflicts Found: YES`, stop and report immediately. Do not change the
charter or plan to match the code.

## Locked Governance

- Final project goals in `docs/00_PROJECT_CHARTER.md` are LOCKED.
- MUST IDs, descriptions, and acceptance criteria are LOCKED.
- EXTENSION goals and the explicit non-V1 scope are LOCKED.
- Phase goals in `docs/01_MASTER_PLAN.md` and phase documents are LOCKED.
- Internal phase modules, implementation details, and test methods may be
  adjusted without changing a phase goal.
- Only status fields may be updated routinely.
- A locked change requires explicit user approval and a recorded ADR.
- Never weaken, replace, or silently remove a requirement to make code pass.

## Completion Order

Every development increment must follow this order:

1. Code changes
2. Code inspection
3. Testing
4. Gate decision
5. Update the current phase document
6. Update `docs/02_CURRENT_STATUS.md`
7. Update `docs/04_CHANGELOG.md`
8. Update `docs/05_TEST_GATES.md`
9. Update a charter status only after full acceptance is proven

A feature may be marked `已经实现` only when real code exists, relevant tests
pass, and its documented acceptance criteria are met. Empty files, interfaces,
protocols, placeholders, or future-phase stubs never count as implemented.

## Engineering Rules

- Do not write fake business results. Future work must raise
  `NotImplementedError` with its target phase until implemented.
- Do not copy unknown-license or third-party business source code.
- Record every external project in `docs/07_OPEN_SOURCE_USAGE.md`.
- Do not replace RTSP, Camera, or any other MUST requirement with an easier
  local-only behavior.
- Do not download datasets, model weights, or large assets without explicit
  user approval.
- Do not commit or push unless the user explicitly requests it.
- Keep source edits scoped to the current phase and its acceptance criteria.

## Conflict Rule

If code, `docs/00_PROJECT_CHARTER.md`, and `docs/01_MASTER_PLAN.md` conflict:

1. Stop related development.
2. Preserve all existing work.
3. Report the exact conflicting files and statements.
4. Wait for user direction.

Never "fix" governance documents merely to agree with code.

## Documentation Lifecycle

For every development task, follow the mandatory reading order above before
editing. Read the current phase's most recent report when one exists. Use the
Charter for final goals, the Master Plan for phase goals, Current Status for
the latest state, ADRs for decisions, Changelog and the latest worklog for
history, Test Gates for acceptance, and Risk Register for open risks. Check
the requested change against these sources and include the result in the
PRE-READ REPORT. If they conflict, apply the Conflict Rule before editing.

After implementation and verification, update the applicable phase document,
Current Status, Changelog, and Test Gates in the Completion Order. Record the
handover using the template below. A documentation-only task updates only the
records relevant to its authorized scope; it does not change requirement or
phase status without the existing acceptance evidence.

## New Markdown Output Rules

- Development handovers: `docs/worklogs/YYYY/MM/YYYY-MM-DD-NN-topic.md`.
- Phase designs: `docs/designs/phase-NN/`.
- Phase validation and acceptance reports: `docs/reports/phase-NN/`.
- Repository governance and maintenance reports: `docs/reports/maintenance/`.
- Do not create temporary Markdown reports in the repository root.
- Keep existing historical reports at their current paths until a separate
  migration updates all references. Do not overwrite or delete history.

See `docs/README.md` for the document map and directory responsibilities.

## Handover Record

At the end of each development task, record these fields in its worklog:

```text
Changed:
Reason:
Validation:
Evidence:
Risk:
Not Verified:
Next Step:
```

Use repository-relative evidence paths and distinguish completed verification
from work not verified. Link the handover from Current Status when it affects
the active phase. A worklog is a handover record, not a substitute for test
results, Gate evidence, or an ADR.
