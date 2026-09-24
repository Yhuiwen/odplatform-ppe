# Phase 8 P8-3 Deterministic Template Fallback Report

Status: `P8-3 IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD: `47206f5b2425572fd8b186312023767d12730f42`
- `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- P8-0: `HUMAN REVIEW PASS`
- P8-1: `HUMAN REVIEW PASS`
- P8-2: `HUMAN REVIEW PASS`
- P8-3: `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`

The Phase 7 tags remain unchanged:

- `phase-7-release-freeze-complete` tag object
  `abb365cb4029ad079717da6cce9abb13eb18317b`, target
  `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`
- `phase-7-web-alert-platform-complete` tag object
  `d97c8249c756dec33a9bb149bf837871b59b3503`, target
  `a30b73c080c18d010fbaa08642868e86acb68022`

## 2. Pre-Read Result

The P8-0 architecture, P8-1 analytics/context contracts, P8-2 report and
grounding validator, current phase records and the two placeholder boundaries
were read before editing. No locked governance or frozen-contract conflict was
found. The authorization records P8-2 as human-review PASS and authorizes only
the deterministic local fallback; the workspace status text was synchronized
to that newer decision.

## 3. Scope

P8-3 implements:

```text
phase8-context-v1
-> TemplateFallback
-> phase8-report-v1
-> SafetyReportGroundingValidator
-> VALID
```

It does not implement a provider adapter, provider selection, authentication,
retry policy, real LLM call, Basic Agent, P8-4 or Phase 9 capability.

## 4. Implementation

### 4.1 `TemplateFallback`

`infra/llm/fallback.py` now accepts only `SafetyAnalysisContext` and builds a
deterministic `StructuredSafetyReport`.

The fallback:

- uses `SafetyContextBuilder.fingerprint(context)` directly;
- copies the exact inclusive reporting period;
- emits `schema_version=phase8-report-v1`;
- emits `generation.mode=TEMPLATE_FALLBACK`;
- sets `generation.degraded=true`;
- uses only existing fact IDs, event IDs, metric IDs, tracker-scoped track IDs,
  source references and available evidence metadata;
- copies every unavailable field and reason code into report limitations;
- contains no random value, wall-clock-derived report text, provider call or
  network import.

### 4.2 Deterministic findings

The generated report contains:

- an executive summary bound to
  `analytics.event_total_count`;
- a total-event finding;
- non-zero event-type counts ordered by count descending and event-type value
  ascending;
- first and last occurrence when the event set is non-empty;
- evidence available/missing counts;
- tracker-scoped recurrence wording that explicitly states `track_id` is not a
  stable person identity;
- a frequency-only risk observation only when one dominant event type exists;
- conservative recommendations for `NO_HELMET`, `NO_VEST` and `PPE_UNKNOWN`
  when the corresponding exact count is positive;
- evidence references only for context facts with available snapshots.

An empty context produces a valid zero-event report, no fabricated facts, no
evidence references and no risk or recommendation.

### 4.3 `ReportService`

`services/report_service.py` now provides deterministic orchestration:

```text
TemplateFallback.generate(context)
-> SafetyReportGroundingValidator.validate(report, context)
-> return report with grounding_status=VALID
```

The service returns a report only when the unchanged P8-2 validator passes.
Validation failure raises `GROUNDING_VALIDATION_FAILED`; malformed fallback
input raises a bounded deterministic error.

## 5. Fail-Closed Behavior

The fallback validates required metric presence, integer ranges, event totals,
event-type totals, evidence counts, occurrence bounds and tracker counts before
constructing a report. Missing required metrics, non-integer total/count
metrics, inconsistent evidence totals or inconsistent tracker metrics raise
`TemplateFallbackError` with `FALLBACK_FAILED`.

The fallback does not repair or infer malformed analytics. It does not use
nearest-neighbor, threshold guessing or free-text number extraction to make a
claim pass grounding.

## 6. Files Changed

Implementation:

- `infra/llm/fallback.py`
- `services/report_service.py`
- `tests/test_template_fallback.py`
- `tests/unit/test_placeholders.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- this report
- `docs/worklogs/2026/09/2026-09-24-05-phase8-p8-3-template-fallback.md`

No provider integration, model, dataset, mapping, training configuration,
inference contract, Phase 5 tracking, Phase 6 compliance/event or Phase 7
storage/dashboard implementation was changed.

## 7. Focused Tests

`python -m pytest -q tests/test_template_fallback.py`

Result: `12 passed`.

Coverage includes:

- deterministic repeated generation;
- unchanged P8-2 grounding validation;
- `ReportService` `VALID` status;
- exact context fingerprint;
- type-count ordering and exact numeric claims;
- event, tracker-scoped track and evidence references;
- empty context behavior;
- exact unavailable-field preservation;
- explicit tracker-scope wording;
- all three recommendation rules;
- unique dominant risk and tied-maximum suppression;
- missing/malformed metric failure;
- validator rejection handling;
- no provider/network imports;
- no absolute-path or credential leakage.

The removed placeholder expectations were replaced by these real
implementations. The remaining placeholder suite still passes.

## 8. Full Regression

```text
python -m pytest -q
460 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host.

## 9. Frozen Assets and Governance

| Asset | SHA256 | Result |
| --- | --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

Charter diff: EMPTY.

## 10. Gate Results

| Gate | Status |
| --- | --- |
| P8-3-G1 typed deterministic provider-independent fallback | PASS |
| P8-3-G2 report fingerprint and reporting-period binding | PASS |
| P8-3-G3 context-grounded fact/metric/track/evidence references | PASS |
| P8-3-G4 unavailable fields and conservative recommendations | PASS |
| P8-3-G5 empty, tie and malformed-metric fail-closed behavior | PASS |
| P8-3-G6 validation-gated `ReportService` output | PASS |
| P8-3-G7 no provider/network/model/upstream dependency | PASS |
| P8-3-G8 full regression and frozen-asset checks | PASS |

## 11. Known Limitations

- No provider adapter or external LLM call exists.
- No provider timeout, retry, rate-limit or authentication path is implemented.
- Free-text semantic contradiction detection remains outside P8-3; grounding
  is structural and deterministic.
- M-021, M-022 and M-023 remain `待实现` in the locked Charter until full
  acceptance.
- Provider integration, Basic Agent, P8-4 and Phase 9 remain unauthorized.

## 12. Final State

`P8-3 IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`

No commit, tag or push was created.
