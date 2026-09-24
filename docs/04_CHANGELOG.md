# Changelog

## 2026-09-24 - Phase 8 Final Integration Release

- Synchronized Phase 8 final integration documentation and reports to
  `FINAL RELEASED`; Phase 9 remains `NOT STARTED`.
- Released the reviewed API, Web / Streamlit and deterministic E2E
  integration under annotated tag `phase-8-final-integration-complete`.
- Preserved the interim tag `phase-8-controlled-agent-complete` and all
  historical provider, schema and checkpoint evidence.
- Final validation: `667 passed, 1 skipped`; `compileall` PASS;
  `git diff --check` PASS. Frozen contracts, model, dataset, training and
  inference hashes remain unchanged.
- No detection, tracking, association, compliance, model, dataset, training
  or Phase 9 change is included.

## 2026-09-24 - Phase 8 Final Integration E2E Demo

- Added a deterministic fixture-driven E2E demo for the reviewed Phase 8
  final integration path:
  `Web facade -> AgentApiService -> AgentService -> ToolRegistry -> audit -> UI projection`.
- Added the bounded input and expected-result fixtures plus an integration
  test that validates normal summary, provider-disabled grounded report
  fallback, forbidden-request refusal and safe UI projection output.
- The demo uses a temporary in-memory SQLite database, fixed audit/context
  clocks, deterministic tool timing, no provider client and no model load.
  It preserves the source event and snapshot identity without mutation.
- Focused E2E validation passed (`6 passed`); the combined E2E/structure/import
  slice passed (`94 passed`); the full repository gate passed
  (`667 passed, 1 skipped`); `compileall` and `git diff --check` passed.
- The Web / Streamlit integration is now `HUMAN REVIEW PASS`. The E2E demo is
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`; Phase 8 remains IN PROGRESS
  and Phase 9 remains NOT STARTED.
- No model, dataset, training, inference, detection, tracking, association,
  compliance, provider request, commit, tag or push was changed or performed.

## 2026-09-24 - Phase 8 Final Integration API and Web / Streamlit

- Added `phase8-agent-api-v1` request/response contracts and
  `AgentApplicationService` as the typed in-process boundary over the
  unchanged `AgentService`.
- Added deployment-owned `TrustedIdentityProvider` resolution, bounded
  request validation and UI-safe projection for all six Agent outcomes.
- Added `web/agent_support.py` as the only Web composition root, using the
  existing analytics, query, report, grounding, fallback, registry, planner
  and append-only audit services with `provider_client=None`.
- Replaced the AI report and Safety Assistant placeholders with bounded
  Streamlit pages and added both to navigation.
- The page data surface is exactly `answer`, `summary`,
  `evidence_references`, `recommendations` and `safe_status`. Pages import
  only the approved Web facade and expose no planner, registry, candidate,
  provider, raw audit, SQL, shell, absolute path or traceback data.
- Added API, Web-boundary and persisted-event integration tests. Focused
  validation passed (`27 passed`); full repository validation passed
  (`660 passed, 1 skipped`), `compileall` PASS and `git diff --check` PASS.
- The API boundary is `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`; the
  Web / Streamlit integration subsequently received `HUMAN REVIEW PASS`.
  Phase 8 remains IN PROGRESS and Phase 9 remains NOT STARTED.
- No model, dataset, training, inference, provider request, durable audit
  store, memory, autonomous loop, commit, tag or push was added.

## 2026-09-24 - Phase 8 Agent Implementation Checkpoint Release

- Recorded P8-6.1 through P8-6.4.3 as `HUMAN REVIEW PASS`.
- Published the controlled Agent implementation checkpoint as the interim
  annotated tag `phase-8-controlled-agent-complete`.
- Verified that only Phase 8 Agent schemas, planner/registry/permission/audit
  services, tests, architecture documents, reports and status documentation
  were included.
- Confirmed no real provider planning request, durable audit storage, memory,
  autonomous loop, model, dataset, training, inference or Phase 9 change was
  included.
- Validation: full repository gate PASS; `compileall` PASS;
  `git diff --check` PASS.
- This is not the Phase 8 final product release and does not authorize Phase
  9.

## 2026-09-24 - Phase 8 P8-6.4.3 AgentService Orchestration

- Added the immutable `phase8-agent-request-v1` and
  `phase8-agent-result-v1` contracts with bounded request identity, trusted
  role/capability context, structured facts, metrics, event/evidence
  references, optional report content and bounded safe errors.
- Replaced the `AgentService` placeholder with orchestration that accepts only
  a typed request, obtains a `phase8-agent-plan-v1` through the existing
  `LLMPlannerAdapter`, and executes only through `ToolRegistry.execute`.
- Preserved deterministic planner fallback and deny-by-default permissions;
  provider candidates are never passed directly to the registry.
- Added append-only audit recording for planner failures, validated plan
  release, tool refusal/error and successful execution. A tool-result audit
  append failure returns `AUDIT_UNAVAILABLE` without releasing a successful
  response.
- Added focused tests for deterministic and LLM-planner success, fallback,
  forbidden requests, tool failure, missing planner audit, audit fail-closed,
  empty results and result serialization.
- P8-6.4.2 is now `HUMAN REVIEW PASS`; P8-6.4.3 is
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`. Durable audit storage,
  memory, autonomous loops, real provider planning requests and Phase 9
  remain not implemented.
- Validation: `632 passed, 1 skipped`; `compileall` PASS;
  `git diff --check` PASS. No commit, tag or push was performed.

## 2026-09-24 - Phase 8 P8-6.4.2 LLM Planner Adapter

- Added a provider-independent `phase8-agent-planner-request-v1` request
  contract and deterministic request builder containing only normalized
  question text, static candidate/tool schema metadata and the request
  binding digest.
- Added an injected `LLMPlannerCandidateClient` boundary returning untrusted
  candidate bytes. The boundary contains no network transport, provider SDK,
  provider-native tool calling or dynamic tool discovery.
- Added `LLMPlannerAdapter`, which makes one optional candidate attempt only
  when `provider:invoke` is allowed, then routes all output through the
  existing strict parser/validator before returning `phase8-agent-plan-v1`.
- Invalid candidates and provider failures fall back to the unchanged
  deterministic planner. Forbidden candidate capabilities are refused
  without privilege escalation. No path calls `ToolRegistry.execute`.
- Added bounded audit events for validated, refused, unknown-tool, invalid
  and provider-failure outcomes without retaining questions, candidate
  payloads, provider output, paths or credentials.
- P8-6.4.1 is now `HUMAN REVIEW PASS`; P8-6.4.2 subsequently received
  `HUMAN REVIEW PASS`. No real provider request,
  AgentService, tool execution, commit, tag or push was performed.

## 2026-09-24 - Phase 8 P8-6.4.1 Plan Candidate Parser and Validator

- Added the immutable, untrusted `phase8-agent-plan-candidate-v1` schema and
  closed reason-code vocabulary without changing `phase8-agent-plan-v1`.
- Added a bounded strict UTF-8 JSON parser that rejects malformed input,
  duplicate keys, non-finite numbers, unknown/missing fields, oversized
  values and unsupported schema/enum values without repair.
- Added deterministic request binding plus intent, tool-version,
  intent-to-tool mapping, argument and deny-by-default permission validation.
- Reused the existing deterministic planner for argument validation and
  exact registry resolution; the candidate validator never calls
  `ToolRegistry.execute`.
- Added focused tests for valid conversion, malformed JSON, unknown/forbidden
  tools, invalid/forbidden arguments, intent conflict, request binding,
  permissions, deterministic conversion and no execution side effects.
- Full gate: `613 passed, 1 skipped`; `compileall` PASS; `git diff --check`
  PASS. The skip is the existing optional Torch test.
- P8-6.4 is now `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`;
  P8-6.4.1 is `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`. No provider
  request, AgentService, tool execution, commit, tag or push was performed.

## 2026-09-24 - Phase 8 P8-6.4 LLM-Assisted Planning Architecture Freeze

- Added the design-only P8-6.4 LLM-assisted Agent planning architecture and
  architecture freeze report.
- Separated the untrusted `phase8-agent-plan-candidate-v1` proposer contract
  from the unchanged executable-plan contract `phase8-agent-plan-v1`.
- Froze deterministic prechecking, strict candidate parsing, bounded semantic
  and argument validation, deterministic final-plan construction,
  `ToolRegistry`-only execution, deny-by-default permission rechecks,
  append-only audit integration and deterministic fallback.
- Prohibited direct LLM tool execution, dynamic tools, arbitrary SQL,
  filesystem access, shell execution, event mutation, evidence deletion,
  alert action and compliance override.
- Preserved the deterministic planner, static registry, `phase8-report-v1`,
  `SafetyReportGroundingValidator`, `TemplateFallback`,
  `phase8-agent-audit-v1` and the `phase-8-provider-pipeline-complete` tag.
- No planner implementation, provider request, dependency, model, dataset,
  training asset or Phase 9 work was added. P8-6.1 through P8-6.3 are
  `HUMAN REVIEW PASS`; P8-6.4 is `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW
  PENDING`.

## 2026-09-24 - Phase 8 P8-6.3 Agent Audit

- Added the immutable `phase8-agent-audit-v1` `AuditEvent` and frozen audit
  execution statuses for planned, successful, failed, refused and unknown
  tool attempts.
- Added an append-only `AgentAuditStore` protocol and
  `InMemoryAgentAuditStore` with immutable append-order snapshots and no
  update, delete, clear or durable persistence operation.
- Added `AgentAuditService` with deterministic plan identity, planner
  integration, tool-result projection and bounded unknown-tool recording.
- Added allowlist metadata sanitization that drops secrets, credentials, raw
  user payloads, provider output, database paths and filesystem paths.
- P8-6.3 subsequently received human review PASS. Durable audit storage,
  AgentService orchestration, P8-6.4 implementation and Phase 9 remain
  unimplemented.

## 2026-09-24 - Phase 8 P8-6.2 Deterministic Agent Planner

- Added the versioned `AgentPlan` contract, `AgentIntent` vocabulary and
  deterministic planner.
- Added exact mapping for `SAFETY_SUMMARY`, `EVENT_STATISTICS`, `EVENT_DETAIL`
  and `SAFETY_REPORT` to the four frozen read-only tools.
- Added bounded question, reporting-period, filter and event-ID validation,
  registry resolution and deny-by-default permission preflight.
- Unknown intents fail with `OUT_OF_SCOPE`; mutation, administration and
  system-action requests fail with `FORBIDDEN_REQUEST`.
- The planner cannot execute a tool and adds no LLM tool calling, provider,
  network, dynamic tool or Agent framework dependency.
- P8-6.2 subsequently received human review PASS. Its deterministic planner
  remains non-executing; P8-6.3 adds the append-only audit boundary.

## 2026-09-24 - Phase 8 P8-6.1 Tool Registry and Permissions

- Added immutable Agent contracts, the exact four-tool static registry,
  deny-by-default permissions, bounded read-only execution, handler reuse of
  existing analytics/query/report services and non-persistent audit metadata.
- Added focused tests for stable ordering, unknown tools, forbidden
  capabilities, allowed reads, all four read-only handlers, audit metadata,
  mutation-like arguments and absence of filesystem/shell/database imports.
- P8-6.1 is `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`. The later P8-6.2
  slice adds the deterministic planner; Agent reasoning, durable audit store,
  provider execution and Phase 9 remain unimplemented.

## 2026-09-24 - Phase 8 P8-6 Basic Agent Architecture Freeze

- Added the P8-6 Basic Safety Agent architecture and freeze report. This is
  design only; no Agent implementation, LLM tool calling, Agent framework or
  provider SDK was added.
