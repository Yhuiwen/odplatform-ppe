# Phase 8 P8-6 Architecture Freeze Report

Status: `P8-6 ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`

Date: 2026-09-24

Post-review note: the architecture freeze subsequently received human review
PASS. The freeze task itself remained design-only. A later, separately
authorized P8-6.1 slice implemented the static read-only tool registry and
permission layer and received human review PASS. A subsequent P8-6.2 slice
implemented the deterministic planner and received human review PASS. A
subsequent P8-6.3 slice implemented the append-only Agent audit boundary;
it subsequently received human review PASS. P8-6.4 design-only architecture
freeze was then completed; LLM-assisted planner implementation, durable audit
storage, Agent orchestration and Phase 9 remain unimplemented.

## 1. Repository Identity

- Branch: `main`
- HEAD and `origin/main`: `962ad45880fbc941582235f7177d0af5ad8fb9e1`
- Checkpoint tag: `phase-8-provider-pipeline-complete`
- Tag object: `447e93a5e92a3ede849dfcbd3e3706e79c525b4e`
- Checkpoint commit: `962ad45880fbc941582235f7177d0af5ad8fb9e1`
- Worktree before P8-6 design: CLEAN

## 2. Pre-Read Result

The required governance, phase, architecture, status, risk, reference and
latest worklog documents were read in the mandatory order. The P8-5
checkpoint, frozen provider contracts and current `AgentService` placeholder
were inspected.

No governance conflict was found.

## 3. Scope

This freeze defines:

- Basic Safety Agent boundary;
- deterministic, non-LLM planner boundary;
- static read-only tool registry;
- deny-by-default permission model;
- four allowed tools;
- forbidden capabilities;
- failure and fallback behavior;
- append-only audit model;
- security and privacy constraints;
- compatibility requirements for P8-5.

This task does not implement any part of the Agent.

## 4. Frozen Architecture

```text
User request
-> AgentService
-> request validation
-> permission policy
-> static tool registry
-> read-only tool handler
-> grounded AgentResult
-> append-only audit record
```

The future module map is:

```text
core/schemas/agent.py
core/agent/tool_registry.py
core/agent/permissions.py
services/agent_tool_service.py
services/agent_service.py
infra/storage/agent_audit_store.py
```

## 5. Tool Registry

The only allowed tools are:

```text
get_safety_summary
get_event_statistics
get_event_details
generate_safety_report
```

Tool registration is static and project-owned. There is no plugin, remote
discovery, user-defined import or dynamic registration path.

The registry versions are:

```text
phase8-agent-tool-registry-v1
phase8-agent-request-v1
phase8-agent-result-v1
phase8-agent-policy-v1
phase8-agent-audit-v1
```

## 6. Permission Decision

The Agent uses deny-by-default capabilities:

```text
safety:read
statistics:read
events:read
reports:generate
provider:invoke
```

Provider invocation is separate from report generation. If provider
invocation is unavailable, the report tool must use the deterministic fallback
and must not claim `PROVIDER_VALIDATED`.

No role can grant SQL, shell, filesystem, event mutation, evidence deletion,
alert action or compliance override.

## 7. Failure and Fallback Decision

Agent failures return typed outcomes:

```text
ANSWERED
INSUFFICIENT_DATA
OUT_OF_SCOPE
TOOL_ERROR
REFUSED
AUDIT_UNAVAILABLE
```

`generate_safety_report` reuses the unchanged P8-5 provider-first path:

```text
SafetyAnalyticsService
-> SafetyContextBuilder
-> ReportService.generate_provider_or_fallback
```

Provider failures route to the unchanged `TemplateFallback`; fallback failure
returns `REPORT_UNAVAILABLE` with no report. The Agent cannot bypass strict
parsing or grounding validation.

## 8. Audit Decision

The audit contract is `phase8-agent-audit-v1`, append-only and Git-ignored at:

```text
artifacts/logs/agent/YYYYMMDD/audit.jsonl
```

The audit record contains request/tool identity, policy version, canonical
argument digest, outcome, safe error, row count, duration and report generation
status. It excludes raw questions by default, raw provider responses, prompts,
credentials, absolute paths and evidence bytes.

Audit persistence failure is fail closed: a successful Agent result is not
returned without a durable audit record.

## 9. Security Decision

- The user question is untrusted text, not an instruction to execute.
- Tool selection is deterministic in P8-6; no LLM tool calling is added.
- Tool names, versions and arguments are validated against frozen schemas.
- No direct SQL, repository, filesystem, shell or generic network access is
  available to Agent tools.
- Evidence bytes and absolute paths are excluded.
- `track_id` remains tracker-scoped.
- Unavailable metrics remain unavailable and cannot be inferred.

## 10. Frozen Compatibility

| Contract or asset | Result |
| --- | --- |
| `core/schemas/safety_report.py` | MATCH / UNCHANGED |
| `services/safety_report_grounding_validator.py` | MATCH / UNCHANGED |
| `infra/llm/fallback.py` | MATCH / UNCHANGED |
| `phase8-report-v1` | UNCHANGED |
| Provider trust boundary | UNCHANGED |
| `phase-8-provider-pipeline-complete` tag | UNCHANGED |
| checkpoint/training/inference/dataset assets | MATCH |
| Charter protected body | UNCHANGED / EMPTY DIFF |

## 11. Validation

This design-only change is validated with:

```text
python -m pytest -q
539 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skipped test is the existing optional Torch evaluation test because Torch
is not installed on this host. Final verification is rerun after documentation
synchronization.

## 12. Gate Results

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-6-AF-G1 | Basic Safety Agent boundary and deterministic planner are frozen | PASS |
| P8-6-AF-G2 | Static read-only tool registry is frozen | PASS |
| P8-6-AF-G3 | Deny-by-default permission model is frozen | PASS |
| P8-6-AF-G4 | Four allowed tool contracts are complete | PASS |
| P8-6-AF-G5 | Forbidden capabilities are explicit | PASS |
| P8-6-AF-G6 | Failure and P8-5 fallback reuse are frozen | PASS |
| P8-6-AF-G7 | Audit and security constraints are frozen | PASS |
| P8-6-AF-G8 | No implementation, dependency, frozen-contract or tag change is included | PASS |

## 13. Known Limitations

- The P8-6 architecture freeze task was design-only and introduced no Basic
  Agent behavior. The separately authorized P8-6.1 slice implements only the
  static read-only tool registry and permission layer, and the P8-6.2 slice
  adds only the deterministic planner. The P8-6.3 slice adds only the
  append-only in-memory audit event, store abstraction and service.
- No integration or runtime evidence exists for the Agent.
- The P8-6.2 deterministic intent parser does not provide general
  natural-language understanding or answer synthesis.
- Whether a read-only query with no results should be `ANSWERED` with zero
  values or `INSUFFICIENT_DATA` remains an implementation-level contract to
  freeze in the P8-6 implementation task.
- Maximum question length, reporting interval and tool latency budget are
  required implementation settings but are not implemented here.
- M-023 remains `待实现`.

## 14. Final State

`P8-6 ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`

The freeze task changed no code, dependency, provider request, model, dataset,
training asset or configuration. Later separately authorized P8-6.1 and
P8-6.2 slices implemented the static registry, permission layer and
deterministic planner; both received human review PASS. P8-6.3 implements the
append-only Agent audit boundary and has received human review PASS. P8-6.4
freezes the LLM-assisted planning architecture and has received human review
PASS. P8-6.4.1 through P8-6.4.3 subsequently implemented and reviewed the
candidate validator, planner adapter and AgentService orchestration. Durable
audit storage and Phase 9 remain not started and require a new authorization.
