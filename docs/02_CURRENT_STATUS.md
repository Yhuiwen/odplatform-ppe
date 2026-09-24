# Current Status

This is the single entry point for the latest project state. Historical
implementation and validation details are preserved in the
[Phase 4 → Phase 5 handover](worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md)
and the linked phase reports. Earlier snapshots may describe past pending
reviews; the statuses below reflect the current accepted records.

## Current Phase

- Phase 8 IN PROGRESS — LLM & Agent. P8-0 Architecture and Contract Freeze is
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-1 Deterministic Safety
  Analytics and Context is `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`.
  P8-2 Structured Report Contract and Grounding Validator is
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-3 Deterministic Template
  Fallback is `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-4 Provider
  Adapter Boundary and Untrusted Output Parsing is
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-5 Real Provider E2E,
  Grounding Enforcement and Safe Fallback is
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. P8-5D Sanitized Provider
  Schema Diagnostics is `HUMAN REVIEW PASS`. P8-5P Provider Prompt Schema
  Conformance Fix is `HUMAN REVIEW PASS`. P8-6 Basic Agent Architecture
  Freeze is `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. P8-6.1 Static
  Read-only Tool Registry and Permission Layer is `HUMAN REVIEW PASS`. P8-6.2
  Deterministic Agent Planner is `HUMAN REVIEW PASS`. P8-6.3 Agent Audit is
  `HUMAN REVIEW PASS`. P8-6.4 LLM-Assisted Agent Planning Architecture is
  `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. P8-6.4.1 Plan Candidate
  Parser and Validator is `HUMAN REVIEW PASS`. P8-6.4.2 LLM Planner Adapter
  is `HUMAN REVIEW PASS`. P8-6.4.3 AgentService Orchestration is
  `HUMAN REVIEW PASS`, and the P8-6 Agent implementation is released as the
  interim checkpoint `phase-8-controlled-agent-complete`; no real provider
  planning request, durable audit store, memory, autonomous loop or Phase 9
  work has started. The authoritative P8-6 design is
  `docs/designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md`; the original
  P8-0 design remains at
  `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`, and ADR-023 freezes a
  deterministic, read-only analytics/context path, provider-independent LLM
  boundary, grounded structured report, local fallback and allowlisted Basic
  Agent tools. P8-1 reads only through `EventQueryService` and builds canonical
  `phase8-context-v1` payloads. P8-2 adds the provider-independent
  `phase8-report-v1` contract, context-fingerprint binding and fail-closed
  reference/numeric/privacy validation. P8-3 adds deterministic local report
  generation over the same context and validates it through the unchanged
  P8-2 boundary. P8-4 adds a provider-independent request/transport boundary,
  strict bounded JSON parsing and candidate-plus-validation orchestration.
  P8-5 adds one configuration-driven OpenAI-compatible chat-completions
  transport, provider-first orchestration and deterministic provider-timeout,
  auth, rate-limit, malformed-output and semantic-failure fallback. An
  initial human-executed OpenAI-compatible request to `deepseek-flash`
  received a response, passed strict JSON syntax parsing, but was rejected
  during `phase8-report-v1` construction with `REPORT_SCHEMA_INVALID`; the
  unchanged fallback then passed. That failure remains historical evidence.
  P8-5D adds bounded sanitized schema diagnostics without weakening the
  report schema or grounding boundary. P8-5P upgrades only provider request
  construction to `phase8-provider-prompt-v2` with an exact schema description
  generated from the authoritative dataclasses and enums, without changing or
  weakening the report schema, parser, grounding validator or fallback. A
  final separately authorized manual request followed prompt v2 and returned
  `PROVIDER_VALIDATED`: transport, strict JSON, `phase8-report-v1` and
  grounding all passed with `PROVIDER`, `degraded=false` and fallback not
  used. P8-6 freezes only the Basic Agent boundary, static read-only tool
  registry, deny-by-default permissions, audit policy and unchanged P8-5
  fallback reuse. P8-6.1 implements the immutable registry, deny-by-default
  permission policy, bounded argument validation, four service adapters and
  non-persistent audit metadata, and has passed human review. P8-6.2 adds a
  deterministic planner with `AgentIntent`/`AgentPlan`, exact tool mapping,
  bounded argument validation, registry resolution and permission preflight;
  it never executes a tool and introduces no LLM tool calling, provider
  change or Agent framework, and has passed human review. P8-6.3 adds the
  immutable `phase8-agent-audit-v1` event, append-only in-memory store
  abstraction, bounded metadata sanitization and `AgentAuditService`; durable
  persistence remains unimplemented. P8-6.4 passed human review and defines
  the untrusted LLM candidate boundary, strict candidate validation,
  deterministic final-plan construction, registry-only execution, permission
  rechecks, audit integration and deterministic fallback. P8-6.4.1 implements
  the `phase8-agent-plan-candidate-v1` schema, bounded strict JSON parser,
  request-binding/intent/tool/argument/permission validation and deterministic
  conversion to `phase8-agent-plan-v1`; it never calls
  `ToolRegistry.execute`. P8-6.4.2 adds a provider-independent planner
  request builder, injected candidate-client boundary, strict validator
  integration, bounded audit metadata and deterministic fallback. Invalid or
  failed candidates fall back to the deterministic planner; forbidden
  candidate capabilities are refused without privilege escalation.
  P8-6.4.3 adds typed `AgentRequest`/`AgentResult`, `AgentService`
  orchestration, validated-plan-only registry execution, append-only audit
  recording for planner/tool outcomes, deterministic fallback support and
  audit-unavailable fail-closed behavior. M-021, M-022 and M-023 remain
  `待实现`; durable audit storage, memory, autonomous loops, real provider
  planning requests and Phase 9 remain not started.
- Phase 7 COMPLETE / RELEASED — Web & Alerts. Base commit
  `a30b73c080c18d010fbaa08642868e86acb68022` carries annotated tag
  `phase-7-web-alert-platform-complete`; final release closure publishes
  annotated tag `phase-7-release-freeze-complete`. Phase 7-0 through Phase 7-6
  are human-reviewed PASS. Phase 7-6 adds the TTS alert adapter, a
  service-owned MP4/USB/RTSP monitoring loop and the Streamlit realtime page;
  MP4, USB Camera, native TTS, browser Streamlit and controlled local RTSP
  validation all passed. M-007 annotated demo video is implemented, validated
  on a real 47/47-frame MP4 and human-reviewed PASS. M-007 remains `待实现`
  in the locked Charter pending Phase 9 acceptance. Remote RTSP reconnect
  behavior, reconciliation automation and retention remain pending.
  M-015 through M-020 remain `待实现` in the locked Charter until full
  acceptance.
- Phase 6 COMPLETE / RELEASED — PPE Compliance Event Engine. Release tag
  `phase-6-compliance-event-engine-complete` targets
  `e24e31ae635e5d5cd1129a9fb519a59b7014f802`.
- Phase 5 COMPLETE / RELEASED — Tracking & Association. Release tag
  `phase-5-tracking-association-complete` targets
  `6da6213f0cc541765f231c81b4264a98f01d5f4a`.
- P5-0, P5-1 and P5-2 are human-reviewed PASS. P5-3 synthetic pipeline
  validation is PASS. The frozen-checkpoint/video runtime validation is
  prepared with an execution-disabled config and passed static preflight, but
  is `BLOCKED / NOT RUN` because this host has no `torch` or `ultralytics`.
- Historical state: Phase 5 IN PROGRESS during P5-0 through the final audit.
  P5-3-G5 was originally recorded as `BLOCKED / NOT RUN`. A subsequent
  explicit human release authorization created the annotated tag
  `phase-5-tracking-association-complete` at commit
  `6da6213f0cc541765f231c81b4264a98f01d5f4a`; the current documentation is
  now synchronized to `COMPLETE / RELEASED`.
- Phase 4 remains `Offline Inference COMPLETE` for its released offline scope.
- Current next allowed step: `PHASE 8 FINAL INTEGRATION REVIEW / DO NOT START
  PHASE 9 OR IMPLEMENT DURABLE AUDIT STORE, MEMORY, AUTONOMOUS LOOP OR REAL
  PROVIDER PLANNING CALLS`.

## Last Completed

- Phase 8 P8-6.3 Agent Audit:
  `HUMAN REVIEW PASS`. Added the immutable
  `phase8-agent-audit-v1` `AuditEvent`, frozen audit statuses, bounded
  allowlist metadata sanitization, an append-only in-memory store
  abstraction and `AgentAuditService`. The service records deterministic
  planner identities, tool success/failure/refusal projections and unknown
  tool attempts without retaining raw questions, arguments, provider output,
  credentials or filesystem/database paths. Durable audit storage remains
  unimplemented.
- Phase 8 P8-6.4.1 Plan Candidate Parser and Validator:
  `HUMAN REVIEW PASS`. Added the immutable
  `phase8-agent-plan-candidate-v1` contract, a bounded strict UTF-8 JSON
  parser, deterministic request binding and semantic checks for intent,
  tool name/version, arguments, registry existence and deny-by-default
  permissions. The validator constructs only a new
  `phase8-agent-plan-v1`; focused tests prove that
  `ToolRegistry.execute` is never called. No provider request,
  AgentService orchestration or tool execution was added.
- Phase 8 P8-6.4.2 LLM Planner Adapter:
  `HUMAN REVIEW PASS`. Added a deterministic
  provider-independent planner request builder, an injected candidate-client
  boundary returning untrusted bytes, strict parser/validator integration,
  bounded audit metadata and deterministic fallback. Invalid candidates and
  provider failures fall back to the deterministic planner; forbidden
  candidate capabilities are refused without reinterpretation. The adapter
  never calls `ToolRegistry.execute`, issues no real provider request and does
  not add AgentService orchestration.
- Phase 8 P8-6.4.3 AgentService Orchestration:
  `HUMAN REVIEW PASS`. Added the typed
  `phase8-agent-request-v1` and `phase8-agent-result-v1` contracts plus the
  `AgentService` orchestration boundary. The service accepts only a validated
  `phase8-agent-plan-v1`, executes at most one request through the static
  `ToolRegistry`, records planner and tool outcomes in the append-only audit
  model, preserves deterministic planner fallback, returns structured
  refusal/tool/audit failures and fails closed when a tool-result audit cannot
  be appended. It adds no direct candidate execution, provider call, durable
  audit store, memory, autonomous loop or dynamic tool capability. The
  implementation is included in interim checkpoint tag
  `phase-8-controlled-agent-complete`.
- Phase 8 P8-6.4 LLM-Assisted Agent Planning Architecture:
  `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. Separated the
  untrusted `phase8-agent-plan-candidate-v1` contract from the unchanged
  `phase8-agent-plan-v1`; froze strict parsing, deterministic validation,
  registry-only execution, deny-by-default permission rechecks, append-only
  audit integration, provider failure fallback and a bounded privacy boundary.
  The freeze added no planner implementation or provider request; P8-6.4.1
  subsequently implemented only the candidate parser/validator slice.
