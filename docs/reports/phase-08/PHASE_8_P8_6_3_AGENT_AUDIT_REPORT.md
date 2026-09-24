# Phase 8 P8-6.3 Agent Audit Report

Status: `P8-6.3 HUMAN REVIEW PASS`

Date: 2026-09-24

## 1. Scope

This implementation adds only the append-only Agent audit model and audit
service authorized after P8-6.2 human review PASS.

Implemented:

- `phase8-agent-audit-v1` `AuditEvent`;
- frozen append-only audit execution statuses;
- bounded metadata sanitization;
- an append-only in-memory store abstraction;
- `AgentAuditService` recording, planner integration and deterministic
  serialization;
- focused privacy, failure, success, unknown-tool and append-order tests.

Not implemented:

- durable database or filesystem audit persistence;
- Agent orchestration, answer synthesis or autonomous reasoning;
- LLM tool calling, provider changes or dynamic tools;
- P8-6.4 or Phase 9 work.

## 2. Changed Files

Implementation:

- `core/schemas/agent.py`
- `core/agent/__init__.py`
- `infra/storage/agent_audit_store.py`
- `services/agent_audit_service.py`

Tests:

- `tests/test_agent_audit.py`
- `tests/unit/test_imports.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/reports/phase-08/PHASE_8_P8_6_ARCHITECTURE_FREEZE_REPORT.md`
- `docs/reports/phase-08/PHASE_8_P8_6_1_TOOL_REGISTRY_REPORT.md`
- `docs/reports/phase-08/PHASE_8_P8_6_2_DETERMINISTIC_PLANNER_REPORT.md`
- this report

## 3. Audit Contract

Schema version:

```text
phase8-agent-audit-v1
```

`AuditEvent` records:

```text
audit_id
request_id
timestamp
principal_ref
role_ref
intent
plan_id
tools_requested
execution_status
failure_status
question_sha256
safe_metadata
```

The frozen execution statuses are:

```text
PLANNED
SUCCESS
FAILURE
REFUSED
UNKNOWN_TOOL
```

Planned and successful events cannot carry a failure status. Failure,
refusal and unknown-tool events require a bounded failure code.

The earlier internal `ToolAuditMetadata` projection now carries the separate
`phase8-agent-tool-audit-v1` version so the formal append-only event has one
unambiguous wire schema.

## 4. Storage Boundary

`AgentAuditStore` is a minimal protocol with two operations:

```text
append(event)
events()
```

`InMemoryAgentAuditStore` stores events in append order and returns an
immutable tuple snapshot. It exposes no update, delete, clear or durable
persistence operation. The storage boundary has no filesystem, database,
shell, network or provider dependency.

Audit append failure is raised as `AUDIT_UNAVAILABLE`. A later AgentService
must fail closed and must not return a successful response without an
append-confirmed event.

## 5. Metadata Sanitization

Only this bounded metadata allowlist can be retained:

```text
duration_ms
fallback_used
policy_version
registry_version
report_generation_status
row_count
tool_version
```

Unknown fields, secrets, credentials, raw user payloads, raw tool data,
provider output, prompt text, database paths and filesystem paths are
dropped. String values must remain short opaque references; numeric and
boolean values are type- and range-checked.

## 6. Integration

`AgentAuditService.record_plan()` accepts the reviewed `AgentPlan` and
`ToolExecutionContext`, derives a deterministic opaque plan ID and records
the intent, tool identity and question SHA256 without retaining the raw
question or plan arguments.

`record_tool_result()` projects an existing `ToolResult` into success,
refusal or failure status and safe metrics without copying its `data`
payload. `record_unknown_tool()` records a bounded unknown-tool attempt as
`UNKNOWN_TOOL` / `TOOL_NOT_FOUND`.

## 7. Validation

Focused:

```text
python -m pytest tests/test_agent_audit.py tests/test_agent_planner.py tests/test_agent_tool_registry.py tests/unit/test_imports.py -q
124 passed
```

Full repository:

```text
python -m pytest -q
589 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skipped test is the existing optional Torch evaluation test because Torch
is not installed on this host.

## 8. Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-6.3-G1 | `phase8-agent-audit-v1` and immutable `AuditEvent` are implemented | PASS |
| P8-6.3-G2 | Append-only store abstraction preserves order and exposes no mutation API | PASS |
| P8-6.3-G3 | Required request, plan, tool, status, failure and timestamp fields are recorded | PASS |
| P8-6.3-G4 | Metadata sanitization rejects secrets, payloads, provider output, credentials and paths | PASS |
| P8-6.3-G5 | Success, failure, refusal and unknown-tool events are recorded safely | PASS |
| P8-6.3-G6 | Planner integration records plan identity without raw questions or arguments | PASS |
| P8-6.3-G7 | Deterministic serialization and append-only behavior are tested | PASS |
| P8-6.3-G8 | P8-5 checkpoint tag and frozen contracts remain unchanged | PASS |

## 9. Frozen Compatibility

- `phase8-report-v1`: unchanged.
- `SafetyReportGroundingValidator`: unchanged.
- `TemplateFallback`: unchanged.
- P8-5 provider transport and trust boundary: unchanged.
- `phase-8-provider-pipeline-complete`: unchanged.
- Model, dataset, training, inference and mapping identities: unchanged.
- Charter body: unchanged.

## 10. Known Limitations

- Audit persistence is process-local and non-durable by authorization.
- `AgentService` orchestration and the final success/failure transaction
  boundary remain unimplemented.
- No real LLM tool call, provider call or Agent runtime execution is
  performed by this slice.
- P8-6.4 design-only architecture freeze passed human review; P8-6.4.1
  through P8-6.4.3 later implemented and reviewed the planner adapter and
  AgentService orchestration. Phase 9 has not started.

## 11. Final State

```text
P8-6.1: HUMAN REVIEW PASS
P8-6.2: HUMAN REVIEW PASS
P8-6.3: HUMAN REVIEW PASS
P8-6.4: ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS
P8-6.4.1 through P8-6.4.3: HUMAN REVIEW PASS
Agent implementation checkpoint: RELEASED
Phase 9: NOT STARTED
```

No commit, tag or push was performed. P8-6.3 subsequently received human
review PASS. P8-6.4 through P8-6.4.3 were subsequently reviewed, and the
reviewed implementation was published under interim checkpoint tag
`phase-8-controlled-agent-complete`.