- Froze the deterministic Agent boundary at `AgentService`, with a static
  read-only tool registry and exactly four tools:
  `get_safety_summary`, `get_event_statistics`, `get_event_details` and
  `generate_safety_report`.
- Froze deny-by-default capabilities, bounded execution, explicit refusal and
  failure outcomes, append-only audit records and strict input validation.
- Froze reuse of the unchanged P8-5 provider-first path and
  `TemplateFallback` for `generate_safety_report`; provider invocation remains
  separately permissioned.
- Prohibited arbitrary SQL, filesystem access, shell execution, event
  mutation, evidence deletion, alert action, compliance override, dynamic
  tools and provider-native tool calling.
- Preserved the `phase-8-provider-pipeline-complete` tag and all frozen P8-5
  report, grounding, fallback, model, dataset, training and inference
  identities.
- P8-6 is `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. P8-6.1
  subsequently received human review PASS, and P8-6.2 adds the deterministic
  planner. M-023 and the other Phase 8 Charter statuses remain `待实现`.

## 2026-09-24 - Phase 8 P8-5 Interim Release Checkpoint

- Published the authorized P8-0 through P8-5 checkpoint as
  `phase-8-provider-pipeline-complete`; this is an interim checkpoint, not the
  final Phase 8 release.
- Marked P8-0 through P8-5 `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED` and
  P8-6 `READY / NOT STARTED`. Basic Agent and Phase 9 remain not started;
  M-021, M-022 and M-023 remain `待实现`.
- Preserved the historical P8-5R `REPORT_SCHEMA_INVALID` rejection and the
  subsequent P8-5D diagnostics and P8-5P prompt-v2 corrective evidence.
- Confirmed the final separately authorized provider request returned
  `PROVIDER_VALIDATED`: transport PASS, strict JSON PASS,
  `phase8-report-v1` PASS, provider grounding VALID, `PROVIDER`,
  `degraded=false` and fallback not used.
- No provider request was issued during this release task. Frozen report,
  grounding and fallback assets retained their recorded hashes; model,
  training, inference and processed-dataset hashes MATCH; Charter diff EMPTY;
  Phase 7 tags unchanged.
- Validation: `539 passed, 1 skipped`; `compileall` PASS;
  `git diff --check` PASS.

## 2026-09-24 - Phase 8 P8-5 Final Real Provider Validation Audit

- Recorded the separately authorized manual OpenAI-compatible provider request
  that returned the sanitized `PROVIDER_VALIDATED` result for
  `deepseek-flash`: transport PASS, strict JSON PASS, exact
  `phase8-report-v1` PASS, provider grounding VALID, `PROVIDER`,
  `degraded=false`, no safe error, no schema diagnostics and fallback not used.
- Verified that this result is reachable only through
  `ReportService.generate_provider_or_fallback()` after strict provider
  candidate parsing and the unchanged P8-2 grounding validator both succeed.
  No implementation inconsistency was found and no code was changed.
- Preserved the earlier P8-5R `REPORT_SCHEMA_INVALID` rejection as historical
  evidence, together with the P8-5D diagnostics and P8-5P prompt-v2
  corrective work. P8-5D and P8-5P are `HUMAN REVIEW PASS`.
- This audit issued no provider request, did not use `--execute`, did not
  inspect or print the API-key value and did not persist raw provider content
  or authorization headers.
- Validation: `539 passed, 1 skipped`; `compileall` PASS;
  `git diff --check` PASS; frozen report/grounding/fallback assets and model,
  training, inference and dataset hashes MATCH; current Charter diff EMPTY;
  Phase 7 tags unchanged. No commit, tag or push occurred.
- P8-5 is
  `IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION PASS / HUMAN REVIEW
  PENDING`; Basic Agent, P8-6 and Phase 9 remain unauthorized.

## 2026-09-24 - Phase 8 P8-5P Provider Prompt Schema Conformance Fix

- Added `infra/llm/report_schema_prompt.py`, which derives a compact JSON
  Schema-like description from the authoritative `phase8-report-v1`
  dataclasses and enums instead of maintaining a second hand-written schema.
- Updated provider request construction to embed the generated description and
  incremented `PROVIDER_PROMPT_VERSION` to
  `phase8-provider-prompt-v2`.
- The prompt now enumerates all top-level and nested required fields, exact
  enum values, nullable-but-required fields, closed-object policy,
  empty-array behavior, provider candidate constants, evidence-reference
  format and tracker-scoped `track_id` semantics.
- Added `tests/test_provider_prompt_schema.py` with seven conformance tests and
  updated P8-5 E2E expectations for prompt v2. The known DeepSeek-like
  malformed fixture still fails closed, while a schema-conforming fixture still
  parses and reaches the unchanged grounding validator.
- Kept `phase8-report-v1`, strict parser behavior, `GroundingValidator`,
  `TemplateFallback`, context contract and fingerprint algorithm unchanged.
  No real provider request or `--execute` was performed.
- Validation: focused provider/prompt tests `80 passed`; full regression
  `539 passed, 1 skipped`; `compileall` PASS; `git diff --check` PASS; frozen
  assets MATCH; Charter diff EMPTY; Phase 7 tags unchanged. No commit, tag or
  push occurred.

## 2026-09-24 - Phase 8 P8-5D Sanitized Provider Schema Diagnostics

- Added a bounded `SchemaDiagnostic` / `SchemaDiagnostics` model for
  `REPORT_SCHEMA_INVALID` with safe JSON path, project-owned diagnostic code,
  expected type or constraint and actual JSON type only.
- Mapped strict report-construction failures to `MISSING_FIELD`,
  `UNEXPECTED_FIELD`, `INVALID_TYPE`, `INVALID_ENUM`, `INVALID_FORMAT`,
  `INVALID_VALUE`, `INVALID_COLLECTION` and
  `SCHEMA_CONSTRUCTION_FAILED`.
- Kept `phase8-report-v1` and `SafetyReportGroundingValidator` unchanged. The
  parser still returns `REPORT_SCHEMA_INVALID`, never repairs output and never
  returns a partial report.
- Bounded diagnostics at 20 entries with deterministic ordering and a
  `truncated` flag. Raw field values, unknown provider field names, raw
  response content, prompts, context payloads, authorization headers and API
  keys are excluded.
- Propagated only sanitized diagnostics through `SafetyLLMClient`,
  `ReportService` and the smoke CLI. Provider failure still routes to the
  unchanged `TemplateFallback`, and fallback grounding remains independent.
- Added focused local MockTransport tests covering missing fields, wrong
  types, invalid enums, nested array paths, ordering, truncation, value/raw
  response/API-key leakage, fallback routing and smoke output.
- Validation: focused provider/diagnostic tests `73 passed`; full regression
  `532 passed, 1 skipped`; `compileall` PASS; `git diff --check` PASS; frozen
  asset hashes MATCH; locked Charter body unchanged; Phase 7 tags unchanged.
  No real provider request, `--execute`, commit, tag or push occurred.

## 2026-09-24 — Phase 8 P8-5R Real Provider Post-Execution Audit

- Recorded the human-executed OpenAI-compatible request to
  `https://api.deepseek.com/chat/completions` with model `deepseek-flash`.
- The provider response envelope and non-empty message content were received,
  and strict JSON syntax parsing succeeded. `phase8-report-v1` construction
  failed with `REPORT_SCHEMA_INVALID`, so provider grounding was not reached.
- The unchanged `TemplateFallback` generated a report and passed the unchanged
  grounding validator. The fallback result is degraded and is not
  `PROVIDER_VALIDATED`.
- Raw provider content was not persisted, so the exact schema mismatch cannot
  be recovered. No additional provider request was issued by this audit.
- At that historical point P8-5 was `IMPLEMENTATION COMPLETE / REAL PROVIDER
  EXECUTED / PROVIDER REPORT SCHEMA REJECTED / TEMPLATE FALLBACK PASS / HUMAN
  REVIEW PENDING`.

## 2026-09-24 — Phase 8 P8-5 Real Provider E2E and Safe Fallback

- Added one configuration-driven OpenAI-compatible chat-completions transport
  behind the frozen P8-4 `ProviderTransport` boundary. The transport uses the
  standard library, one request attempt, a finite timeout, no retries and a
  `262144`-byte response limit.
- Added environment-only provider configuration for `PPE_LLM_ENDPOINT`,
  `PPE_LLM_MODEL` and `PPE_LLM_API_KEY`; credentials are excluded from YAML,
  request data, representations, errors and logs.
- Added provider-first `ReportService.generate_provider_or_fallback()`. A
  provider candidate can escape only after strict P8-4 parsing and unchanged
  P8-2 grounding validation.
- Added deterministic semantic and operational failure handling: malformed or
  schema-invalid output, fingerprint mismatch, fabricated references, numeric
  contradiction, path leakage, timeout, auth, rate limit, HTTP, unavailable,
  empty and oversized responses route to `TemplateFallback`.
- Fallback remains `TEMPLATE_FALLBACK` with `degraded=true` and passes the same
  unchanged validator. Fallback failure returns `REPORT_UNAVAILABLE` without a
  report; provider success and fallback success remain distinguishable.
- Added a smoke CLI requiring explicit `--execute`. At the implementation
  point, with no runtime `PPE_LLM_*` configuration it reported `NOT_EXECUTED`;
  no credential use, raw response persistence or fallback-only provider PASS
  was fabricated. The later human execution is recorded by the P8-5R audit.
- Validation: focused Phase 8 tests `109 passed`; full regression
  `520 passed, 1 skipped`; `compileall` PASS; `git diff --check` PASS; frozen
  asset hashes MATCH; Charter diff EMPTY; Phase 7 tags unchanged. At that
  point P8-5 was `IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION NOT
  EXECUTED / HUMAN REVIEW PENDING`; Basic Agent, P8-6 and Phase 9 remain
  unauthorized.

## 2026-09-24 — Phase 8 P8-4 Provider Adapter Boundary and Untrusted Output Parsing

- Added the provider-independent `SafetyLLMClient`, typed request/response
  contracts, injectable transport protocol and structured provider error
  categories under `infra/llm/`.
- Added deterministic `ProviderRequestBuilder` policy with
  `phase8-provider-request-v1`, `phase8-provider-prompt-v1`, safe P8-1 context
  payloads, construction-time removal, context fingerprint binding, finite
  timeout and a `262144`-byte response limit.
- Added strict `ProviderResponseParser` handling for untrusted provider bytes:
  UTF-8/BOM validation, exact object shapes, duplicate-key rejection,
  non-finite-value rejection, fingerprint/version/enum checks and
  `phase8-report-v1` construction.
- Added `ReportService.generate_provider_report()` returning a candidate plus
  the unchanged P8-2 `ReportValidationResult`. P8-4 does not silently fall
  back, mutate invalid output or mark unvalidated provider output accepted.
- Added focused tests for deterministic requests, safe context, versioning,
  valid parsing, malformed/empty/oversized/schema-invalid output, fabricated
  events/tracks, numeric contradictions, path leaks, timeout/auth/rate-limit
  mapping, secret redaction, zero network access and vendor independence.
