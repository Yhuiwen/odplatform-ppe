# Phase 8 Final Integration Architecture

Status: `PHASE 8 FINAL INTEGRATION ARCHITECTURE: FROZEN / HUMAN REVIEW PASS`

Date: 2026-09-24

Repository path: `docs/designs/phase-08/PHASE_8_FINAL_INTEGRATION_ARCHITECTURE.md`.

Checkpoint base:

- Commit: `56c0f49095c7b4ad39f273e0884652daad26a19f`
- Branch: `main`
- Tag: `phase-8-controlled-agent-complete`
- Tag object: `ca46c884b29783892bdaa002e6a40efa491a34e5`

This document is design-only. It does not implement an Agent API, change the
Streamlit pages, call a provider, load a model, mutate events or start Phase 9.

## 1. Authority and Scope

The locked Charter goals in scope are M-021, M-022, M-023 and the relevant
Phase 8 portion of M-024. ADR-023 and the reviewed P8-6 architecture remain
authoritative for trust, tools, permissions, planning, grounding and audit.

The final integration layer has one purpose:

```text
Authenticated user workflow
-> application API boundary
-> existing AgentService
-> existing validated plan and static ToolRegistry
-> existing read-only analytics/query/report services
-> append-only Agent audit
-> UI-safe structured result
```

The integration layer may compose existing services. It must not redesign the
Agent, add tools, change a frozen contract or create a second execution path.

## 2. Non-Goals

This design does not authorize:

- a public REST, GraphQL, WebSocket or RPC service;
- an authentication system or identity database;
- durable Agent audit storage;
- Agent memory, autonomous loops or multi-step planning;
- provider-native tool calling or dynamic tools;
- direct SQLite access from the API or UI;
- raw evidence, filesystem or shell access from the Agent;
- event mutation, alert actions or compliance overrides;
- new provider, Agent framework or model dependencies;
- changes to Phase 4 through Phase 7 behavior;
- Phase 9 integration and delivery work.

The phrase "Agent API" in this document means a typed in-process application
boundary under `services/`. It does not mean a new network service.

## 3. Current Assets and Missing Integration Surface

| Area | Current state | Final integration requirement |
| --- | --- | --- |
| Agent orchestration | `services/agent_service.py` accepts `AgentRequest` and returns `AgentResult` | Call it through a typed application facade; do not expose it directly to page code |
| Planner | `services/llm_planner_adapter.py` plus deterministic fallback | Reuse unchanged |
| Tool execution | Static four-tool `ToolRegistry` with deny-by-default permissions | Remain the only execution point |
| Analytics/query | `SafetyAnalyticsService` and `EventQueryService` | Reuse unchanged through registered tool handlers |
| Report | Provider-first `ReportService` with grounded `TemplateFallback` | Reuse unchanged; report page must display generation path and degradation |
| Audit | Append-only process-local `AgentAuditService` | Persist for the process/session lifetime; durable storage remains a known limitation |
| Web | `web/pages/6_AI报告.py` and `web/pages/7_AI助手.py` are placeholders | Future pages may be wired only through the application facade |

The future implementation targets are expected to be:

```text
services/agent_api_service.py
web/agent_support.py
web/pages/6_AI报告.py
web/pages/7_AI助手.py
tests/test_agent_api.py
tests/test_agent_web_boundary.py
tests/integration/test_phase8_final_integration.py
```

These paths are an implementation plan, not created or authorized by this
freeze.

## 4. Agent API Boundary

### 4.1 Boundary Name and Responsibility

The future boundary is `AgentApplicationService`.

It is responsible for:

1. accepting a typed caller request without allowing caller-selected tool,
   role, capability, provider or audit identities;
2. obtaining trusted identity from a deployment-owned
   `TrustedIdentityProvider`;
3. constructing the existing immutable `AgentRequest`;
4. calling `AgentService.execute()` exactly once;
5. projecting the existing `AgentResult` into a bounded UI-safe view;
6. mapping domain outcomes to presentation states without changing the
   underlying result contract.

It is not responsible for planning, permission decisions, tool lookup,
analytics, report generation, grounding or audit writes. Those remain with
their existing services.

### 4.2 Proposed Application Contract

The future application request is separate from the frozen domain request:

```text
phase8-agent-api-v1

request_id       server-generated opaque request identity
operation        ASK | GENERATE_REPORT
question         bounded UTF-8 text
requested_period optional inclusive UTC interval
filters          optional supported event filters
```

`operation` selects a user-facing workflow, not a tool. A report-page request
may use the server-owned fixed question for report generation, but the existing
deterministic planner and validator still determine and validate the resulting
intent. The caller may not submit `tool_name`, `tool_version`, `arguments`,
`role`, `capabilities`, `principal_ref` or an audit ID.

