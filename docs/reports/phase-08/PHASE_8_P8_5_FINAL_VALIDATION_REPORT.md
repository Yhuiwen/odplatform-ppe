# Phase 8 P8-5 Final Real Provider Validation Report

Status: `P8-5 IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION PASS / HUMAN REVIEW PENDING`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD and `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Working tree: uncommitted P8-0 through P8-5P implementation and
  documentation changes
- P8-0 through P8-4: `HUMAN REVIEW PASS`
- P8-5D: `HUMAN REVIEW PASS`
- P8-5P: `HUMAN REVIEW PASS`
- P8-5:
  `IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION PASS / HUMAN REVIEW PENDING`
- Commit, tag and push: NOT PERFORMED

Phase 7 release tags remain unchanged:

- `phase-7-release-freeze-complete`: tag object
  `abb365cb4029ad079717da6cce9abb13eb18317b`, target
  `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`
- `phase-7-web-alert-platform-complete`: tag object
  `d97c8249c756dec33a9bb149bf837871b59b3503`, target
  `a30b73c080c18d010fbaa08642868e86acb68022`

## 2. Scope and Evidence Boundary

The final successful real-provider request was executed manually outside this
audit. This audit did not issue another provider request, did not use
`--execute`, did not inspect or print the API-key value and did not retain raw
provider content.

The audit records the human-provided sanitized result and verifies that the
existing implementation permits exactly that result only through the intended
provider success path. It does not claim packet-level observation or a
reproducible provider-side transcript beyond the sanitized output.

## 3. Final Sanitized Result

Provider family:

```text
openai-compatible
```

Provider reference:

```text
openai-compatible
```

Model reference:

```text
deepseek-flash
```

Human-observed sanitized output:

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

Audit result:

| Item | Result |
| --- | --- |
| Real request executed | YES, manually |
| Transport | PASS |
| Provider response | RECEIVED |
| Strict JSON | PASS |
| `phase8-report-v1` | PASS |
| Provider grounding | VALID |
| Generation path | `PROVIDER` |
| Degraded | `false` |
| Final status | `PROVIDER_VALIDATED` |
| Fallback | NOT USED |
| Safe error | NONE |
| Schema diagnostics | NONE |

## 4. Implementation Audit

The following implementation facts support the sanitized result:

1. `PROVIDER_VALIDATED` can only be constructed in the provider branch after
   `SafetyLLMClient.generate_candidate()` succeeds and the unchanged P8-2
   `SafetyReportGroundingValidator.validate()` returns valid.
2. The provider success branch returns immediately with
   `generation_path=PROVIDER`; it does not call `TemplateFallback`.
3. The `ReportGenerationResult` invariant requires provider success to have
   `degraded=false`, a report, `grounding_status=valid`, provider metadata and
   no safe error.
4. Strict JSON and exact `phase8-report-v1` construction must complete before
   a `ProviderCandidate` exists. Schema failure raises
   `REPORT_SCHEMA_INVALID` instead.
5. The unchanged grounding validator must return `valid` before the provider
   result is returned.
6. `safe_error_code=null` is valid only on the provider-success branch. The
   smoke CLI derives it from `result.safe_error`.
7. `schema_diagnostics=null` is valid because no schema error existed and the
   smoke CLI emits diagnostics only from `safe_error.schema_diagnostics`.
8. The final successful attempt followed the P8-5P prompt-v2 schema
   conformance update. Prompt compliance remains non-authoritative; the strict
   parser and grounding validator remain the security boundary.

No implementation inconsistency was discovered. No code change is included in
this audit.

## 5. Historical Evidence Preserved

The earlier failed and corrective runs remain historical evidence:

1. Initial configuration/execution attempt: runtime configuration was absent,
   the smoke gate returned `NOT_EXECUTED`, and no request was issued.
2. First real-provider attempt: transport/envelope and strict JSON succeeded,
   but `phase8-report-v1` construction failed with
   `REPORT_SCHEMA_INVALID`; grounding was not reached and `TemplateFallback`
   passed.
3. P8-5D: bounded sanitized schema diagnostics were added; no raw provider
   content or credential value was retained.
4. P8-5P: prompt v2 replaced loose prose with a schema description generated
   from the authoritative report dataclasses/enums.
5. Final manual retry: the provider response satisfied the unchanged schema,
   passed grounding and returned `PROVIDER_VALIDATED`.

The success does not erase or relabel the earlier failures.

## 6. Security Audit

- The API-key value was not requested, inspected, printed or persisted by this
  audit.
- `PPE_LLM_*` runtime variables were absent at audit time; the final request
  had already completed and its temporary runtime configuration was removed.
- No authorization header is persisted in the repository.
- No raw provider response is stored.
- No credential-bearing `.env` or runtime file was added.
- No further provider request was performed.
- Secret-pattern scans are limited to file paths and counts; matching secret
  values are never rendered.

## 7. Final Regression

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

## 8. Frozen Contract and Asset Verification

| Contract or asset | SHA256 | Result |
| --- | --- | --- |
| `core/schemas/safety_report.py` | `4aee24b9841bd5a8dc48f82ad93b2feaf51f9336eacbcaca8dd1f4ab0a811d42` | MATCH / UNCHANGED |
| `services/safety_report_grounding_validator.py` | `f014f2245cdf17178ae7c21f8cd6c2597a3810a8420600da3e7906825e8fd399` | MATCH / UNCHANGED |
| `infra/llm/fallback.py` | `1fdba8a8562d9760f6ac695e84b485accd3df4908c9215368dda05bc555d20ac` | MATCH / UNCHANGED |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

`phase8-context-v1`, `phase8-report-v1`, the grounding validator and
`TemplateFallback` semantics remain unchanged. The current working-tree
Charter diff is EMPTY.

## 9. Gate Results

| Gate | Result |
| --- | --- |
| P8-5-G1 | PASS |
| P8-5-G2 | PASS |
| P8-5-G3 | PASS |
| P8-5-G4 | PASS |
| P8-5-G5 | PASS |
| P8-5-G6 | PASS |
| P8-5-G7 | PASS / REAL PROVIDER VALIDATED |
| P8-5-G8 | PASS / final regression, frozen assets, governance and tags verified |

## 10. Working Tree and Publication

- Working tree: DIRTY WITH UNCOMMITTED P8-0 THROUGH P8-5P CHANGES
- Runtime artifacts accidentally staged: NONE
- Existing Phase 7 tags: UNCHANGED
- Commit: NOT CREATED
- Tag: NOT CREATED
- Push: NOT PERFORMED

## 11. Known Limitations

- The successful provider result is based on the human-provided sanitized
  output; raw provider content was intentionally not retained.
- Provider cost, latency, rate-limit behavior, long-run stability and report
  quality have not been fully characterized.
- The provider is validated for this authorized smoke request, not for every
  future provider response or context.
- Basic Agent, P8-6 and Phase 9 remain unauthorized.
- M-021, M-022 and M-023 remain `待实现` pending the applicable Phase 8
  release and acceptance review.

## 12. Final State

`P8-5 IMPLEMENTATION COMPLETE / REAL PROVIDER VALIDATION PASS / HUMAN REVIEW PENDING`

No additional provider request, `--execute`, commit, tag, push, Basic Agent or
P8-6 work was performed. Waiting for final human review.
