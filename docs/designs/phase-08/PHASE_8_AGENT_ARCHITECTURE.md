# Phase 8 Safety Intelligence Agent Architecture

Status: `P8-0 THROUGH P8-5 COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED; P8-5D HUMAN REVIEW PASS; P8-5P HUMAN REVIEW PASS; P8-6 ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS; P8-6.1/P8-6.2/P8-6.3 HUMAN REVIEW PASS; P8-6.4 ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS; P8-6.4.1/P8-6.4.2/P8-6.4.3 HUMAN REVIEW PASS; P8-FI ARCHITECTURE/API/WEB/E2E HUMAN REVIEW PASS; PHASE 8 FINAL RELEASED`

Date: 2026-09-24

Authority:

- Locked goal: `docs/00_PROJECT_CHARTER.md`, M-021 through M-023.
- Phase goal: `docs/phases/PHASE_08_LLM_AGENT.md`.
- Boundary decision: ADR-023.
- Operational data source: `services/event_query_service.py`.

This document defines architecture and contracts only. It does not implement a
provider, load a model, execute inference, call an external service, install a
dependency, or change any Phase 0 through Phase 7 component.

## 1. Purpose

The Phase 8 Safety Intelligence Agent turns persisted, deterministic compliance
events into explainable safety analytics and structured reports.

The authoritative runtime path remains:

```text
Video
-> Detection
-> Tracking
-> PPE Association
-> Compliance Engine
-> Event Store
-> Safety Analytics / Agent
```

The agent is strictly downstream and read-only. It consumes persisted event
projections and verified evidence metadata. It never participates in deciding
whether a person is compliant.

## 2. Goals

- Calculate deterministic event statistics from the authoritative event store.
- Build a versioned, reproducible context that separates facts, calculated
  metrics, metadata and unavailable fields.
- Support provider-independent LLM report generation behind a typed boundary.
- Produce a structured report whose factual claims reference deterministic
  source records.
- Provide a deterministic local fallback when an LLM provider is unavailable,
  times out, returns malformed output or fails validation.
- Define a Basic Agent boundary that can answer platform questions only through
  a small allowlist of read-only services and tools.
- Isolate report and agent failures from the monitoring pipeline.
- Define privacy, secret-handling, evaluation and change-control rules before
  implementation starts.

## 3. Non-Goals

Phase 8 does not:

- inspect raw frames or images to decide PPE compliance;
- override detection, tracking, association or compliance decisions;
- create, alter, delete or reclassify authoritative compliance events;
- infer stable person identity from `track_id`;
- infer violation duration when the schema has no duration field;
- claim alert-delivery statistics when no delivery telemetry exists;
- send raw evidence images to an external model by default;
- allow arbitrary SQL, shell, filesystem or network tools;
- implement Multi-Agent, autonomous loops or external side effects;
- introduce LangChain, LlamaIndex, AutoGen or another agent framework;
- modify the frozen model, dataset, class mapping, training configuration,
  inference contract or released Phase 5 through Phase 7 behavior.

## 4. Trust and Data-Flow Boundary

```text
Phase 6 event identity
        |
        v
SQLite event store
        |
        v
EventQueryService              read-only authoritative boundary
        |
        v
SafetyAnalyticsService         deterministic calculations only
        |
        v
SafetyContextBuilder           versioned, reproducible context
        |
        v
SafetyLLMClient                provider-independent protocol
        |
        v
StructuredSafetyReport         grounded output contract
        |
        v
ReportService                  orchestration, validation and fallback
```

The Basic Agent is a sibling read path:

```text
User question
-> AgentService
-> allowlisted read-only tools
-> EventQueryService / SafetyAnalyticsService
-> grounded answer or explicit refusal
```

The report and agent paths must never write to the event database or call the
monitoring pipeline.

## 5. Component Responsibilities

