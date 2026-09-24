# 2026-09-24 - Phase 8 P8-5P Provider Prompt Schema Conformance Worklog

Status: `P8-5P PROVIDER PROMPT SCHEMA CONFORMANCE COMPLETE / HUMAN REVIEW PENDING`

## Changed

- Added `infra/llm/report_schema_prompt.py` to derive a compact schema
  description from the authoritative `phase8-report-v1` dataclasses and enums.
- Updated `infra/llm/request_builder.py` to embed the generated schema and
  exact provider success rules in the provider system message.
- Incremented `PROVIDER_PROMPT_VERSION` from
  `phase8-provider-prompt-v1` to `phase8-provider-prompt-v2`.
- Added `tests/test_provider_prompt_schema.py` and updated provider E2E tests
  for prompt v2.
- Added this worklog and the P8-5P report, and synchronized necessary status,
  architecture, phase, changelog and test-gate documents.

## Reason

The prior provider prompt used loose prose and omitted exact nested fields,
enums, nullable-required fields, closed-object policy and empty-array policy.
The provider therefore had insufficient instruction to construct the exact
frozen `phase8-report-v1` object. P8-5P makes the prompt express the existing
contract without changing the contract itself.

## Validation

- Focused provider/prompt suite: `80 passed`.
- Full repository suite: `539 passed, 1 skipped`.
- `python -m compileall -q .`: PASS.
- `git diff --check`: PASS.
- Current working-tree Charter diff: EMPTY.
- Frozen report, grounding and fallback files: UNCHANGED.
- Frozen checkpoint, training config, inference config and processed dataset:
  MATCH.
- Phase 7 tags: unchanged.
- Real provider request: NOT ISSUED BY P8-5P.
- `--execute`: NOT USED.

## Evidence

- `docs/reports/phase-08/PHASE_8_P8_5P_PROMPT_SCHEMA_CONFORMANCE_REPORT.md`
- `infra/llm/report_schema_prompt.py`
- `tests/test_provider_prompt_schema.py`
- `docs/05_TEST_GATES.md`

## Risk

The generated schema description improves provider instructions but is not a
security boundary and does not guarantee provider conformance. The unchanged
strict parser and `SafetyReportGroundingValidator` continue to reject extra,
missing, malformed, fabricated or contradictory output.

## Not Verified

- No real provider request followed the prompt change.
- `PROVIDER_VALIDATED` remains unproven.
- The historical provider mismatch cannot be reconstructed from retained
  evidence.
- Basic Agent, P8-6 and Phase 9 were not started.

## Next Step

Human review P8-5P. Do not issue another provider request, use `--execute`,
change `phase8-report-v1`, weaken grounding, modify fallback semantics, commit,
tag, push or start P8-6 without a new authorization.
