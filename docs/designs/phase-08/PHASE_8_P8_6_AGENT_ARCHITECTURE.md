# Phase 8 P8-6 Basic Safety Agent Architecture

Status: `P8-6 ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`

Date: 2026-09-24

Checkpoint base: `phase-8-provider-pipeline-complete`

This document is design-only. It does not implement Agent code, LLM tool
calling, a provider SDK, an Agent framework, filesystem access or event
mutation. Separately authorized work now provides the static tool registry,
permission layer and deterministic planner described here. Agent
orchestration, reasoning and later Agent components remain unimplemented.

## 1. Authority and Goal

The locked Charter goal is M-023: an AI Agent must support controlled queries
and analysis over internal platform data and refuse requests that exceed its
permissions or cannot be verified.

P8-6 freezes the Basic Safety Agent boundary:

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

The implementation target for a later authorization is:

```text
core/schemas/agent.py
core/agent/planner.py
core/agent/tool_registry.py
core/agent/permissions.py
services/agent_tool_service.py
services/agent_service.py
infra/storage/agent_audit_store.py
```

At freeze time these paths were planned architecture, not implementation
evidence. Separately authorized P8-6.1 work implements
`core/schemas/agent.py`, `core/agent/tool_registry.py`,
`core/agent/permissions.py` and `services/agent_tool_service.py`. The
separately authorized P8-6.2 slice adds `core/agent/planner.py`. The remaining
full Agent boundary remains unimplemented. A separately authorized P8-6.3
slice now implements the audit event contract, append-only in-memory store
abstraction and `AgentAuditService`.

## 2. Non-Goals

P8-6 does not:

- implement `AgentService`;
- add LLM tool calling or provider-native function calling;
- allow a model to choose tools dynamically;
- add LangChain, LlamaIndex, AutoGen or another Agent framework;
- add arbitrary SQL, shell, filesystem or generic HTTP tools;
- mutate events, status, snapshots, alerts, compliance decisions or settings;
- expose raw evidence bytes, absolute paths, database rows or credentials;
- modify `phase8-report-v1`, `GroundingValidator` or `TemplateFallback`;
- change the P8-5 provider transport or trust boundary;
- treat this freeze as implementation authorization for later Agent
  components or Phase 9.

## 3. Basic Safety Agent Boundary

`AgentService` is the only public orchestration boundary. It accepts a typed
request, applies deterministic routing, invokes at most one read-only tool per
request in the first implementation, and returns a typed result.

The P8-6 planner is deterministic and rule-based. The user question and tool
outputs never become executable instructions. The LLM provider may be used
only inside the `generate_safety_report` tool through the already released
P8-5 report path.

```text
Question
  |
  +-- summary intent ------> get_safety_summary
  +-- statistics intent ---> get_event_statistics
  +-- event intent --------> get_event_details
  +-- report intent -------> generate_safety_report
  |
  +-- unsupported intent --> REFUSED / OUT_OF_SCOPE
```

No multi-step autonomous loop, recursive tool planning or model-directed tool
selection is part of P8-6.

## 4. Contracts

The following names and versions are frozen for the later implementation:

```text
phase8-agent-request-v1
phase8-agent-result-v1
phase8-agent-tool-registry-v1
phase8-agent-policy-v1
phase8-agent-audit-v1
```

### 4.1 AgentRequest

```text
request_id       caller or service generated opaque identifier
principal_ref    allowlisted principal role reference, not a credential
question         bounded UTF-8 user text
requested_period optional reporting interval
filters          optional typed event filters
```

`requested_period` starts and ends at inclusive UTC bounds. The first
implementation must reject an interval that exceeds the configured maximum
range. `filters` may contain only supported event type, status,
tracker-scoped track ID and approved time bounds.

### 4.2 AgentResult

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

The status vocabulary is:

```text
ANSWERED
INSUFFICIENT_DATA
OUT_OF_SCOPE
TOOL_ERROR
REFUSED
AUDIT_UNAVAILABLE
```