- Phase 8 P8-6.2 Deterministic Agent Planner:
  `HUMAN REVIEW PASS`. Added the versioned
  `AgentPlan` contract, deterministic supported/unknown/forbidden intent
  classification, exact mapping to the four frozen read-only tools, bounded
  question and argument validation, registry resolution and permission
  preflight. The planner cannot execute a tool and adds no LLM, network,
  provider or Agent framework dependency.
- Phase 8 P8-6.1 Static Read-only Tool Registry and Permission Layer:
  `HUMAN REVIEW PASS`. Exactly four immutable
  tools are registered; permissions are deny-by-default; unknown tools,
  forbidden capabilities and unknown or mutation-like arguments fail closed;
  all handlers delegate to existing services; each execution emits bounded
  audit metadata without persisting it yet.
- Phase 8 P8-6 Basic Agent Architecture Freeze:
  `ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`. The design defines a
  deterministic Agent planner, static
  read-only registry with `get_safety_summary`, `get_event_statistics`,
  `get_event_details` and `generate_safety_report`, deny-by-default
  permissions, bounded execution, append-only audit, explicit refusal
  behavior and reuse of the unchanged P8-5 provider/fallback path. No Agent
  code, LLM tool calling, provider request, dependency or upstream contract
  change was made.
- Phase 8 P8-5 Release Checkpoint:
  `P8-0 THROUGH P8-5 COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. The
  interim checkpoint records the deterministic analytics/context, grounded
  report, fallback, provider boundary, provider validation and documentation
  under annotated tag `phase-8-provider-pipeline-complete`. It is not the
  Phase 8 final release. No provider request was issued during this release
  task. At checkpoint creation, P8-6 was `READY / NOT STARTED`; its subsequent
  architecture freeze passed human review and is recorded above. P8-6.1
  implements the static registry and permission layer, and P8-6.2 adds the
  deterministic planner without tool execution. P8-6.3 adds append-only
  in-memory audit recording with privacy filtering. Basic Agent orchestration
  and Phase 9 remain not started.
- Phase 8 P8-5 Final Real Provider Validation:
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`. A separately authorized
  manual request to the OpenAI-compatible
  `deepseek-flash` path returned `PROVIDER_VALIDATED` with transport PASS,
  strict JSON PASS, `phase8-report-v1` PASS, provider grounding VALID,
  `generation_path=PROVIDER`, `degraded=false`, no safe error, no schema
  diagnostics and no fallback. This audit issued no further provider request.
  Earlier configuration non-execution, schema rejection/fallback and prompt
  conformance evidence remain preserved. The validation audit itself performed
  no commit, tag or push; checkpoint publication is recorded separately above.
