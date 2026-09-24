# Phase 8 P8-6.4.3 AgentService Orchestration Report

Status: `P8-6.4.3 HUMAN REVIEW PASS`

Date: 2026-09-24

Checkpoint base: `phase-8-provider-pipeline-complete`

Post-review note: P8-6.4.3 subsequently received human review PASS. The
implementation is included in interim checkpoint tag
`phase-8-controlled-agent-complete`. No durable audit store, memory,
autonomous loop, real provider planning request or Phase 9 work is included.

## 1. Scope

P8-6.4.3 implements only the AgentService orchestration boundary authorized
after P8-6.4.1 and P8-6.4.2 human review PASS:

```text
AgentRequest
-> LLMPlannerAdapter
-> deterministic fallback when needed
-> validated phase8-agent-plan-v1
-> ToolRegistry.execute
-> AgentAuditService
-> AgentResult
```

No memory, autonomous loop, dynamic tool, provider integration, durable audit
storage or Phase 9 behavior is included.

## 2. Changed Files

Implementation:

- `core/schemas/agent.py`
- `services/agent_service.py`

Tests:

- `tests/test_agent_service.py`
- `tests/unit/test_placeholders.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/designs/phase-08/PHASE_8_P8_6_4_AGENT_PLANNING_ARCHITECTURE.md`
- `docs/designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md`
- `docs/reports/phase-08/PHASE_8_P8_6_4_2_LLM_PLANNER_ADAPTER_REPORT.md`
- this report

## 3. Request Contract

`phase8-agent-request-v1` is implemented as an immutable bounded contract:

```text
request_id
principal_ref
role
question
requested_period
filters
capabilities
```

`role` and `capabilities` are trusted execution identity supplied by the
platform adapter. They are not inferred from question text or provider
output. The question is normalized and bounded, period/filter mappings are
copied immutably, and supported role/capability values remain the existing
project-owned enums. `AgentRequest.to_context()` constructs the unchanged
`ToolExecutionContext` used by planning and execution.

## 4. Result Contract

`phase8-agent-result-v1` is implemented with the frozen fields:

```text
schema_version
request_id
audit_id
status
answer
facts
metrics
event_refs
evidence_refs
report
safe_error
```

The result uses the existing `AgentOutcome` vocabulary:

```text
ANSWERED
INSUFFICIENT_DATA
OUT_OF_SCOPE
TOOL_ERROR
REFUSED
AUDIT_UNAVAILABLE
```

Facts, metrics, event references, evidence references and report content
remain structured. `answer` is advisory text only. Successful results require
an append-confirmed `audit_id`; every non-success result carries a bounded
`ToolError`. Deterministic JSON serialization is provided without requiring
Ultralytics, provider or runtime result objects.

## 5. Orchestration Behavior

`AgentService` follows these checks:

1. Accept only a typed `AgentRequest`.
2. Delegate planning to the existing `LLMPlannerAdapter`; this preserves the
   optional candidate attempt, strict parser/validator and deterministic
   fallback already reviewed in P8-6.4.1 and P8-6.4.2.
3. Reject any outcome that is not a validated `phase8-agent-plan-v1`.
4. Call `ToolRegistry.execute` with the validated tool name and arguments.
5. Never call a handler, candidate, provider object or dynamic tool directly.
6. Project only the selected tool's structured result into `AgentResult`.
7. Record the plan and tool outcome through the append-only
   `AgentAuditService`.
8. Fail closed as `AUDIT_UNAVAILABLE` if the tool-result audit append cannot
   be confirmed.

The service does not retry, recurse, plan multiple tools, maintain memory or
enter an autonomous loop.

## 6. Outcome Mapping

| Condition | Agent result | Audit behavior |
| --- | --- | --- |
| Validated plan and successful tool result | `ANSWERED` or `INSUFFICIENT_DATA` | Planner event plus `SUCCESS` tool event |
| Empty summary/statistics/detail result | `INSUFFICIENT_DATA` | Planner event plus `SUCCESS` tool event |
| Same-origin LLM candidate failure | Deterministic fallback result | Bounded failure event, plan event, then tool event |
| Forbidden or invalid request | `REFUSED` or `OUT_OF_SCOPE` | Existing planner event or bounded service refusal event |
| Tool refusal or handler failure | `REFUSED` or `TOOL_ERROR` | Existing planner event plus tool `REFUSED`/`FAILURE` event |
| Invalid successful tool payload | `TOOL_ERROR` | Bounded `TOOL_RESULT_INVALID` failure event |
| Audit append unavailable | `AUDIT_UNAVAILABLE` | No successful result is released |
| Unknown intent | `OUT_OF_SCOPE` | Bounded refusal/failure event |

