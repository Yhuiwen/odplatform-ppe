# Phase 8 P8-5R Real Provider Post-Execution Audit Report

Status: `REAL PROVIDER EXECUTED / PROVIDER REPORT SCHEMA REJECTED / TEMPLATE FALLBACK PASS / HUMAN REVIEW PENDING`

Date: 2026-09-24

Repository identity:

- Branch: `main`
- HEAD and `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Commit, tag and push by this audit: NOT PERFORMED

## 1. Scope

This audit records one real provider request that was already executed manually
by the human operator. The audit does not issue another network request, does
not use `--execute`, does not inspect the API-key value and does not modify any
provider, schema, grounding or fallback contract.

## 2. Recorded Execution

- Provider family: `openai-compatible`
- Provider reference: `openai-compatible`
- Endpoint: `https://api.deepseek.com/chat/completions`
- Model reference: `deepseek-flash`
- Command: `python scripts/run_p8_5_provider_smoke.py --execute`
- Observed sanitized result:

```json
{"degraded":true,"generation_path":"TEMPLATE_FALLBACK","grounding_status":"valid","model_ref":"deepseek-flash","provider_ref":"openai-compatible","reason":"provider path used safe fallback","safe_error_code":"REPORT_SCHEMA_INVALID","status":"TEMPLATE_FALLBACK"}
```

## 3. Audit Questions

### 3.1 Does `REPORT_SCHEMA_INVALID` prove transport success?

For the implemented smoke path, yes: the provider transport returned a
`TransportResponse`, the envelope was accepted, non-empty message content was
extracted, and control reached report-schema construction. This is not an
independent packet-level proof, but it is sufficient to conclude that the
configured transport call completed and returned usable provider content.

### 3.2 Was a provider response received?

YES. `REPORT_SCHEMA_INVALID` is emitted only after the OpenAI-compatible
response envelope has been parsed and `choices[0].message.content` has been
extracted as non-empty content.

### 3.3 Was provider message content extracted?

YES. `_extract_message_content()` accepted the response envelope and returned
the message content to the strict report parser.

### 3.4 Did JSON syntax parsing succeed before report-schema validation?

YES. `ProviderResponseParser.parse()` completed UTF-8, BOM, size, duplicate-key
and strict-JSON checks, then entered `_build_report()`. The parser emits
`REPORT_SCHEMA_INVALID` only when strict JSON has already loaded successfully
but report construction fails.

### 3.5 Did `phase8-report-v1` construction fail?

YES. The sanitized `REPORT_SCHEMA_INVALID` code records failure during
construction of the exact provider report schema.

### 3.6 Was provider grounding validation reached?

NO. Parser failure occurs before a `ProviderCandidate` exists. The unchanged
P8-2 `SafetyReportGroundingValidator` is therefore not called for the rejected
provider content.

### 3.7 Does `grounding_status=valid` belong to TemplateFallback?

YES. After provider rejection, `ReportService.generate_provider_or_fallback()`
runs the unchanged deterministic `TemplateFallback`, validates that fallback
report through P8-2 and exposes the fallback's `VALID` result. It is not a
provider-candidate grounding result.

## 4. Schema Failure Boundary

`ProviderResponseParser.parse()` defines this sequence:

```text
bounded bytes
-> UTF-8 / BOM / JSON-syntax checks
-> exact nested phase8-report-v1 construction
-> ProviderCandidate
-> unchanged P8-2 grounding validation
```

`REPORT_SCHEMA_INVALID` is emitted in `infra/llm/response_parser.py` when
strict JSON parsing succeeds but `_build_report()` raises a schema-construction
error. The parser returns only a bounded provider error code and message. The
raw provider response is not retained, logged or persisted by the transport,
parser, report service or smoke CLI.

Consequences:

- The exact mismatched field or value cannot be recovered from the sanitized
  evidence.
- No provider response body can be reconstructed from the audit record.
- The audit does not speculate about the provider's missing, unknown or invalid
  field.
- `phase8-report-v1` is not weakened to accommodate the provider response.
- `GroundingValidator` is not changed.

## 5. Generation Path Separation

| Path | Outcome |
| --- | --- |
| Provider transport and envelope | RESPONSE RECEIVED / CONTENT EXTRACTED |
| Strict JSON syntax | PASS |
| `phase8-report-v1` construction | REJECTED / `REPORT_SCHEMA_INVALID` |
| Provider candidate grounding | NOT REACHED |
| Template fallback generation | PASS |
| Template fallback grounding | VALID |
| Final generation path | `TEMPLATE_FALLBACK` / `degraded=true` |
| Final provider validation | NOT `PROVIDER_VALIDATED` |

## 6. Validation Evidence

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

| Frozen asset | SHA256 | Result |
| --- | --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

- Charter diff: EMPTY.
- `phase-7-release-freeze-complete`: tag object
  `abb365cb4029ad079717da6cce9abb13eb18317b`, target
  `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`.
- `phase-7-web-alert-platform-complete`: tag object
  `d97c8249c756dec33a9bb149bf837871b59b3503`, target
  `a30b73c080c18d010fbaa08642868e86acb68022`.
- Persisted bearer value scan: `NO_MATCH`.
- API-key assignment scan: `NO_MATCH`.
- Raw provider response pattern scan: `NO_MATCH`.
- Broad `sk-...` scan: one false-positive source identifier only; no credential
  value was present.

## 7. Final Status

`P8-5 IMPLEMENTATION COMPLETE / REAL PROVIDER EXECUTED / PROVIDER REPORT
SCHEMA REJECTED / TEMPLATE FALLBACK PASS / HUMAN REVIEW PENDING`

The exact remaining blocker to `PROVIDER_VALIDATED` is a provider response that
satisfies the unchanged exact `phase8-report-v1` schema and then passes the
unchanged P8-2 grounding validator. The current raw provider output is not
persisted, so the concrete schema mismatch cannot be diagnosed without a new
authorized execution; this audit does not request or perform that execution.

## 8. Safety Boundary

- Another provider request: NOT EXECUTED.
- `--execute`: NOT USED.
- API-key value: NOT INSPECTED OR PRINTED.
- Authorization header: NOT PERSISTED.
- Raw provider response: NOT PERSISTED.
- `phase8-report-v1`: UNCHANGED.
- Grounding validator: UNCHANGED.
- Commit, tag and push: NOT PERFORMED.
- Basic Agent, P8-6 and Phase 9: NOT STARTED.
