# Phase 8 P8-5D Sanitized Provider Schema Diagnostics Report

Status: `P8-5D SANITIZED SCHEMA DIAGNOSTICS COMPLETE / HUMAN REVIEW PENDING`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD and `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Working tree: uncommitted P8-0 through P8-5R implementation plus P8-5D
  diagnostics and documentation
- P8-0 through P8-4: `HUMAN REVIEW PASS`
- P8-5: `IMPLEMENTATION COMPLETE / REAL PROVIDER EXECUTED / PROVIDER REPORT
  SCHEMA REJECTED / TEMPLATE FALLBACK PASS / HUMAN REVIEW PENDING`
- P8-5D: `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`
- Commit, tag and push: NOT PERFORMED

Phase 7 release tags remain unchanged:

- `phase-7-release-freeze-complete`: tag object
  `abb365cb4029ad079717da6cce9abb13eb18317b`, target
  `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`
- `phase-7-web-alert-platform-complete`: tag object
  `d97c8249c756dec33a9bb149bf837871b59b3503`, target
  `a30b73c080c18d010fbaa08642868e86acb68022`

## 2. Pre-Read and Scope

The authorization, `AGENTS.md`, current status, technical decisions, test
gates, Phase 8 document, Phase 8 architecture, P8-5 and P8-5R reports,
report/parser/provider/client/service/CLI implementation and relevant tests
were read before editing.

This task improves only the failure evidence for an already rejected provider
report:

```text
strict JSON syntax PASS
-> phase8-report-v1 construction FAIL
-> REPORT_SCHEMA_INVALID
-> bounded sanitized diagnostics
-> unchanged TemplateFallback
```

The task does not issue a real provider request, does not use `--execute`,
does not persist raw provider output and does not change report, grounding,
fallback or trust-boundary semantics.

Conflicts found in the frozen contracts: NO.

## 3. Frozen Architecture Diff Audit

`docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md` is untracked in the
current worktree, so a Git object diff from its original creation is not
available. Comparison against the recorded P8-0 freeze report found only:

- subphase numbering synchronization;
- current-status wording;
- the already-authorized P8-5 sequence clarification and P8-5D status row.

No change was found to:

- `phase8-context-v1`;
- `phase8-report-v1`;
- grounding semantics;
- fallback semantics;
- provider trust boundary;
- privacy boundary.

## 4. Sanitized Diagnostic Contract

`infra/llm/provider.py` adds bounded project-owned types:

```text
SchemaDiagnostic
  path
  code
  expected
  actual_type
  constraint

SchemaDiagnostics
  diagnostics
  truncated
  maximum_errors