- P8-3 is now `HUMAN REVIEW PASS`. P8-4 is
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`; real provider execution,
  P8-5, Basic Agent and Phase 9 remain unauthorized.
- Validation: `485 passed, 1 skipped`; focused P8-4 tests `26 passed`;
  `compileall` PASS; `git diff --check` PASS; frozen asset hashes MATCH;
  Charter diff EMPTY; Phase 7 tags unchanged. No commit, tag or push was
  created.

## 2026-09-24 — Phase 8 P8-3 Deterministic Template Fallback

- Replaced the `TemplateFallback` and `ReportService` placeholders with typed,
  provider-independent implementations over the frozen `phase8-context-v1`
  contract.
- Added deterministic `phase8-report-v1` generation with
  `TEMPLATE_FALLBACK`, `degraded=true`, the frozen context fingerprint, exact
  reporting period, event counts, evidence availability, tracker-scoped
  grouping and conservative recommendation rules.
- Claims reference only context facts, metrics, tracker-scoped track IDs and
  available evidence records. Unavailable fields and reason codes are copied
  exactly into report limitations.
- `ReportService` validates the fallback with the unchanged P8-2 grounding
  validator and returns `grounding_status=VALID` only after validation passes.
  Missing, malformed or inconsistent required metrics fail closed.
- Added focused tests for deterministic output, empty periods, type ordering,
  exact references, all recommendation branches, tracker-scope wording, risk
  ties, metric corruption, validator failure, privacy boundaries and
  provider/network import exclusion.
- P8-2 is now `HUMAN REVIEW PASS`. P8-3 is
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`; provider integration,
  real LLM calls, Basic Agent and P8-4 remain unauthorized.
- Validation: `460 passed, 1 skipped`; `compileall` PASS; `git diff --check`
  PASS; frozen asset hashes MATCH; Charter diff EMPTY. No commit, tag or push
  was created.

## 2026-09-24 — Phase 8 P8-2 Structured Report Contract and Grounding Validator

- Added the provider-independent `phase8-report-v1` schema for report
  generations, grounded observations/risk claims, recommendations, evidence
  metadata and explicit limitations.
- Bound every report to `SafetyContextBuilder.fingerprint(context)` through
  `source_context_sha256`; changed or malformed fingerprints fail validation.
- Added deterministic, fail-closed validation for unknown fact, metric, event,
  tracker-scoped track, source and evidence references.
- Added exact structured numeric validation against referenced
  `MetricValue.value`; mismatches are rejected without fuzzy matching.
- Enforced recommendation basis integrity, unavailable-field preservation and
  contradictory-claim detection, and rejected absolute path, database path,
  credential-like field, bearer-token and credential-URI leakage.
- Added reproducible canonical report and validation-result serialization plus
  focused tests for valid/empty reports, fabricated references, numeric
  mismatch, ungrounded content, stable error ordering and no provider/network
  dependency.
