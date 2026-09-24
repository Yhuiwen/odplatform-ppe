# Phase 8 P8-6.4 LLM-Assisted Agent Planning Architecture

Status: `P8-6.4 ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`

Date: 2026-09-24

Checkpoint base: `phase-8-provider-pipeline-complete`

This document remains a design-only freeze. Separately authorized P8-6.4.1
work implements the strict candidate parser, validator and deterministic
conversion to `AgentPlan`; it does not implement LLM tool calling, provider
integration, AgentService orchestration, tool execution or a change to the
deterministic planner, static tool registry, permission policy, append-only
audit contract or P8-5 report pipeline.

## 1. Authority and Goal

P8-6.4 defines how an optional language model may assist the existing
deterministic Agent planner without gaining execution authority.

The design has four invariants:

1. The language model may propose a candidate only.
2. Deterministic project code validates and canonicalizes every candidate.
3. The existing `ToolRegistry` remains the only tool execution boundary.
4. Failure to understand or validate a request falls back to the deterministic
   planner or a safe refusal.

The target future flow is:

```text
User request
-> AgentService request normalization
-> deterministic precheck and intent classification
-> optional LLM planner candidate
-> strict candidate parser
-> bounded semantic and argument validation
-> deterministic AgentPlan construction
-> ToolRegistry resolution and version enforcement
-> deny-by-default permission verification
-> append-only audit event
-> final non-executable AgentPlan
```

Tool execution remains a later, separate call:

```text
final AgentPlan
-> ToolRegistry.execute
-> permission recheck
-> static read-only tool handler
-> ToolResult
```

## 2. Non-Goals and Prohibitions

P8-6.4 does not:

- implement an LLM planner, provider adapter or Agent orchestration;
- expose tools directly to a provider;
- use provider-native function calling or tool-call APIs;
- let provider output execute a tool, SQL statement, command or file operation;
- add dynamic tools, plugins, remote tool discovery or user-supplied imports;
- replace or weaken the deterministic planner;
- change `phase8-agent-plan-v1`;
- change `phase8-agent-audit-v1`;
- change `phase8-report-v1`, `SafetyReportGroundingValidator` or
  `TemplateFallback`;
- add an Agent framework or provider SDK dependency;
- mutate events, evidence, alerts, compliance decisions or settings;
- enter Phase 9.

The following capabilities remain hard prohibitions:

```text
direct LLM tool execution
dynamic tools
arbitrary SQL
filesystem access
shell execution
event mutation
evidence deletion
alert action
compliance override
```

## 3. LLM Planner Boundary

The language model is an untrusted intent and argument suggester. It is not an
orchestrator, policy authority, permission source, registry or executor.

The deterministic planner remains the authority for:

- detecting forbidden, mutation-like, administration and system-action
  requests before any provider call;
- classifying supported intents when its bounded rules are sufficient;
- mapping an intent to one exact static tool and version;
- validating reporting periods, filters, event IDs, limits and offsets;
- producing the canonical final `AgentPlan`.

The optional LLM candidate may assist only when all of the following hold:

- the deterministic precheck did not classify the request as forbidden;
- a planning provider is explicitly configured and enabled;
- the caller has the existing `provider:invoke` capability;
- the normalized question, candidate response and timeline remain within
  configured bounds.

If deterministic classification already produces a supported intent and tool,
the candidate cannot change that intent or tool. It may propose bounded
arguments only for that same mapped tool. If deterministic classification is
`UNKNOWN`, the candidate may propose one supported intent from the frozen
vocabulary for deterministic validation. A candidate that changes an explicit
supported intent, selects an unknown tool or requests a forbidden outcome is
rejected.

No provider output is an instruction to the AgentService. It is data.

## 4. AgentPlan and Candidate Contracts

### 4.1 Existing Final Plan Contract

The final executable-plan contract remains unchanged:

```text
phase8-agent-plan-v1
```

Required final fields:

```text
schema_version
intent
tool_name
tool_version
arguments
question_sha256
```

Only deterministic project code may construct the final `AgentPlan`. The raw
question is not copied into the plan; only its canonical SHA256 is retained.
The final plan remains non-executable until `ToolRegistry.execute` is called.

### 4.2 New Candidate Contract

The LLM-facing contract is a separate versioned candidate:

```text
phase8-agent-plan-candidate-v1
```

Required fields:

