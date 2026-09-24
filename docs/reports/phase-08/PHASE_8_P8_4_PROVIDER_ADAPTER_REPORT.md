# Phase 8 P8-4 Provider Adapter Boundary and Untrusted Output Parsing Report

Status: `P8-4 IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD: `47206f5b2425572fd8b186312023767d12730f42`
- `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Working tree: expected uncommitted P8-0 through P8-4 changes
- P8-0: `HUMAN REVIEW PASS`
- P8-1: `HUMAN REVIEW PASS`
- P8-2: `HUMAN REVIEW PASS`
- P8-3: `HUMAN REVIEW PASS`
- P8-4: `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`

Phase 7 release tags remain unchanged:

- `phase-7-release-freeze-complete`: tag object
  `abb365cb4029ad079717da6cce9abb13eb18317b`, target
  `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`
- `phase-7-web-alert-platform-complete`: tag object
  `d97c8249c756dec33a9bb149bf837871b59b3503`, target
  `a30b73c080c18d010fbaa08642868e86acb68022`

No commit, tag, push, real provider call, external smoke test, API key or
runtime artifact was created by P8-4.

## 2. Pre-Read Audit

The P8-4 authorization, `AGENTS.md`, project status documents, Phase 8 phase
document and architecture, P8-0 through P8-3 reports, P8-1 context schema,
P8-2 report/validator, P8-3 fallback, existing LLM placeholder, dependency
manifests and Phase 8 tests were read before editing. No locked-contract or
governance conflict was found.

The workspace still labeled P8-3 as `IMPLEMENTATION COMPLETE / HUMAN REVIEW
PENDING`; the P8-4 authorization explicitly records P8-3 human review PASS.
This was a stale status text, not a contract change. P8-4 synchronizes the
listed status documents to that authorized state.

P8-1, P8-2 and P8-3 behavior and file contents were not changed.

## 3. Contract Verification

### 3.1 `phase8-context-v1`

- The four frozen top-level sections remain `observed_facts`,
  `calculated_metrics`, `metadata` and `unavailable_fields`.
- Canonical JSON and `SafetyContextBuilder.fingerprint(context)` are reused
  without changing their algorithm.
- Only `metadata.generated_at` is excluded by the fingerprint; the provider
  request removes that field from the transmitted payload so request
  construction is deterministic.
- Raw evidence bytes, absolute paths, SQL, secrets, environment values and
  internal stack traces remain outside the provider payload.

### 3.2 `phase8-report-v1`

- The schema and `SafetyReportGroundingValidator` were not modified.
- Provider output must be parsed into the existing report types.
- No provider text, wrapper or metadata can bypass the unchanged validator.
- Provider candidates must declare `mode=LLM`, `degraded=false`, no failure
  code and `grounding_status=unvalidated`.

### 3.3 `TemplateFallback`

- P8-3 remains provider-independent and deterministic.
- `TEMPLATE_FALLBACK` and `degraded=true` remain unchanged.
- `ReportService.generate(context)` retains its previous fallback and
  validation behavior.
- Provider failure cannot mutate fallback output or silently select fallback
  in the new P8-4 candidate path.

## 4. Implemented Architecture

```text
phase8-context-v1
        |
        v
ProviderRequestBuilder
        |
        v
SafetyLLMClient
        |
        v
injected ProviderTransport
        |
        v
untrusted TransportResponse
        |
        v
ProviderResponseParser
        |
        v
unvalidated phase8-report-v1 candidate
        |
        v
unchanged SafetyReportGroundingValidator
        |
        v
ProviderReportResult.valid
```

No concrete network or provider adapter is included in P8-4. The transport is
an injected protocol; focused tests use a deterministic fake transport.

## 5. Files Changed

Provider implementation:

- `infra/llm/provider.py`
- `infra/llm/request_builder.py`
- `infra/llm/response_parser.py`
- `infra/llm/llm_client.py`
- `services/report_service.py`

Tests:

- `tests/test_provider_adapter.py`
- `tests/unit/test_placeholders.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md` status only
- this report
- `docs/worklogs/2026/09/2026-09-24-06-phase8-p8-4-provider-adapter.md`

No model, dataset, mapping, training configuration, inference contract,
Phase 5 tracking, Phase 6 compliance/event or Phase 7 implementation was
changed.

## 6. SafetyLLMClient Boundary

`SafetyLLMClient` owns only provider-independent orchestration:

```text
generate_candidate(context) -> ProviderCandidate
generate_report(context) -> StructuredSafetyReport
```

`generate_report` returns the parsed candidate in `UNVALIDATED` state. It does
not claim grounding acceptance and does not return an Ultralytics, SDK or
provider-native object.

The client has no vendor import, SDK selection, API key, URL construction,
retry loop or network implementation. It depends only on the project-owned
request builder, transport protocol and strict parser.

