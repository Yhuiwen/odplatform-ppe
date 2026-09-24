# Phase 8 P8-5 Real Provider E2E, Grounding Enforcement and Safe Fallback Report

Status: `P8-5 IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION PASS / HUMAN REVIEW PENDING`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD: `47206f5b2425572fd8b186312023767d12730f42`
- `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Remote: `https://github.com/Yhuiwen/odplatform-ppe.git`
- Working tree: uncommitted P8-0 through P8-5 implementation and documentation
  changes
- P8-0: `HUMAN REVIEW PASS`
- P8-1: `HUMAN REVIEW PASS`
- P8-2: `HUMAN REVIEW PASS`
- P8-3: `HUMAN REVIEW PASS`
- P8-4: `HUMAN REVIEW PASS`
- P8-5:
  `IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION PASS / HUMAN REVIEW PENDING`

Phase 7 release tags remain unchanged:

- `phase-7-release-freeze-complete`: tag object
  `abb365cb4029ad079717da6cce9abb13eb18317b`, target
  `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`
- `phase-7-web-alert-platform-complete`: tag object
  `d97c8249c756dec33a9bb149bf837871b59b3503`, target
  `a30b73c080c18d010fbaa08642868e86acb68022`

This audit made no additional commit, tag, push, real provider call or real
credential use.

## 2. Pre-Read and Pre-Implementation Audit

The P8-5 authorization, AGENTS guidance, project status documents, Phase 8
phase and architecture records, P8-0 through P8-4 reports, current schemas,
analytics/context builder, grounding validator, fallback, request builder,
parser, client, report service, tests and dependency environment were read
before implementation.

Audited state:

- P8-0 through P8-4 were recorded as human-reviewed PASS by the authorization.
- `SafetyAnalyticsService` and `SafetyContextBuilder` remain deterministic and
  provider-independent.
- `SafetyReportGroundingValidator` remains the unchanged P8-2 acceptance
  boundary.
- `TemplateFallback` remains deterministic and independent of any provider.
- `ProviderTransport` remains the P8-4 injection boundary.
- `SafetyLLMClient` remains responsible for request construction, transport
  invocation and strict candidate parsing only.
- `ReportService.generate()` retains its existing fallback-only behavior.
- `ReportService.generate_provider_report()` retains its candidate plus
  validation behavior.
- Provider error categories remain `PROVIDER_UNAVAILABLE`,
  `PROVIDER_TIMEOUT`, `PROVIDER_HTTP_ERROR`, `PROVIDER_RATE_LIMITED`,
  `PROVIDER_AUTH_ERROR`, `PROVIDER_RESPONSE_TOO_LARGE`,
  `PROVIDER_EMPTY_RESPONSE`, `PROVIDER_MALFORMED_RESPONSE`,
  `REPORT_SCHEMA_INVALID` and `GROUNDING_REJECTED`.
- Host Python is `3.13.6`.
- Host network libraries include `requests`, `httpx`, `aiohttp` and
  `urllib3`; no provider SDK is installed.
- No `PPE_LLM_ENDPOINT`, `PPE_LLM_MODEL` or `PPE_LLM_API_KEY` variable is set.

Conflict found: the existing Phase 8 documents assigned the `P8-5` label to
Basic Agent, while this authorization assigns P8-5 to real-provider E2E.
This is an internal subphase sequencing change; no locked Phase goal, MUST
definition or P8-1/P8-2/P8-3/P8-4 contract was changed. Basic Agent remains
unauthorized.

## 3. Selected Provider

P8-5 implements exactly one concrete provider transport family:

```text
OpenAI-compatible chat-completions
```

The runtime provider reference, endpoint and model remain configuration-driven
through:

```text
PPE_LLM_ENDPOINT
PPE_LLM_MODEL
PPE_LLM_API_KEY
```

The repository default provider label is `openai-compatible`. A specific
vendor, endpoint and model are `PENDING_SELECTION` because no runtime values
or credential are available and the authorization explicitly prohibits
inventing credentials.

No OpenAI, Anthropic, Ollama, LangChain, LlamaIndex, AutoGen or other SDK was
added. The implementation uses the Python standard library through the single
P8-4 `ProviderTransport` boundary.