| Component | Responsibility | Must not do |
| --- | --- | --- |
| `EventQueryService` | Existing read-only access to events, filters, statistics and evidence verification | Direct SQL from Phase 8, mutation, inference |
| `SafetyAnalyticsService` | Deterministic filtering, grouping, temporal aggregation and evidence-availability accounting | Call an LLM, invent unavailable metrics, modify events |
| `SafetyContextBuilder` | Convert analytics into the versioned `SafetyAnalysisContext` | Include unverified information or raw evidence bytes |
| `SafetyLLMClient` | Provider-independent report-generation protocol | Bind domain services to OpenAI, DeepSeek, Ollama or another provider |
| `ReportService` | Orchestrate analytics, context, LLM call, grounding validation and fallback | Persist or alter compliance events |
| `TemplateFallback` | Deterministic local report generation when LLM output is unusable | Claim that an LLM generated the report |
| `AgentService` | Route a question to read-only allowlisted tools and return a grounded answer or refusal | Execute arbitrary code, SQL, shell commands or external actions |
| `StructuredSafetyReport` | Typed, serializable report with explicit grounding references | Mix recommendations with unsupported factual claims |

## 6. Authoritative Read Contract

Phase 8 reads through `EventQueryService`; it does not import repositories for
new query paths and does not execute SQL directly.

The current `PersistedEvent` projection is:

```text
id
timestamp
track_id
type
confidence
snapshot
status
```

The current read methods are:

```text
query_events
list_events
statistics
get_event
sources
snapshot_events
evidence
```

### 6.1 Contract limitations

The following limitations are part of the frozen Phase 8 design:

- `track_id` is a tracker-scoped identifier. It may group events within one
  runtime scope, but it is not a stable personnel identity.
- There is no persisted violation start/end or duration field. Duration
  statistics are `UNAVAILABLE` unless a future schema extension supplies them.
- There is no persisted alert-delivery telemetry table. Delivery-rate and
  delivery-latency statistics are `UNAVAILABLE`.
- A snapshot path proves that a reference exists, not that the bytes were
  recently decoded. Byte-level integrity remains an explicit evidence check
  outside normal LLM context creation.
- `source` can be a local path or stream label. Its raw value is not sent to an
  external provider by default.
- Missing data is represented as unavailable. It is never silently converted
  to zero, compliant, violation or a fabricated estimate.

## 7. SafetyAnalyticsService Contract

`SafetyAnalyticsService` is deterministic and has no LLM dependency.

### 7.1 Query

The initial analytics query contains:

```text
start_at             required UTC interval start, inclusive
end_at               required UTC interval end, inclusive
track_id             optional tracker-scoped filter
event_type           optional NO_HELMET | NO_VEST | PPE_UNKNOWN
status               optional open | acknowledged | resolved | dismissed
source               optional exact stored-source filter
```

The interval, filter values and generated timestamp are recorded in context
metadata. The future implementation must inject or otherwise freeze the clock
for reproducibility tests.

### 7.2 Supported outputs

The initial deterministic surface is:

- reporting interval;
- total event count;
- event count by violation type;
- event count by status;
- tracker-scoped event counts, explicitly labeled as `track_id` groups;
- UTC day distribution and first/last occurrence;
- evidence-reference availability count;
- source grouping using a local opaque source reference for external contexts;
- deterministic ordered event facts for referenced events.

All counts and metrics have stable metric IDs. The analytics layer does not
perform semantic interpretation; it only calculates and labels values.

### 7.3 Unsupported outputs

The initial context must include explicit unavailable entries for:

- violation duration or average duration;
- unique-person counts;
- cross-camera or cross-session identity;
- alert delivery success, failure, acknowledgement or latency;
- causal attribution not directly represented by stored event data.

Unsupported fields may be added later only through a versioned contract change
with tests and review. They may not be approximated from unrelated fields.

### 7.4 Pagination and completeness

Aggregate methods operate on the filtered authoritative set. Detailed event
facts are read deterministically in bounded pages ordered by
`timestamp DESC, event_id ASC`.

