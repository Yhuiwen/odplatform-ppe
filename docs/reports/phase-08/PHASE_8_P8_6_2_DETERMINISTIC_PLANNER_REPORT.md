# Phase 8 P8-6.2 Deterministic Planner Report

Status: `P8-6.2 HUMAN REVIEW PASS`

Date: 2026-09-24

Post-review note: P8-6.2 subsequently received human review PASS. A separate
P8-6.3 slice adds the append-only in-memory Agent audit boundary; durable
audit storage, AgentService orchestration, P8-6.4 and Phase 9 remain
unimplemented.

## 1. Scope

This implementation adds only the deterministic Agent planner authorized
after P8-6.1 human review PASS.

Implemented:

- `AgentIntent` and `AgentPlan` contracts;
- deterministic intent classification;
- exact intent-to-tool mapping for the four frozen read-only tools;
- bounded question, reporting-period, filter and event-ID validation;
- registry resolution and deny-by-default permission preflight;
- planner errors that fail closed without executing a tool.

Not implemented:

- `AgentService` orchestration or answer synthesis;
- LLM tool calling, provider-native function calling or autonomous reasoning;
- dynamic tools or tool registration;
- durable Agent audit storage;
- provider changes;
- P8-6.3 or Phase 9 work.

## 2. Changed Files

Implementation:

- `core/schemas/agent.py`
- `core/agent/planner.py`
- `core/agent/__init__.py`

Tests:

- `tests/test_agent_planner.py`
- `tests/unit/test_imports.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md`
- `docs/reports/phase-08/PHASE_8_P8_6_ARCHITECTURE_FREEZE_REPORT.md`
- `docs/reports/phase-08/PHASE_8_P8_6_1_TOOL_REGISTRY_REPORT.md`
- this report

## 3. AgentPlan Contract

`AgentPlan` version:

```text
phase8-agent-plan-v1
```

Fields:

```text
schema_version
intent
tool_name
tool_version
arguments
question_sha256
```

Only the four supported read-only intents may produce a plan. The raw
question is not copied into the plan; only its canonical SHA256 is retained.

## 4. Intent Mapping

| Intent | Tool |
| --- | --- |
| `SAFETY_SUMMARY` | `get_safety_summary` |
| `EVENT_STATISTICS` | `get_event_statistics` |
| `EVENT_DETAIL` | `get_event_details` |
| `SAFETY_REPORT` | `generate_safety_report` |

Unknown intents return `OUT_OF_SCOPE`. Mutation, administration and system
action requests are classified as `FORBIDDEN_REQUEST` and fail closed.

## 5. Planning Boundary

```text
question
-> deterministic classification
-> exact static tool mapping
-> argument validation
-> registry resolution
-> permission preflight
-> AgentPlan
```

The planner contains no call to `ToolRegistry.execute`. It cannot invoke a
tool handler, provider, model, network client or shell. Execution remains a
separate future boundary and must pass the registry.

## 6. Security and Validation

- Questions are whitespace-normalized, non-empty and capped at 2,000 UTF-8
  bytes by default.
- Reporting periods use the existing `ReportingPeriod` UTC contract and are
  capped at 366 days by default.
- Filters must match the resolved tool descriptor's input schema.
- `event_type`, `status`, `track_id`, `limit`, `offset` and `event_id` receive
  bounded project-owned validation.
- Unknown filters, null filter values, unknown tools, unsupported intents and
  forbidden requests fail closed.
- `ToolPermissionPolicy` checks the required capability before a plan is
  returned.
- No LLM, HTTP, network, filesystem or Agent framework dependency is added.

## 7. Tests

Focused:

```text
python -m pytest tests/test_agent_planner.py tests/test_agent_tool_registry.py tests/unit/test_imports.py -q
112 passed
```

Full repository:

```text
python -m pytest -q
577 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skipped test is the existing optional Torch evaluation test because Torch
is not installed on this host.

## 8. Frozen Compatibility

- `phase8-report-v1`: unchanged.
- `SafetyReportGroundingValidator`: unchanged.
- `TemplateFallback`: unchanged.
- P8-5 provider transport and trust boundary: unchanged.
- `phase-8-provider-pipeline-complete`: unchanged.
- Model, dataset, training, inference and mapping identities: unchanged.
- Charter body: unchanged.

## 9. Known Limitations

- `AgentService` remains a future-phase placeholder; the planner exists but
  orchestration, audit persistence and answer synthesis do not.
- The planner uses deterministic keyword rules; it is not natural-language
  understanding and does not call an LLM.
- Durable audit storage remains unimplemented.
- No real tool execution is performed by the planner unit tests.
- P8-6.3 implements only the append-only in-memory audit contract,
  sanitization and service and has passed human review; durable persistence is
  not implemented.
- P8-6.4 architecture freeze passed human review; P8-6.4.1 through P8-6.4.3
  later implemented and reviewed the planner adapter and AgentService
  orchestration. Phase 9 has not started.

## 10. Final State

```text
P8-6.1 Static Read-only Tool Registry and Permission Layer:
HUMAN REVIEW PASS

P8-6.2 Deterministic Agent Planner:
HUMAN REVIEW PASS

P8-6.3 Append-only Agent Audit:
HUMAN REVIEW PASS

P8-6.4 LLM-Assisted Planning Architecture:
ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS

P8-6 Basic Agent:
IMPLEMENTATION CHECKPOINT RELEASED

Phase 9:
NOT STARTED
```

No commit, tag or push was performed by this slice. P8-6.3 subsequently passed
human review; P8-6.4 through P8-6.4.3 were later implemented and reviewed, and
the Agent implementation checkpoint was published under tag
`phase-8-controlled-agent-complete`. Durable audit storage, provider planning
execution and Phase 9 still require new authorization.