- P8-1 is `HUMAN REVIEW PASS`. P8-2 is
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`; provider integration,
  TemplateFallback implementation, Basic Agent and P8-3 remain unauthorized.
  Validation: `450 passed, 1 skipped`; `compileall` PASS; `git diff --check`
  PASS. No commit, tag or push was created.

## 2026-09-24 — Phase 8 P8-1 Deterministic Safety Analytics

- Added `SafetyAnalyticsService`, `SafetyContextBuilder` and the
  `phase8-context-v1` schema over the existing read-only `EventQueryService`
  boundary.
- Implemented exact event counts, type/status/tracker-scoped distributions,
  UTC day buckets, first/last occurrence, evidence availability and opaque
  source-reference aggregation.
- Froze and tested inclusive `[start_at, end_at]` reporting semantics,
  deterministic event/metric/unavailable ordering and canonical JSON
  serialization.
- Added method-level `SafetyContextBuilder.fingerprint(context)` without
  changing the frozen context schema with a `context_sha256` field.
- Added focused tests for interval validation, empty datasets, duplicate or
  unsupported records, missing `track_id`, source-path exclusion, deterministic
  query-order variation, schema validation and reproducibility.
- P8-0 is human-reviewed PASS. P8-1 is `HUMAN REVIEW PASS`; the subsequent
  P8-2 contract/validation scope was separately authorized. Provider
  integration remains unauthorized. M-021 through M-023 remain `待实现`.

## 2026-09-24 — Phase 8 P8-0 Architecture and Contract Freeze

- Added the authoritative Safety Intelligence Agent architecture and ADR-023.
- Froze the downstream read-only boundary over `EventQueryService`, with no
  model, dataset, training, inference, tracking, association, compliance or
  Phase 7 implementation changes.
- Defined deterministic `SafetyAnalyticsService`, versioned
  `phase8-context-v1`, provider-independent `SafetyLLMClient`,
  `phase8-report-v1`, grounding validation, failure isolation and local
  fallback.
- Defined the privacy allowlist, secret handling, Basic Agent read-only tool
  boundary and future deterministic/mock evaluation strategy.
- Recorded explicit schema limitations: tracker-scoped `track_id`, no stable
  person identity, no persisted violation duration and no alert-delivery
  telemetry.
- Added the P8-0 architecture freeze report and worklog. No provider, API call,
  dependency, code, commit, tag or push was created; M-021 through M-023 remain
  `待实现`.
- P8-0 subsequently passed human review before the authorized P8-1 work.

## 2026-09-24 — Phase 7 Final Release Closure

- Completed the authorized final release review for Phase 7 runtime
  finalization and M-007 annotated demo video delivery.
- Confirmed Phase 7-0 through Phase 7-6 PASS, M-007 implementation and real
  MP4 validation PASS, and M-007 Human Review PASS.
- Published the final annotated tag `phase-7-release-freeze-complete` without
  moving or replacing `phase-7-web-alert-platform-complete`.
- Final release gate: `414 passed, 1 skipped`; `python -m compileall -q .`:
  PASS; `git diff --check`: PASS.
- Frozen identities verified: checkpoint, training configuration, inference
  configuration, processed dataset payload and M-007 demo SHA256 all MATCH.
- The locked Charter body and M-007 `待实现` status remain unchanged. Remote
  RTSP, reconnect/backoff, annotation quality acceptance and Phase 9 Charter
  acceptance remain pending.

## 2026-09-23 — Phase 7 M-007 Annotated Demo Video

- Added `AnnotatedFrameRenderer`, `AnnotatedVideoWriter`,
  `AnnotatedVideoService` and a structured offline MP4 CLI.
- Rendering uses the frozen checkpoint and existing `VideoReader` /
  `InferenceService` boundaries, deterministic class colors, clipped boxes,
  class labels and confidence values. No tracking or compliance overlay was
  added.
- Output is staged as one directory and published by a single atomic rename
  only after the source, processed, written and decoded output frame counts
  match. Failures release the encoder and remove the staging directory.
- Added `demo.mp4`, `run.json`, `frames.jsonl`, `summary.json` and
  `renderer.log` metadata validation. The default output root is Git-ignored.
- Real frozen-checkpoint MP4 validation processed 47/47 frames at 1280x720
  and produced output SHA256
  `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949`.
- Validation: `414 passed, 1 skipped`; `python -m compileall .`: PASS;
  `git diff --check`: PASS. M-007 remains `待实现` in the locked Charter
  pending human review and Phase 9 acceptance. No commit, tag or push.

## 2026-09-23 — Phase 7 Release Freeze Preparation

- Audited Phase 7-0 through Phase 7-6, the published base release identity,
  the P7-6 runtime evidence and the frozen model/data/training/inference
  hashes.
- Added `docs/reports/phase-07/PHASE_07_FINAL_RELEASE_REPORT.md` and recorded
  the release freeze candidate as `PASS / HUMAN REVIEW PENDING`.
- Added the M-007 annotated demo video tool design covering offline MP4
  rendering, deterministic overlays, output metadata, frame-count checks,
  atomic publication and fail-closed errors.
- Preserved M-007 as `待实现` in the locked Charter. The design is not
  implementation evidence, and no annotated video was rendered or validated.
- The locked Charter body remains unchanged because its hash guard rejects
  non-status content edits; the requested Charter status note was therefore
  withheld and recorded in the release-freeze report instead.
- Validation: `407 passed, 1 skipped`; `python -m compileall -q .`: PASS;
  `git diff --check`: PASS; frozen asset hashes MATCH.
- No model, dataset, mapping, training configuration, checkpoint, core
  pipeline, commit, tag or push action was performed.

## 2026-09-23 — Phase 7-6 Runtime Validation

- Executed the requested runtime order: MP4 regression, USB Camera, native
  TTS, Streamlit browser runtime and RTSP runtime.
- MP4 regression processed 47/47 frames with the frozen checkpoint and
  produced the complete inference-to-event persistence path without runtime
  errors.
- Native Windows SAPI TTS through `pyttsx3` returned successfully. Real USB
  Camera open/read/close and real local MediaMTX RTSP open/read/close both
  passed with recorded latency, resource and screenshot evidence.
- The real Streamlit browser executed Overview, Event Explorer, Evidence
  Viewer, Statistics and a browser-driven MP4 realtime session to
  `COMPLETED`.
- Full validation: `407 passed, 1 skipped`; `python -m compileall -q .`: PASS;
  `git diff --check`: PASS; Charter diff: empty.
- Runtime evidence remains Git-ignored under `artifacts/validation/P7-6/`.
  Remote RTSP, reconnect/backoff, annotated video rendering and M-007/M-008
  final acceptance remain pending. No commit, tag or push was created.

## 2026-09-23 — Phase 7-6 Release Finalization

- Added the lazy, injectable `TTSService` and `TTSAlertAdapter` with stable
  `TTS_UNAVAILABLE` / `TTS_BACKEND_FAILED` errors, event-id idempotency,
  per-track/type cooldown and structured failure isolation.
- Added `MonitoringService`, session-scoped monitoring assembly and the
  Streamlit realtime page for MP4, USB Camera and RTSP. The service owns the
  background worker and reuses the existing inference, tracking, association,
  compliance, event, SQLite, snapshot and alert boundaries.
- Added `configs/monitoring.yaml` and the execution-disabled
  `configs/p7_6_validation.yaml` real Camera/RTSP validation design with
  frozen checkpoint identity, bounded reads and Git-ignored evidence.
- Added TTS, monitoring lifecycle, SQLite/snapshot ordering, configuration,
  page-boundary and integration tests. Full validation:
  `407 passed, 1 skipped`; `python -m compileall .`: PASS;
  `git diff --check`: PASS.
- The base Phase 7 release commit and tag already exist. At the initial
  finalization implementation checkpoint, real RTSP, native `pyttsx3` audio
  and browser Streamlit runtime had not yet been executed. The subsequent
  Phase 7-6 runtime validation executed all three and recorded the results in
  `docs/reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_RESULT.md`. This
  finalization change set remains uncommitted for human review; no commit,
  new tag or push was created.

## 2026-09-23 — Phase 7 Release Preparation Audit

- Audited the complete uncommitted Phase 7 change set: no staged files,
  no model/media/database/snapshot/archive artifacts, no credentials or
  tokens, and no pending file above approximately 75 KB.
- Confirmed the release-boundary `.gitignore` coverage for model checkpoints,
  processed/external datasets, validation evidence and generated event
  outputs; all corresponding local assets remain outside Git.
- Synchronized Phase 7 documentation so 7-0 through 7-5 are recorded as
  human-reviewed PASS and 7-Release is `AUDIT COMPLETE FOR HUMAN REVIEW /
  NOT PUBLISHED`.
- Recorded the remaining V1 limitations without converting them into
  completion claims: TTS is unimplemented, real RTSP is not runtime-tested,
  annotated video rendering is pending, and M-007/M-008 final acceptance
  remains open.
- Full validation: `390 passed, 1 skipped`; `python -m compileall .`: PASS;
  `git diff --check`: PASS; Charter diff: empty. The skip is the existing
  optional Torch evaluation test.
- No commit, push or tag was created; publication waits for explicit human
  review.

## 2026-09-23 — Phase 7-5 Runtime Validation

- Added `scripts/run_phase7_runtime_validation.py` to compose the existing MP4
  source, frozen inference service, person-only ByteTrack, Person-PPE
  association, compliance/event engine, Phase 6 JSONL, SQLite ingestion,
  evidence snapshot, dashboard query and Console/Web alert boundaries.
- Added `scripts/validate_phase7_dashboard_runtime.py` and executed Overview,
  Event Explorer, Evidence Viewer and Statistics with Streamlit `AppTest`
  against the run-specific SQLite and snapshot evidence.
- Run `20260923T131111Z` processed 47/47 MP4 frames on CPU with the frozen
  EXP-001 checkpoint. It produced 77 detections, 66 track updates, one
  unknown association, 66 compliance findings and one persisted
  `PPE_UNKNOWN` event, with zero runtime errors.
- Verified the generated event through JSONL, SQLite, a SHA256/dimension-checked
  snapshot and dashboard query while preserving the original Phase 6
  `event_id`; Console and in-process Web alerts both reported `delivered`.
- Opened and read a real USB Camera device index `0`, then released it. The
  injected disconnect lifecycle produced observable `SOURCE_DISCONNECTED`.
  Real RTSP was not tested.
- A local Streamlit server returned HTTP 200 for the health endpoint and root
  page. Hosted/remote Web alert delivery and TTS remain unimplemented.
- Full validation: `390 passed, 1 skipped`; `python -m compileall .`: PASS;
  `git diff --check`: PASS; Charter diff: empty. The skip is the existing
  optional Torch evaluation test.
- At the time of that completion, Phase 7-5 was `COMPLETE FOR HUMAN REVIEW`
  and release remained `WAITING`; it was subsequently recorded as
  `COMPLETE / HUMAN REVIEW PASS`. Python 3.12.1 differs from frozen
  `INF-RUNTIME-001` Python 3.10.4, real RTSP and TTS remain unvalidated, and
  M-007/M-008 final acceptance is still pending. No commit, push or tag.

## 2026-09-23 — Phase 7-4 Camera / RTSP Input

- Added `SourceType`, `SourceState`, `SourceMetadata` and `SourceStatus`
  contracts plus the unified `VideoSource` open/read/status/close protocol.
- Added `MP4VideoSource` over the frozen sequential `VideoReader`, with
  ordered frames, EOF handling and release cleanup.
- Added `USBCameraSource` and `RTSPVideoSource` with injected capture
  factories, live-source timestamps, open/read failure states, bounded timeout
  settings and idempotent release behavior.
- Added credential- and query-free RTSP URI projection so status and errors do
  not expose stream secrets.
- Added lifecycle, mock source, invalid source, disconnect and static
  no-direct-capture tests. Business, dashboard and script layers do not call
  `cv2.VideoCapture`.
- Full validation: `390 passed, 1 skipped`; compileall, `git diff --check`
  and Charter diff PASS. The skip is the existing optional Torch test.
- Real Camera/RTSP devices or streams were not opened; reconnect
  orchestration, monitoring integration, annotated rendering and M-008
  acceptance remain pending. Phase 7-3 is recorded as human-reviewed PASS.
  No commit, push or tag.

## 2026-09-23 — Phase 7-3 Dashboard & Alerts

- Added a read-only `EventQueryService` for dashboard filtering, pagination,
  statistics, source discovery and verified evidence projection without
  exposing SQL directly to Streamlit pages.
- Added Streamlit navigation and page sources for Overview, Event Explorer,
  Evidence Viewer and Statistics. Pages read SQLite/snapshot data only through
  the dashboard support/service boundary and do not import inference,
  tracking, association or compliance implementations.
- Added `AlertMessage`, `AlertResult`, an `AlertAdapter` protocol,
  `AlertService` fan-out, and Console/Web adapters. Delivery is idempotent by
  the preserved Phase 6 `event_id`; adapter failures are isolated.
- Added dashboard, event-query and alert-adapter tests plus structure/import
  contracts. Streamlit, Pandas and Plotly are not installed on this host, so
  actual browser rendering was not executed; source and service contracts are
  covered by tests.
- Full validation: `377 passed, 1 skipped`; compileall, `git diff --check`
  and Charter diff PASS. The skip is the existing optional Torch test.
- Phase 7-2 is recorded as human-reviewed PASS. TTS, Camera/RTSP, annotation
  rendering, reconciliation automation and retention remain unimplemented.
  No commit, push or tag.

## 2026-09-23 — Phase 7-2 Evidence Snapshot

- Added `SnapshotReference` metadata validation and the independent
  `SnapshotRepository` boundary while preserving the frozen `event_id`.
- Implemented atomic JPEG evidence storage below
  `artifacts/events/snapshots/YYYYMMDD/`, with UTC date partition,
  `event_<event-id>.jpg` filename, SHA256, dimensions, MIME type and
  relative POSIX paths.
- Added `SnapshotService` orchestration that verifies the event, reuses
  identical evidence idempotently, rejects conflicting replacement evidence
  and associates snapshot metadata so `PersistedEvent.snapshot` resolves to a
  real file.
- Added storage, repository, duplicate-policy and Phase 6 event-to-file
  integration tests. A failed metadata write retains a possible orphan
  evidence file rather than deleting it silently.
- Full validation: `361 passed, 1 skipped`; compileall and
  `git diff --check` PASS. The skip is the existing optional Torch test.
- Phase 7-1 is recorded as human-reviewed PASS. Phase 7-2 is complete for
  human review. Annotation rendering, reconciliation automation, retention,
  dashboard, alerts/TTS and Camera/RTSP remain unimplemented. No commit, push
  or tag.

## 2026-09-23 — Phase 7-1 SQLite Event Storage

- Added the persisted-event projection, status/query contracts and internal
  storage row without changing the frozen Phase 6 JSONL wire contract.
- Added checksummed SQLite migration `0001_phase7_events` with
  `schema_migrations`, `workers`, `events`, `snapshots` and `statistics`
  tables, the frozen indexes, foreign-key enforcement and UTC timestamp
  policy.
- Implemented `Database`, `EventRepository` and `EventIngestService` with
  short `BEGIN IMMEDIATE` writes, idempotent `event_id` ingestion,
  restart-persistent reads, query filters and lifecycle status updates.
- Added unit tests for schemas, migrations, repository and ingestion, plus an
  integration test from a real Phase 6 `ComplianceEvent` through SQLite and
  database restart.
- Full validation: `352 passed, 1 skipped`; compileall, `git diff --check`
  and Charter diff PASS. Snapshot files, dashboard, alerts/TTS and
  Camera/RTSP remain unimplemented. No commit, push or tag.

## 2026-09-23 — Phase 7-0 Web & Alert Architecture Freeze

- Added the Phase 7 pre-read, current-architecture audit, target architecture,
  data contracts, risk register and architecture-freeze report under
  `docs/reports/phase-07/` and `docs/designs/phase-07/`.
- Added ADR-022 to freeze SQLite-first persistence, Streamlit V1, one
  `VideoSource` interface for MP4/USB Camera/RTSP, date-partitioned evidence
  snapshots and Console/Web/TTS alert adapters.
- Defined a separate persisted-event projection with `id`, `timestamp`,
  `track_id`, `type`, `confidence`, `snapshot` and `status`; the Phase 6
  four-field JSONL wire contract remains unchanged.
- Recorded RISK-020 through RISK-026 and froze Phase 7-0 through 7-Release in
  the Master Plan and Phase 7 document.
- No implementation, code, test, model, dataset, mapping, training,
  evaluation, tracking or event-engine change occurred. No commit, push or
  tag.

## 2026-09-23 — Phase 6 PPE Compliance Event Engine

- Added `AssociationResult -> ComplianceInput -> ComplianceResult ->
  ComplianceEvent` under the existing `core/`, `services/` and `infra/`
  architecture.
- Implemented conservative Helmet/Vest rules with `NO_HELMET`, `NO_VEST` and
  `PPE_UNKNOWN`; missing, uncertain and conflicting evidence is never forced
  into a person assignment.
- Added five-frame and one-second temporal confirmation, event
  deduplication, recovery, cooldown and append-only `outputs/events.jsonl`
  storage.
- Added a deterministic offline fixture/demo and focused adapter, rule,
  temporal, event and storage tests. No Torch, YOLO, GPU, camera or RTSP use
  is required.
- Full validation: `332 passed, 1 skipped`; compileall and
  `git diff --check` PASS. The skip is the existing optional Torch test.
- Frozen model, dataset, mapping, training configuration and Phase 5 tracking
  implementation remain unchanged.

## 2026-09-23 — Phase 5 Release Final Audit

- Audited the complete uncommitted Phase 5 change set, staged contents,
  untracked files, frozen asset hashes and release-file boundaries.
- Confirmed no model, dataset, video, database or credential artifact is
  included in the release change set; the staged area is empty.
- Corrected implementation-level documentation to record M-009 and M-010 as
  `IMPLEMENTED / Runtime Evidence Pending` while preserving their locked
  Charter status as `待实现`.
- Added `docs/reports/phase-05/P5_RELEASE_FINAL_AUDIT.md` and the corresponding
  worklog. Phase 5 remains NOT RELEASED because real checkpoint, inference and
  ByteTrack runtime evidence is still blocked.
- Full validation: `307 passed, 1 skipped`; compileall and
  `git diff --check` PASS; Charter working-tree diff empty.
- No commit, push or tag occurred.

## 2026-09-23 — Phase 5 Final Release Preparation

- Added `docs/reports/phase-05/P5_FINAL_RELEASE_REPORT.md`, consolidating the
  Interface Freeze, ByteTrack adapter, Person-PPE association and synthetic
  pipeline evidence.
- Recorded real runtime validation as `BLOCKED / NOT RUN`: `best.pt` was not
  loaded, YOLO11 inference was not executed, and real ByteTrack was not run.
- Kept Phase 5 at `PREPARED FOR HUMAN REVIEW / NOT RELEASED`; the
  `phase-5-tracking-association-complete` tag is not authorized while
  P5-FR-4 is blocked.
- Full validation: `307 passed, 1 skipped`; compileall and
  `git diff --check` PASS; Charter working-tree diff empty.
- M-009 and M-010 remain `待实现`. No model, dataset or training
  configuration was modified; no commit, push or tag occurred.

## 2026-09-23 — P5-3 Tracking & Association Validation

- Added an integrated synthetic pipeline suite for
  `DetectionResult -> PersonTrackingAdapter -> TrackResult ->
  PPEAssociationAdapter -> AssociationResult`.
- Covered single-person, multiple-person, PPE-present, missing-PPE and
  ambiguous-association paths with a scripted ByteTrack backend and the real
  conservative association adapter.
- Added `configs/p5_3_validation.yaml` and
  `scripts/run_tracking_association_validation.py` for frozen checkpoint,
  validated MP4, statistics and runtime-fingerprint preparation.
- Static preflight verified the checkpoint SHA256
  `1c144eef...871f61` and validated video SHA256 `b630d851...b852` without
  loading either asset; it returned `BLOCKED_RUNTIME_DEPENDENCIES` because
  `torch` and `ultralytics` are not installed.
- Full validation: `307 passed, 1 skipped`; compileall and
  `git diff --check` PASS; Charter working-tree diff empty.
- P5-3 is complete for human review. Real runtime validation is prepared but
  NOT RUN; M-009 and M-010 remain `待实现`. No model load, real inference,
  ByteTrack execution, dataset mutation, training, checkpoint change, commit,
  push or tag occurred.

## 2026-09-23 — P5-2 Person-PPE Association

- Replaced the association placeholder with `PPEPersonAssociationAdapter`
  behind the frozen `PPEAssociationAdapter` contract.
- Preserved confidence `0.25`, containment `0.50`, IoU `0.10`, ambiguity
  margin `0.10`, containment-before-IoU priority and one assignment per PPE.
- Restricted assignment targets to existing person `TrackResult` values and
  PPE classes `1` through `4`; person/unsupported PPE input fails closed.
- Added deterministic candidate ranking, explicit `unknown` for missing
  candidates or ambiguous leading candidates, and no nearest-distance path.
- Added focused tests for helmet, vest, multiple people, wrong candidates,
  ambiguity, missing PPE, empty input, IoU-only geometry, confidence,
  invalid class/frame context and disabled execution.
- Full validation: `300 passed, 1 skipped`; compileall and
  `git diff --check` PASS; Charter working-tree diff empty.
- M-009 and M-010 remain `待实现`; P5-2 is complete for human review and
  P5-3 has not started. No model load, inference, real ByteTrack execution,
  dataset mutation, training, checkpoint change, commit, push or tag occurred.

## 2026-09-23 — P5-1 Person-only ByteTrack Adapter

- Added `ByteTrackPersonTrackingAdapter` behind the frozen
  `PersonTrackingAdapter` contract, with a lazy private Ultralytics backend and
  an injectable backend for deterministic tests.
- Restricted tracking input to `class_id=0` / `person`, applied the frozen
  `0.25` confidence threshold, rejected invalid class/frame context, and
  returned only project-owned `TrackResult` values.
- Preserved the P5-0 ByteTrack thresholds, enabled the adapter runtime state
  and added `fuse_score: true` to the frozen configuration boundary.
- Added focused tests for continuous single-person tracks, multiple people,
  enter/leave, missing frames, invalid classes, duplicate backend matches and
  disabled execution.
- Full validation: `286 passed, 1 skipped`; compileall and
  `git diff --check` PASS; Charter working-tree diff empty.
- Real Ultralytics ByteTrack execution was not performed because the current
  workspace lacks `ultralytics` and `torch`. M-009 and M-010 remain `待实现`;
  P5-1 is complete for human review and P5-2 has not started.
- No model load, inference, dataset mutation, mapping change, training,
  checkpoint change, commit, push or tag occurred.

## 2026-09-23 — P5-0 Tracking & Association Interface Freeze

- Added model-independent `TrackResult` and `AssociationResult` contracts,
  explicit `associated` / `unknown` status and person-only tracking boundary.
- Froze `configs/tracker.yaml` for Ultralytics `8.4.157` ByteTrack and added
  `configs/association.yaml` with containment `0.50`, IoU `0.10`, confidence
  `0.25`, ambiguity margin `0.10`, no nearest-distance assignment and explicit
  unknown output.
- Added ADR-020, Phase 5 design/report/worklog and focused schema/config tests.
- Phase 5 is now `IN PROGRESS`; P5-0 is complete for human review. M-009 and
  M-010 remain `待实现`.
- No ByteTrack execution, association run, model load, inference, dataset
  mutation, training or checkpoint change occurred. No commit/push/tag.

## 2026-09-23 — Document Governance Optimization Phase B

- Added the Phase 4 → Phase 5 handover at
  `docs/worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md`,
  establishing the worklog handover workflow and preserving the former
  Current Status text verbatim as a dated historical snapshot.
- Simplified `docs/02_CURRENT_STATUS.md` to a concise current-state entry with
  links to detailed reports, risks, frozen assets and the handover.
- Phase and MUST statuses, deferred requirement ownership and the next allowed
  step remain unchanged. No training, implementation or release occurred.

## 2026-09-23 — Phase 4 Scope Boundary Clarification

- Added ADR-019: M-008 remains V1 MUST; annotated video rendering remains
  M-007 acceptance work. Corrected the prior Extension classification while
  retaining ADR-018's offline release decision and historical records.
- Assigned delivery to Phase 7 integration and final acceptance to Phase 9.
- Clarified Phase 5 entry: offline gates PASS, deferred ownership recorded,
  no frozen asset conflict, existing input prerequisite and user authorization.
- Synchronized scope wording in status, plan, gates, phase documents and README.
- Charter, MUST statuses and phase completion statuses are unchanged.
- Documentation only; no runtime tests, training, commit or push.
- Known limitation: the unchanged documentation governance test still requires
  the superseded Extension wording; no full-suite PASS is claimed.

## 2026-09-23 — Phase 4 Scope Adjustment and Offline Inference Release

- Added ADR-018 to re-scope Phase 4 as `Offline Inference`: structured image
  inference, sequential local MP4 inference, frozen runtime/checkpoint, and
  real validation evidence.
- Deferred Camera, RTSP, real-time/network behavior, M-008 and annotated video
  rendering from Phase 4; Charter M-008 remains `待实现`. ADR-019 clarifies
  that these remain MUST obligations; this historical release record is retained.
- Updated the Phase 4 milestone name to
  `phase-4-offline-inference-complete`; the original
  `phase-4-inference-complete` name is explicitly not used.
- Updated README, Master Plan, current status, Phase 4 document and test-gate
  records to report `Phase 4: Offline Inference COMPLETE`,
  `Camera/RTSP: Deferred MUST`, and `Phase 5: WAITING`.
- No detector or tracker behavior was changed, no model or dataset was
  modified, and Phase 5 was not started.

## 2026-09-23 — Phase 4C-2 Real MP4 Inference Validation

- 新增 `configs/video_validation.yaml` 和
  `scripts/run_video_validation.py`；validation-only 配置显式启用执行，
  frozen `configs/inference.yaml` 保持 `execution_enabled: false`。
- 使用 `INF-RUNTIME-001` 加载 frozen
  `models/checkpoints/EXP-001/best.pt`，checkpoint SHA256 保持
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`。
- 顺序处理 external public-domain MP4 的全部 47/47 帧，未跳帧、未 batch、
  未 async、未迁移 CUDA；检测 77 项（person 76、no_vest 1），端到端耗时
  15.1920268 s，处理速率 3.0937281 FPS。