The future application response is a projection, not a new replacement for
`phase8-agent-result-v1`:

```text
request_id
audit_id
status
presentation_state
answer
facts
metrics
event_refs
evidence_refs
report
safe_error
provider_status
degraded
```

The projection may omit internal fields but may not repair, reinterpret,
strengthen or replace an `AgentResult`.

### 4.3 Trusted Identity

`TrustedIdentityProvider` is a deployment-owned boundary:

```text
browser/session context
-> TrustedIdentityProvider.resolve()
-> principal_ref + role + capabilities
```

Rules:

1. Principal, role and capabilities never come from the question, form data or
   provider output.
2. Unknown, missing or unauthenticated identity fails closed before
   `AgentService.execute()`.
3. A local demo identity is allowed only in an explicitly labeled local demo
   mode and must never be selected silently in a shared deployment.
4. Provider invocation remains a separately granted `provider:invoke`
   capability.
5. The UI may display a role label, but it may not edit or elevate it.

### 4.4 UI-Safe Outcome Mapping

| Agent outcome | Presentation state | Data released |
| --- | --- | --- |
| `ANSWERED` | `success` | Structured facts, metrics, references and optional grounded report |
| `INSUFFICIENT_DATA` | `empty` | Zero/empty structured result and audit ID |
| `OUT_OF_SCOPE` | `out_of_scope` | Safe answer and audit ID only |
| `REFUSED` | `refused` | Safe refusal code and audit ID only |
| `TOOL_ERROR` | `tool_error` | Safe error code/message and audit ID only |
| `AUDIT_UNAVAILABLE` | `audit_unavailable` | Blocking error and audit ID if one exists; no successful data |

The API must not return:

- raw planner candidates, prompts or provider responses;
- provider schema diagnostics beyond the existing sanitized public error;
- raw SQL, database rows or filesystem paths;
- evidence bytes or absolute snapshot paths;
- credentials, environment values or authorization headers;
- provider chain-of-thought or internal tracebacks.

## 5. Web Integration Boundary

### 5.1 Current Boundary

ADR-022 requires Streamlit pages to call services only. Before implementation,
the two Phase 8 pages raised `NotImplementedError`. They are now implemented
only through the approved `web.agent_support` facade; this status update does
not widen the frozen architecture.

The implemented import direction is:

```text
web/pages/6_AI报告.py
web/pages/7_AI助手.py
-> web/agent_support.py
-> services/agent_api_service.py
-> services/agent_service.py
-> core/agent/tool_registry.py
-> existing read-only services
```

Page code must not import:

```text
sqlite3
infra.database.*
infra.llm.*
core.agent.tool_registry
services.agent_tool_service
services.agent_service
planner/candidate parser modules
inference/tracking/association/compliance modules
```

`web/agent_support.py` is the composition root. It builds the existing
`EventQueryService`, analytics/context/report services, `AgentToolService`,
`LLMPlannerAdapter`, `AgentAuditService` and `AgentApplicationService` in the
same dependency order already used by the Agent implementation.

### 5.2 Session and Rerun Policy

- The composition is session-scoped, using `st.session_state`, consistent
  with the existing dashboard and monitoring support modules.
- A request executes only after an explicit form submission or button action.
  Streamlit reruns must not re-execute the last request.
- A server-generated request ID is created once per submitted action.
- The current process-local audit store persists only for the session/process.
  Restart durability is not claimed.
- Rebuilding the composition must not silently replace a session audit store
  while a result is displayed.

### 5.3 AI Report Page

The future AI report page may provide:

- reporting-period controls;
- supported event type and status filters;
- a generate action;
- report generation path, degraded state and grounding status;
- structured summary, findings, risks, recommendations, limitations and
  evidence references;
- the Agent audit ID;
- verified evidence links through the existing safe reference/viewer path.

The page must not:

- select a provider, model or API key;
- invoke `ReportService`, `SafetyLLMClient` or a transport directly;
- display raw provider output or hidden diagnostics;
- claim provider success when `generation_path` is `TEMPLATE_FALLBACK`;
- claim grounding if the structured report is unavailable.

### 5.4 AI Assistant Page

The future AI assistant page may provide:

- a bounded natural-language question field;
- approved period and event filters;
- a submit action;
- an answer summary with structured facts, metrics, event references and
  evidence references;
- status, safe error and audit ID.

The page may not expose tool selection, raw plan arguments, arbitrary SQL,
filesystem paths, mutation actions or provider controls. Forbidden requests
must be presented as refusals and must not be converted into a different tool
call.

