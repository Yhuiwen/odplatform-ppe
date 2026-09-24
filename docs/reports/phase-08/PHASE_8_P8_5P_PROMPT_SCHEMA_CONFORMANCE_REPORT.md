# Phase 8 P8-5P Provider Prompt Schema Conformance Report

Status: `P8-5P PROVIDER PROMPT SCHEMA CONFORMANCE COMPLETE / HUMAN REVIEW PENDING`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD and `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Working tree: uncommitted P8-0 through P8-5P implementation and
  documentation changes
- P8-0 through P8-4: `HUMAN REVIEW PASS`
- P8-5: `IMPLEMENTATION COMPLETE / REAL PROVIDER EXECUTED / PROVIDER REPORT
  SCHEMA REJECTED / TEMPLATE FALLBACK PASS / HUMAN REVIEW PENDING`
- P8-5D: `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`
- P8-5P:
  `PROVIDER PROMPT SCHEMA CONFORMANCE COMPLETE / HUMAN REVIEW PENDING`
- Commit, tag and push: NOT PERFORMED

Phase 7 release tags remain unchanged:

- `phase-7-release-freeze-complete`: tag object
  `abb365cb4029ad079717da6cce9abb13eb18317b`, target
  `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`
- `phase-7-web-alert-platform-complete`: tag object
  `d97c8249c756dec33a9bb149bf837871b59b3503`, target
  `a30b73c080c18d010fbaa08642868e86acb68022`

## 2. Pre-Read and Scope

The authorization, `AGENTS.md`, Phase 8 phase document, Phase 8 architecture,
P8-5 and P8-5D reports, report schema, request builder, parser, client,
provider contracts, report service and provider-related tests were read before
editing.

This task changes only provider prompt/request construction. It does not issue
a real provider request, use `--execute`, persist credentials or raw provider
content, modify `phase8-report-v1`, weaken `GroundingValidator`, alter
`TemplateFallback`, or start P8-6.

Conflicts found in the frozen contracts: NO.

## 3. Authoritative Schema Audit

The authoritative schema source is:

```text
core/schemas/safety_report.py
```

All top-level fields are required:

```text
schema_version
source_context_sha256
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

The exact nested contract is:

| Object | Required fields | Value constraints |
| --- | --- | --- |
| `reporting_period` | `start_at`, `end_at`, `interval_semantics` | Non-empty UTC-style strings; `interval_semantics` is `[start_at,end_at]` |
| `generation` | `mode`, `degraded`, `provider_ref`, `failure_code` | `mode` is `LLM`, `TEMPLATE_FALLBACK` or `REPORT_UNAVAILABLE`; `degraded` is boolean; nullable fields remain required |
| `SafetyReportClaim` | `claim_id`, `kind`, `statement`, `fact_refs`, `metric_refs`, `event_refs`, `track_refs`, `source_refs`, `evidence_refs`, `numeric_claims` | `kind` is fixed to `observation` in summary/findings and `risk` in risk observations; every reference array may be empty |
| `TrackReference` | `track_id`, `track_scope` | Non-negative integer; `track_scope` is `tracker_scoped` |
| `MetricNumericClaim` | `metric_ref`, `value` | Identifier and finite number |
| `ReportRecommendation` | `recommendation_id`, `action`, `priority`, `basis_finding_refs`, `basis_fact_refs`, `basis_metric_refs` | Recommendations remain advisory; basis arrays may be empty at schema level but grounding may require a valid basis |
| `ReportEvidenceReference` | `evidence_ref`, `event_id`, `track_id`, `track_scope`, `snapshot_ref`, `occurred_at` | `evidence_ref` must use `EVID:<event_id>`; `track_scope` is `tracker_scoped`; snapshot and timestamp are non-empty |
| `ReportLimitation` | `field`, `reason_code`, `statement` | Identifiers and non-empty statement |

The report object and every nested object prohibit additional properties.
Every required field must be present even when its value is `null`, `[]` or an
empty string where the schema permits it.

Provider success requires:

```text
generation.mode = LLM
generation.degraded = false
generation.provider_ref = a non-secret provider label or null
generation.failure_code = null
grounding_status = unvalidated
schema_version = phase8-report-v1
source_context_sha256 = the supplied context fingerprint
```

## 4. Root-Cause Audit

The previous `phase8-provider-prompt-v1` request described the report in prose
but did not expose the complete machine-readable contract.

The concrete gaps were:

- all eleven top-level fields were not explicitly enumerated;
- nested object names and field sets were not complete;
- enum values were not represented exactly;
- nullable-but-required `generation.provider_ref` and
  `generation.failure_code` were not expressed as required fields;