## 7. Provider Transport Boundary

`ProviderTransport.send(request) -> TransportResponse` is the sole transport
seam. `TransportResponse` contains only:

- HTTP-like status code;
- response bytes.

Transport failures use the structured `ProviderTransportError` category.
Tests inject a fake transport and no network library or socket is used.

P8-4 intentionally does not implement:

- HTTP transport;
- provider authentication;
- provider SDK adapters;
- automatic retries;
- streaming;
- tool calling;
- provider selection.

## 8. Provider Request Contract

`ProviderRequest` contains:

- request version `phase8-provider-request-v1`;
- prompt version `phase8-provider-prompt-v1`;
- expected report schema `phase8-report-v1`;
- non-secret provider and model labels;
- finite timeout;
- deterministic maximum response size `262144` bytes;
- source context SHA256;
- canonical safe context JSON;
- one fixed system instruction and one user context message.

The request rejects:

- invalid provider/model labels;
- unbounded or non-finite timeouts;
- non-canonical context JSON;
- fields outside the four frozen context sections;
- `metadata.generated_at`;
- absolute-path patterns;
- credential-like assignments.

For the same context and provider/model configuration, request construction is
byte-stable. It contains no wall-clock timestamp, random identifier, raw image,
raw evidence bytes, SQL, environment dump or secret.

## 9. Prompt and Message Versioning

The initial prompt contract is:

```text
phase8-provider-prompt-v1
```

The prompt explicitly requires strict machine-readable JSON, names the
authoritative context, requires preservation of the context fingerprint,
prohibits invented events/tracks/metrics/identity paths and identifies
`track_id` as tracker-scoped rather than stable person identity.

The prompt is not treated as a security boundary. Parsing and P8-2 grounding
validation remain authoritative.

## 10. Safe Context Behavior

Only the frozen Phase 8 context is transmitted. The builder removes
`metadata.generated_at` to avoid construction-time drift and does not add raw
source paths, snapshots, database content or credentials.

Relative snapshot references already present in the P8-1 context remain
metadata references only. No snapshot or image bytes are read or embedded.

## 11. Response Size Policy

- Maximum accepted response size: `262144` bytes.
- The limit is frozen in request and parser policy.
- Size is checked before UTF-8 decoding or JSON parsing.
- Oversized responses fail with `PROVIDER_RESPONSE_TOO_LARGE`.
- Raw response bodies are not included in errors, logs or report metadata.

## 12. Strict JSON Parsing

The parser accepts only:

- raw bytes;
- valid UTF-8 without BOM;
- one strict JSON object with no prose or Markdown wrapper;
- no duplicate object keys;
- no `NaN` or `Infinity`;
- exact `phase8-report-v1` field sets at every nested object;
- lower-case context SHA256 matching the request;
- `LLM`, `degraded=false`, no failure code and `unvalidated`;
- complete nested claim, recommendation, evidence and limitation structures.

It rejects rather than repairs malformed JSON, unknown fields, wrong enum
values, wrong field types, provider-declared validation, mismatched
fingerprints and malformed references.

## 13. Provider Error Model

The frozen provider-layer categories are:

```text
PROVIDER_UNAVAILABLE
PROVIDER_TIMEOUT
PROVIDER_HTTP_ERROR
PROVIDER_RATE_LIMITED
PROVIDER_AUTH_ERROR
PROVIDER_RESPONSE_TOO_LARGE
PROVIDER_EMPTY_RESPONSE
PROVIDER_MALFORMED_RESPONSE
REPORT_SCHEMA_INVALID
GROUNDING_REJECTED
```

HTTP-like mapping is deterministic:

- `401` and `403`: authentication error;
- `429`: rate limited;
- other non-2xx: HTTP error;
- transport timeout/unavailability: corresponding transport category.

The client replaces raw transport error text with a fixed safe category
message. Test failures confirm that a fake secret-like message is not present
in the raised exception or its representation. Semantic failures are never
retried.

## 14. Timeout Policy

Requests require a finite positive timeout. The default P8-4 policy is
`60.0` seconds. The fake transport tests validate that timeout propagation is
mapped to `PROVIDER_TIMEOUT` without opening a socket.

No retry behavior is implemented. Schema-invalid output, grounding failures,
fabricated IDs and numeric contradictions are semantic failures and must not
be retried.

## 15. Provider Metadata

The frozen report schema is unchanged. Provider and model request metadata
remain in:

- `ProviderRequest`;
- `ProviderCandidate.request`;
- `ProviderReportResult.request`.

The parsed report carries only the optional non-secret `provider_ref` already
supported by `ReportGeneration`. No prompt, raw response, model URL, API key
or provider-specific payload was added to `phase8-report-v1`.

## 16. ReportService Integration Status

The existing deterministic API remains:

```text
ReportService.generate(context) -> StructuredSafetyReport
```