## 4. Credential Source Policy

- Credentials are resolved only from environment variables named by
  `configs/llm.yaml`.
- YAML contains environment-variable names and non-secret policy only.
- Credential values are excluded from dataclass `repr`, request bodies,
  reports, errors, test output and worklogs.
- Non-local HTTP endpoints are rejected; HTTP is allowed only for loopback
  development endpoints.
- Endpoints with embedded credentials, query strings or fragments are
  rejected.
- Missing runtime configuration returns `NOT_EXECUTED`; it does not create a
  fabricated provider result.

## 5. Provider Transport Implementation

`infra/llm/chat_transport.py` adds
`OpenAICompatibleChatTransport` behind the unchanged P8-4
`ProviderTransport.send(request) -> TransportResponse` contract.

Transport policy:

- one request attempt only;
- no retries;
- finite request timeout from `phase8-provider-request-v1`;
- maximum response size `262144` bytes;
- no streaming;
- no request or response logging;
- no raw provider payload persistence;
- no provider SDK;
- no provider-specific context, grounding, fallback or event-store logic.

The transport sends one deterministic chat-completions envelope containing
the frozen system and user messages, `temperature=0`, `stream=false` and an
optional JSON-object response format. It accepts only an OpenAI-compatible
`choices[0].message.content` string and returns those bytes to the unchanged
strict parser.

Operational errors are mapped to bounded provider categories:

- HTTP `401` and `403` -> `PROVIDER_AUTH_ERROR`
- HTTP `429` -> `PROVIDER_RATE_LIMITED`
- other non-2xx -> `PROVIDER_HTTP_ERROR`
- timeout -> `PROVIDER_TIMEOUT`
- DNS/connect/read/unavailable -> `PROVIDER_UNAVAILABLE`
- oversized body -> `PROVIDER_RESPONSE_TOO_LARGE`
- empty content -> `PROVIDER_EMPTY_RESPONSE`
- malformed envelope or JSON -> `PROVIDER_MALFORMED_RESPONSE`

Raw provider error text and authorization headers are not exposed to callers.

## 6. Provider Request and Parsing Boundary

The existing P8-4 request and parser contracts are reused without weakening:

- request version: `phase8-provider-request-v1`
- prompt version at the original implementation point:
  `phase8-provider-prompt-v1`
- prompt version used by the final successful attempt:
  `phase8-provider-prompt-v2`
- context version: `phase8-context-v1`
- report schema: `phase8-report-v1`
- response limit: `262144` bytes

Only the safe context sections are sent:

```text
observed_facts
calculated_metrics
metadata
unavailable_fields
```

`metadata.generated_at` is excluded from transport input. Raw evidence images,
absolute paths, database content, environment values, credentials and SQL are
not sent.

Provider output remains untrusted. It must pass the unchanged strict parser
before a `ProviderCandidate` exists. The candidate must then pass the
unchanged P8-2 `SafetyReportGroundingValidator` before it can escape the
report service.

## 7. Provider-First Orchestration

`ReportService.generate_provider_or_fallback()` implements the authorized
provider-first flow:

```text
phase8-context-v1
-> provider candidate parse
-> unchanged P8-2 grounding validation
-> provider report, if VALID
```

If the provider path fails:

```text
provider failure
-> TemplateFallback.generate(context)
-> unchanged P8-2 grounding validation
-> degraded TEMPLATE_FALLBACK report, if VALID
```

If fallback generation or validation fails:

```text
REPORT_UNAVAILABLE
```

No invalid provider candidate is returned to callers. There is no
`trusted_provider`, `skip_grounding`, `force_accept` or equivalent bypass.

## 8. Generation Result and Safe Error Metadata

`ReportGenerationResult` keeps provider success distinguishable from fallback
success:

```text
status
generation_path
degraded
report
provider_metadata
safe_error
grounding_status
```

Permitted paths:

```text
PROVIDER
TEMPLATE_FALLBACK
UNAVAILABLE
```

Safe provider metadata may contain only:

```text
provider_ref
model_ref
request_version
prompt_version
report_schema_version
```

