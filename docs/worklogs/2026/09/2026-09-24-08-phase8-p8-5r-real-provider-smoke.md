# 2026-09-24 - Phase 8 P8-5R Real Provider Smoke Worklog

Status: `REAL PROVIDER EXECUTED / PROVIDER REPORT SCHEMA REJECTED / TEMPLATE FALLBACK PASS / HUMAN REVIEW PENDING`

## Historical Pre-Smoke Audit

- Branch: `main`
- HEAD: `47206f5b2425572fd8b186312023767d12730f42`
- `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Existing P8-0 through P8-5 changes are preserved.
- Configured provider reference: `openai-compatible`.
- `PPE_LLM_ENDPOINT`: absent.
- `PPE_LLM_MODEL`: absent.
- `PPE_LLM_API_KEY`: absent.
- No credential value was read, printed, logged or stored.
- Timeout: `60.0` seconds.
- Maximum response size: `262144` bytes.
- Real execution remains gated behind the explicit `--execute` flag.
- Conflicts found: NO.

## Validation

- Focused regression: `109 passed`.
- Smoke CLI without `--execute`: `NOT_EXECUTED`.
- Reason: `required runtime configuration is missing: PPE_LLM_ENDPOINT`.
- Real request attempted: NO.
- Network requests issued: 0.

## Changed

- Appended the P8-5R real-provider validation attempt to
  `docs/reports/phase-08/PHASE_8_P8_5_PROVIDER_E2E_REPORT.md`.
- Added this worklog.

## Reason

Record the authorized P8-5R smoke attempt and its preconditions without
fabricating a provider validation result when runtime configuration is absent.

## Evidence

- `docs/reports/phase-08/PHASE_8_P8_5_PROVIDER_E2E_REPORT.md`
- `docs/reports/phase-08/PHASE_8_P8_5R_POST_EXECUTION_AUDIT_REPORT.md`
- Focused test command result: `109 passed`
- Historical smoke CLI result: `NOT_EXECUTED`

## Risk

Actual endpoint, model, credential, network behavior, provider response shape
and grounding result remain unverified.

## Not Verified

- real transport success or failure
- provider envelope parsing
- `phase8-report-v1` parsing
- context fingerprint match
- grounding acceptance or rejection
- provider versus fallback outcome

## Next Step

Human review the post-execution audit. Do not issue another provider request,
weaken `phase8-report-v1`, modify the grounding validator, or start Basic
Agent, P8-6 or Phase 9 without new authorization.

## Human-Executed Real Request

The human operator separately executed exactly:

```text
python scripts/run_p8_5_provider_smoke.py --execute
```

Sanitized execution identity:

- Provider family: `openai-compatible`
- Endpoint: `https://api.deepseek.com/chat/completions`
- Model: `deepseek-flash`

Sanitized result:

```json
{"degraded":true,"generation_path":"TEMPLATE_FALLBACK","grounding_status":"valid","model_ref":"deepseek-flash","provider_ref":"openai-compatible","reason":"provider path used safe fallback","safe_error_code":"REPORT_SCHEMA_INVALID","status":"TEMPLATE_FALLBACK"}
```

## Post-Execution Audit

- Real request executed: YES, by the human operator. This task did not issue
  another request and did not use `--execute`.
- Provider response received: YES.
- Provider envelope parsing: PASS.
- Provider message content extraction: PASS.
- Strict JSON syntax parsing: PASS.
- `phase8-report-v1` construction: REJECTED with `REPORT_SCHEMA_INVALID`.
- Provider grounding validation: NOT REACHED.
- Template fallback generation: PASS.
- Template fallback grounding validation: VALID.
- Provider validation: NOT `PROVIDER_VALIDATED`.
- Exact provider schema mismatch: UNRECOVERABLE because raw provider content
  was intentionally discarded and not persisted.

The `grounding_status=valid` result belongs to the deterministic fallback
report only. It must not be attributed to the rejected provider candidate.

## Final Status

`P8-5 IMPLEMENTATION COMPLETE / REAL PROVIDER EXECUTED / PROVIDER REPORT
SCHEMA REJECTED / TEMPLATE FALLBACK PASS / HUMAN REVIEW PENDING`
