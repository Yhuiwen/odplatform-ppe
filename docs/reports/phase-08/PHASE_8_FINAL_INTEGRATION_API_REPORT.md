# Phase 8 Final Integration API Boundary Report

Status: `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`

Date: 2026-09-24

Checkpoint base:

- Branch: `main`
- Commit: `56c0f49095c7b4ad39f273e0884652daad26a19f`
- Tag: `phase-8-controlled-agent-complete`
- Tag object: `ca46c884b29783892bdaa002e6a40efa491a34e5`

This report records the in-process Agent application boundary only. It does
not issue a provider request, load a model, expose a network API, implement
durable audit storage, start Phase 9 or claim final Phase 8 release.

The subsequent final integration Web and deterministic E2E work passed human
review, and Phase 8 is now `FINAL RELEASED` under
`phase-8-final-integration-complete`.

## 1. Scope

The API boundary implements:

- `phase8-agent-api-v1` request and response contracts;
- trusted identity resolution outside caller-controlled request fields;
- construction of the existing immutable `AgentRequest`;
- one call to the existing `AgentService`;
- bounded projection of `AgentResult` into a UI-safe response;
- deterministic presentation-state and safe-error mapping.

The boundary does not plan, authorize, dispatch, generate reports, write
audit events or access SQLite directly. Those responsibilities remain in the
existing Agent service graph.

## 2. Changed Files

```text
core/schemas/agent_api.py
services/agent_api_service.py
tests/test_agent_api.py
```

## 3. Request Contract

`AgentApiRequest` exposes only:

```text
schema_version
request_id
operation
question
requested_period
filters
```

`operation` is limited to `ASK` and `GENERATE_REPORT`. A report request uses a
server-owned question. Callers cannot submit a tool name, role, capability,
principal, provider, SQL, filesystem path, audit identifier or arbitrary
planner arguments through the application request.

Input validation is bounded and rejects unsupported fields, empty or
oversized questions, non-JSON mappings, unknown operations and malformed
request identities.

## 4. Trusted Identity

`TrustedIdentityProvider` resolves `principal_ref`, `role` and capabilities
outside the caller request. Missing, invalid or failed identity resolution
fails closed before `AgentService.execute()`.

The principal and role are never inferred from question text, form data,
provider output or client-supplied fields. The application API does not
expose the identity provider or its configuration to the browser.

## 5. Execution Boundary

The execution flow is:

```text
AgentApiRequest
-> TrustedIdentityProvider
-> AgentRequest
-> AgentService
-> validated phase8-agent-plan-v1
-> ToolRegistry
-> existing read-only service
-> append-only Agent audit
-> AgentResult
-> AgentApiResponse
```

The API facade neither accepts a raw candidate nor calls a tool handler. Only
the existing `AgentService` and registry path can execute a validated plan.

## 6. Response Projection

`AgentApiResponse` exposes bounded structured data:

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

Non-answered outcomes cannot release facts, metrics, evidence references or a
report. Successful outcomes require an audit identifier and cannot include a
safe error. The projection excludes raw planner candidates, prompts, provider
responses, planner/tool names, audit metadata, SQL, shell commands, absolute
paths and traceback details.

## 7. Presentation Mapping

| Agent outcome | Presentation state |
| --- | --- |
| `ANSWERED` | `success` |
| `INSUFFICIENT_DATA` | `empty` |
| `OUT_OF_SCOPE` | `out_of_scope` |
| `REFUSED` | `refused` |
| `TOOL_ERROR` | `tool_error` |
| `AUDIT_UNAVAILABLE` | `audit_unavailable` |

Unsafe lower-level results are replaced with a bounded `UNSAFE_AGENT_RESULT`
failure. Unsafe error detail is replaced with fixed safe text.

## 8. Tests

`tests/test_agent_api.py` covers:

- successful projection and audit preservation;
- rejection of caller-selected internal fields;
- missing and failed identity paths;
- forbidden requests without tool execution;
- tool failure projection;
- server-owned report questions;
- all six outcome mappings;
- unsafe result and error redaction;
- deterministic response serialization.

Focused validation:

```text
27 passed
```

This count is for the API and Web integration focused set recorded by the
subsequent Web task. The API-only tests are included in that passing set.

## 9. Compatibility

The implementation preserves:

- `phase8-context-v1`;
- `phase8-report-v1`;
- `SafetyReportGroundingValidator`;
- `TemplateFallback`;
- `phase8-agent-plan-v1`;
- `phase8-agent-audit-v1`;
- the static four-tool `ToolRegistry`;
- deny-by-default permissions;
- `phase-8-controlled-agent-complete`.

No model, dataset, training configuration, inference contract or Phase 5/6/7
implementation was changed.

## 10. Limitations

- The API is an in-process application boundary, not a network service.
- Production authentication is not implemented.
- Agent audit remains process/session-local.
- Durable audit storage, memory and autonomous loops are not implemented.
- No real provider planning request is issued by this boundary.
- M-021, M-022 and M-023 remain `待实现` in the locked Charter.

## 11. Final State

```text
Agent API boundary:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

Web integration:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

Deterministic E2E demo:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

Phase 8:
FINAL RELEASED

Release tag:
phase-8-final-integration-complete

Phase 9:
NOT STARTED

Commit:
ASSIGNED AT RELEASE TIME

Tag:
phase-8-final-integration-complete

Push:
PHASE 8 RELEASE PUBLISHED
```