Safe errors contain a category, bounded message and provider reference. They
do not contain API keys, authorization headers, raw requests, environment
dumps, filesystem paths or secret-bearing stack traces.

## 9. Provider Success Path

Provider success requires all of:

1. one configured OpenAI-compatible endpoint and model;
2. a successful bounded network response;
3. a valid provider envelope and non-empty message content;
4. strict `phase8-report-v1` parsing;
5. unchanged P8-2 grounding validation PASS.

Only then does the result use:

```text
status = PROVIDER_VALIDATED
generation_path = PROVIDER
degraded = false
grounding_status = valid
```

Fallback success is never relabeled as provider success.

## 10. Provider Semantic Failure Path

The following provider outcomes route to deterministic fallback and are not
retried:

- malformed JSON or envelope;
- schema-invalid report;
- context fingerprint mismatch;
- fabricated event ID;
- fabricated track ID;
- fabricated evidence reference;
- numeric contradiction;
- unavailable-field contradiction;
- absolute path leakage;
- ungrounded finding or risk observation.

Parsing failures retain their strict provider categories. Grounding failures
carry `GROUNDING_REJECTED`; the original invalid provider report is discarded.

## 11. Provider Operational Failure Path

Unavailable, timeout, HTTP, rate-limit, authentication, empty, oversized and
malformed responses route to the same fallback path without raising into the
monitoring pipeline.

No retry loop is implemented in P8-5. Semantic failures are never retried.

## 12. TemplateFallback Behavior

P8-3 behavior is unchanged:

- `generation.mode = TEMPLATE_FALLBACK`
- `generation.degraded = true`
- deterministic local generation only
- exact P8-1 context fingerprint
- only facts, metrics, tracker-scoped tracks and available evidence from the
  supplied context
- unchanged P8-2 grounding validation before return

Fallback output preserves the provider failure category as
`generation.failure_code` when a provider path failed.

## 13. REPORT_UNAVAILABLE Behavior

If fallback generation raises or fallback validation rejects:

```text
status = REPORT_UNAVAILABLE
generation_path = UNAVAILABLE
degraded = true
report = null
grounding_status = null
safe_error = bounded failure
```

No synthetic or invalid report is returned.

## 14. Real Provider Smoke Result

The initial smoke CLI check was executed without `--execute`:

```text
python scripts/run_p8_5_provider_smoke.py
```

Exact result:

```json
{"degraded": null, "generation_path": null, "grounding_status": null, "model_ref": null, "provider_ref": null, "reason": "required runtime configuration is missing: PPE_LLM_ENDPOINT", "safe_error_code": null, "status": "NOT_EXECUTED"}
```

At that time, no `PPE_LLM_ENDPOINT`, `PPE_LLM_MODEL` or `PPE_LLM_API_KEY` was
configured, so no network request was issued. This historical pre-execution
check is superseded by the human-executed real request in section 14.2.

The CLI requires `--execute` before a network call can be attempted. It uses a
small deterministic zero-event context, makes at most one request and prints
only sanitized metadata.

### 14.1 P8-5R Real Provider Validation Attempt

Date: 2026-09-24

Pre-smoke audit:

- Branch: `main`
- HEAD: `47206f5b2425572fd8b186312023767d12730f42`
- `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Working tree: existing P8-0 through P8-5 changes preserved
- Configured `provider_ref`: `openai-compatible`
- Configured endpoint presence: NO (`PPE_LLM_ENDPOINT` absent)
- Configured model presence: NO (`PPE_LLM_MODEL` absent)
- API-key presence: NO (`PPE_LLM_API_KEY` absent)
- Timeout policy: `60.0` seconds
- Maximum response size: `262144` bytes
- Smoke execution gate: explicit `--execute` required
- Conflicts found: NO

Focused pre-smoke regression:

```text
python -m pytest -q tests/test_chat_transport.py
  tests/test_provider_e2e.py tests/test_provider_adapter.py
  tests/test_template_fallback.py tests/test_safety_report_grounding.py
  tests/test_safety_analytics.py