```

Allowed diagnostic categories are:

```text
MISSING_FIELD
UNEXPECTED_FIELD
INVALID_TYPE
INVALID_ENUM
INVALID_FORMAT
INVALID_VALUE
INVALID_COLLECTION
SCHEMA_CONSTRUCTION_FAILED
```

Diagnostic paths use deterministic JSON-path syntax such as `$`,
`$.schema_version`, `$.key_findings[0].finding_id` or
`$.recommendations[1].basis_refs`. The implementation validates path shape,
bounds diagnostic text, and permits only bounded JSON type names for
`actual_type`.

Raw field values, raw provider response text, unknown provider field names,
free-form provider text, API keys, authorization headers, absolute paths and
source context payloads are not included.

## 5. Parser Behavior

`infra/llm/response_parser.py` keeps the existing public failure identity:

```text
ProviderErrorCode.REPORT_SCHEMA_INVALID
```

After strict JSON syntax parsing succeeds, a `phase8-report-v1` construction
failure now returns that code with `SchemaDiagnostics`. The parser:

- never repairs provider output;
- never returns a partial or invalid report;
- never weakens required fields, types, enums or nested shapes;
- diagnoses nested arrays and objects with bounded paths;
- orders diagnostics deterministically;
- records at most `20` diagnostics;
- sets `truncated=true` when additional failures exist;
- falls back to `SCHEMA_CONSTRUCTION_FAILED` at `$` if no narrower diagnostic
  can be produced safely.

## 6. Error Propagation

Sanitized diagnostics propagate through the existing safe error path:

```text
ProviderResponseParser
-> ProviderError.schema_diagnostics
-> SafetyLLMClient
-> SafeProviderError.schema_diagnostics
-> ReportGenerationResult
-> smoke CLI JSON metadata
```

`services/report_service.py` preserves its existing provider-first routing.
An invalid provider report still produces `TEMPLATE_FALLBACK`, and fallback
grounding remains independent from the rejected provider candidate. No raw
report object, raw JSON, prompt, context body or credential can escape through
the diagnostic wrapper.

`scripts/run_p8_5_provider_smoke.py` may print only:

- `schema_diagnostics`;
- `schema_diagnostics_truncated`;
- existing sanitized provider status metadata.

## 7. Focused Test Coverage

`tests/test_schema_diagnostics.py` adds local MockTransport coverage for:

- missing required field;
- wrong primitive type;
- invalid enum;
- nested-array path;
- deterministic multiple diagnostics;
- stable ordering;
- count limit and truncation;
- invalid field-value non-leakage;
- raw-response and unknown-field-name non-leakage;
- API-key non-leakage;
- unchanged `REPORT_SCHEMA_INVALID` public code;
- invalid provider report routing to fallback;
- fallback grounding remaining VALID;
- smoke CLI output containing only sanitized diagnostics.

Focused command:

```text
python -m pytest -q tests/test_schema_diagnostics.py \
  tests/test_provider_e2e.py tests/test_provider_adapter.py \
  tests/test_chat_transport.py
```

Result: `73 passed`.

## 8. Full Validation

```text
python -m pytest -q
532 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host.

No real provider request was issued during P8-5D. No `--execute` invocation
was made.

## 9. Frozen Contract and Asset Verification

| Asset or contract | SHA256 | Result |
| --- | --- | --- |
| `core/schemas/safety_report.py` | `4aee24b9841bd5a8dc48f82ad93b2feaf51f9336eacbcaca8dd1f4ab0a811d42` | MATCH / UNCHANGED |
| `services/safety_report_grounding_validator.py` | `f014f2245cdf17178ae7c21f8cd6c2597a3810a8420600da3e7906825e8fd399` | MATCH / UNCHANGED |
| `infra/llm/fallback.py` | `1fdba8a8562d9760f6ac695e84b485accd3df4908c9215368dda05bc555d20ac` | MATCH / UNCHANGED |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

The current working-tree Charter diff is EMPTY. Phase 7 tags are unchanged.

## 10. Changed Files

Implementation and tests:

- `infra/llm/provider.py`
- `infra/llm/response_parser.py`
- `infra/llm/llm_client.py`
- `services/report_service.py`
- `scripts/run_p8_5_provider_smoke.py`
- `tests/test_schema_diagnostics.py`

Required status documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`
- `docs/reports/phase-08/PHASE_8_P8_5D_SCHEMA_DIAGNOSTICS_REPORT.md`
- `docs/worklogs/2026/09/2026-09-24-09-phase8-p8-5d-schema-diagnostics.md`

## 11. Known Limitations

- The historical DeepSeek schema mismatch remains unrecoverable because raw
  provider content was intentionally not persisted.
- P8-5D makes a future authorized `REPORT_SCHEMA_INVALID` attempt diagnosable;
  it does not prove the provider's current output is valid.
- The provider has not been marked `PROVIDER_VALIDATED`.
- Basic Agent, P8-6 and Phase 9 remain unauthorized.
- M-021, M-022 and M-023 remain `待实现` in the locked Charter.

## 12. Final State

`P8-5D SANITIZED SCHEMA DIAGNOSTICS COMPLETE / HUMAN REVIEW PENDING`

No commit, tag, push, real provider request or `--execute` was performed.