- Phase 8 P8-5P Provider Prompt Schema Conformance:
  `HUMAN REVIEW PASS`.
  Added a machine-derived compact schema description for the unchanged
  `phase8-report-v1` contract and embedded it in provider request
  construction. Prompt v2 now enumerates top-level and nested required fields,
  exact enum values, nullable-but-required fields, closed-object policy,
  empty-array behavior, provider candidate constants and reference policy.
  The change addresses the prior loose-prose prompt gap without modifying the
  report schema, strict parser, grounding validator, fallback behavior,
  context contract or fingerprint algorithm. Focused provider tests passed
  (`80 passed`) and the full repository gate passed (`539 passed, 1 skipped`).
  No real provider request or `--execute` was performed at that subphase.
- Phase 8 P8-5D Sanitized Provider Schema Diagnostics:
  `HUMAN REVIEW PASS`. Extended the existing
  strict parser failure path with a bounded, deterministic diagnostic model
  for `REPORT_SCHEMA_INVALID`. The public failure code remains unchanged, no
  invalid report is repaired or partially accepted, diagnostics are capped at
  20 with a `truncated` flag, and only safe JSON paths, project-owned
  categories, expected type or constraint and actual JSON type are exposed.
  Raw field values, unknown field names, raw provider content, prompts,
  context payloads, credentials and authorization headers are excluded.
  `ReportService` and the smoke CLI propagate only the sanitized metadata;
  provider failure still routes to the unchanged `TemplateFallback`. No real
  provider request or `--execute` was performed at that subphase.
- Phase 8 P8-5R Real Provider Post-Execution Audit:
  `REAL PROVIDER EXECUTED / PROVIDER REPORT SCHEMA REJECTED / TEMPLATE
  FALLBACK PASS / HUMAN REVIEW PENDING`. The human operator executed one
  OpenAI-compatible request against
  `https://api.deepseek.com/chat/completions` with model `deepseek-flash`.
  The provider response envelope and non-empty message content were received,
  and strict JSON parsing succeeded. `phase8-report-v1` construction then
  failed with `REPORT_SCHEMA_INVALID`, so provider grounding validation was not
  reached. The unchanged `TemplateFallback` generated a report and passed the
  unchanged grounding validator; that `valid` status belongs only to fallback.
  Raw provider content was not persisted, so the exact schema mismatch cannot
  be recovered. This audit issued no additional provider request.
- Phase 8 P8-5:
  `COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`.
  Added one configuration-driven
  OpenAI-compatible chat-completions transport behind the frozen P8-4
  `ProviderTransport` boundary, environment-only credential resolution,
  finite timeout and bounded response handling. `ReportService` now provides
  provider-first orchestration: only a strictly parsed candidate that passes
  the unchanged P8-2 grounding validator can be returned as
  `PROVIDER_VALIDATED`. Semantic and operational failures route to the
  unchanged deterministic `TemplateFallback`; fallback failure returns
  `REPORT_UNAVAILABLE` without exposing an invalid report. Historical attempts
  include a configuration non-execution and a `REPORT_SCHEMA_INVALID`
  rejection with fallback PASS; these remain preserved. The final separately
  authorized manual request followed prompt v2 and passed strict parsing,
  schema construction and grounding, returning `PROVIDER_VALIDATED` with
  fallback not used. No credential value, provider SDK, model, dataset or
  upstream pipeline was changed.
- Phase 8 P8-4: `HUMAN REVIEW PASS`. Added the
  provider-independent `SafetyLLMClient`, deterministic request builder,
  injectable transport protocol and strict untrusted-output parser. Provider
  requests contain only the safe P8-1 context with construction time removed,
  preserve the frozen fingerprint, use fixed request/prompt/schema versions,
  require a finite timeout and enforce a `262144`-byte response limit. Provider
  responses must be exact bounded UTF-8 JSON, cannot contain duplicate keys or
  non-finite values, and are returned only as `unvalidated`
  `phase8-report-v1` candidates. `ReportService.generate_provider_report()`
  passes the candidate through the unchanged P8-2 validator without silently
  selecting fallback. No real provider, transport, SDK, API key, network call,
  model, dataset or upstream pipeline was changed.
- Phase 8 P8-3: `HUMAN REVIEW PASS`. Added the
  deterministic `TemplateFallback` and minimal `ReportService` orchestration.
  The fallback accepts only `phase8-context-v1`, reuses
  `SafetyContextBuilder.fingerprint(context)`, emits
  `TEMPLATE_FALLBACK` with `degraded=true`, copies all unavailable fields
  exactly, and reports only metrics/facts/evidence present in the context.
  `ReportService` runs the unchanged P8-2 grounding validator and returns
  `VALID` only on success; missing, malformed or inconsistent required metrics
  fail closed. No provider SDK, network call, real LLM invocation or upstream
  pipeline change was introduced.
- Phase 8 P8-2: `HUMAN REVIEW PASS`. Added the
  provider-independent `phase8-report-v1` schema and deterministic
  `SafetyReportGroundingValidator`. Reports bind to the P8-1 context
  fingerprint; fact, metric, event, tracker-scoped track, source, evidence and
  structured numeric references are validated against the supplied context.
  Invalid, unknown, unavailable, ungrounded, contradictory or path-leaking
  reports fail closed. No provider SDK, network call, LLM invocation, fallback
  implementation or upstream pipeline change was introduced.