`answer` is advisory text only. It cannot serve as the sole source of a
factual claim. Facts, metrics, event references and evidence references remain
structured and are validated against the tool output.

### 4.3 ToolRequest and ToolResult

Every tool has one typed request and one typed result. A handler receives no
raw SQL, filesystem path, shell command, environment mapping or provider
client from the caller.

```text
ToolRequest:
  request_id
  tool_name
  tool_version
  principal_ref
  arguments
  deadline

ToolResult:
  tool_name
  tool_version
  status
  data
  source_refs
  row_count
  duration_ms
  safe_error
```

`arguments` is validated by the tool-specific schema before any service call.
Unknown fields fail closed.

## 5. Static Tool Registry

The registry is an immutable, project-owned allowlist. Dynamic registration,
plugins, user-supplied imports and remote tool discovery are prohibited.

Each `ToolDescriptor` contains:

```text
tool_name
tool_version
description
effect
input_schema
output_schema
required_capabilities
timeout_seconds
max_calls_per_request
enabled
```

The registry contains only:

```text
get_safety_summary
get_event_statistics
get_event_details
generate_safety_report
```

An unknown tool name, duplicate registration, missing version, changed
descriptor or unsupported effect fails closed before handler execution.

## 6. Allowed Tool Contracts

### 6.1 `get_safety_summary`

Purpose: return a bounded, deterministic summary for one reporting interval.

Input:

```text
start_at
end_at
event_type       optional
status           optional
track_id         optional, tracker-scoped only
```

Implementation dependency:

```text
SafetyAnalyticsService.analyze
-> SafetyContextBuilder.build
```

Output contains event totals, type/status/track/day distributions, first and
last occurrence, evidence availability and explicit unavailable fields.
Raw source labels and raw evidence are excluded.

### 6.2 `get_event_statistics`

Purpose: answer aggregate-count questions without loading detailed event
content.

Input:

```text
start_at
end_at
event_type       optional
status           optional
track_id         optional
```

Implementation dependency:

```text
EventQueryService.statistics
```

Output contains total count, counts by type/status/day and earliest/latest
timestamps. Source counts, when exposed, use opaque `SRC-<16 hex>` references
only. The result cannot claim unique-person identity, duration or alert
delivery statistics.

### 6.3 `get_event_details`

Purpose: return bounded event metadata for verification or drill-down.

Input:

```text
event_id         optional exact event identity
start_at         optional when event_id is absent
end_at           optional when event_id is absent
event_type       optional
status           optional
track_id         optional
limit            default 20, maximum 100
offset           non-negative
```

Implementation dependency:

```text
EventQueryService.get_event
EventQueryService.query_events
```

Output contains only the persisted projection:

```text
id
timestamp
track_id
type
confidence
snapshot_ref
status
```

Evidence bytes, absolute filesystem paths, database rows and internal
exception details are excluded.

### 6.4 `generate_safety_report`

Purpose: generate one grounded safety report through the released P8-5 path.

Input:

```text
start_at
end_at
event_type       optional
status           optional
track_id         optional
```

Implementation dependency:

```text
SafetyAnalyticsService.analyze
-> SafetyContextBuilder.build
-> ReportService.generate_provider_or_fallback
```

The tool returns the existing structured report result and generation path.
It does not expose provider candidates, raw provider output, prompts,
credentials or schema diagnostics outside the already sanitized public error
fields.

This tool is the only Agent path that may invoke the configured provider. No
Agent model or tool-call protocol controls that invocation.

## 7. Permission Model

The policy is deny-by-default. A principal receives only explicit
capabilities:

```text
safety:read
statistics:read
events:read
reports:generate
provider:invoke
```

Initial role mapping:

| Principal role | Capabilities |
| --- | --- |
| `safety_viewer` | `safety:read`, `statistics:read` |
| `event_viewer` | `events:read` |
| `safety_reporter` | read capabilities plus `reports:generate`; `provider:invoke` remains separately controlled |
| `system` | all allowlisted read/report capabilities; no mutation capability exists |