Planner errors that already contain an `AuditEvent` are not duplicated.
Planner errors without an audit event are recorded by `AgentService`, so a
valid typed request does not silently bypass the audit boundary.

## 7. Security and Compatibility

- The provider candidate is never passed to `ToolRegistry.execute`.
- `AgentService` never imports or invokes a tool handler directly.
- Unknown intent, forbidden mutation/admin/system requests and permission
  failures remain fail-closed.
- Anonymous capabilities still resolve through the existing
  deny-by-default `ToolPermissionPolicy`; provider invocation is not inferred.
- No raw question, tool arguments, provider output, credentials, database path
  or filesystem path is added to audit records.
- The existing report provider path and `TemplateFallback` remain unchanged.
- `phase8-report-v1`, `SafetyReportGroundingValidator`, `TemplateFallback`,
  the static registry, deterministic planner and candidate validator remain
  unchanged.
- The `phase-8-provider-pipeline-complete` tag remains at its original target.

## 8. Tests

Focused command:

```text
python -m pytest tests/test_agent_service.py tests/test_llm_planner_adapter.py tests/test_agent_audit.py tests/unit/test_placeholders.py -q
36 passed
```

Coverage includes:

- full deterministic successful flow;
- validated LLM candidate success through the registry;
- provider failure with deterministic fallback;
- forbidden request without tool execution;
- tool failure with structured safe error;
- planner failure recorded by AgentService when the adapter supplied no event;
- audit append failure fail-closed;
- empty tool result mapped to `INSUFFICIENT_DATA`;
- immutable result serialization.

Full repository gate:

```text
python -m pytest -q
632 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skipped test is the existing optional Torch evaluation test because Torch
is not installed on this host.

## 9. Frozen Compatibility

| Contract or asset | Result |
| --- | --- |
| `phase8-agent-plan-v1` | UNCHANGED |
| `phase8-agent-plan-candidate-v1` | UNCHANGED |
| `phase8-agent-tool-registry-v1` | UNCHANGED |
| `phase8-agent-policy-v1` | UNCHANGED |
| `phase8-agent-audit-v1` | UNCHANGED |
| Deterministic planner | UNCHANGED |
| Static four-tool registry | UNCHANGED |
| Deny-by-default permissions | UNCHANGED |
| `phase8-report-v1` | UNCHANGED |
| `SafetyReportGroundingValidator` | UNCHANGED |
| `TemplateFallback` | UNCHANGED |
| P8-5 provider transport and trust boundary | UNCHANGED |
| `phase-8-provider-pipeline-complete` | UNCHANGED |
| Model, dataset, training and inference assets | UNCHANGED |

No real provider request was issued. No model, dataset, training,
inference, compliance or tracking artifact was modified.

## 10. Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-6.4.3-G1 | Typed bounded request/result contracts are implemented | PASS |
| P8-6.4.3-G2 | Only validated `phase8-agent-plan-v1` can execute | PASS |
| P8-6.4.3-G3 | `ToolRegistry.execute` is the only execution path | PASS |
| P8-6.4.3-G4 | Deterministic fallback and permissions are preserved | PASS |
| P8-6.4.3-G5 | Planner and tool outcomes are audited | PASS |
| P8-6.4.3-G6 | Audit append failure fails closed | PASS |
| P8-6.4.3-G7 | Focused behavior and serialization tests pass | PASS |
| P8-6.4.3-G8 | Frozen contracts, assets and checkpoint remain unchanged | PASS |

## 11. Limitations

- P8-6.4.3 has passed human review and is included in the interim checkpoint
  tag `phase-8-controlled-agent-complete`.
- Audit storage remains append-only and process-local; durable persistence is
  not implemented.
- Agent memory, autonomous loops, multi-step planning and dynamic tools are
  not implemented.
- The planner adapter still uses an injected candidate client; no real
  provider planning request has been issued.
- The Agent answer text is advisory and derives only from validated tool
  output; no additional LLM answer synthesis is present.
- M-021, M-022 and M-023 remain `待实现`.

## 12. Final State

```text
P8-6.4.2 LLM planner adapter: HUMAN REVIEW PASS
P8-6.4.3 AgentService orchestration:
HUMAN REVIEW PASS

Durable audit storage: NOT IMPLEMENTED
Memory and autonomous loop: NOT IMPLEMENTED
Real provider planning request: NOT RUN
Phase 9: NOT STARTED
```

The implementation report itself performed no commit, tag or push. The
subsequent checkpoint release task published the reviewed implementation
under tag `phase-8-controlled-agent-complete`.