- Phase 8 P8-1: `HUMAN REVIEW PASS`. Added
  deterministic `SafetyAnalyticsService`, read-only bounded analytics over
  `EventQueryService`, opaque source aggregation, `phase8-context-v1` schemas,
  canonical serialization and a method-level context fingerprint. Focused
  tests cover exact counts, interval boundaries, deterministic ordering, empty
  and partial data, source-path exclusion, missing required fields,
  schema validation and reproducibility. No provider, network call,
  dependency or upstream implementation was changed.
- Phase 2 Training: `已经实现`; EXP-001 baseline training completed using its
  single authorized run. M-004：已经实现.
- Phase 3 Evaluation: `已经实现`; model comparison, selection and independent
  evaluation were completed and human review passed. M-005：已经实现.
- Phase 4 Offline Inference: `已经实现` for the scope in ADR-018; offline release
  gates are PASS. Full M-006/M-007 acceptance was not implied by that release.
- Phase 5 Tracking & Association: `已经实现（COMPLETE / RELEASED）`; P5-0 froze `TrackResult`,
  `AssociationResult`, person-only ByteTrack boundaries and unknown-safe
  containment/IoU policy. P5-1 implements the person-only ByteTrack adapter
  behind that boundary. P5-2 implements conservative Person-PPE association
  with explicit `unknown`. P5-3 validates the complete adapter composition
  with deterministic synthetic frames; at the Phase 5 release point, real
  runtime and integrated video verification were blocked by missing runtime
  dependencies. Phase 7-5 later executed one real MP4 path with Ultralytics
  ByteTrack and the association adapter, so M-009 and M-010 now have
  `IMPLEMENTED / Phase 7-5 Runtime Evidence Recorded / Charter Acceptance
  Pending` status. The locked Charter statuses remain `待实现` until full
  acceptance is reviewed. The release tag records the implemented,
  synthetically validated and human-authorized Phase 5 package; it does not
  retroactively convert the historical P5-3-G5 block into a Phase 5 PASS.
- Phase 6 PPE Compliance Event Engine: `已经实现（COMPLETE / RELEASED）`;
  `AssociationResult -> ComplianceInput -> ComplianceResult ->
  ComplianceEvent` is implemented with conservative Helmet/Vest/Unknown
  rules, five-frame and one-second confirmation, event deduplication,
  recovery, cooldown and JSONL storage. M-011 through M-014 remain
  `待实现` until the full Charter acceptance evidence is reviewed.
- Phase 7-0 Architecture Freeze: `COMPLETE / HUMAN REVIEW PASS`.
  The audit, target architecture, data contracts, technology decision, risk
  register and implementation order are recorded. No SQLite, snapshot,
  Streamlit, Camera/RTSP or alert implementation was created.
- Phase 7-1 Event Storage: `COMPLETE / HUMAN REVIEW PASS`. Added the persisted
  event DTO, SQLite connection/transaction boundary, checksummed migration
  `0001_phase7_events`, event repository with query/status support and
  idempotent `EventIngestService`. Phase 6 JSONL remains unchanged. Snapshot
  files remained pending at this review point.
- Phase 7-2 Evidence Snapshot: `COMPLETE / HUMAN REVIEW PASS`. Added atomic JPEG
  storage below `artifacts/events/snapshots/YYYYMMDD/`, relative-path and
  SHA256/dimension metadata, a separate snapshot repository, idempotent
  duplicate policy and event association through the existing persisted-event
  query projection.
- Phase 7-3 Dashboard & Alerts: `COMPLETE / HUMAN REVIEW PASS`. Added a read-only
  event query/statistics service, four Streamlit page sources, a verified
  evidence viewer, explicit navigation, Console and Web alert adapters, and
  service-boundary tests. Streamlit, Pandas and Plotly are not installed on
  this host, so actual browser rendering was not executed. TTS, Camera/RTSP,
  annotation rendering, reconciliation automation and retention remain
  pending.
- Phase 7-4 Camera/RTSP Input: `COMPLETE / HUMAN REVIEW PASS`. Added
  `SourceMetadata`/`SourceStatus`, the `VideoSource` lifecycle protocol and
  MP4, USB Camera and RTSP adapters. Status transitions, connection failures,
  release cleanup and RTSP URI redaction are tested with injected captures.
  At Phase 7-4 review time, real Camera/RTSP devices or streams were not
  opened; M-008 remains `待实现`. Phase 7-5 later opened a real USB Camera,
  but no real RTSP endpoint.
- Phase 7-5 Runtime Validation: `COMPLETE / HUMAN REVIEW PASS`. Executed one
  CPU-only MP4 smoke path with the frozen checkpoint and changed the event
  path through inference, tracking, association, compliance, JSONL, SQLite,
  snapshot evidence, dashboard queries and Console/Web alert delivery.
  Processed 47/47 frames, generated one `PPE_UNKNOWN` event, verified one
  snapshot and found no runtime errors. Streamlit AppTest passed all four
  pages, a local Streamlit health/root check passed, and a real USB Camera
  open/read/close lifecycle passed. Real RTSP, TTS, annotated rendering and
  M-007/M-008 final acceptance remain pending.
- Phase 7 Release Preparation Audit: `AUDIT COMPLETE FOR HUMAN REVIEW`.
  Verified the uncommitted release change set, empty staged area, Git-ignore
  boundary, generated-artifact exclusions, absence of model/media/database
  files, credential/token scan, documentation status consistency and the
  complete repository test baseline. Publication remains unauthorized.
- Phase 7-6 Release Finalization: `COMPLETE / RUNTIME VALIDATION PASS /
  HUMAN REVIEW PASS`. Added the lazy, injectable TTS service and cooldown/isolation
  adapter; added `MonitoringService`, session-scoped dashboard assembly and a
  realtime Streamlit page for MP4, USB Camera and RTSP. Runtime evidence now
  includes MP4 regression, real USB Camera, native `pyttsx3`/Windows SAPI,
  browser-driven Streamlit pages and a real local MediaMTX RTSP stream. The
  subsequent authorized release closure committed and published this work.