- 新增 Git-ignored `artifacts/validation/P4C-2/video_validation.json`、
  `frame_summary.json` 和 schema-backed `validation_report.json`。
- 新增 `tests/test_video_validation_config.py`，验证 validation-only 配置、
  frozen inference contract 和 Git-ignore 边界。
- Phase 4C-2 COMPLETE，Phase 5 WAITING。未执行 RTSP、Camera、tracking、
  association、compliance、events、alerts、Web 或 LLM；未修改 dataset、
  mapping、training config 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4C-1 Real Image Inference Validation

- 新增 `configs/validation.yaml` 和 `scripts/run_image_validation.py`；validation
  配置单独启用执行，frozen `configs/inference.yaml` 保持
  `execution_enabled: false`。
- 增加显式 `execution_enabled` 调用级 override，并修正 Torch runtime
  fingerprint 读取为 `torch.__version__`，从而严格匹配冻结的
  `2.5.1+cpu` 而不是 wheel metadata 的 `2.5.1`。
- 在 `INF-RUNTIME-001` 中使用 frozen `models/checkpoints/EXP-001/best.pt`
  完成一次外部 public-domain construction image 的真实推理；checkpoint
  SHA256 保持
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`。
- Hot inference 返回 5 个 `DetectionResult`：person 2、hardhat 1、
  no_hardhat 1、no_vest 1；cold start 为 14.237 s，warm inference 为
  176.386 ms。
- 新增 Git-ignored `artifacts/validation/P4C-1/image_validation.json` 和
  `validation_report.json`，并通过既有 validation schemas 重新构造验证。
- Phase 4C-1 image validation COMPLETE；video、tracking、association、
  compliance、events 和 alerts 未执行。未修改 dataset、mapping、training
  config 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4C-0 Real Inference Validation Design

- 新增 `docs/phases/PHASE_04C_VALIDATION_DESIGN.md`，定义真实 checkpoint +
  external image / short MP4 验证流程、证据字段、Git-ignored `artifacts/`
  输出政策和 fail-closed 错误边界。
- 新增 `core/schemas/validation.py`，定义 model-independent
  `ImageValidationRecord`、`VideoValidationRecord` 和
  `InferenceValidationReport`；记录 detection statistics、confidence、
  latency、processing time 和 processing FPS。
- 新增 `tests/test_validation_schema.py`，只验证 schema creation、计数一致性
  和 JSON serialization，不加载模型或访问真实输入。
- Phase 4C-0 COMPLETE，Phase 4C-1 WAITING。未加载 `best.pt`、未执行真实
  inference，未修改模型、dataset 或 training assets，未 commit/push/tag。

## 2026-09-23 — Phase 4B-2b MP4 Video Inference Implementation

- 新增 `core/video/reader.py`，实现 lazy OpenCV、本地 MP4 顺序读取、
  metadata extraction、timestamp generation 和结构化 reader errors。
- 新增 `services/video_inference_service.py`，串联 `VideoReader`、
  `InferenceService`、`FrameInferenceResult` 和 `VideoInferenceResult`；
  不复制 detector 参数、checkpoint 校验或结果解析逻辑。
- 为 `YOLODetector` 和 `InferenceService` 增加共享 frame-level entry
  point，使图片与视频使用同一冻结 CPU/checkpoint/class-filter 策略。
- 新增 `scripts/run_video_inference.py`，支持
  `python scripts/run_video_inference.py xxx.mp4` 并输出结构化 JSON；
  missing、invalid format、empty、decode 和 disabled execution 都有稳定
  error code。
- 新增 `tests/test_video_inference.py`，默认使用 fake capture 和 fake
  inference service，覆盖顺序、frame count、metadata、serialization、
  disabled execution 和错误处理，不加载 `best.pt`。
- Phase 4B-2b COMPLETE，Phase 4B-3 WAITING。未执行真实大规模视频测试，
  未修改 dataset、mapping、training config 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4B-2a Video Inference Architecture Design

- 新增 `docs/phases/PHASE_04B2_VIDEO_DESIGN.md` 和
  `docs/reports/phase-04/PHASE_04B2_VIDEO_DESIGN_REPORT.md`，定义本地 MP4 顺序推理、
  `VideoReader -> FrameProcessor -> InferenceService -> Result Writer`
  流水线、runtime policy、错误处理和非目标。
- 新增 `core/schemas/video.py`，只定义 `FrameData`、`VideoMetadata`、
  `FrameInferenceResult` 和 JSON-serializable `VideoInferenceResult`，
  不包含 OpenCV/Torch/Ultralytics 依赖或视频读取实现。
- 新增 `tests/test_video_schema.py`，验证 schema creation、字段完整性和
  serialization。
- Phase 4B-2a COMPLETE，Phase 4B-2b WAITING。未修改 detector/service，
  未加载模型、未执行真实视频推理，未修改 dataset、mapping、training
  assets 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4B-1 Single Image Inference

- 新增 `core/inference/detector.py` 与 `core/inference/__init__.py`，实现
  lazy-loading `YOLODetector`、frozen checkpoint size/SHA256 检查、CPU-only
  device policy、固定 `imgsz/conf/iou/max_det/classes` 和
  `DetectionResult` 转换。
- 实现 `services/inference_service.py` 的单图路径检查、格式验证和 detector
  委托；video 与 Camera/RTSP 仍为明确的 future-phase placeholder。
- 新增 `scripts/run_image_inference.py`，支持
  `python scripts/run_image_inference.py image.jpg` 并输出 JSON；默认
  `execution_enabled: false` 时返回明确的 `execution_disabled`。
- 新增 `tests/test_image_inference.py`，默认使用 fake model/image loader，
  不加载真实 `best.pt`；覆盖 invalid input、disabled execution、lazy load、
  schema output、checkpoint tamper 和 CLI error output。
- Phase 4B-1 COMPLETE，Phase 4B-2 WAITING。未执行真实推理，未修改 dataset、
mapping、training artifact 或 checkpoint，未 commit/push/tag。

## 2026-09-23 — Phase 4B-0 Inference Runtime Freeze

- 新增 `docs/phases/PHASE_04B_RUNTIME_FREEZE.md`，冻结 release checkpoint
  `models/checkpoints/EXP-001/best.pt` 及 SHA256
  `1c144eef...871f61`。
- 冻结 `INF-RUNTIME-001`：Windows x86_64、Python 3.10.4、PyTorch
  2.5.1+cpu、torchvision 0.20.1、Ultralytics 8.4.157、NumPy 2.2.6、
  OpenCV 5.0.0.93；依赖来源固定为 `locks/EVAL-001/requirements.txt`。
- 冻结 CPU-only device policy、`imgsz: 640`、confidence `0.25`、
  NMS IoU `0.45`、五类 output filter、input formats、`DetectionResult`
  output reference 和 fail-closed error handling policy。
- 将 `configs/inference.yaml` 从 planned defaults 更新为只读配置契约；
  `execution_enabled: false`，不包含推理逻辑，不加载模型。
- Phase 4A COMPLETE，Phase 4B-0 COMPLETE，Phase 4B-1 WAITING。
- 未执行模型加载或推理，未修改 dataset 或训练产物，未 commit/push/tag。

## 2026-09-23 — Phase 4A Inference Architecture Design

- 完成 Phase 3 人工审核 PASS 后的状态同步：Phase 3 COMPLETE，M-005
  `已经实现`，Phase 4A 进入 design-only 工作。
- 新增 `docs/reports/phase-04/PHASE_4A_PRECHECK_REPORT.md`，审计现有 inference 占位接口、
  `configs/inference.yaml`、detection schemas、缺失模块和风险。
- 新增 `docs/phases/PHASE_04_INFERENCE_DESIGN.md`，定义 Input Adapter、
  YOLO11 detector wrapper、统一 `DetectionResult`、未来 P5-P7 集成边界和
  Phase 4A non-goals。
- 新增 `core/schemas/detection.py`，只定义无模型依赖的结果数据结构及
  JSON-serializable `to_dict()`；现有 Detector、Pipeline、Service 和 CLI
  占位实现保持不变。
- 新增 `tests/test_detection_schema.py` 验证结果创建、字段完整性和序列化。
- 未加载 `best.pt`、未启动推理、未实现 ByteTrack/PPE 关联/规则/事件/告警/
  Web/LLM/Agent，未修改 dataset、mapping、weights 或 EXP-001 配置，未 commit
  或 push。

## 2026-09-22 — Phase 3 Final Release Freeze

- 创建 `docs/reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md`，汇总 P3-G1～G4 技术 PASS、M-005
  技术完成/人工验收待定、最终 best.pt 模型、artifact 清单、SHA256 和限制。
- 冻结现有 EVAL-001、CMP-001、SEL-001 证据及实现/配置/测试哈希；不改写既有
  报告或 EXP-001_RELEASE_MODEL.yaml，不新增模型实测或调优。
- 本轮全量测试 213 passed / 1 skipped；离线复算与证据身份核验通过。
- Freeze COMPLETED / AWAITING HUMAN REVIEW；GitHub NOT_RELEASED。
  明确 Phase 4 需人工审核、模型/推理配置确认和开始指令，未进入开发。
- 未训练、未修改 dataset/mapping/weights 或 Phase 2 artifacts；未 commit/push。

## 2026-09-22 — P3-G4 Final Comparative Model Selection

- SEL-001 正式记录选择 EXP-001 best.pt（epoch 75），保留原验证集选择；last.pt
  保留为参考。没有新增模型实测、重新训练、调阈值或修改权重。
- 新增 `P3_MODEL_SELECTION_REPORT.md` 与 `EXP-001_RELEASE_MODEL.yaml`，记录
  候选、既有评估证据、PPE 合规关注点、取舍、SHA256 与限制；人工审核 PENDING。
- 全量测试 213 passed / 1 skipped；compileall、离线复算、清单身份与证据哈希
  校验通过。P3-G4 技术门禁 PASS；Phase 3 尚未发布，未进入 Phase 4。
- 未修改 dataset、mapping、EXP-001 weights、既有评估/比较结果或 Phase 2
  artifacts；未 commit/push。

## 2026-09-22 — P3-G3 Model Comparison

- 完成 CMP-001：EXP-001 best.pt（epoch 75）与 last.pt（epoch 95）的同条件
  checkpoint 对照；两者调用相同 ValService，使用相同 test split、参数、代码与 runtime。
- 新增配置、比较入口、条件一致性验证与离线复算；checkpoint 仅能从 Phase 2
  冻结清单选择。保留 EVAL-001，并精确复现其 best 指标。
- 输出 `P3_MODEL_COMPARISON_REPORT.md` 和机器可读 summary，包含四项总体指标、
  七类 AP、no_hardhat / no_vest / small-object recall 与取舍分析。
- 全量测试 213 passed / 1 skipped；专用环境相关测试 29 passed。P3-G3 PASS，
  等待人工审核；P3-G4 仍未完成，不改变原 best 选择。
- 未训练、未下载模型、未修改 EXP-001 配置/权重、dataset/mapping 或 Phase 2
  artifacts；未 commit/push，未进入 Phase 4。

All notable project changes are recorded here. This project follows a
phase-based log rather than claiming semantic-release completeness.

## 2026-09-22

### GitHub Phase Milestone Release Governance

- Added ADR-017 GitHub Phase Milestone Release Strategy.

### P2-0 Training Environment Preparation & Dependency Boundary Review

- Added `docs/designs/phase-02/P2-0_DEPENDENCY_STRATEGY.md` comparing a Windows NVIDIA
  GPU environment, WSL2 with CUDA, a controlled cloud GPU, and CPU fallback.
- Added `docs/designs/phase-02/P2-0_VERSION_MATRIX.md` for Python, PyTorch, CUDA,
  Ultralytics, and YOLO11 version decisions. Exact versions and the model
  weight source remain pending and no installation was performed.
- Added `docs/reports/phase-02/P2-0_TRAINING_READINESS.md` with Dataset `PASS`,
  Experiment `PASS`, Environment `NOT READY`, GPU `PENDING`, Dependencies
  `PENDING`, and recorded P2-0-G1 through P2-0-G6 as PASS.
- Re-audited the live environment: Windows 11 `10.0.22631`, Python `3.13.6`,
  pip `25.3`, PyTorch not installed, Ultralytics not installed, CUDA
  unavailable, no NVIDIA GPU detected, Intel Iris Xe only, approximately
  `31.65 GiB` visible RAM, and Intel Core i5-1340P with 16 logical processors.
- Re-verified all three frozen dataset fingerprints against the training
  contract and confirmed the processed seven-class order without modifying
  the dataset.
- Updated the Phase 2 status record to mark P2-0 complete for review and P2-1
  environment setup as the next allowed step.
- No dependency, driver, dataset, or model weight was downloaded or installed;
  no training or evaluation was executed; no frozen EXP-001 field was changed.
- Validation: pytest `173 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-1 Training Environment Setup