- additional-property rejection was stated only generally, not at each object
  level;
- empty-array behavior and the distinction between required and nullable were
  not explicit;
- claim, recommendation, evidence and limitation item structures were not
  exact;
- provider-generation success requirements were not represented as exact
  constants.

This explains why the prior real provider response could pass transport and
strict JSON syntax while still failing `phase8-report-v1` construction with
unexpected top-level/generation fields and missing required fields. The exact
raw response is unavailable because P8-5 intentionally did not persist it.

## 5. Prompt Conformance Implementation

`infra/llm/report_schema_prompt.py` now derives a compact JSON Schema-like
description from the authoritative report dataclasses and enums. It includes:

- every top-level and nested field;
- required-field sets;
- exact enum values;
- nullable required fields;
- provider candidate constants;
- closed-object policy at every object level;
- bounded identifier, SHA256 and evidence-reference patterns;
- empty-array policy;
- reference and provider-label policies.

`PROVIDER_PROMPT_VERSION` is now:

```text
phase8-provider-prompt-v2
```

`infra/llm/request_builder.py` embeds the generated schema description in the
provider system message. The provider is instructed to output exactly one JSON
object, no Markdown or prose, exact field names, every required field, no
additional fields, the exact `source_context_sha256`, no invented references,
and tracker-scoped `track_id` semantics.

No large synthetic report example was added. The exact schema instructions are
preferred, avoiding a second independently maintained report schema and
avoiding fake values that could conflict with the supplied context.

Prompt compliance is not treated as a security boundary. The unchanged strict
parser and unchanged `SafetyReportGroundingValidator` remain authoritative.

## 6. Focused Test Coverage

`tests/test_provider_prompt_schema.py` adds seven tests covering:

- complete authoritative top-level fields;
- generation fields and provider success rules;
- nested fields, enum values and claim-kind specialization;
- `track_scope` declaration and required/property consistency;
- additional-field prohibition and empty-array policy;
- deterministic request construction;
- known malformed DeepSeek-like output still fails closed;
- schema-conforming fixture parsing and grounding reachability.

Focused command:

```text
python -m pytest -q tests/test_provider_prompt_schema.py \
  tests/test_provider_adapter.py tests/test_provider_e2e.py \
  tests/test_schema_diagnostics.py tests/test_chat_transport.py
```

Result: `80 passed`.

## 7. Full Validation

```text
python -m pytest -q
539 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host.

No real provider request was issued during P8-5P. No `--execute` invocation
was made.

## 8. Frozen Contract and Asset Verification

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

## 9. Changed Files

Implementation and tests:

- `infra/llm/report_schema_prompt.py`
- `infra/llm/request_builder.py`
- `infra/llm/provider.py`
- `tests/test_provider_prompt_schema.py`
- `tests/test_provider_e2e.py`

Required status documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`
- `docs/reports/phase-08/PHASE_8_P8_5P_PROMPT_SCHEMA_CONFORMANCE_REPORT.md`
- `docs/worklogs/2026/09/2026-09-24-10-phase8-p8-5p-prompt-schema-conformance.md`

## 10. Gate Results

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-5P-G1 | Authoritative schema was derived from code rather than prior prose | PASS |
| P8-5P-G2 | Prompt exposes all top-level and nested required fields | PASS |
| P8-5P-G3 | Prompt exposes enums, nullability, closed-object and empty-array policy | PASS |
| P8-5P-G4 | Provider candidate requirements preserve the frozen contract | PASS |
| P8-5P-G5 | `phase8-report-v1`, grounding and fallback behavior remain unchanged | PASS |
| P8-5P-G6 | Focused and full test gates pass | PASS |
| P8-5P-G7 | No real provider request, `--execute`, credential persistence or raw output retention occurs | PASS |
| P8-5P-G8 | Frozen assets, Charter and Phase 7 tags remain unchanged | PASS |

## 11. Known Limitations

- Prompt v2 improves instruction conformance but cannot guarantee provider
  output correctness.
- No real provider request was executed after the prompt change, so provider
  `PROVIDER_VALIDATED` status remains unproven.
- The historical provider response was not retained, so its exact mismatch
  cannot be reconstructed.
- Unexpected provider fields, missing fields and invalid values still fail
  closed through the unchanged parser and grounding validator.
- Basic Agent, P8-6 and Phase 9 remain unauthorized.
- M-021, M-022 and M-023 remain `待实现` in the locked Charter.

## 12. Final State

`P8-5P PROVIDER PROMPT SCHEMA CONFORMANCE COMPLETE / HUMAN REVIEW PENDING`

No commit, tag, push, real provider request or `--execute` was performed.
Waiting for human review. Do not start P8-6.