- Phase 7 Release Freeze Preparation: `COMPLETE / HUMAN REVIEW PASS`. Audited Phase 7 subphase status, the base release identity,
  the P7-6 runtime evidence and frozen asset hashes. Added the M-007 annotated
  demo video tool design and the final release report. The Charter M-007
  status remains `待实现`; no model, dataset, training, inference or core
  pipeline was changed. The authorized final release closure followed.
- Phase 7 M-007 Annotated Demo Video: `COMPLETE / REAL MP4 RUNTIME PASS /
  HUMAN REVIEW PASS`. Added deterministic frame annotation,
  staged atomic MP4 writing, decoded frame-count and dimension verification,
  metadata artifacts and rollback. A frozen-checkpoint CPU run processed
  47/47 frames into a 47-frame 1280x720 MP4 with SHA256
  `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949`.
  The Charter M-007 status remains `待实现`; the authorized Phase 7 release
  closure committed and published the reviewed implementation.
- Phase 1 Data remains `实现中` in the Master Plan. M-001, M-002 and M-003
  remain `待实现` in the Charter; completed data substeps are not a claim of
  their final acceptance.

## Completed Capabilities

- Frozen `CSS-PPE-10-V1` data artifact, Strategy C mapping and processed
  dataset are recorded; data quality was assessed without source mutation.
- EXP-001 YOLO11n training and Phase 3 test evaluation/model selection have
  reproducible evidence. Selected release checkpoint: EXP-001 `best.pt`.
- Single-image structured inference through `InferenceService` and
  `YOLODetector`; real-image validation used the frozen checkpoint.
- Sequential local MP4 structured inference through `VideoReader` and
  `VideoInferenceService`; real validation processed all 47/47 source frames.
- P5-1 person-only ByteTrack adapter: lazy backend isolation, class-0 filtering,
  confidence filtering, fail-closed errors and project-owned `TrackResult`
  output. Adapter behavior is tested with an injected backend; real
  Ultralytics ByteTrack execution is not verified.
- P5-2 conservative Person-PPE association: containment `0.50`, IoU `0.10`,
  confidence `0.25`, ambiguity margin `0.10`, deterministic ranking and
  explicit `unknown`. Synthetic tests cover single/multiple people, wrong
  candidates, ambiguity, missing PPE and empty input; real video integration
  is not verified.
- P5-3 integrated synthetic validation: the full
  `DetectionResult -> TrackResult -> AssociationResult` adapter chain passes
  single-person, multi-person, PPE-present, missing-PPE and ambiguous cases.
  A validation-only config and script prepare frozen checkpoint/video
  execution and report dependency readiness without loading the model.
- P5 release final audit: completed evidence, frozen identities, limitations
  and gates are consolidated in the Phase 5 final audit report. M-009 and
  M-010 are implemented at the audit layer. The historical P5-3-G5 block
  remains recorded, while the later explicit release authorization is
  recorded by `phase-5-tracking-association-complete`.
- Phase 6 compliance/events: Project-owned `ComplianceInput`,
  `ComplianceResult` and `ComplianceEvent` contracts; conservative
  Helmet/Vest/Unknown rules; five-frame/one-second temporal confirmation;
  active-cycle deduplication; recovery/cooldown; and Git-ignored JSONL event
  storage are implemented. The offline fixture and tests require no model
  runtime, GPU, camera or network stream.
- LLM and Agent remain outside completed scope. The dashboard, Console/Web/TTS
  alert adapters, service-owned monitoring loop and source adapter layer are
  implemented. Phase 7-6 adds real local RTSP runtime evidence. ByteTrack and
  association adapters are implemented and synthetically integrated; Phase 7-5
  additionally exercised them in one real MP4 runtime path, but stable-ID
  quality and broad association acceptance remain unverified.
- Phase 7 architecture is frozen: SQLite-first storage, date-partitioned
  snapshot evidence, Streamlit V1, one `VideoSource` boundary for MP4/USB
  Camera/RTSP, Console/Web/TTS alert adapters and a separate persisted-event
  projection. The frozen Phase 6 JSONL wire contract is unchanged.
- Phase 7-1 SQLite event storage persists the in-memory Phase 6 `event_id`,
  retains the original numeric `source_timestamp`, uses a separate wall-clock
  ISO 8601 `timestamp`, supports restart-persistent query/status operations
  and stores deterministic bbox metadata without changing the four-field
  JSONL wire record.
- Phase 7-2 evidence storage writes caller-supplied frames as JPEG through an
  atomic temporary file, partitions by UTC capture date, stores only relative
  POSIX paths, records SHA256/dimensions/MIME type and makes
  `PersistedEvent.snapshot` point to the verified file. Identical retries are
  idempotent; conflicting evidence replacement is rejected. Metadata-write
  failure leaves an orphan candidate rather than deleting evidence.
- Phase 7-3 dashboard queries SQLite through `EventQueryService`; Streamlit
  pages do not import the inference, tracking, association or compliance
  pipeline. Event filtering, source/type/status filters, pagination,
  statistics and verified snapshot evidence display are implemented at the
  source/service contract level.
- Phase 7-3 alerts use an ordered `AlertService` and `AlertAdapter` contract
  with Console and in-process Web implementations. Adapters are idempotent by
  the preserved Phase 6 `event_id`, isolate failures and return structured
  delivered/failed/skipped results.
- Phase 7-4 source adapters expose `idle`, `opening`, `live`, `degraded`,
  `ended`, `failed` and `closed` states. MP4 delegates to the frozen
  `VideoReader`; USB Camera and RTSP own capture lifecycle; RTSP logs/status
  use credential- and query-free URIs. Business, dashboard and script layers
  do not call `cv2.VideoCapture` directly.
- Phase 7-5 composes the existing runtime boundaries into an end-to-end MP4
  smoke path without modifying upstream logic. The test run used the frozen
  `best.pt` and `configs/inference.yaml`, produced 77 detections, 66 track
  updates, one unknown association, 66 compliance findings and one persisted
  event, then verified JSONL, SQLite, snapshot SHA256/dimensions, dashboard
  queries, Console delivery and in-process Web delivery. The run ID is
  `20260923T131111Z`; evidence remains under Git-ignored
  `artifacts/validation/P7-5/`.