Rules:

1. A tool cannot run unless every required capability is granted.
2. `provider:invoke` is not implied by `reports:generate`.
3. Permission checks occur before handler execution and before audit data
   collection beyond the denial record.
4. Principal values, roles and capability lists are validated against
   project-owned enums or allowlists.
5. No role grants SQL, shell, filesystem, event mutation, evidence deletion,
   alert action or compliance override.
6. Permission denial returns `REFUSED` or `OUT_OF_SCOPE` and never silently
   downgrades to a different tool.

If provider invocation is disabled or not granted, `generate_safety_report`
may use the existing deterministic `ReportService.generate()` path and must
label the result `TEMPLATE_FALLBACK`; it must not claim provider validation.

## 8. Execution Policy

- One tool per request for the first P8-6 implementation.
- One request execution is bounded by a total deadline.
- Every tool has a finite per-tool timeout.
- No retry loop, recursive tool call or autonomous multi-step planning.
- Tool input and output sizes are bounded.
- Database reads use existing paginated service contracts.
- Detailed queries default to 20 rows and cap at 100.
- The first implementation must freeze a maximum reporting interval and
  maximum question length in configuration.
- Cancellation or timeout returns a structured failure without partial
  fabrication.
- Tool handlers return project-owned values, never SQLite rows,
  Ultralytics objects or provider response objects.

## 9. Forbidden Capabilities

The following are hard failures, not permission-deniable conveniences:

```text
arbitrary SQL
filesystem access
shell execution
event mutation
snapshot/evidence deletion
alert action
compliance override
model or dataset mutation
training or evaluation execution
dynamic code execution
dynamic tool registration
raw provider tool calling
direct detector/tracker/association invocation
```

An Agent request cannot change event status, delete evidence, send an alert,
modify compliance output, access secrets or inspect raw images.

## 10. Failure Behavior and Fallback Reuse

The Agent has no fail-open path.

| Condition | Result |
| --- | --- |
| Invalid or oversized question | `REFUSED` / `INVALID_REQUEST` |
| Unknown or unsupported intent | `OUT_OF_SCOPE` |
| Missing or invalid period | `REFUSED` / `INVALID_REQUEST` |
| Principal lacks capability | `REFUSED` / `UNAUTHORIZED` |
| Unknown tool or version | `TOOL_ERROR` / `TOOL_NOT_FOUND` |
| Empty but valid result | `INSUFFICIENT_DATA` or `ANSWERED` with zero metrics |
| Tool timeout | `TOOL_ERROR` / `TOOL_TIMEOUT` |
| Database or service failure | `TOOL_ERROR` with a sanitized code |
| Provider unavailable, timeout, rate limit or malformed output | Existing P8-5 fallback path |
| Provider and fallback both fail | `REPORT_UNAVAILABLE`; no report |
| Audit sink unavailable | `AUDIT_UNAVAILABLE`; no successful response |
| Unverifiable factual question | `INSUFFICIENT_DATA` or `REFUSED`; never guess |

Provider failure behavior reuses P8-5 exactly:

```text
provider candidate
-> strict parser
-> unchanged GroundingValidator
-> provider result OR TemplateFallback
-> REPORT_UNAVAILABLE if fallback fails
```

The Agent cannot bypass grounding, replace the fallback or expose a rejected
provider candidate.

## 11. Audit Logging Model

Every accepted, denied and failed Agent request produces one append-only audit
record. The audit model is `phase8-agent-audit-v1`.

Recorded fields:

```text
audit_id
request_id
timestamp
principal_ref
role_ref
question_sha256
intent
tool_name
tool_version
arguments_sha256
policy_version
registry_version
outcome
safe_error_code
row_count
duration_ms
report_generation_status
fallback_used
```

Excluded fields:

