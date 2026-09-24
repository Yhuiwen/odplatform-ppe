# 2026-09-24 - Phase 8 P8-5D Sanitized Schema Diagnostics Worklog

Status: `P8-5D SANITIZED SCHEMA DIAGNOSTICS COMPLETE / HUMAN REVIEW PENDING`

## Changed

- Added bounded `SchemaDiagnostic`, `SchemaDiagnostics` and
  `SchemaDiagnosticCode` contracts under `infra/llm/provider.py`.
- Extended `ProviderError` and `SafeProviderError` with optional sanitized
  diagnostics.
- Updated `infra/llm/response_parser.py` so a strict-JSON payload that fails
  `phase8-report-v1` construction still returns `REPORT_SCHEMA_INVALID` and
  includes safe paths, categories, expected constraints and actual JSON types.
- Limited diagnostics to 20 entries with deterministic ordering and a
  `truncated` flag.
- Propagated only sanitized diagnostics through `SafetyLLMClient`,
  `ReportService` and the provider smoke CLI.
- Added `tests/test_schema_diagnostics.py`.
- Added this worklog and the P8-5D report, and synchronized necessary status,
  architecture, changelog, phase and test-gate documents.

## Reason

The prior real-provider attempt failed at `phase8-report-v1` construction, but
raw provider content was intentionally not retained. The failure could not be
diagnosed without weakening the schema or persisting unsafe provider data.
P8-5D adds bounded, privacy-safe evidence for future authorized failures while
preserving strict parsing, grounding and fallback behavior.

## Validation

- Focused provider/diagnostic suite: `73 passed`.
- Full repository suite: `532 passed, 1 skipped`.
- `python -m compileall -q .`: PASS.
- `git diff --check`: PASS.
- Current working-tree Charter diff: EMPTY.
- Frozen report, grounding and fallback files: UNCHANGED.
- Frozen checkpoint, training config, inference config and processed dataset:
  MATCH.
- Phase 7 tags: unchanged.
- Real provider request: NOT ISSUED BY P8-5D.
- `--execute`: NOT USED.

## Evidence

- `docs/reports/phase-08/PHASE_8_P8_5D_SCHEMA_DIAGNOSTICS_REPORT.md`
- `tests/test_schema_diagnostics.py`
- `docs/reports/phase-08/PHASE_8_P8_5R_POST_EXECUTION_AUDIT_REPORT.md`
- `docs/05_TEST_GATES.md`

## Risk

Diagnostics intentionally omit actual values and unknown field names, so they
identify schema locations and failure categories but not the provider's exact
content. The public `REPORT_SCHEMA_INVALID` failure remains unchanged and no
provider candidate is accepted without the existing strict parser and
grounding validator.

## Not Verified

- No new real provider response was requested or inspected.
- The historical schema mismatch cannot be reconstructed.
- Provider schema validity and `PROVIDER_VALIDATED` status remain unproven.
- Basic Agent, P8-6 and Phase 9 were not started.

## Next Step

Human review P8-5D. Do not issue another provider request, use `--execute`,
change `phase8-report-v1`, modify the grounding validator or fallback rules,
commit, tag, push, start Basic Agent, start P8-6 or start Phase 9 without a new
authorization.