109 passed
```

Because required runtime configuration is absent, the authorized real request
was not executed:

```text
REAL PROVIDER VALIDATION NOT EXECUTED
```

Observed result:

```text
request attempted: NO
network requests issued: 0
endpoint host: NOT AVAILABLE
transport result: NOT ATTEMPTED
provider parsing: NOT RUN
phase8-report-v1 schema: NOT RUN
context fingerprint: NOT RUN
grounding: NOT RUN
generation path: NOT AVAILABLE
degraded: null
fallback status: NOT RUN
safe error code: null
```

The CLI non-execution check returned:

```json
{"degraded": null, "generation_path": null, "grounding_status": null, "model_ref": null, "provider_ref": null, "reason": "required runtime configuration is missing: PPE_LLM_ENDPOINT", "safe_error_code": null, "status": "NOT_EXECUTED"}
```

No credential value was read, printed or written. No provider host or
authorization header was recorded. This pre-smoke attempt does not change the
P8-5 final state after the human-executed real request:

```text
P8-5 IMPLEMENTATION COMPLETE /
REAL PROVIDER EXECUTED /
PROVIDER REPORT SCHEMA REJECTED /
TEMPLATE FALLBACK PASS /
HUMAN REVIEW PENDING
```

### 14.2 Human-Executed Real Provider Request

Date: 2026-09-24

The human operator executed:

```text
python scripts/run_p8_5_provider_smoke.py --execute
```

Sanitized runtime identity:

- Provider family: `openai-compatible`
- Endpoint: `https://api.deepseek.com/chat/completions`
- Model: `deepseek-flash`

Observed sanitized result:

```json
{"degraded":true,"generation_path":"TEMPLATE_FALLBACK","grounding_status":"valid","model_ref":"deepseek-flash","provider_ref":"openai-compatible","reason":"provider path used safe fallback","safe_error_code":"REPORT_SCHEMA_INVALID","status":"TEMPLATE_FALLBACK"}
```

Post-execution audit conclusions:

- A real provider request was executed by the human operator.
- A provider response was received and the OpenAI-compatible envelope was
  accepted.
- Non-empty `choices[0].message.content` was extracted.
- Strict JSON parsing succeeded before report-schema construction.
- `phase8-report-v1` construction failed with `REPORT_SCHEMA_INVALID`.
- The provider candidate was not constructed and provider grounding validation
  was not reached.
- The unchanged `TemplateFallback` generated a report and passed the unchanged
  P8-2 grounding validator.
- The returned `grounding_status=valid` belongs only to the fallback report,
  not to the rejected provider candidate.
- The exact provider schema mismatch cannot be recovered because raw provider
  content was intentionally not persisted.

The result is not `PROVIDER_VALIDATED`. Provider success and fallback success
remain separate outcomes.

## 15. Focused Tests

Command:

```text
python -m pytest -q tests/test_chat_transport.py
  tests/test_provider_e2e.py tests/test_provider_adapter.py
  tests/test_template_fallback.py tests/test_safety_report_grounding.py
  tests/test_safety_analytics.py
```

Result: `109 passed`.

Coverage includes:

- provider-valid report returned as `PROVIDER`;
- provider success not degraded;
- malformed and schema-invalid provider output -> fallback;
- fingerprint mismatch, fabricated event, fabricated track, numeric
  contradiction and path leakage -> fallback;
- timeout, auth, rate limit, unavailable, HTTP failure, empty and oversized
  provider responses -> fallback;
- fallback validation PASS, `TEMPLATE_FALLBACK` identity and `degraded=true`;
- fallback failure -> `REPORT_UNAVAILABLE` without a report;
- invalid provider candidate never escapes the service;
- zero-event provider and fallback behavior;
- secret-like text absent from serialized errors and metadata;
- no real provider SDK or network dependency;
- explicit `--execute` gate for the smoke CLI.

## 16. Full Regression