If the context omits detailed events due to a size policy, metadata must record
the selection policy and omitted count. Silent truncation is prohibited. The
aggregate remains based on the full filtered query unless the context explicitly
states otherwise.

## 8. SafetyAnalysisContext Contract

The version identifier is:

```text
phase8-context-v1
```

The context must contain four separate top-level sections:

```text
observed_facts
calculated_metrics
metadata
unavailable_fields
```

### 8.1 Observed facts

Each `EventFact` contains:

```text
fact_id
event_id
occurred_at
type
confidence
track_id
source_ref
status
evidence_available
snapshot_ref
```

Rules:

- `fact_id` is deterministic, for example `EVT:<event_id>`.
- `event_id` is copied exactly from the persisted event.
- `track_id` is included only as a tracker-scoped reference.
- `source_ref` is an opaque local alias when source grouping is needed; the raw
  stored source is excluded from external-provider context by default.
- `snapshot_ref` is the stored relative POSIX path or `null`.
- Snapshot bytes are never embedded.

### 8.2 Calculated metrics

Each `MetricValue` contains:

```text
metric_id
name
value
unit
definition
sample_size
```

Metric values must be derived from the same filtered event set recorded in
metadata. A metric may reference supporting fact IDs but may not introduce
facts absent from the context.

### 8.3 Metadata

Metadata contains:

```text
schema_version
context_version
analytics_version
generated_at
reporting_period
query_filters
event_schema_version
source_of_truth
detail_selection_policy
provider_data_policy
```

### 8.4 Unavailable fields

Each unavailable entry contains:

```text
field
reason_code
reason
```

The LLM may restate an unavailable field as a limitation. It may not infer a
value for it.

### 8.5 Canonical serialization

For a fixed event snapshot, query and clock, context serialization is
reproducible:

- UTF-8 JSON;
- sorted object keys at serialization boundaries;
- no insignificant whitespace in canonical form;
- UTC ISO 8601 timestamps;
- enum values from the frozen event vocabulary;
- deterministic tuple ordering;
- finite numeric values only;
- no runtime object addresses, local absolute paths or provider metadata.

## 9. Provider-Independent LLM Boundary

The conceptual protocol is:

```text
SafetyLLMClient.generate_report(
    context: SafetyAnalysisContext
) -> StructuredSafetyReport
```

The domain and report layers know only this protocol. Provider selection,
authentication, SDK objects, retries and transport details remain inside a
future adapter under `infra/llm/`.

No provider may be selected by changing `SafetyAnalyticsService`,
`SafetyContextBuilder`, `ReportService` or the report schema.

Provider implementation is deferred beyond P8-0.

## 10. StructuredSafetyReport Contract

The report version identifier is:

```text
phase8-report-v1
```

The report contains:

```text
schema_version
reporting_period
generation
executive_summary
key_findings
risk_observations
recommendations
evidence_references
limitations
grounding_status
```

`generation` identifies:

```text
mode                 LLM | TEMPLATE_FALLBACK | REPORT_UNAVAILABLE
degraded             boolean
provider_ref         optional non-secret provider label
failure_code         optional structured failure code
```

### 10.1 Grounded claims

Executive summaries, key findings and risk observations use one shared claim
shape:

```text
claim_id
kind                 observation | risk
statement
fact_refs
metric_refs
event_refs
track_refs
source_refs
evidence_refs
numeric_claims
```

Every factual statement requires at least one valid `fact_ref` or `metric_ref`.
A risk observation may use deterministic metrics and must remain labeled as an
observation or interpretation.

### 10.2 Recommendations

Each recommendation contains:

```text
recommendation_id
action
priority
basis_finding_refs
basis_fact_refs
basis_metric_refs
```

Recommendations are advisory and visibly separate from facts. They may not
introduce a platform measurement, event ID, person identity or compliance
decision.

### 10.3 Evidence references

An evidence reference contains:

```text
event_id
track_id optional
snapshot_ref optional
occurred_at optional
```

Absolute filesystem paths, image bytes, credentials, query strings and provider
errors are prohibited.

## 11. Grounding Policy

The following rules are mandatory for LLM and fallback output:

1. Every event ID in the report must exist in `observed_facts`.
2. Every track ID must belong to the referenced fact or deterministic metric.
3. Every numeric factual claim must match a referenced metric or fact value.
4. Every recommendation must reference at least one valid fact or metric.
5. Unavailable fields may appear only in `limitations` or as explicit missing
   evidence, never as an inferred value.
6. Event and snapshot references must use stable persisted identities.
7. A report with unresolved references, unknown IDs or inconsistent numbers is
   rejected.
8. Rejected LLM output is never returned as a normal report.
9. Template fallback follows the same grounding rules.
10. The report must state that `track_id` is tracker-scoped whenever it groups
    activity by that identifier.

The future implementation must provide a schema and grounding validator before
provider integration is accepted.

## 12. Basic Agent Boundary

The P8-6 architecture freeze supersedes the provisional tool list in this
original P8-0 design. The authoritative Basic Safety Agent contract is
`docs/designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md`.

Allowlisted tools:

```text
get_safety_summary
get_event_statistics
get_event_details
generate_safety_report
```

Every tool is read-only, has a typed request and response, and reuses an
existing deterministic service. Registration is static and project-owned. No
dynamic tool registration, model-directed tool selection, generic SQL tool or
generic network tool is allowed. `generate_safety_report` reuses the unchanged
P8-5 provider-first path and `TemplateFallback`; provider invocation remains a
separate capability.

The agent returns one of:

```text
ANSWERED
INSUFFICIENT_DATA
OUT_OF_SCOPE
TOOL_ERROR
REFUSED
AUDIT_UNAVAILABLE
```

An answer must carry the same fact, metric and evidence references as a report
claim. The agent must refuse:

- requests to change event history;
- requests to override compliance decisions;
- requests for unsupported personal identity;
- requests outside the allowlisted tool surface;
- requests to invent missing measurements;
- requests for raw evidence contents or secrets.

## 13. Failure and Fallback Policy

Failure isolation is mandatory. Phase 8 failures must not raise into or delay
the Phase 0 through Phase 7 monitoring path.

Structured failure codes include:

```text
PROVIDER_UNAVAILABLE
PROVIDER_TIMEOUT
PROVIDER_RATE_LIMITED
MALFORMED_PROVIDER_OUTPUT
REPORT_SCHEMA_INVALID
GROUNDING_VALIDATION_FAILED
EMPTY_EVENT_SET
EVIDENCE_UNAVAILABLE
PARTIAL_DATABASE_DATA
CONTEXT_LIMIT_EXCEEDED
FALLBACK_FAILED
```

Behavior:

| Condition | Required behavior |
| --- | --- |
| Provider unavailable, timeout or rate limit | Attempt deterministic `TemplateFallback`; mark `degraded=true` and preserve the failure code |
| Malformed output or schema failure | Reject provider output and use fallback |
| Hallucinated event/track ID or inconsistent number | Reject provider output and use fallback |
| Empty event set | Produce a valid empty-period report; never invent activity |
| Missing snapshot | Keep the event fact, mark evidence unavailable, omit evidence bytes |
| Partial or unreadable database data | Do not send partial context externally; return a failed report with a bounded error |
| Fallback failure | Return `REPORT_UNAVAILABLE`; do not fabricate a report |
| Agent tool failure | Return `TOOL_ERROR` or `INSUFFICIENT_DATA`; do not retry outside policy |

The fallback report is deterministic and must identify itself as
`TEMPLATE_FALLBACK`.

## 14. Security and Privacy Policy

### 14.1 External-provider allowlist

By default, an external provider may receive only:

- event IDs;
- event timestamps;
- event types;
- confidence values already persisted;
- tracker-scoped IDs with an explicit non-identity label;
- event status;
- snapshot relative reference presence;
- deterministic aggregate metrics;
- reporting interval and filter metadata;
- unavailable-field declarations.

### 14.2 Excluded by default

External providers must not receive:

- image, frame or snapshot bytes;
- local absolute paths;
- SQLite files or database rows;
- raw RTSP URLs with credentials or query strings;
- API keys, tokens, environment values or `.env` contents;
- worker display names or personnel-identifying data;
- server logs or unredacted exception payloads;
- arbitrary user-supplied files or shell output.

### 14.3 Secret handling

- Provider credentials come only from environment variables or an external
  secret manager.
- Secret values never appear in YAML, source, logs, reports, fixtures, CLI
  history or Git.
- Provider errors are redacted before logging or returning them to callers.
- Prompts and contexts are logged only through an explicit debug policy with
  redaction and a bounded retention period.
- No real credential may be added during P8-0.

## 15. Evaluation Strategy

Future implementation gates must cover:

### Deterministic analytics

- exact counts by type, status, day and reporting interval;
- first/last occurrence;
- tracker-scoped grouping without stable-person claims;
- evidence availability;
- empty dataset behavior;
- database and filter errors.

### Context reproducibility

- fixed query plus fixed clock produces byte-equivalent canonical JSON;
- ordering is stable;
- all facts, metrics, metadata and unavailable fields are separated;
- raw source paths and evidence bytes are excluded.

### Schema validation

- valid report round-trips;
- missing fields, unknown enum values and invalid references fail;
- recommendation and observation separation is enforced.

### Grounding and numeric consistency

- fabricated event IDs fail validation;
- unknown track IDs fail validation;
- unsupported numbers fail validation;
- recommendations without evidence references fail validation;
- unavailable duration and alert-delivery metrics cannot become claims.

### Provider and fallback behavior

- provider unavailable, timeout, malformed output, rate limit and schema failure
  trigger deterministic fallback;
- fallback is labeled degraded;
- fallback cannot generate unsupported facts;
- provider exceptions do not escape the report service;
- no network call occurs in unit tests.

### Agent boundaries

- allowlisted tools only;
- out-of-scope and write attempts are refused;
- answers preserve evidence references;
- tool errors remain structured and isolated.

### Mock LLM testing

- deterministic mock providers return fixed structured reports for assertions;
- hallucination fixtures are rejected;
- no live API is required for the standard test suite.

## 16. Dependency and Framework Policy

P8-0 uses design documents only and adds no dependency.

The initial implementation should prefer the Python standard library and
existing project dependencies. A provider SDK may be considered only in a
later task after a separate provider ADR. LangChain, LlamaIndex and other agent
frameworks are not approved for P8-0 and must not be introduced implicitly.

## 17. Proposed Subphase Boundary

| Subphase | Scope | Status |
| --- | --- | --- |
| P8-0 | Architecture and contract freeze | DESIGN COMPLETE / HUMAN REVIEW PASS |
| P8-1 | Deterministic analytics and versioned context schema | IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS |
| P8-2 | Structured report contract and grounding validator | HUMAN REVIEW PASS |
| P8-3 | Deterministic local template fallback | HUMAN REVIEW PASS |
| P8-4 | Provider-independent adapter and strict untrusted output parsing | HUMAN REVIEW PASS |
| P8-5 | Real provider E2E, grounding enforcement and safe fallback | COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED |
| P8-5D | Sanitized provider schema diagnostics | HUMAN REVIEW PASS |
| P8-5P | Provider prompt schema conformance fix | HUMAN REVIEW PASS |
| P8-6 | Basic Agent architecture: deterministic read-only tools, permissions and audit | ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS |
| P8-6.1 | Static read-only tool registry and permission layer | IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS |
| P8-6.2 | Deterministic Agent planner | HUMAN REVIEW PASS |
| P8-6.3 | Append-only Agent audit model and service | HUMAN REVIEW PASS |
| P8-6.4 | LLM-assisted Agent planning architecture | ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS |
| P8-6.4.1 | Plan candidate parser, validator and deterministic conversion | HUMAN REVIEW PASS |
| P8-6.4.2 | LLM planner adapter and deterministic fallback | HUMAN REVIEW PASS |
| P8-6.4.3 | AgentService orchestration over validated plans | HUMAN REVIEW PASS |
| P8-6 checkpoint | Controlled Agent implementation | RELEASED / tag `phase-8-controlled-agent-complete` |

