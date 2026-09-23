# PHASE_SCOPE_CLARIFICATION_REPORT

Date: 2026-09-23

Base HEAD: `3623542e37cef207235975cae44a3f7bef081254`

Status: Documentation clarification complete; awaiting human review. No commit/push.

## 1. Modified files

Paths below are repository-relative.

- `README.md`: synchronize deferred MUST wording.
- `docs/01_MASTER_PLAN.md`: clarify scope and deferred ownership without changing phase statuses.
- `docs/02_CURRENT_STATUS.md`: scope wording and deferred MUST ownership only.
- `docs/03_TECHNICAL_DECISIONS.md`: clarify ADR-018 and append ADR-019.
- `docs/04_CHANGELOG.md`: record clarification and correct historical scope classification with attribution to ADR-019.
- `docs/05_TEST_GATES.md`: correct deferred requirement classification, preserving PASS decisions.
- `docs/phases/PHASE_04_INFERENCE.md`: distinguish offline completion from deferred MUST acceptance.
- `docs/phases/PHASE_05_TRACKING_ASSOCIATION.md`: clarify entry conditions; goal and not-started status unchanged.
- `docs/phases/PHASE_07_WEB_ALERTS.md`: acknowledge implementation/integration ownership.
- `docs/phases/PHASE_09_INTEGRATION_DELIVERY.md`: acknowledge final acceptance ownership.
- `docs/reports/maintenance/PHASE_SCOPE_CLARIFICATION_REPORT.md`: new review report.

No files moved or deleted. No historical ADR or report deleted.

## 2. ADR-019 summary

M-008 remains a V1 MUST. Annotated video rendering remains part of M-007
acceptance. Both are deferred from Phase 4, not converted into optional work.
Phase 7 owns implementation and page/service integration; Phase 9 owns final
Charter acceptance. This allocation keeps the real-time input dependency with
Phase 7 monitoring integration. It does not expand M-008 from Camera OR RTSP
to requiring both. ADR-018's offline release decision, evidence and tag remain.

## 3. MUST preservation check

- Charter matches HEAD after Git line-ending normalization; no Charter edit.
- M-007 and M-008 remain `待实现` with their original acceptance criteria.
- All ten Master Plan phase status cells match HEAD.
- Phase 5, Phase 7 and Phase 9 locked goals and not-started statuses remain.
- No code, test, configuration, model or dataset file changed.

## 4. Phase 4 final scope

`Offline Inference COMPLETE`: offline image inference, sequential local MP4
structured inference, frozen runtime/checkpoint identity and real validation
evidence. Camera/RTSP and annotated video rendering remain unimplemented
MUST work. P4-G3 remains deferred, not PASS. Offline completion does not claim
full M-007 or M-008 acceptance.

## 5. Phase 5 entry condition

- Phase 4 Offline Inference Gates PASS (both existing offline tables).
- Deferred ownership and delivery phase explicitly recorded.
- No frozen asset conflict, checked at entry to the implementation task.
- Existing detection-output prerequisite and separate authorization satisfied.

Phase 5 remains WAITING. No new frozen-asset verification or implementation
permission is claimed by this document-only task.

## 6. Validation result

- `git diff --check`: PASS for the documentation changes.
- Requested `rg` scope scan reviewed; no active definition in docs or README
  classifies M-008 or M-007 annotated rendering as an Extension.
- Tracked Markdown local file links: no missing target files.
- Read-only comparison: Charter unchanged, ten phase statuses preserved,
  Phase 5/7/9 locked goals preserved, all changed files are Markdown.
- `git status`: only the listed Markdown edits and this new report.
- No training, inference, runtime tests, experiment generation, commit or push.

### Known validation limitation

`tests/unit/test_documentation_governance.py` still contains two literal
assertions requiring the superseded Extension wording in the Phase 4 document
and README. Static inspection shows those assertions are incompatible with the
corrected documents. Tests were neither modified nor executed, per scope; this
report does not claim a passing test suite. A separately authorized test update
should validate preserved MUST ownership rather than obsolete wording.

Historical design snapshots remain historical. This task does not reorganize
reports, shorten CURRENT_STATUS, resolve Phase 1 acceptance, or implement any
deferred capability.