```text
python -m pytest -q
520 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host.

## 17. Frozen Contracts and Assets

The following remain unchanged:

- `SafetyAnalyticsService`
- `SafetyContextBuilder`
- `phase8-context-v1`
- context fingerprint algorithm
- `phase8-report-v1`
- `SafetyReportGroundingValidator`
- `TemplateFallback` deterministic rules
- P8-4 provider request, error and parser contracts

| Asset | SHA256 | Result |
| --- | --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

Charter diff: EMPTY. Phase 7 tags retain their recorded tag objects and target
commits.

## 18. Secret and Artifact Scan

- The audit did not inspect, print or persist the API-key value.
- No credential value was written to YAML, source, tests, reports or worklogs.
- Tests use only the non-secret placeholder `test-secret` inside isolated
  fixture objects.
- No raw provider response was committed or written to a report/worklog.
- No credential-bearing runtime file or runtime artifact was created by the
  audited smoke path.
- No model, dataset, training, inference, Phase 5, Phase 6 or Phase 7 asset was
  changed.

## 19. Gate Results

| Gate | Status |
| --- | --- |
| P8-5-G1 Exactly one real provider is implemented behind the frozen P8-4 abstraction | PASS |
| P8-5-G2 Provider candidates escape only after strict parsing and unchanged P8-2 grounding validation | PASS |
| P8-5-G3 Semantic provider failures deterministically route to TemplateFallback | PASS |
| P8-5-G4 Operational provider failures deterministically route to TemplateFallback | PASS |
| P8-5-G5 TemplateFallback uses the unchanged validator and retains degraded identity | PASS |
| P8-5-G6 Fallback failure terminates as REPORT_UNAVAILABLE without invalid report exposure | PASS |
| P8-5-G7 Real provider evidence is recorded accurately and separately from fallback; secrets are not persisted | PASS / REAL PROVIDER VALIDATED |
| P8-5-G8 Full regression, frozen contracts/assets, governance and Phase 7 tag checks pass | PASS |

## 20. Known Limitations

- A real OpenAI-compatible request was executed against
  `https://api.deepseek.com/chat/completions` with model `deepseek-flash`.
- Historical attempts include a configuration non-execution and a
  `REPORT_SCHEMA_INVALID` rejection followed by fallback; these remain
  preserved in the audit trail.
- The final separately authorized manual attempt used prompt v2, passed
  strict parsing and the unchanged grounding validator, and returned
  `PROVIDER_VALIDATED` with fallback not used.
- Provider cost, latency, rate limits and actual report quality have not been
  measured.
- No retry or backoff policy is implemented by design.
- Free-text semantic contradiction detection remains outside the deterministic
  grounding validator.
- Basic Agent, P8-6 and Phase 9 remain unauthorized.
- M-021, M-022 and M-023 remain `待实现` in the locked Charter.

## 21. Unresolved Decisions

- Whether the observed provider schema mismatch warrants a future transport,
  prompt or parser change without weakening the frozen contract.
- Secret-manager integration and production credential rotation.
- Production context-size and detailed-event selection policy.
- Token budget, rate-limit and cost-control policy.
- Report persistence, retention and export policy.
- Whether a future provider SDK is justified beyond the current standard
  library transport.
- Basic Agent subphase numbering and authorization boundary.

## 22. Final State

`P8-5 IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION PASS / HUMAN REVIEW PENDING`

Basic Agent, P8-6, Phase 9, commit, tag and push remain unauthorized.

## 23. Final Real Provider Validation Update

The final manual provider validation completed after the historical failure,
diagnostic and prompt-v2 repair chain. Sanitized result:

```json
{
  "degraded": false,
  "generation_path": "PROVIDER",
  "grounding_status": "valid",
  "model_ref": "deepseek-flash",
  "provider_ref": "openai-compatible",
  "reason": "real provider call completed",
  "safe_error_code": null,
  "schema_diagnostics": null,
  "schema_diagnostics_truncated": null,
  "status": "PROVIDER_VALIDATED"
}
```

The result therefore records:

```text
Transport: PASS
Provider response: RECEIVED
Strict JSON: PASS
phase8-report-v1: PASS
Provider grounding: VALID
Generation path: PROVIDER
Degraded: false
Fallback: NOT USED
Safe error: NONE
Schema diagnostics: NONE
Final status: PROVIDER_VALIDATED
```

This audit issued no additional provider request. Full regression, frozen
asset and security evidence are recorded in
`docs/reports/phase-08/PHASE_8_P8_5_FINAL_VALIDATION_REPORT.md`.

Final state:

`P8-5 IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION PASS / HUMAN REVIEW
PENDING`
