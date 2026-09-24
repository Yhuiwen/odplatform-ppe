# Phase 8 P8-0 Architecture Freeze Report

Status: `P8-0 DESIGN COMPLETE / HUMAN REVIEW PASS`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD: `47206f5b2425572fd8b186312023767d12730f42`
- `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Working tree before P8-0 edits: CLEAN
- Phase 7 final release commit:
  `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`
- Phase 7 final tag: `phase-7-release-freeze-complete`
- Existing base tag: `phase-7-web-alert-platform-complete`
- Existing Phase 7 tags were not moved, recreated or deleted.

## 2. Pre-Read Result

The authoritative repository documents were read before design work. No
governance conflict was found.

Phase 8 scope is already locked as `LLM Report + Fallback + Basic Agent`.
The authoritative phase file is `docs/phases/PHASE_08_LLM_AGENT.md`; no
duplicate `PHASE_08_AGENT.md` was created.

The repository currently contains only placeholder boundaries:

- `infra/llm/llm_client.py`
- `infra/llm/fallback.py`
- `services/report_service.py`
- `services/agent_service.py`

No LLM provider, provider SDK, agent framework, LLM configuration or real
credential exists. M-021, M-022 and M-023 remain `待实现`.

## 3. Identified Phase 8 Requirements

- Generate safety reports from structured platform data without fabricating
  events, IDs, measurements or conclusions.
- Provide a deterministic local fallback when the LLM is unavailable or its
  output is invalid.
- Permit a Basic Agent to query and analyze internal platform data only through
  controlled tools.
- Keep the agent downstream of detection, tracking, association, compliance
  and event persistence.
- Keep policy, evidence, security and failure behavior explicit before
  implementation.

## 4. Proposed Architecture

```text
Inference
-> Tracking
-> Association
-> Compliance
-> Event Store
        |
        v
SafetyAnalyticsService
        |
        v
SafetyContextBuilder
        |
        v
SafetyLLMClient
        |
        v
StructuredSafetyReport
```

`ReportService` orchestrates the report path and owns fallback selection.
`AgentService` is a separate read-only path over an allowlist of query and
analysis tools.

The complete design is in
`docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`.

## 5. Deterministic and LLM Responsibilities

Deterministic responsibilities:

- interval and event filtering;
- counts by type, status, day and tracker scope;
- first/last occurrence;
- evidence-reference availability;
- source-reference grouping;
- context serialization and reproducible ordering;
- grounding validation;
- local template fallback.

LLM responsibilities:

- natural-language synthesis of supplied facts and metrics;
- clearly labeled risk interpretation;
- advisory recommendations linked to deterministic references.

The LLM does not detect PPE, assign tracks, associate PPE, create events,
change event status, calculate unsupported metrics or decide compliance.

## 6. Input Contract

Phase 8 reads through `EventQueryService`. The authoritative
`PersistedEvent` projection is:

```text
id
timestamp
track_id
type
confidence
snapshot
status
```

The context contract is versioned as `phase8-context-v1` and separates:

```text
observed_facts
calculated_metrics
metadata
unavailable_fields
```

`track_id` is tracker-scoped and is not treated as stable personal identity.
Duration and alert-delivery statistics are explicitly unavailable under the
current schema.

## 7. Output Contract

The report contract is versioned as `phase8-report-v1`. It retains separate
claims, evidence references, recommendations and limitations.

Every factual claim must reference a fact or metric. Every recommendation must
reference supporting facts or metrics. The report records whether generation
used `LLM`, `TEMPLATE_FALLBACK` or `REPORT_UNAVAILABLE`.

## 8. Grounding Policy

- Event IDs must exist in the context.
- Track IDs must belong to referenced facts or metrics.
- Numeric claims must match deterministic context values.
- Recommendations remain advisory and visibly separate from facts.
- Unavailable fields cannot become inferred claims.
- Invalid provider output is rejected and never returned as a normal report.
- Template fallback obeys the same grounding rules.

## 9. Failure Isolation

Provider failure, timeout, malformed output, schema failure, unsupported
references, missing evidence, partial database data and empty event sets have
explicit outcomes. Report and agent execution is read-only and isolated from
the Phase 0 through Phase 7 monitoring path.

The deterministic fallback is required for M-022. If fallback itself fails, the
result is `REPORT_UNAVAILABLE`; no synthetic report is returned.

## 10. Privacy and Security

Only structured event metadata and deterministic metrics may enter an external
provider under an explicit policy. Raw images, snapshot bytes, absolute paths,
credentials, databases, environment values, raw RTSP identities and personnel
data are excluded by default.

Provider credentials come from environment variables or an external secret
manager. They must not enter Git, logs, reports, fixtures or provider error
messages.

## 11. Testing Strategy

Future P8 tests must cover deterministic analytics, reproducible context,
schema validation, hallucinated event IDs, numeric consistency, provider
failure isolation, empty data, mock LLM behavior, fallback labeling and Agent
tool permission boundaries.

No test may require a live external API.

## 12. Files Changed by P8-0

- `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`
- `docs/reports/phase-08/PHASE_8_P8_0_ARCHITECTURE_FREEZE_REPORT.md`
- `docs/worklogs/2026/09/2026-09-24-02-phase8-p8-0-architecture-freeze.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/03_TECHNICAL_DECISIONS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `README.md`

No Python, test, configuration, model, dataset or training file is changed.

## 13. Validation

Validation after the documentation patch:

```text
python -m pytest -q
414 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The single skip is the existing optional Torch evaluation test
(`tests/unit/test_evaluation.py:213`; Torch is not installed on this host).
The frozen checkpoint, training configuration, inference configuration and
processed dataset hashes match. Both Phase 7 tags retain their existing target
commits. A credential-pattern scan found no matching secret. Generated runtime
artifacts remain Git-ignored.

## 14. Gate Results

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-0-G1 | Authoritative Phase 8 scope and repository status are audited | PASS |
| P8-0-G2 | Downstream read-only trust boundary is frozen | PASS |
| P8-0-G3 | Deterministic analytics and versioned context contracts are defined | PASS |
| P8-0-G4 | Provider-independent report and fallback contracts are defined | PASS |
| P8-0-G5 | Grounding and evidence-reference policy is defined | PASS |
| P8-0-G6 | Failure, privacy, secret and Basic Agent tool boundaries are defined | PASS |
| P8-0-G7 | Future deterministic and mock-based evaluation strategy is defined | PASS |
| P8-0-G8 | No implementation, external call, dependency, frozen-asset change, commit, tag or push is included | PASS |

## 15. Unresolved Decisions

- LLM provider and provider-specific authentication.
- Whether a small HTTP adapter or provider SDK is appropriate.
- Production context-size threshold.
- Report retention and export formats.
- Final fallback wording and localization.
- Agent planning strategy and model/provider selection.

None of these decisions changes the read-only boundary, context separation,
grounding contract, fallback requirement or failure-isolation rule.

## 16. P8-1 Recommendation

P8-0 passed human review. P8-1 was authorized for only deterministic work:

1. freeze typed analytics/context schemas;
2. implement `SafetyAnalyticsService` against `EventQueryService`;
3. implement canonical `SafetyContextBuilder` serialization;
4. implement context-schema validation and unit tests; report-level grounding
   validation is deferred to P8-2 with the report contract;
5. keep provider integration and network calls out of P8-1.

Final P8-0 state: `P8-0 DESIGN COMPLETE / HUMAN REVIEW PASS`.