- Selected `D. Controlled Cloud GPU` as the EXP-001 environment architecture
  because the current host has no NVIDIA GPU or CUDA support.
- Added `docs/designs/phase-02/P2-1_ENVIRONMENT_DECISION.md` with the selected option,
  rejected alternatives, cost/risk controls, and the impact on EXP-001.
- Added `docs/designs/phase-02/P2-1_DEPENDENCY_SPECIFICATION.md` with planned versions
  for Python `3.11.16`, PyTorch `2.11.0+cu128`, CUDA `12.8`, torchvision
  `0.26.0+cu128`, Ultralytics `8.4.158`, NumPy `2.2.6`, and key supporting
  packages.
- Added `docs/designs/phase-02/P2-1_SETUP_PLAN.md` with provisioning, installation,
  non-training verification, rollback, and runtime-freeze procedures.
- Updated the P2-0 readiness record with `Environment Decision: SELECTED`,
  `Provisioning: NOT STARTED`, and `Dependency Freeze: PENDING`.
- No cloud instance was provisioned; no dependency or model weight was
  downloaded; no training, evaluation, dataset mutation, or class mapping
  change was performed.
- Validation: pytest `173 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-2 Training Execution Authorization Review

- Added `docs/reports/phase-02/P2-2_CLOUD_ENVIRONMENT_REVIEW.md`. Provider, region,
  GPU, VRAM, CUDA capability, OS image, storage, cost estimate, and retention
  policy are explicitly `PENDING_SELECTION`.
- Added `docs/reports/phase-02/P2-2_DEPENDENCY_FREEZE.md`. Python, PyTorch, CUDA,
  torchvision, Ultralytics, and NumPy remain planned and uninstalled, so the
  dependency freeze remains `PENDING`.
- Added `docs/reports/phase-02/P2-2_EXP001_EXECUTION_REVIEW.md`. Verified the canonical
  EXP-001 dataset, model, seven-class output, paths, logging settings, and
  eight required metrics without modifying the configuration.
- Added `docs/reports/phase-02/P2-2_TRAINING_AUTHORIZATION.md`. Dataset, mapping, and
  experiment review pass; environment, dependencies, and GPU remain pending;
  authorization is `NOT GRANTED`.
- No cloud instance was provisioned; no dependency, wheel, or model weight was
  downloaded; no training or dataset mutation occurred.
- Validation: pytest `173 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-3 Cloud Provider Selection & Cost Review

- Added `docs/reports/phase-02/P2-3_CLOUD_PROVIDER_SELECTION.md` comparing AutoDL,
  Alibaba Cloud GPU ECS, Tencent Cloud GPU, and RunPod/Vast.ai-style
  alternatives.
- Selected AutoDL with an RTX 4090 24GB design target; RTX 3090 24GB is
  recorded only as a contingency and is not treated as the same runtime.
- Recorded a 40 GPU-hour planning limit and CNY 150 compute/storage ceiling
  for the AutoDL path. The estimates are not provider quotations.
- Recorded data-upload, credential, retention, image-identity, and cleanup
  requirements for the future isolated environment.
- Updated the P2-2 authorization checklist so Environment and GPU read
  `DESIGN SELECTED / NOT PROVISIONED`; Authorization remains `NOT GRANTED`.
- No cloud instance was provisioned; no dependency, dataset, or model weight
  was uploaded or downloaded; no training was executed.
- Validation: pytest `174 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-4-G3 AutoDL Dependencies Provisioning

- Connected to the user-provided AutoDL instance `bcb849a74f-38320766`
  (RTX 4090 24GB, Ubuntu 20.04.5 LTS) using key authentication.
- Created the isolated conda environment `ppe-exp001` with Python `3.10.21`
  without changing the base environment.
- Installed `torch 2.5.1+cu124`, `torchvision 0.20.1+cu124`,
  `torchaudio 2.5.1+cu124`, `ultralytics 8.4.157`,
  `opencv-python 5.0.0.93`, NumPy `2.2.6`, PyYAML `6.0.3`, tqdm `4.70.1`,
  matplotlib `3.10.9`, and psutil `7.2.2`.
- Verified `torch.cuda.is_available() == True`, RTX 4090 visibility, and
  successful PyTorch, Ultralytics, OpenCV, and NumPy imports.
- Recorded that planned Ultralytics `8.4.158` was not published by the
  configured index and pinned the resolved `8.4.157` instead.
- Added `docs/reports/phase-02/P2-4-G3_DEPENDENCY_VERIFICATION_REPORT.md`.
- No dataset transfer, model weight download, training execution, dataset
  mutation, mapping change, experiment change, or source-code change occurred.

### P2-4-G4 Dataset Transfer & Integrity Verification

- Transferred `data/processed/css-ppe-10-v1/` unchanged to
  `/root/autodl-tmp/datasets/css-ppe-10-v1/` using recursive SCP without
  compression or restructuring.
- Verified 5,604 total files, 2,799 images, 2,799 labels, and the frozen split
  counts: train 2,603, valid 114, test 82.
- Verified the processed seven-class order:
  `person, hardhat, no_hardhat, vest, no_vest, machinery, vehicle`.
- Verified the processed `data.yaml` SHA256 as `45cc2717...d2878a`, the
  upstream source `data.yaml` as `5c393e7...d21b34`, the source manifest as
  `ea0de4b0...f98d795`, and the processed manifest file as
  `dbfe43c4...831c2c`.
- Verified all 5,602 entries in `metadata/checksums.sha256` and all 5,604
  entries in the external full dataset manifest.
- Added `docs/P2-4-G4_DATASET_VERIFICATION_REPORT.md`.
- No training, `yolo train`, model weight download, label modification,
  annotation regeneration, class mapping change, or EXP-001 configuration
  change occurred.
- Validation: pytest `174 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-4 Final AutoDL Provisioning Gate