Its fallback and validation behavior is unchanged.

The new P8-4 API is:

```text
ReportService.generate_provider_report(context, client)
    -> ProviderReportResult
```

`ProviderReportResult` contains the parsed candidate, original request and
unchanged P8-2 `ReportValidationResult`. A valid result means the candidate
passed grounding. An invalid result is returned for fail-closed review or a
future P8-5 fallback decision; P8-4 does not silently substitute fallback or
mark the provider candidate valid.

## 17. Grounding Validator Integration

The following remain unchanged:

- context fingerprint checks;
- fact, metric, event, track, source and evidence reference checks;
- exact numeric checks;
- unavailable-field and limitation checks;
- privacy/path checks;
- fail-closed behavior and deterministic error ordering.

Provider output cannot alter, weaken, repair or bypass the validator.

## 18. TemplateFallback Compatibility

P8-3 focused tests and all existing grounding tests pass unchanged. The
fallback still emits:

- `TEMPLATE_FALLBACK`;
- `degraded=true`;
- the exact P8-1 context fingerprint;
- only grounded facts, metrics, tracks and available evidence.

The provider path does not mutate fallback output.

## 19. Security and Secret Handling

- No real credential or API key was added.
- Tests use only the non-secret placeholder
  `api_key=not-a-real-secret`.
- No secret environment variable value is read.
- No secret is included in request, report, exception or worklog content.
- Raw provider output is never copied into a provider error.
- Provider transport exceptions are not chained into caller-visible errors.
- Logging behavior remains deferred; P8-4 adds no provider response logging.

## 20. Mock Transport and No-Network Verification

`tests/test_provider_adapter.py` defines a deterministic `FakeTransport` with
zero network behavior. It supports:

- valid grounded JSON;
- malformed JSON;
- duplicate JSON keys;
- empty and whitespace-only output;
- oversized output;
- schema-invalid output;
- fingerprint mismatch;
- fabricated event;
- fabricated track;
- numeric contradiction;
- path leak;
- timeout, auth, rate-limit and HTTP status failures.

The focused test suite also monkeypatches `socket.socket` to fail and confirms
that the provider flow still completes through the fake transport.

## 21. Focused Tests

Command:

```text
python -m pytest -q tests/test_provider_adapter.py
```

Result: `26 passed`.

Combined Phase 8 focused regression:

```text
python -m pytest -q \
  tests/test_provider_adapter.py \
  tests/test_template_fallback.py \
  tests/test_safety_report_grounding.py \
  tests/unit/test_placeholders.py
```

Result: `65 passed`.

The obsolete `LLMClient.complete()` placeholder expectation was removed from
`tests/unit/test_placeholders.py`; the remaining future-phase placeholders
still fail explicitly.

## 22. Full Regression

```text
python -m pytest -q
485 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host.

## 23. Frozen Assets and Governance

| Asset | SHA256 | Result |
| --- | --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

Charter diff: EMPTY. MUST definitions, Phase goals and Phase 7 tags are
unchanged.

## 24. Gate Results

| Gate | Status |
| --- | --- |
| P8-4-G1 provider-independent client and injectable transport boundary | PASS |
| P8-4-G2 deterministic safe request construction and P8-1 fingerprint binding | PASS |
| P8-4-G3 strict untrusted `phase8-report-v1` parsing | PASS |
| P8-4-G4 accepted candidates require the unchanged P8-2 validator | PASS |
| P8-4-G5 malformed, oversized, invalid, fabricated and contradictory output fails closed | PASS |
| P8-4-G6 timeout/auth/rate-limit errors are deterministic and secret-safe | PASS |
| P8-4-G7 fake transport and focused tests perform zero real network/provider access | PASS |
| P8-4-G8 full regression, frozen contracts/assets, governance and tag checks pass | PASS |

## 25. Known Limitations

- No real provider or HTTP transport exists.
- Provider selection, authentication, endpoint, model cost and rate policy
  remain unresolved.
- Provider context-size handling beyond the response-size limit is not
  implemented.
- P8-4 returns candidate validation only; provider-first plus fallback E2E is
  deferred to P8-5.
- Free-text semantic contradiction detection remains outside the deterministic
  grounding validator.
- No real LLM-generated report has been evaluated.
- M-021, M-022 and M-023 remain `待实现` in the locked Charter.

## 26. Unresolved Decisions

- Provider choice and whether to use a small HTTP adapter or an approved SDK.
- API authentication and secret-manager integration.
- Production context-size policy and detailed-event selection defaults.
- Long-term report retention and export formats.
- Retry/backoff policy, if any, for transport-only failures.
- P8-5 provider-first/fallback behavior after separate authorization.

## 27. Final State

`P8-4 IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`

Real provider execution, P8-5, Basic Agent and Phase 9 remain unauthorized.
No commit, tag or push was created.