### 5.5 Rendering and Evidence

- Structured report and metric content must be rendered from typed fields,
  not by evaluating or executing model output.
- Provider text is not rendered as trusted HTML.
- Evidence is referenced by the existing relative/opaque reference and opened
  through the existing evidence service path.
- Absolute paths, raw image bytes and database handles remain outside the UI
  response.

## 6. End-to-End User Workflow

```text
1. User opens a Phase 8 page.
2. Web composition root builds the read-only service graph.
3. The request is tied to a trusted principal, role and capability set.
4. The page submits only bounded question, period and supported filters.
5. AgentApplicationService constructs AgentRequest.
6. AgentService invokes the planner adapter.
7. The deterministic planner or a validated LLM candidate produces
   phase8-agent-plan-v1.
8. ToolRegistry performs permission and argument enforcement.
9. The selected read-only handler calls the existing analytics, query or
   report service.
10. Report generation uses provider-first validation plus TemplateFallback,
    or the report call may be kept provider-disabled for deterministic demos.
11. Append-only Agent audit records planning and execution outcomes.
12. AgentService returns AgentResult.
13. AgentApplicationService projects the result into UI-safe fields.
14. The page renders structured data, degradation state and audit identity.
```

At no point does the browser, page, question, planner candidate or provider
write to the event database or invoke an upstream detection pipeline.

## 7. Demo Scenario

The final integration demo must be deterministic and must not require a real
provider request.

1. Start the existing Streamlit application with read-only event data.
2. Show the Overview and one persisted event as the source of truth.
3. On the AI report page, select a fixed UTC period and generate a report with
   provider invocation disabled. Require `TEMPLATE_FALLBACK`, `degraded=true`
   and grounded output.
4. On the AI assistant page, ask for a safety summary for the same period.
5. Ask for aggregate event statistics.
6. Ask for one exact event ID and show the structured event reference without
   exposing snapshot bytes or absolute paths.
7. Submit a forbidden mutation request and show `REFUSED` with no tool
   execution.
8. Show the audit ID for each request and explain that audit storage is
   process/session-local in this release.
9. Optionally demonstrate provider success only in a separately authorized
   environment; the standard demo must pass without provider credentials.

The demo must not present a fallback report as provider-validated and must not
present an absent metric as zero.

## 8. Integration Test Plan

### 8.1 API Boundary Tests

- trusted identity is taken only from `TrustedIdentityProvider`;
- question text cannot set or elevate role, capability, principal or tool;
- unknown, missing and unauthenticated identities fail closed;
- `ASK` and report-page workflows still pass through the unchanged planner and
  registry;
- all four supported intents execute only through `ToolRegistry`;
- forbidden and mutation-like requests return refusal without execution;
- provider-disabled report generation returns grounded `TEMPLATE_FALLBACK`;
- provider failure and invalid provider output reuse the existing fallback;
- `AUDIT_UNAVAILABLE` releases no successful data;
- response serialization is deterministic and bounded.

### 8.2 Web Boundary Tests

- page modules import only the approved web support facade;
- pages do not import SQLite, provider transports, tool handlers, planner
  internals or upstream inference modules;
- Streamlit reruns do not re-execute a submitted request;
- UI projection maps all six Agent outcomes without widening data release;
- report degradation, generation path and grounding status are displayed
  accurately;
- evidence references remain relative/opaque;
- no raw provider response, secret, absolute path or evidence byte appears in
  page data.

### 8.3 End-to-End Fixture Test

Use a temporary SQLite database and verified test snapshot metadata:

```text
persisted event fixture
-> EventQueryService
-> AgentRequest
-> summary/statistics/detail/report operations
-> AgentResult
-> UI-safe projection
-> audit identity assertions
```

The fixture test must verify:

- each operation keeps the original event identity;
- summary, statistics and detail values agree with the event query service;
- provider-disabled report output is grounded and degraded;
- one forbidden request produces no tool execution;
- success, refusal, failure and fallback outcomes produce audit records;
- no event, snapshot or upstream pipeline state is mutated.

### 8.4 Regression Gates

Final integration implementation must run:

```text
python -m pytest -q
python -m compileall -q .
git diff --check
```

It must also verify that frozen contracts, model, dataset, training,
inference and released Phase 7 tags remain unchanged. No unit or integration
test may issue a real provider or model request.

## 9. Deployment Considerations

### 9.1 Supported Deployment Shape

The first deployment remains a single-process Streamlit application with an
in-process Agent service graph. A separate web API or worker is not part of
this design.

For a shared deployment:

- place Streamlit behind the organization's TLS/authentication boundary;
- supply a real `TrustedIdentityProvider`;
- disable local demo identities;
- keep the event database and snapshot root read-only to the Agent path;
- use environment variables or a secret manager for provider credentials;
- bound concurrent requests and request size;
- record operational failures without secrets.

### 9.2 Configuration and Secrets

- `configs/llm.yaml` stores environment-variable names and non-secret policy
  only.
- `PPE_LLM_ENDPOINT`, `PPE_LLM_MODEL` and `PPE_LLM_API_KEY` remain runtime
  environment values.
- No provider request is required for deployment health or deterministic demo.
- Provider planning remains disabled unless explicitly configured and
  authorized.

### 9.3 Availability and Failure Isolation

- A report/provider failure must not affect the monitoring pipeline.
- Audit append failure returns `AUDIT_UNAVAILABLE`, not an unaudited success.
- Database or query failure returns a bounded Agent tool error.
- An unavailable provider can degrade to the existing local report fallback.
- Streamlit page startup must not load a model or contact a provider.

### 9.4 Known Deployment Limitations

- Agent audit is process/session-local and is lost on restart.
- No durable audit store or retention policy is implemented.
- No production authentication adapter is implemented.
- No remote/multi-user API hardening beyond the service boundary is claimed.
- No long-running Agent worker or autonomous process exists.

## 10. Security Review

### 10.1 Threat Model

| Threat | Control |
| --- | --- |
| User asks to delete or mutate an event | Deterministic precheck and prohibition return `REFUSED`; no mutation tool exists |
| User prompt claims a higher role | Role and capabilities come only from `TrustedIdentityProvider` |
| UI submits a tool name or arbitrary arguments | API request rejects those fields; planner and registry own intent/tool selection |
| Provider returns a dynamic or unknown tool | Candidate validation rejects it before registry access |
| Provider output contains fabricated facts | Strict report schema plus unchanged grounding validator rejects it |
| Provider output contains SQL, paths or shell text | Candidate/report validation fails closed or keeps data out of the projection |
| UI queries SQLite directly | Composition/import tests reject direct database imports from pages |
| Evidence path leaks to UI/provider | Only relative/opaque references are returned; bytes and absolute paths are excluded |
| Audit append fails | Success is withheld and `AUDIT_UNAVAILABLE` is returned |
| Streamlit rerun repeats an action | Execute only on explicit submission and retain the submitted result in session state |
| Secret appears in logs or response | Environment-only secrets and bounded sanitized errors; no secret fields exist in contracts |

### 10.2 Security Invariants

```text
No request -> no tool execution.
No trusted identity -> no request.
No validated phase8-agent-plan-v1 -> no registry execution.
No registry execution -> no tool result.
No successful audit append -> no successful release.
No grounded report -> no report claim.
No allowlisted read capability -> refusal.
No Phase 9 work -> no final-delivery claim.
```

## 11. Frozen Compatibility

The following remain unchanged by this design:

| Asset or contract | Required state |
| --- | --- |
| `phase8-context-v1` | UNCHANGED |
| `phase8-report-v1` | UNCHANGED |
| `SafetyReportGroundingValidator` | UNCHANGED |
| `TemplateFallback` | UNCHANGED |
| `phase8-agent-plan-v1` | UNCHANGED |
| `phase8-agent-audit-v1` | UNCHANGED |
| `phase8-agent-request-v1` | UNCHANGED |
| `phase8-agent-result-v1` | UNCHANGED |
| Static four-tool `ToolRegistry` | UNCHANGED |
| Deny-by-default `ToolPermissionPolicy` | UNCHANGED |
| `phase-8-controlled-agent-complete` | UNCHANGED |
| Model, dataset, training and inference assets | UNCHANGED |

## 12. Deferred Decisions

The following are intentionally deferred and do not weaken the boundary:

- production authentication and principal provisioning;
- durable audit storage and retention;
- remote API transport and its authentication model;
- report export formats and long-term report retention;
- provider cost, rate and concurrency policy beyond the existing bounded
  transport;
- user-facing localization and visual design of the future pages.

Any change to these decisions requires a separately authorized implementation
or ADR.

## 13. Freeze State

```text
Phase 8 final integration architecture:
FROZEN / HUMAN REVIEW PASS

Agent API boundary:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

Web integration boundary:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

Deterministic E2E demo:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

End-to-end workflow:
FROZEN

Integration test plan:
FROZEN

Deployment and security review:
FROZEN

Implementation:
API AND WEB IMPLEMENTED / HUMAN REVIEW PASS

E2E:
IMPLEMENTED / HUMAN REVIEW PASS

Phase 8:
FINAL RELEASED

Release tag:
phase-8-final-integration-complete

Phase 9:
NOT STARTED
```