- Added `docs/reports/phase-02/P2-4_FINAL_PROVISIONING_REPORT.md` consolidating instance,
  runtime, dependency, dataset, safety, and final-gate evidence.
- Marked P2-4-G1 through P2-4-G6 PASS.
- Recorded Environment `READY`, Dataset `READY`, and Training
  `PENDING AUTHORIZATION`.
- Confirmed no training, `yolo train`, `python train.py`, model download,
  benchmark, or evaluation was executed.
- Updated project status and Phase 2 records to mark P2-4 complete without
  marking training, model, or experiment work complete.
- Validation: pytest `174 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5 EXP-001 Training Execution Authorization Review

- Added `docs/reports/phase-02/P2-5_TRAINING_AUTHORIZATION_REPORT.md` with a `BLOCKED` result.
- Recorded that the dataset, mapping, fingerprints, output paths, and runtime
  fingerprint were present, while unresolved training parameters, weight
  binary provenance, complete environment freeze, and explicit human
  authorization still prevented execution.
- No training, weight download, dataset modification, mapping modification, or
  configuration modification was performed.

### P2-5.1 EXP-001 Configuration Freeze Review

- Added `docs/reports/P2-5.1_CONFIGURATION_FREEZE.md` and
  `P2-5.1_CONFIGURATION_FREEZE_REPORT.md`.
- Froze model `YOLO11n`, Ultralytics `8.4.157`, starting weight reference
  `yolo11n.pt`, dataset `CSS-PPE-10-V1`, seven classes, `imgsz: 640`,
  `epochs: 100`, `batch: 16`, `optimizer: AdamW`, learning rate `0.001` with
  cosine schedule, `seed: 42`, single-GPU `cuda:0`, `workers: 8`, and the
  canonical output/log/report/checkpoint paths.
- Froze the EXP-001 augmentation configuration and recorded SHA256 hashes for
  the canonical configuration, schema, augmentation file, and alias template.
- Kept `execution_enabled: false` and training authorization `NOT GRANTED`.
- No model weight was downloaded, no training was executed, and no dataset or
  mapping was modified.
- Validation: pytest `175 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5.2 EXP-001 Weight Registration

- Registered the official Ultralytics `yolo11n.pt` initialization checkpoint
  from the `ultralytics/assets` `v8.3.0` release at
  `models/pretrained/yolo11n.pt`.
- Verified the `5,613,764` byte content length, MD5
  `261474e91b15f5ef14a63c21ce6c0cbb`, PyTorch checkpoint ZIP structure, and
  SHA256 `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Added `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` and
  `P2-5.2_WEIGHT_REGISTRATION_REPORT.md`.
- Updated the P2-2 authorization checklist, configuration-freeze record,
  training strategy, README, current-status record, and focused tests to
  distinguish the registered initialization weight from a training result.
- The weight remains Git-ignored and has not been transferred to the remote
  training environment. No training was executed, and no dataset, mapping, or
  EXP-001 configuration was modified.
- Validation: pytest `177 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5.3 EXP-001 Dependency Freeze

- Exported `ppe-exp001` to `locks/EXP-001/conda-environment.yml` with exact
  conda build strings and to `locks/EXP-001/pip-freeze-all.txt` with the
  complete resolved pip package set.
- Added `locks/EXP-001/conda-explicit.lock` and
  `locks/EXP-001/runtime-fingerprint.yaml`.
- Recorded AutoDL instance `bcb849a74f-38320766`, RTX 4090 UUID, `24,564 MiB`
  VRAM, compute capability `8.9`, NVIDIA driver `560.35.03`, CUDA driver API
  `12.6`, PyTorch CUDA runtime `12.4`, cuDNN `90100`, Python `3.10.21`,
  PyTorch `2.5.1+cu124`, and Ultralytics `8.4.157`.
- Verified all exported locks against the current remote output and confirmed
  `python -m pip check` reports no broken requirements.
- Added `docs/reports/P2-5.3_DEPENDENCY_FREEZE.md` and
  `P2-5.3_DEPENDENCY_FREEZE_REPORT.md`; updated the training authorization
  checklist to mark dependencies `FROZEN / VERIFIED`.
- No training was executed; no dependency was installed; no dataset, mapping,
  weight, or EXP-001 canonical configuration was modified.
- Validation: pytest `178 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5.4 EXP-001 Remote Weight Transfer Verification

- Transferred the registered `yolo11n.pt` initialization checkpoint to
  `/root/autodl-tmp/models/pretrained/yolo11n.pt` after confirming that the
  remote destination did not already exist.
- Verified the remote file exists and matches the local artifact at
  `5,613,764` bytes and SHA256
  `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Added `docs/reports/EXP-001_REMOTE_WEIGHT_VERIFY.md` with local path, remote
  path, size, SHA256 evidence, match result, and the `READY` decision.
- Updated `docs/weights/EXP-001_WEIGHT_MANIFEST.yaml` and the P2-2
  authorization checklist to record the remote copy as `VERIFIED`.
- No training or model execution occurred; no dataset, mapping, fingerprint,
  or EXP-001 canonical configuration was modified; no commit or push was
  performed.
- Validation: pytest `179 passed`; compileall passed; `git diff --check`
  passed; Charter diff empty.

### P2-5.5 EXP-001 Baseline Training Execution

- Executed the explicitly authorized YOLO11n baseline on AutoDL instance
  `bcb849a74f-38320766` using the frozen `CSS-PPE-10-V1` dataset, canonical
  EXP-001 configuration, and registered `yolo11n.pt` initialization weight.
- Training ran from `2026-09-22T08:00:02Z` to `2026-09-22T08:19:29Z`,
  completed 95 of 100 epochs, achieved the best validation result at epoch
  75, and stopped early after 20 epochs without improvement.
- Overall validation result: precision `0.899`, recall `0.649`, mAP50
  `0.767`, and mAP50-95 `0.480`; per-class metrics were also produced.
- Produced Git-ignored best and last checkpoints, training log, resolved
  arguments, epoch metrics, confusion matrices, PR/F1 curves, validation
  plots, run record, and frozen configuration snapshot.
- Best checkpoint: `5,479,891` bytes; SHA256
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
- Added `docs/reports/EXP-001_TRAINING_EXECUTION_REPORT.md` and marked M-004
  `已经实现`. M-005 remains `待实现`; Phase 3 has not started.
- Recorded that Ultralytics downloaded `yolo26n.pt` only for its one-time AMP
  compatibility check. The log states that it was not used for training and
  it did not replace the frozen YOLO11n initialization weight.
- The one-run authorization record is now `CONSUMED`; no dataset, mapping,
  fingerprint, or canonical configuration was modified, and no second run is
  authorized.
- Verified the host was idle and issued an AutoDL shutdown after archiving the
  evidence; no remote dataset, weight, or run artifact was deleted.

## 2026-09-21

### Phase 0 Foundation initialized

- Created the complete engineering directory and Python package skeleton.
- Added six YAML configuration files with future-phase status markers.
- Added path, YAML loading, logging, timing, system information, and detection
  schema foundations.
- Added explicit `NotImplementedError` boundaries for Phase 1 through Phase 9
  business modules.
- Added the locked project charter, master plan, ten phase documents, ADR log,
  dataset card, open-source usage record, risk register, and test gate system.
- Added Phase 0 unit tests and repository retention files.
- Initialized the Git repository without committing or pushing.

### Phase 0 Gate verified

- `python -m pytest`: 92 passed.
- `python -m compileall .`: passed.
- `git diff --check`: passed with all project files in intent-to-add state,
  then the intent-to-add index state was removed.
- G0-1 through G0-13: PASS.
- Phase status updated to `已经实现`; all MUST and Extension business statuses
  remain `待实现`.

### Pre-Phase 1 Reference Intake

- Added `docs/09_REFERENCE_ASSETS.md`.
- Added ADR-007 and ADR-008.
- Added RISK-011 and RISK-012.
- Updated AGENTS mandatory reading order.
- No business implementation.
- No teacher asset copied.
- Validation: pytest 99 passed; compileall passed.

### Phase 1A Dataset Source & License Gate

- Added `docs/10_DATA_SOURCE_EVIDENCE.md`.
- Verified the original Roboflow Universe Construction Site Safety project,
  CC BY 4.0 license, source class names, version 27 counts, split, and download
  mechanism.
- Added ADR-009 to freeze Roboflow CSS version 27 with the `yolov8` export.
- Updated the dataset card to `SOURCE VERIFIED / NOT DOWNLOADED`.
- Marked P1A `已经实现`; P1B through P1E remain `待实现`.
- M-001 remains `待实现`.
- No dataset, model weight, conversion, commit, or push.
- Validation: pytest 110 passed; compileall passed; `git diff --check` passed;
  charter diff empty.

### Phase 1B Download & Raw Snapshot Tooling

- Replaced the dataset placeholder with P1B-only snapshot, inspection, file
  counting, deterministic manifest, archive verification, and image-label pair
  validation capabilities.
- Added `inspect`, `snapshot`, and `verify` commands to
  `scripts/prepare_dataset.py`; conversion, remapping, cleaning, and
  deduplication remain intentionally unimplemented.
- Added a synthetic fixture and offline tests so default pytest never requires
  the real CSS download.
- User downloaded workspace `roboflow-universe-projects`, project
  `construction-site-safety`, version `27`, format `yolov8` through the
  Roboflow API with their own account.
- Copied the extracted directory without modification to the Git-ignored
  external snapshot and generated `source.json`, `counts.json`,
  `checksums.sha256`, and a concise Markdown snapshot summary.
- Actual snapshot: 2,799 images and labels, 5,601 manifest files, zero missing
  labels, zero orphan labels, 23 empty label files, zero zero-byte images, and
  22 exact SHA-256 duplicate files retained without deletion.
- Actual `data.yaml`: 10 classes; all five target semantics are present, but the
  count and class metadata conflict with the P1A-frozen 2,801-image, 25-class
  source record.
- P1B remains `实现中 / VALIDATION FAILED`; P1C has not started; M-001 remains
  `待实现`. No source data was edited to resolve the mismatch.
- Validation: pytest 125 passed; compileall, `git diff --check`, and Charter
  diff are recorded in the final Phase 1B validation report for this working
  tree.

### P1B.1 Dataset Freeze Correction

- Added ADR-010: dataset freeze requires a complete export artifact
  fingerprint because a Roboflow version number alone is not a training
  artifact identity.
- Recorded `RISK-015`: version metadata differs from the materialized export
  artifact.
- Preserved the historical CSS-V1 record and marked it
  `BLOCKED / NEEDS FREEZE CORRECTION`.
- Added `CSS-V1.1 Candidate` with the observed YOLOv8 artifact fingerprint:
  10 classes, 2,799 images, train/valid/test 2,603/114/82, `data.yaml`
  SHA256 `5c393e74...d21b34`, and manifest SHA256 `ea0de4b0...f98d795`.
