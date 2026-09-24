# Phase 8 P8-6.1 Tool Registry and Permission Layer Report

Status: `P8-6.1 IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`

Date: 2026-09-24

Post-review note: P8-6.1 subsequently received human review PASS. A later,
separately authorized P8-6.2 slice added the deterministic planner. Agent
orchestration, durable audit storage, P8-6.4 and Phase 9 remain unimplemented.
P8-6.2 received human review PASS, and a separate P8-6.3 slice now implements
the non-durable append-only Agent audit boundary.

## 1. Scope

This implementation authorizes only the static, read-only tool registry and
permission layer defined by the P8-6 architecture freeze.

Implemented:

- immutable Agent capability, role, tool, context, result and audit contracts;
- a static registry containing exactly four allowlisted tools;
- deny-by-default role/capability checks before handler execution;
- bounded tool argument validation;
- read-only service adapters that reuse existing services;
- deterministic registry ordering and audit metadata generation.

Not implemented:

- LLM tool calling or provider-native function calling;
- dynamic tool registration;
- append-only Agent audit storage;
- Agent reasoning, answer synthesis or Phase 9 work.

The deterministic planner was not part of P8-6.1 and was implemented later by
the separately authorized P8-6.2 slice.

## 2. Changed Files

Implementation:

- `core/schemas/agent.py`
- `core/agent/__init__.py`
- `core/agent/permissions.py`
- `core/agent/tool_registry.py`
- `services/agent_tool_service.py`

Tests:

- `tests/test_agent_tool_registry.py`
- `tests/unit/test_imports.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- this report

## 3. Static Registry

The registry is constructed only from the frozen descriptors:

```text
get_safety_summary
get_event_statistics
get_event_details
generate_safety_report
```

All entries have effect `READ_ONLY`, one call per request, a finite timeout and
a fixed `1.0.0` tool version. The registry exposes no `register` method and
rejects unknown names, duplicate entries, missing entries, descriptor changes
and version mismatches.

## 4. Permission Model

The policy is deny-by-default:

| Role | Capabilities |
| --- | --- |
| `safety_viewer` | `safety:read`, `statistics:read` |
| `event_viewer` | `events:read` |
| `safety_reporter` | read capabilities plus `reports:generate` |
| `system` | all frozen read/report capabilities, including separate `provider:invoke` |

`provider:invoke` is not implied by `reports:generate`. Forbidden capability
classes such as SQL, filesystem, shell, mutation, evidence deletion, alert
action and compliance override are rejected before a handler can run.

## 5. Service Reuse

The four handlers delegate to existing components:

- `SafetyAnalyticsService`
- `SafetyContextBuilder`
- `EventQueryService`
- `ReportService`

The registry does not duplicate the analytics calculations, report schema,
grounding validator or deterministic fallback. `generate_safety_report` uses
the provider-first path only when an existing provider client and
`provider:invoke` capability are both present; otherwise it uses the existing
validated fallback path.

## 6. Security Boundaries

- Unknown tool names fail before handler execution.
- Tool arguments are restricted to each descriptor's allowlist.
- SQL, path, shell and mutation-like arguments are refused.
- Agent modules do not import `os`, `pathlib`, `shutil`, `sqlite3`, `subprocess`
  or `ctypes`.
- Raw arguments are never copied into audit metadata; only a canonical SHA256
  digest is recorded.
- Successful, denied and failed executions emit bounded audit metadata.
- No provider request, model load, dataset change, training action or Phase 9
  work is performed by this implementation.

## 7. Validation

Focused:

```text
python -m pytest tests/test_agent_tool_registry.py tests/unit/test_imports.py tests/unit/test_placeholders.py -q
99 passed
```

Full repository:

```text
python -m pytest -q
555 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skipped test is the existing optional Torch evaluation test because Torch
is not installed on this host.

## 8. Freeze Compatibility

- `phase8-report-v1`: unchanged.
- `SafetyReportGroundingValidator`: unchanged.
- `TemplateFallback`: unchanged.
- P8-5 provider transport and trust boundary: unchanged.
- `phase-8-provider-pipeline-complete`: unchanged.
- Model, dataset, training, inference and mapping identities: unchanged.
- Charter body: unchanged.

## 9. Known Limitations

- `AgentService` remains a future-phase placeholder; P8-6.1 itself provided no
  planner or natural-language answer path. The later P8-6.2 planner is
  deterministic and still does not synthesize answers.
- The audit sink is not implemented; this slice generates bounded metadata but
  does not persist it.
- Real provider invocation through `generate_safety_report` is not exercised
  by the unit suite.
- Maximum question length, maximum reporting interval and total request
  deadline enforcement remain for later Agent orchestration work.

## 10. Final State

```text
P8-6.1 Static Read-only Tool Registry and Permission Layer:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

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

The later P8-6.4.1 through P8-6.4.3 slices completed and received human review
PASS. The reviewed implementation is recorded by interim tag
`phase-8-controlled-agent-complete`. Do not implement durable audit storage,
memory, autonomous loops, real provider planning calls or Phase 9 without a
new authorization.