```text
raw question text by default
raw provider response
prompt text
context payload
API key or authorization header
absolute filesystem path
evidence bytes
database row dump
raw exception traceback
```

The default storage path for a later implementation is:

```text
artifacts/logs/agent/YYYYMMDD/audit.jsonl
```

It remains Git-ignored. Audit append failure is fail closed: no tool result is
returned as successful unless its audit record is durable. Audit records are
local operational evidence, not external-provider input.

## 12. Security Constraints

### 12.1 Input Security

- The question is untrusted text, never executable instructions.
- Tool selection is deterministic and cannot be changed by prompt content.
- Tool arguments are schema-validated with unknown fields rejected.
- Tool names and versions must exactly match the static registry.
- No user-supplied import path, SQL fragment, command, URL or filesystem path
  is accepted.

### 12.2 Data Security

- Phase 8 reads only through `EventQueryService` and deterministic services.
- Absolute paths, evidence bytes, database files, credentials, environment
  values and raw provider content are excluded.
- `track_id` is always labeled tracker-scoped and never treated as stable
  person identity.
- Source grouping uses opaque references.
- Unsupported metrics remain explicitly unavailable.

### 12.3 Provider Security

- No provider SDK is required by the Agent.
- No LLM tool-call schema is exposed to the provider.
- `generate_safety_report` uses the already frozen report boundary.
- Provider credentials remain environment-only and never enter Agent tool
  arguments, output or audit records.
- Provider failure never delays or writes to the monitoring pipeline.

## 13. P8-5 Compatibility

P8-6 freezes the following compatibility requirements:

| Contract or asset | Requirement |
| --- | --- |
| `phase8-report-v1` | UNCHANGED |
| `SafetyReportGroundingValidator` | UNCHANGED |
| `TemplateFallback` | UNCHANGED |
| P8-5 provider transport and trust boundary | UNCHANGED |
| `phase8-context-v1` | UNCHANGED |
| `phase-8-provider-pipeline-complete` tag | UNCHANGED |
| checkpoint/training/inference/dataset assets | UNCHANGED |

## 14. Future Implementation Test Plan

P8-6 implementation requires focused tests for:

- static registry completeness and duplicate rejection;
- exact allowlist enforcement;
- deny-by-default permissions;
- provider capability separation;
- invalid period, unknown field, oversized input and invalid principal;
- each tool's typed input/output and pagination limits;
- no direct SQL, shell, filesystem or upstream pipeline import;
- event/evidence references remaining grounded;
- provider-disabled fallback labeling;
- provider failure and fallback failure reuse;
- audit record completeness, append-only behavior and fail-closed writes;
- absence of secrets, raw provider content and absolute paths in output;
- compatibility with unchanged P8-5 contracts.

No real provider request is required for unit or integration tests.

## 15. Freeze Gates

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

## 16. Final State

```text
P8-6 architecture freeze: COMPLETE / HUMAN REVIEW PASS
P8-6.1 static registry and permission layer: IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS
P8-6.2 deterministic planner: HUMAN REVIEW PASS
P8-6.3 append-only Agent audit: HUMAN REVIEW PASS
P8-6.4 LLM-assisted planning architecture: ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS
P8-6.4.1 plan candidate parser and validator: HUMAN REVIEW PASS
P8-6.4.2 LLM planner adapter: HUMAN REVIEW PASS
P8-6.4.3 AgentService orchestration: HUMAN REVIEW PASS
Agent reasoning, memory and autonomous loop: NOT IMPLEMENTED
Phase 8 Agent implementation checkpoint: RELEASED
Phase 8 final integration: NOT COMPLETE
Phase 9: NOT STARTED
```

The architecture freeze has passed human review. P8-6.1 through P8-6.4.2 also
have human review PASS. P8-6.4.3 implements AgentService orchestration over
validated plans and has passed human review. The implementation is recorded
by interim tag `phase-8-controlled-agent-complete`. Durable audit storage,
memory, autonomous loops, Phase 8 final integration and Phase 9 require
separate authorization.