- Phase 7-6 reuses those frozen boundaries in `MonitoringService` instead of
  duplicating detector, tracker, association or compliance logic. The
  service owns one background worker, exposes immutable status, preserves
  persist-before-alert ordering and reloads the persisted snapshot reference
  before fan-out. TTS uses stable event idempotency, per-track/type cooldown
  and structured failure isolation.
- The M-007 annotated demo tool composes `VideoReader` and `InferenceService`
  into sequential frame inference and deterministic box/label rendering.
  `AnnotatedVideoWriter` stages all five artifacts, decodes the MP4 for
  frame-count and dimension verification, then publishes by one atomic
  directory rename. The real run processed 47/47 frames and produced output
  SHA256 `293a51688d0f34170abbe9e104a1b4e31d679d072a81bf71eed6d0c9a45e8949`.
- The Phase 7 release audit found no forbidden pending artifact. All changed
  files are source, tests, configuration or documentation; the largest
  pending file is approximately 75 KB, no tracked file exceeds 256 KB, and
  model, data, validation evidence and generated event outputs remain ignored.

## Current Runtime

- Phase 4 runtime ID: `INF-RUNTIME-001`; Windows x86_64, Python `3.10.4`,
  PyTorch `2.5.1+cpu`, torchvision `0.20.1`, Ultralytics `8.4.157`.
- Runtime policy: CPU only. Frozen `configs/inference.yaml` keeps
  `execution_enabled: false`; real validation used separate explicit configs.
- The P5-3 preflight host is Python `3.13.6` with OpenCV `5.0.0`; `torch`,
  `torchvision` and `ultralytics` are not installed. The frozen P5-3
  validation config remains `execution_enabled: false`.
- Phase 6 validation ran on the same Python `3.13.6` governance host using
  only project-owned schemas and standard-library JSONL storage; no model
  runtime dependency was added.
- Phase 7-5 validation used an isolated Windows CPU-only environment with
  Python `3.12.1`, PyTorch `2.5.1+cpu`, torchvision `0.20.1+cpu`,
  Ultralytics `8.4.157`, OpenCV `5.0.0`, NumPy `2.2.6`, Streamlit `1.64.0`,
  Pandas `3.0.6` and lap `0.5.12`. Python 3.12.1 differs from frozen
  `INF-RUNTIME-001` Python 3.10.4 and is recorded as a release limitation.
- M-007 validation used the frozen `INF-RUNTIME-001` Python `3.10.4`,
  PyTorch `2.5.1+cpu`, Ultralytics `8.4.157`, OpenCV `5.0.0` runtime and
  NumPy `2.2.6` environment.
- Phase 8 P8-5 was implemented and tested on Python `3.13.6` using the
  standard-library transport. No provider SDK is installed and no
  `PPE_LLM_ENDPOINT`, `PPE_LLM_MODEL` or `PPE_LLM_API_KEY` runtime value is
  configured.
- Training used a separately frozen AutoDL RTX 4090 environment. The
  EXP-001 one-run authorization is `CONSUMED`; it does not authorize retraining.

## Frozen Assets

- Dataset: `CSS-PPE-10-V1`, source identity and manifests in
  [Dataset Card](06_DATASET_CARD.md) and `docs/dataset_contracts/`.
- Mapping: Strategy C, seven training classes; five PPE compliance classes
  retain their locked order. See [ADR log](03_TECHNICAL_DECISIONS.md).
- Release checkpoint: `models/checkpoints/EXP-001/best.pt`, SHA256
  `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`.
- Training configuration and runtime: `configs/training/exp001_baseline.yaml`
  and `locks/EXP-001/`; inference config: `configs/inference.yaml`.
- Dataset, mapping, training assets, checkpoint and frozen inference config
  must remain unchanged without the applicable approval and new evidence.

## Current Risks

- [Risk Register](08_RISK_REGISTER.md) is authoritative for risk statuses.
  RISK-001 schedule pressure; RISK-004 PPE occlusion; RISK-005 Person-PPE
  misassignment; RISK-006 single-frame alert jitter; RISK-008 RTSP instability.
- Phase 7 architecture risks: RISK-020 SQLite migration drift; RISK-021
  Streamlit runtime coupling; RISK-022 Camera/RTSP instability; RISK-023
  evidence retention; RISK-024 alert/TTS failure isolation; RISK-025 event
  identity compatibility; RISK-026 statistics divergence.
- M-007 annotated-output integrity is tracked as RISK-027; one short MP4
  passed, while long-duration throughput, codec portability and visual
  annotation quality review remain open.
- Phase 7-5 reduces uncertainty for the MP4/SQLite/snapshot/dashboard/
  Console/Web path and real USB Camera lifecycle. Phase 7-6 adds a controlled
  local MediaMTX RTSP lifecycle and native Windows SAPI TTS call, but does not
  close RISK-008 or RISK-022 because remote RTSP, reconnect/backoff and
  stale-frame behavior remain untested. RISK-024 has TTS
  cooldown/failure-isolation tests plus a successful native backend call;
  long-running alert delivery remains unverified. Retention remains open.
- RISK-017 retains data-quality findings, including small-object performance
  and perceptual cross-split candidates. Candidates are not confirmed leaks.
- Remote RTSP behavior, reconnect/backoff and production monitoring remain
  unvalidated. Phase 7-6 validated a controlled local RTSP stream and
  MP4/USB/browser paths. M-007 annotated output is implemented and one short
  real MP4 was decoded, inspected and verified; this does not complete full
  M-007/M-008 acceptance or establish long-duration/codec coverage.

## Deferred Requirements

### Deferred MUST ownership

- M-007 annotated video rendering: `待实现`; the tool design is complete at
  `docs/designs/phase-07/PHASE_7_M007_ANNOTATED_DEMO_VIDEO_DESIGN.md` and the
  implementation passed one real 47/47-frame MP4 validation. Human review and
  Phase 9 final acceptance remain pending. Phase 7 owns delivery and Phase 9
  owns final Charter acceptance.
- M-008 Camera/RTSP: `待实现`; Phase 7 live-input/real-time monitoring
  integration owns delivery, Phase 9 owns final Charter acceptance.
- Neither requirement is an Extension. ADR-019 clarifies the assignment;
  Charter definitions and acceptance criteria remain unchanged.
- Phase 4 Offline Inference completion does not set P4-G3 to PASS or complete
  the full M-007/M-008 acceptance criteria.