- The candidate remains explicitly `Candidate, not frozen`.
- No dataset file was modified, downloaded, remapped, or deleted.
- P1C remains not started and M-001 remains `待实现`.

### P1B.2 Dataset Candidate Decision Gate

- Added `docs/11_DATASET_CANDIDATE_EVALUATION.md` comparing CSS-V1 and
  CSS-V1.1 by source identity, artifact fingerprint, counts, classes, PPE
  relevance, advantages, risks, and V1 suitability.
- Added ADR-011: V1 dataset selection prioritizes reproducibility, verified
  artifact identity, PPE task relevance, license clarity, and training
  feasibility rather than maximum class count.
- CSS-V1 remains `BLOCKED / NEEDS FREEZE CORRECTION`; CSS-V1.1 remains
  `Candidate, not frozen`.
- No dataset was downloaded or modified, no class conversion was performed,
  and no model was trained.
- P1C remains not started and M-001 remains `待实现`.

### P1B.3 Final Dataset Freeze Decision

- Added `docs/12_DATASET_FREEZE_DECISION.md`.
- Rejected CSS-V1 because its metadata identity cannot be bound to a
  materialized artifact.
- Promoted `CSS-V1.1 Candidate` to the frozen dataset ID `CSS-PPE-10-V1`.
- Froze the 10-class list, `data.yaml` SHA256, manifest SHA256, 2,799 images,
  and train/valid/test `2,603/114/82`.
- Added ADR-012: V1 dataset identity is defined by artifact fingerprint, not
  only by a Roboflow version number.
- Added P1B-F1 through P1B-F5 freeze gates.
- No dataset was downloaded or modified, no class conversion was performed,
  and no model was trained.
- P1C remains not started and M-001 remains `待实现`.

### P1C-0 Class Mapping Design Gate

- Added `docs/13_CLASS_MAPPING_DESIGN.md` with the frozen dataset identity,
  ten-class source distribution, and candidate mappings A, B, and C.
- Documented training, inference, rule-engine, tracker, association, event, and
  LLM-report implications without making a final mapping selection.
- Added ADR-013: class mapping must be frozen before label conversion,
  processed dataset generation, or training.
- Added RISK-016 for incorrect class mapping reducing compliance detection
  quality.
- Added P1C-0 design gates and offline tests.
- No source data, labels, `data.yaml`, or frozen fingerprint was modified.
- P1C conversion remains not started and M-001 remains `待实现`.

### P1C-1 Class Mapping Decision Gate

- Added `docs/14_CLASS_MAPPING_DECISION.md`.
- Selected Strategy C and froze the seven-class training mapping while
  preserving the five ADR-003 compliance classes at IDs 0 through 4.
- Added `machinery` and `vehicle` as scene-context classes.
- Explicitly discarded `Mask`, `NO-Mask`, and `Safety Cone` with reasons and
  future-extension rules.
- Added ADR-014 and strengthened RISK-016 with the pre-conversion mapping
  freeze requirement.
- Added P1C-1 gates and offline mapping-identity tests.
- No source data, labels, `data.yaml`, or frozen fingerprint was modified.
- P1C conversion remains not started and M-001 remains `待实现`.

### P1C-2 Dataset Conversion Implementation

- Added `docs/dataset_contracts/CSS-PPE-10-V1-MAPPING.yaml` as the frozen
  `PPE-MAPPING-V1` source-to-training contract.
- Added `services/dataset_conversion_service.py` with deterministic
  image/label conversion, source fingerprint verification, per-image SHA-256
  checks, class mapping, discard accounting, metadata generation, and safe
  output replacement.
- Added `convert` to `scripts/prepare_dataset.py`; the default source is
  `CSS-PPE-10-V1` and the default mapping is `PPE-MAPPING-V1`.
- Generated the Git-ignored `data/processed/css-ppe-10-v1/` artifact:
  train/valid/test `2,603/114/82`, total `2,799` images and labels, seven
  target classes, `30,375` retained boxes, and `8,460` discarded boxes.
- Discarded boxes: `Mask` `1,792`, `NO-Mask` `3,362`, and `Safety Cone`
  `3,306`; unknown source class IDs: `[]`.
- Added fake-free offline tests for deterministic mapping, unknown IDs,
  discard statistics, coordinate preservation, image hash preservation,
  output YAML, source immutability, and repeatability.
- Added `docs/15_DATASET_CONVERSION_REPORT.md` and P1C-2 gates.
- M-001 remains `待实现`; P1D, training, commit, and push were not started.

### P1D-0 Dataset Quality Validation Design Gate

- Added `docs/16_DATASET_QUALITY_PLAN.md` with frozen observation-only
  principles and explicit Q1 through Q9 quality dimensions.
- Froze normalized bbox thresholds: small `< 0.01`, medium `< 0.09`, and
  large `>= 0.09`; small-object risk is `LOW < 20%`,
  `MEDIUM 20% to < 40%`, and `HIGH >= 40%`.
- Froze the planned perceptual duplicate algorithm and threshold as 64-bit
  dHash with Hamming distance `<= 5`, while leaving real-data execution to
  P1D-1.
- Added `utils/quality_metrics.py` for deterministic bbox validation, size
  buckets, class distribution, exact duplicate grouping, and cross-split
  leakage grouping.
- Added `services/dataset_quality_service.py` as a read-only validator
  architecture. It records dataset manifest hashes before and after analysis
  and exposes no repair or write operation.
- Added offline tests for plan structure, immutability, invalid bbox
  detection, deterministic class distribution, deterministic duplicate
  detection, leakage observation, and unchanged dataset hashes.
- Added ADR-015 and RISK-017. No real dataset quality report was generated,
  no dataset was modified, and no model was trained.
- P1C-2 conversion implementation is recorded as manually reviewed PASS;
  P1D-0 is completed for review; P1D real execution is not started; M-001
  remains `待实现`; no commit or push was performed.

### P1D-1 Real Dataset Quality Validation

- Executed the observation-only validator against the real
  `data/processed/css-ppe-10-v1/` payload.
- Fixed the hash scope to `data.yaml`, train/valid/test images, and labels;
  metadata and report files are excluded from the payload fingerprint.
- Verified payload hash
  `bc762204e2305164cfdbc492d15269b84c4ce4ff3cfdcdc805baf84c5616237b`
  before and after validation, covering 5,599 payload files.
- Structure result: PASS for 2,799 images, 2,799 labels, and seven classes
  across train `2603` / valid `114` / test `82`.
- Class distribution: 30,375 valid boxes, 23,421 PPE five-class boxes, and a
  maximum-to-minimum class ratio of approximately `6.20`.
- Empty labels: 32 (`1.14%`), classified as image-without-object and retained.
- Bounding boxes: 30,375 valid lines, zero invalid bbox, invalid class,
  invalid coordinate, or malformed line.
- Duplicate analysis: zero exact image duplicate groups and five dHash
  candidate pairs at Hamming distance `<= 5`.
- Leakage analysis: zero exact cross-split groups; two perceptual cross-split
  candidate groups across `valid` and `test`, retained as risk evidence only.
- Recorded HIGH small-object risk for `hardhat`, `no_hardhat`, `vest`, and
  `vehicle`, plus MEDIUM risk for `person` and `no_vest`.
- Generated `docs/17_DATASET_QUALITY_REPORT.md` and Git-ignored
  `data/processed/css-ppe-10-v1/metadata/quality_report.json`.
- Added G1D1-1 through G1D1-10, all PASS. No data was modified, no model
  was trained, and no commit or push was performed.
- P1D-1 is completed/PASS; P1E is not started; M-001 remains `待实现`.

### P1E-0 Dataset Release & Training Preparation Design Gate

- Added `docs/dataset_contracts/CSS-PPE-10-V1-TRAINING.yaml`, binding the
  processed dataset, `PPE-MAPPING-V1` class order, source/processed
  fingerprints, quality report, and immutable training-release boundary.
- Added the `experiments/` structure with README, baseline and augmentation
  design templates, and dedicated `runs/` and `reports/` retention
  directories.
- Added `configs/training/schema.yaml` and
  `configs/training/exp001_baseline.yaml` as non-executable configuration
  contracts. Unresolved values remain explicit `PENDING_DESIGN_REVIEW`
  placeholders.
- Added `docs/18_TRAINING_STRATEGY.md` comparing YOLO11n and YOLO11s,
  defining the EXP-001 baseline, recording the required experiment fields, and
  freezing the required metric list.
- Added ADR-016: all experiments must be configuration-driven and manual
  command-line-only experiments are not accepted as reproducible records.
- Added RISK-018 for experiment reproducibility risk.
- Added G1E0-1 through G1E0-7 and focused tests for the contract, schema,
  experiment ID format, no training execution, dataset fingerprints, and
  Charter integrity.
- No model weight was downloaded, no training was executed, no dataset or
  label was modified, and no commit or push was performed.
- P1E-0 is completed for review; P1E itself remains not started; M-001 remains
  `待实现`.

### P1E-1 Baseline Training Preparation Review

- Added the P1E-1 training contract audit, experiment configuration audit,
  training environment audit, reproducibility checklist, and EXP-001
  training runbook under `docs/reports/`.
- Verified the frozen training contract against all three materialized SHA-256
  fingerprints and confirmed the seven-class `PPE-MAPPING-V1` order.
- Made the canonical EXP-001 configuration authoritative and converted
  `experiments/configs/baseline.yaml` into an explicit template alias. The
  canonical experiment ID is unique and matches `EXP-\d{3}`.
- Added explicit dataset-contract, processed-dataset, model, output, log,
  report, checkpoint, device, and hyperparameter-status fields to the
  training schema and EXP-001 template.
- Environment audit: Python `3.13.6`; PyTorch `NOT INSTALLED`;
  Ultralytics `NOT INSTALLED`; CUDA unavailable; no NVIDIA GPU detected.
  Result: `NOT READY FOR TRAINING`.
- No dependency was installed, no model weight was downloaded, no training was
  executed, and no dataset was modified.
- P1E-1 is completed with `P1E1-G1` through `P1E1-G7` PASS. The next allowed
  step is P2 Training Execution Preparation; training remains prohibited
  pending a new instruction.
- M-001 remains `待实现`.

### P2-7 EXP-001 Training Result Freeze

- Added the result freeze report and machine-readable best-model manifest with
  dataset/config/weight identity, best epoch, final training-validation metrics,
  runtime fingerprint, command/epoch-loop durations and 29 hashed artifacts.
- Verified both dataset manifests and preserved dataset, mapping, frozen config,
  checkpoints, dependency locks and the existing Charter status change.
- Current Phase is `P2-7 Training Result Freeze`; EXP-001 Training is `COMPLETED`.
- No training, evaluation, Phase 3 work, commit or push was performed.

### P3-1 EXP-001 Test Evaluation (Awaiting Human Review)

- Implemented ValService, the evaluation CLI and deterministic replayable metrics;
  added a fixed test protocol and evaluation-only dependency pins under EVAL-001.
- Evaluated the unchanged EXP-001 best.pt on 82 test images / 561 boxes. Seven-class
  P/R/mAP50/mAP50-95: 0.798669 / 0.712315 / 0.733203 / 0.465122.
- Retained all seven per-class AP entries, the five PPE aggregate, confusion matrix,
  per-image predictions/ground truth/errors and small-object recall diagnostics.
- Cross-checked matching/AP against Ultralytics 8.4.157 and replayed retained results.
- Added PHASE_3_EVALUATION_REPORT.md and EXP-001_EVALUATION_SUMMARY.json. M-005
  technical evidence is complete, awaiting human review; comparison/model-selection
  gates remain pending. No Phase 4 entry, training, commit or push.
- Dataset, mapping, weights, training configuration and Phase 2 release artifacts
  were preserved. The CPU evaluation environment is separate from the training lock.
