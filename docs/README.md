# Documentation Guide

## Purpose

The `docs/` directory records the project's goals, phase plan, current state,
architecture decisions, acceptance evidence, and development handovers. Start
with `AGENTS.md` at the repository root for the required reading order and
development protocol. Use repository-relative paths in documentation so links
remain usable after checkout on another machine.

## Core Documents

| Document | Responsibility |
| --- | --- |
| `00_PROJECT_CHARTER.md` | Locked final goal, MUST requirements, Extension scope, and acceptance criteria. |
| `01_MASTER_PLAN.md` | Phase plan, dependencies, goals, and phase status. |
| `02_CURRENT_STATUS.md` | Single entry point for the latest project state and next allowed step; historical detail stays in phase records and handovers. |
| `03_TECHNICAL_DECISIONS.md` | Append-only ADRs and architecture decisions. |
| `04_CHANGELOG.md` | Short historical index of completed changes. |
| `05_TEST_GATES.md` | Acceptance rules, gate decisions, and evidence references. |
| `08_RISK_REGISTER.md` | Open risks, mitigations, and risk status. |

For data identity, dependency and reference-asset work, also read
`06_DATASET_CARD.md`, `07_OPEN_SOURCE_USAGE.md`, and `09_REFERENCE_ASSETS.md`.
Current phase plans and gates are under `phases/`.

## Directory Rules

### designs

Store new phase design documents in `docs/designs/phase-NN/`, where `NN` is
the two-digit phase number. A design describes proposed behavior and does not
by itself prove implementation or acceptance.

### reports

Store new phase validation and acceptance reports in
`docs/reports/phase-NN/`. Reports identify the evidence, validation performed,
result, and limits of the claim. Keep existing historical reports at their
current paths until a separately authorized migration updates their references.

### worklogs

Store development handovers in `docs/worklogs/YYYY/MM/`, named
`YYYY-MM-DD-NN-topic.md`. Each records Changed, Reason, Validation, Evidence,
Risk, Not Verified, and Next Step. Read the latest worklog before new
development; when none exists yet, use the newest Changelog entry.

### maintenance

Store repository governance and maintenance reports in
`docs/reports/maintenance/`. These reports record document-system changes
without altering feature acceptance or phase status.

Do not add temporary Markdown reports at the repository root. Preserve older
reports and decisions for audit; document navigation does not supersede the
Charter, phase gates, or ADRs.