P8-0, P8-1, P8-2, P8-3 and P8-4 received human review. P8-3 implements the
deterministic local fallback and validates it against the frozen report
contract. P8-4 implements the provider-independent request/transport boundary,
strict bounded JSON parsing and candidate-plus-validation orchestration. P8-5
adds one configuration-driven OpenAI-compatible transport behind that boundary
and provider-first orchestration with strict parsing, unchanged grounding
validation, deterministic fallback and `REPORT_UNAVAILABLE`. The human-executed
P8-5R request received a `deepseek-flash` provider response and passed strict
JSON syntax parsing, but `phase8-report-v1` construction was rejected as
`REPORT_SCHEMA_INVALID`; provider grounding was not reached and the unchanged
fallback passed grounding. That historical result is not
`PROVIDER_VALIDATED`. P8-0 through P8-5 are checkpointed by
`phase-8-provider-pipeline-complete`; this is not the final Phase 8 release.
P8-6 has since completed its Basic Agent architecture freeze and received
human review PASS. P8-6.1 implements the static read-only registry and
permission layer and has received human review PASS. P8-6.2 adds the
deterministic planner and has received human review PASS. P8-6.3 adds the
append-only in-memory audit model and service and has received human review
PASS. Durable audit storage, Agent orchestration and reasoning remain not
started. P8-6.4 is design-only and freezes an untrusted LLM candidate, strict
validation, deterministic final-plan construction, registry-only execution,
permission rechecks and deterministic fallback. Separately authorized
P8-6.4.1 through P8-6.4.3 implementations, final integration API/Web/E2E
validation and the final release have since completed and received human
review PASS. Phase 9 remains not started and requires separate authorization.
P8-5D adds bounded sanitized JSON-path diagnostics for future authorized
`REPORT_SCHEMA_INVALID` failures without changing the report schema, grounding
semantics, fallback semantics, provider trust boundary or privacy boundary.
P8-5P derives a compact schema description from the authoritative
`phase8-report-v1` dataclasses and enums and embeds it in
`phase8-provider-prompt-v2`. The provider is now instructed with exact
top-level and nested fields, enums, nullable-but-required values,
closed-object rules, empty-array behavior and provider candidate constants.
This changes request construction only. The report schema, parser, grounding
validator, fallback semantics, context contract and fingerprint remain
unchanged, and prompt compliance is not a security boundary. P8-5P itself did
not issue a provider request. A later separately authorized manual request
following prompt v2 returned `PROVIDER_VALIDATED`: transport, strict JSON,
`phase8-report-v1` and provider grounding all passed with `PROVIDER`,
`degraded=false`, no safe error, no schema diagnostics and fallback not used.
The earlier `REPORT_SCHEMA_INVALID` rejection remains historical evidence.

## 18. Unresolved Decisions

The following are intentionally deferred:

- provider selection and authentication mechanism;
- whether a provider SDK is justified versus a small HTTP adapter;
- production context-size limit and detailed-event selection defaults;
- long-term report storage and retention policy;
- exact fallback template wording and localization;
- whether report export formats are required beyond structured JSON;
- P8-6 implementation values for maximum question length, maximum reporting
  interval and tool latency budgets;
- production principal provisioning and authentication mechanism.

These decisions do not block P8-0 because they do not alter the read-only
boundary, context separation, grounding policy, fallback requirement or
failure-isolation rule.