## Latest Reports

- [Phase 8 P8-5 final real provider validation report](reports/phase-08/PHASE_8_P8_5_FINAL_VALIDATION_REPORT.md).
- [Phase 8 P8-5P prompt schema conformance report](reports/phase-08/PHASE_8_P8_5P_PROMPT_SCHEMA_CONFORMANCE_REPORT.md).
- [Phase 8 P8-5P prompt schema conformance worklog](worklogs/2026/09/2026-09-24-10-phase8-p8-5p-prompt-schema-conformance.md).
- [Phase 8 P8-5D schema diagnostics report](reports/phase-08/PHASE_8_P8_5D_SCHEMA_DIAGNOSTICS_REPORT.md).
- [Phase 8 P8-5D schema diagnostics worklog](worklogs/2026/09/2026-09-24-09-phase8-p8-5d-schema-diagnostics.md).
- [Phase 8 P8-5R post-execution audit](reports/phase-08/PHASE_8_P8_5R_POST_EXECUTION_AUDIT_REPORT.md).
- [Phase 8 P8-5 provider E2E report](reports/phase-08/PHASE_8_P8_5_PROVIDER_E2E_REPORT.md).
- [Phase 8 P8-5R real provider smoke worklog](worklogs/2026/09/2026-09-24-08-phase8-p8-5r-real-provider-smoke.md).
- [Phase 8 P8-5 worklog](worklogs/2026/09/2026-09-24-07-phase8-p8-5-provider-e2e.md).
- [Phase 8 P8-4 provider adapter report](reports/phase-08/PHASE_8_P8_4_PROVIDER_ADAPTER_REPORT.md).
- [Phase 8 P8-4 worklog](worklogs/2026/09/2026-09-24-06-phase8-p8-4-provider-adapter.md).
- [Phase 8 P8-2 report grounding validation report](reports/phase-08/PHASE_8_P8_2_REPORT_GROUNDING_VALIDATION_REPORT.md).
- [Phase 8 P8-2 worklog](worklogs/2026/09/2026-09-24-04-phase8-p8-2-report-grounding.md).
- [Phase 8 P8-3 template fallback report](reports/phase-08/PHASE_8_P8_3_TEMPLATE_FALLBACK_REPORT.md).
- [Phase 8 P8-3 worklog](worklogs/2026/09/2026-09-24-05-phase8-p8-3-template-fallback.md).
- [Phase 8 P8-1 deterministic analytics report](reports/phase-08/PHASE_8_P8_1_DETERMINISTIC_ANALYTICS_REPORT.md).
- [Phase 8 P8-1 worklog](worklogs/2026/09/2026-09-24-03-phase8-p8-1-deterministic-analytics.md).
- [Phase 8 P8-0 architecture freeze report](reports/phase-08/PHASE_8_P8_0_ARCHITECTURE_FREEZE_REPORT.md).
- [Phase 8 Safety Intelligence Agent architecture](designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md).
- [Phase 8 P8-6 Basic Safety Agent architecture](designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md).
- [Phase 8 P8-6 architecture freeze report](reports/phase-08/PHASE_8_P8_6_ARCHITECTURE_FREEZE_REPORT.md).
- [Phase 8 P8-6.1 tool registry report](reports/phase-08/PHASE_8_P8_6_1_TOOL_REGISTRY_REPORT.md).
- [Phase 8 P8-6.1 worklog](worklogs/2026/09/2026-09-24-12-phase8-p8-6-1-tool-registry.md).
- [Phase 8 P8-6.2 deterministic planner report](reports/phase-08/PHASE_8_P8_6_2_DETERMINISTIC_PLANNER_REPORT.md).
- [Phase 8 P8-6.3 Agent audit report](reports/phase-08/PHASE_8_P8_6_3_AGENT_AUDIT_REPORT.md).
- [Phase 8 P8-6.3 Agent audit worklog](worklogs/2026/09/2026-09-24-14-phase8-p8-6-3-agent-audit.md).
- [Phase 8 P8-6.4 LLM-assisted planning architecture](designs/phase-08/PHASE_8_P8_6_4_AGENT_PLANNING_ARCHITECTURE.md).
- [Phase 8 P8-6.4 architecture freeze report](reports/phase-08/PHASE_8_P8_6_4_ARCHITECTURE_FREEZE_REPORT.md).
- [Phase 8 P8-6.4.1 plan candidate validator report](reports/phase-08/PHASE_8_P8_6_4_1_PLAN_VALIDATOR_REPORT.md).
- [Phase 8 P8-6.4.2 LLM planner adapter report](reports/phase-08/PHASE_8_P8_6_4_2_LLM_PLANNER_ADAPTER_REPORT.md).
- [Phase 8 P8-6.4.3 AgentService orchestration report](reports/phase-08/PHASE_8_P8_6_4_3_AGENT_SERVICE_REPORT.md).
- [Phase 8 P8-6.4.3 AgentService worklog](worklogs/2026/09/2026-09-24-16-phase8-p8-6-4-3-agent-service.md).
- [Phase 8 Agent implementation checkpoint release report](reports/phase-08/PHASE_8_AGENT_CHECKPOINT_RELEASE_REPORT.md).
- [Phase 8 P8-0 worklog](worklogs/2026/09/2026-09-24-02-phase8-p8-0-architecture-freeze.md).
- [Phase 7-0 architecture freeze report](reports/phase-07/PHASE_7_ARCHITECTURE_FREEZE_REPORT.md).
- [Phase 7-1 event storage report](reports/phase-07/PHASE_7_1_EVENT_STORAGE_REPORT.md).
- [Phase 7-2 evidence snapshot report](reports/phase-07/PHASE_7_2_EVIDENCE_SNAPSHOT_REPORT.md).
- [Phase 7-3 dashboard and alert report](reports/phase-07/PHASE_7_3_DASHBOARD_ALERT_REPORT.md).
- [Phase 7-4 camera and RTSP input report](reports/phase-07/PHASE_7_4_CAMERA_RTSP_REPORT.md).
- [Phase 7-5 runtime validation report](reports/phase-07/PHASE_7_5_RUNTIME_VALIDATION_REPORT.md).
- [Phase 7-6 release finalization report](reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_REPORT.md).
- [Phase 7-6 runtime validation result](reports/phase-07/PHASE_7_6_RUNTIME_VALIDATION_RESULT.md).
- [Phase 7 release freeze report](reports/phase-07/PHASE_07_FINAL_RELEASE_REPORT.md).
- [M-007 annotated demo video tool design](designs/phase-07/PHASE_7_M007_ANNOTATED_DEMO_VIDEO_DESIGN.md).
- [M-007 annotated demo video implementation report](reports/phase-07/PHASE_7_M007_IMPLEMENTATION_REPORT.md).
- [Phase 7 release complete report](reports/phase-07/PHASE_07_RELEASE_COMPLETE_REPORT.md).
- [Phase 7 release closure worklog](worklogs/2026/09/2026-09-24-01-phase7-release-closure.md).
- [Phase 7 M-007 implementation worklog](worklogs/2026/09/2026-09-23-18-phase7-m007-implementation.md).
- [Phase 7 release-freeze preparation worklog](worklogs/2026/09/2026-09-23-17-phase7-release-freeze-preparation.md).
- [Phase 7-6 release finalization worklog](worklogs/2026/09/2026-09-23-16-phase7-release-finalization.md).
- [Phase 7 release audit report](reports/phase-07/PHASE_7_RELEASE_AUDIT_REPORT.md).
- [Phase 7 architecture audit](reports/phase-07/PHASE_7_ARCHITECTURE_AUDIT.md).
- [Phase 7 target architecture](designs/phase-07/PHASE_7_TARGET_ARCHITECTURE.md).
- [Phase 7 data contracts](designs/phase-07/PHASE_7_DATA_CONTRACTS.md).
- [Phase 7 risk register](reports/phase-07/PHASE_7_RISK_REGISTER.md).
- [Phase 6 final release report](reports/phase-06/PHASE_06_FINAL_RELEASE_REPORT.md).
- [Phase 6 test report](reports/phase-06/PHASE_06_TEST_REPORT.md).
- [P5 final release preparation](reports/phase-05/P5_FINAL_RELEASE_REPORT.md).
- [P5 release final audit](reports/phase-05/P5_RELEASE_FINAL_AUDIT.md).
- [P5 documentation sync report](reports/phase-05/P5_DOCUMENTATION_SYNC_REPORT.md).
- [P5 release final audit worklog](worklogs/2026/09/2026-09-23-07-phase5-release-final-audit.md).
- [P5 final release worklog](worklogs/2026/09/2026-09-23-06-phase5-final-release-preparation.md).
- [P5-3 tracking and association validation](reports/phase-05/P5-3_VALIDATION_REPORT.md).
- [P5-3 validation worklog](worklogs/2026/09/2026-09-23-05-phase5-p5-3-validation.md).
- [P5-2 Person-PPE association implementation](reports/phase-05/P5-2_IMPLEMENTATION_REPORT.md).
- [P5-1 ByteTrack adapter implementation](reports/phase-05/P5-1_IMPLEMENTATION_REPORT.md).
- [Phase 4C-1 real-image validation](reports/phase-04/PHASE_04C1_IMAGE_VALIDATION_REPORT.md).
- [Phase 4C-2 real-MP4 validation](reports/phase-04/PHASE_04C2_VIDEO_VALIDATION_REPORT.md).
- [Phase 4 scope clarification](reports/maintenance/PHASE_SCOPE_CLARIFICATION_REPORT.md)
  and [Phase 4 phase document](phases/PHASE_04_INFERENCE.md).