```text
schema_version
request_binding_sha256
proposed_intent
proposed_tool_name
proposed_tool_version
proposed_arguments
reason_code
```

Allowed `reason_code` values must be a closed project-owned enum. The first
implementation should use bounded codes equivalent to:

```text
SUMMARY_REQUEST
STATISTICS_REQUEST
EVENT_DETAIL_REQUEST
REPORT_REQUEST
INSUFFICIENT_CONTEXT
```

The candidate must not contain:

- free-form chain-of-thought or reasoning transcripts;
- raw event rows, evidence bytes or database rows;
- filesystem paths, URLs, SQL, shell fragments or credentials;
- executable code, tool-call envelopes or provider-native function payloads;
- updates to principal, role, capability, policy or registry state.

`request_binding_sha256` binds the candidate to a deterministic canonical
projection of the normalized request and frozen planner contract. It is not a
credential and does not replace request validation.

The candidate is never stored as a final plan and is never passed directly to
the tool registry.

## 5. Plan Validation Flow

Validation is fail-closed and ordered:

### Step 1 - Request normalization

- Normalize whitespace and reject empty or oversized questions.
- Enforce the configured maximum question size.
- Reject invalid principal, role or request identity.
- Never interpret question text as executable instructions.

### Step 2 - Deterministic precheck

- Run the existing deterministic classifier.
- Reject forbidden, mutation, administration and system-action requests
  before any provider call.
- Resolve the deterministic intent and exact tool mapping when possible.

### Step 3 - Optional candidate acquisition

- Call the provider only if planning is enabled and authorized.
- Use one bounded attempt, a finite timeout and a finite response-size limit.
- Send only the normalized question and static planning schema metadata.
- Treat timeout, auth failure, rate limit, transport failure, empty response
  and malformed response as candidate failure, not as authority.

### Step 4 - Strict candidate parsing

- Accept bounded UTF-8 JSON only.
- Reject duplicate keys, non-finite numbers, unknown fields, missing fields,
  wrong schema version, wrong field types and oversized payloads.
- Do not repair malformed output or partially accept a candidate.

### Step 5 - Semantic and argument validation

- Verify the candidate binding and schema version.
- Enforce the frozen intent-to-tool mapping.
- Reject unknown, disabled or version-mismatched tools.
- Reject a candidate that conflicts with a supported deterministic intent or
  tool.
- Validate every argument with the tool descriptor and the existing bounded
  project-owned validators.
- Reject unknown arguments, invalid periods, invalid filters, invalid event
  identities and values outside pagination limits.

### Step 6 - Deterministic plan construction

- Copy only validated intent, tool identity and arguments into a new final
  `AgentPlan`.
- Recompute `question_sha256` and canonical argument identity.
- Never copy provider prose, rationale, confidence or additional fields.

### Step 7 - Registry and permission enforcement

- Resolve the exact tool name and version through `ToolRegistry`.
- Apply `ToolPermissionPolicy` before returning the plan.
- Repeat permission and argument enforcement at execution time.

### Step 8 - Audit

- Append the accepted, rejected, fallback or provider-failure planning outcome
  before releasing a successful plan.
- Fail closed if append-only audit storage is unavailable.

## 6. ToolRegistry Enforcement Point

`ToolRegistry` is the sole execution enforcement point.

Rules:

1. The provider cannot import, resolve or call a tool handler.
2. A candidate cannot bypass registry resolution by naming a handler directly.
3. Only the exact static allowlist is valid:

```text
get_safety_summary
get_event_statistics
get_event_details
generate_safety_report
```

4. Tool names and versions must match the frozen descriptor.
5. Tool effect must remain `READ_ONLY`.
6. A plan may contain one tool call only.
7. `ToolRegistry.execute` rechecks permissions and the closed argument
   allowlist before handler invocation.
8. Unknown tools, dynamic registration and descriptor changes fail closed.

The planner returns a plan. It never returns a `ToolResult`, provider result
object or handler reference.

## 7. Permission Verification

Permission verification remains deny-by-default and occurs twice:

```text
candidate validation
-> ToolPermissionPolicy.authorize()
-> final AgentPlan

execution
-> ToolRegistry.execute()
-> ToolPermissionPolicy.authorize()
-> static handler
```

The candidate cannot:

- declare or elevate a role;
- add capabilities;
- impersonate another principal;
- obtain `provider:invoke` through a tool request;
- alter the static role-to-capability map.

Planning-provider access uses the existing `provider:invoke` capability and is
off by default. A distinct planning capability, if ever required, needs a new
reviewed contract; it must not be silently added here.

The report tool still requires `reports:generate` and separately requires
`provider:invoke` for provider-backed report generation. A planning candidate
does not grant either permission.

## 8. Audit Integration

The append-only audit contract remains `phase8-agent-audit-v1`. This freeze
does not change its fields or status vocabulary.

The future implementation must append planning outcomes without retaining:

- raw prompts or raw provider output;
- chain-of-thought or provider reasoning;
- raw questions by default;
- raw arguments or event data;
- secrets, authorization headers or credentials;
- filesystem or database paths.

Outcome mapping uses the existing statuses:

| Planning outcome | Audit status | Required safe failure code |
| --- | --- | --- |
| Validated final plan released | `PLANNED` | none |
| Forbidden or unauthorized request | `REFUSED` | bounded policy code |
| Candidate proposes unknown tool | `UNKNOWN_TOOL` | `TOOL_NOT_FOUND` |
| Malformed or invalid candidate | `FAILURE` | `INVALID_PLANNER_OUTPUT` |
| Provider unavailable or failed | `FAILURE` | bounded provider code |
| Deterministic fallback plan released | `PLANNED` | none |

When a provider attempt fails but a deterministic fallback plan succeeds, both
the provider failure and the accepted fallback may be represented as separate
append-only events. The audit order must reflect actual occurrence.

If a planner-specific audit field is later required, it must be introduced as
a separately versioned companion contract. `phase8-agent-audit-v1` must not be
silently redefined.

## 9. Provider Failure Handling

Provider failure never blocks or fabricates a final plan.

```text
provider candidate unavailable or invalid
-> deterministic planner fallback
-> validated AgentPlan OR safe refusal
```

Fallback behavior:

- If the deterministic planner produced a valid supported plan, use that plan
  and label the planning path as deterministic in audit metadata.
- If deterministic classification is unknown, return `OUT_OF_SCOPE`.
- If the request is forbidden, return `REFUSED`.
- If required arguments remain invalid, return a structured refusal or
  insufficient-data outcome without executing a tool.
- Do not retry indefinitely and do not escalate permissions after failure.

Planner fallback is separate from report-generation fallback:

```text
planner provider failure
-> deterministic planner or refusal

report provider failure
-> unchanged P8-5 TemplateFallback
```

`TemplateFallback` is not a planner fallback and must not be repurposed as one.
Likewise, a planner candidate must never be treated as a grounded safety
report candidate.

## 10. Invalid Output Fallback

Invalid provider output is rejected before any tool or registry interaction.

Reject:

- malformed JSON or duplicate keys;
- wrong or missing candidate schema version;
- unknown or missing fields;
- non-finite numeric values;
- invalid request binding;
- unsupported intent or tool;
- invalid or unbounded arguments;
- any mutation, SQL, filesystem, shell or external-action request;
- any attempt to change policy, capability or registry state.

There is no repair, fuzzy matching, best-effort coercion or partial plan.
After rejection, only the deterministic planner fallback path may proceed.

## 11. Privacy Boundary

### 11.1 Outbound boundary

The optional planner provider may receive only:

- the bounded normalized user question;
- the frozen candidate schema description;
- the four allowed tool names, versions and bounded argument schemas;
- a request binding digest.

It must not receive:

- event rows, snapshots, evidence bytes or database content;
- audit history or prior tool results;
- filesystem paths, database paths or source labels;
- environment values, credentials, authorization headers or tokens;
- model, dataset, training or inference artifacts.

### 11.2 Inbound boundary

Provider output is untrusted data. Only validated candidate fields may enter
the final plan. Provider prose, reasoning, confidence labels and unknown
fields are dropped before validation and are not persisted.

### 11.3 Storage boundary

- Raw planner prompts and raw provider responses are not persisted.
- The question is retained as a canonical SHA256 by default.
- Candidate and argument hashes are sufficient for deterministic audit
  correlation.
- Secrets remain environment-only and never enter candidate, plan, result or
  audit records.

## 12. Security Failure Conditions

The following conditions are hard failures:

```text
provider attempts direct tool execution
candidate contains a dynamic or unknown tool
candidate contains SQL or a generic query body
candidate contains a filesystem path or shell command
candidate requests event mutation, evidence deletion, alert action or
compliance override
candidate changes principal, role, policy or registry state
registry execution is bypassed
audit append cannot be confirmed
```

No failure may fall back to a more privileged interpretation.

## 13. Frozen Compatibility

The future implementation must preserve:

| Contract or asset | Requirement |
| --- | --- |
| `phase8-agent-plan-v1` | UNCHANGED |
| `phase8-agent-tool-registry-v1` | UNCHANGED |
| `phase8-agent-policy-v1` | UNCHANGED |
| `phase8-agent-audit-v1` | UNCHANGED |
| Deterministic planner | UNCHANGED AND AVAILABLE |
| Static four-tool registry | UNCHANGED |
| Deny-by-default permissions | UNCHANGED |
| `phase8-report-v1` | UNCHANGED |
| `SafetyReportGroundingValidator` | UNCHANGED |
| `TemplateFallback` | UNCHANGED |
| P8-5 provider transport and trust boundary | UNCHANGED |
| `phase-8-provider-pipeline-complete` tag | UNCHANGED |
| Model, dataset, training and inference assets | UNCHANGED |

## 14. Future Implementation Test Plan

A later separately authorized implementation must include tests for:

- the exact candidate schema and deterministic serialization;
- valid candidate acceptance through a deterministic mock provider;
- unknown intent and unknown tool rejection;
- direct tool-call, SQL, filesystem, shell and mutation payload rejection;
- explicit-intent conflict rejection;
- argument, period, pagination and event-ID validation;
- candidate-to-`AgentPlan` canonicalization;
- `ToolRegistry` resolution and version enforcement;
- deny-by-default permission preflight and execution-time recheck;
- provider timeout, auth, rate-limit, empty and malformed response fallback;
- deterministic fallback when the provider is unavailable;
- fail-closed behavior when no valid fallback plan exists;
- append-only planned, refused, failed and fallback audit outcomes;
- privacy assertions for prompts, output, plan, result and audit records;
- zero real provider requests in the unit and integration suite.

No implementation is authorized by this freeze.

## 15. Freeze Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-6.4-AF-G1 | LLM planner boundary and deterministic authority are frozen | PASS |
| P8-6.4-AF-G2 | Candidate and final `AgentPlan` contracts are separated | PASS |
| P8-6.4-AF-G3 | Plan parsing, validation and fallback order are frozen | PASS |
| P8-6.4-AF-G4 | Static `ToolRegistry` remains the only execution enforcement point | PASS |
| P8-6.4-AF-G5 | Deny-by-default permission and provider-access boundaries are frozen | PASS |
| P8-6.4-AF-G6 | Append-only audit integration preserves `phase8-agent-audit-v1` | PASS |
| P8-6.4-AF-G7 | Provider failure, invalid output and privacy boundaries are frozen | PASS |
| P8-6.4-AF-G8 | No implementation, provider request, dependency, frozen-contract or tag change is included | PASS |

## 16. Final State

```text
P8-6.4 LLM-assisted planning architecture:
ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS

P8-6.4.1 plan candidate parser and validator:
HUMAN REVIEW PASS

P8-6.4.2 LLM planner adapter:
HUMAN REVIEW PASS

AgentService:
HUMAN REVIEW PASS

Phase 8 Agent implementation checkpoint:
RELEASED

Deterministic planner:
UNCHANGED

Static ToolRegistry:
UNCHANGED

Append-only audit:
UNCHANGED

P8-5 provider pipeline:
CHECKPOINT RELEASED / UNCHANGED

Phase 9:
NOT STARTED
```

The design is approved. P8-6.4.1 implements only the untrusted candidate
parser, validator and deterministic final-plan conversion. P8-6.4.2
implements only the provider-independent planner request/candidate-client
boundary, strict validator integration, bounded audit metadata and
deterministic fallback; it issues no real provider request and has passed
human review. P8-6.4.3 implements only the typed request/result boundary and
`AgentService` orchestration over validated `phase8-agent-plan-v1` values,
registry-only execution and append-only audit recording. Durable audit
storage, memory, autonomous loops, Phase 8 final integration and Phase 9
require separate authorization. The reviewed implementation is recorded by
interim tag `phase-8-controlled-agent-complete`.