- [Phase 2 training execution](reports/EXP-001_TRAINING_EXECUTION_REPORT.md)
  and [Phase 3 final release](reports/phase-03/PHASE_3_FINAL_RELEASE_REPORT.md).
- [Phase 4 → Phase 5 handover](worklogs/2026/09/2026-09-23-01-phase4-phase5-handover.md)
  preserves the former 753-line status document in full.
- This documentation cleanup is recorded in
  [Phase B governance report](reports/maintenance/DOCUMENT_GOVERNANCE_PHASE_B_REPORT.md).

## Next Allowed Step

`PHASE 8 FINAL INTEGRATION REVIEW / DO NOT START PHASE 9 OR IMPLEMENT DURABLE
AUDIT STORE, MEMORY, AUTONOMOUS LOOP OR REAL PROVIDER PLANNING CALLS`.

P8-0, P8-1, P8-2, P8-3 and P8-4 are human-reviewed PASS. P8-5 implements one
OpenAI-compatible provider transport behind the frozen P8-4 boundary and
provider-first orchestration with strict parsing, unchanged grounding
validation, deterministic fallback and `REPORT_UNAVAILABLE` handling. The
earlier P8-5R request was rejected as `REPORT_SCHEMA_INVALID` before provider
grounding; that failure remains historical evidence. P8-5D adds bounded
sanitized diagnostics for that failure class, and P8-5P replaces loose prompt
prose with a schema description derived from the authoritative report
dataclasses and enums. A later separately authorized manual request followed
prompt v2 and returned `PROVIDER_VALIDATED`: transport, strict JSON,
`phase8-report-v1`, and provider grounding all passed with `PROVIDER`,
`degraded=false`, no safe error, no schema diagnostics and fallback not used.
No further provider request may be executed. The P8-0 through P8-5 interim
checkpoint is released. P8-6 architecture passed human review and P8-6.1 now
implements and has passed review for the static read-only registry and
permission layer. P8-6.2 adds the deterministic planner and has passed human
review. P8-6.3 adds append-only in-memory audit events, privacy filtering and
the `AgentAuditService`, and has passed human review. P8-6.4 passed human
review and froze the LLM-assisted planning boundary and its untrusted
candidate/validation path. P8-6.4.1 implements the strict candidate parser,
validator and deterministic final-plan conversion only, and has passed human
review. P8-6.4.2 adds the provider-independent planner request builder,
injected candidate-client boundary, strict validator integration, bounded
audit metadata and deterministic fallback without real provider execution,
and has passed human review. P8-6.4.3 implements the typed request/result
boundary and `AgentService` orchestration over validated plans, the static
registry and append-only audit events; it has passed human review and is
released under interim checkpoint tag `phase-8-controlled-agent-complete`.
Durable audit storage, memory, autonomous loops, real provider planning
execution and Phase 9 remain not started. M-021, M-022 and M-023 remain
`待实现`.
