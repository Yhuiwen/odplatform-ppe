# Phase 8 P8-2 Report Grounding Validation Report

Status: `P8-2 IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD: `47206f5b2425572fd8b186312023767d12730f42`
- `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- P8-0: `DESIGN COMPLETE / HUMAN REVIEW PASS`
- P8-1: `IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`
- Phase 7 tags remain unchanged:
  - `phase-7-release-freeze-complete` tag object
    `abb365cb4029ad079717da6cce9abb13eb18317b`, target
    `07e7986cf1e5a803a25dcac58ee2cce4e6c50c20`
  - `phase-7-web-alert-platform-complete` tag object
    `d97c8249c756dec33a9bb149bf837871b59b3503`, target
    `a30b73c080c18d010fbaa08642868e86acb68022`

## 2. Pre-Read Result

The P8-2 authorization, AGENTS.md, authoritative Phase 8 design and P8-0/P8-1
reports, P8-1 schema/builder/analytics implementation, report and Agent
placeholders and the existing dependency manifests were read before editing.
No governance or frozen-contract conflict was found.

P8-1's inclusive `[start_at, end_at]` reporting period remains unchanged. The
report copies the exact `ReportingPeriod` and validation rejects a mismatch.
Adjacent report windows must therefore be constructed by the caller so they do
not unintentionally double-count a shared boundary timestamp.

## 3. Contract Verification

The frozen `phase8-context-v1` contract remains unchanged:

- top-level sections are `observed_facts`, `calculated_metrics`, `metadata`
  and `unavailable_fields`;
- canonical context serialization remains sorted-key, compact UTF-8 JSON;
- `SafetyContextBuilder.fingerprint(context)` remains a method-level SHA256
  that excludes only `metadata.generated_at`;
- no `context_sha256` field was added;
- event references remain persisted event IDs;
- `track_id` remains tracker-scoped, never stable person identity;
- opaque source references remain `SRC-<16 lowercase hex>`;
- unavailable fields remain explicit and are never inferred.

No P8-1 implementation file was modified.

## 4. Files Changed

- `core/schemas/safety_report.py`
- `services/safety_report_grounding_validator.py`
- `tests/test_safety_report_grounding.py`
- `docs/reports/phase-08/PHASE_8_P8_2_REPORT_GROUNDING_VALIDATION_REPORT.md`
- `docs/worklogs/2026/09/2026-09-24-04-phase8-p8-2-report-grounding.md`
- Required status synchronization in README, Master Plan, Current Status,
  Changelog, Test Gates and the Phase 8 phase document.

No model, dataset, mapping, training configuration, inference contract,
Phase 5/6/7 implementation, provider placeholder or dependency file was
modified.

## 5. `phase8-report-v1` Schema

`StructuredSafetyReport` contains:

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

Claims remain separate from recommendations. Each claim exposes explicit,
machine-readable references:

```text
claim_id
kind
statement
fact_refs
metric_refs
event_refs
track_refs
source_refs
evidence_refs
numeric_claims
```

`track_refs` use `track_scope: tracker_scoped` and cannot represent an employee
or stable person identity. `ReportGeneration` accepts only `LLM`,
`TEMPLATE_FALLBACK` or `REPORT_UNAVAILABLE`; P8-2 does not implement any of
those producers.

## 6. Source Context Fingerprint Binding

Every report carries `source_context_sha256`. The validator recomputes the
value using the frozen P8-1 method:

```text
SafetyContextBuilder.fingerprint(context)
```

Missing, malformed or mismatched fingerprints produce
`CONTEXT_FINGERPRINT_MISMATCH`. The fingerprint remains outside the
`phase8-context-v1` payload.

## 7. Grounding and Numeric Validation

Validation checks:

- fact references against `observed_facts.fact_id`;
- metric references against `calculated_metrics.metric_id`;
- event references against `observed_facts.event_id`;
- tracker-scoped track references against referenced event facts or
  tracker-scoped metrics;
- source references against the referenced event facts;
- evidence references against top-level verified evidence metadata and context
  snapshot metadata;
- top-level evidence event, track, timestamp and snapshot identity;
- structured numeric claim values exactly against the referenced
  `MetricValue.value`;
- recommendation bases against report findings, context facts and context
  metrics.

No fuzzy number matching or free-text numeric inference is used.

## 8. Fail-Closed and Recommendation Semantics

The validator returns deterministic structured errors and never repairs,
rewrites, removes or guesses bad content. Unknown references, ungrounded
findings, ungrounded risk observations, invalid recommendation bases,
unavailable-field claims and numeric mismatches reject the report.

Recommendations remain advisory. A recommendation must have at least one
valid finding, fact or metric basis; the validator does not judge whether the
recommended action is professionally optimal.

## 9. Limitation and Privacy Handling

Report limitations must correspond exactly to the supplied context's
unavailable fields and reason codes. Missing or contradictory limitations
produce `UNAVAILABLE_FIELD_CLAIM`. This preserves the P8-1 boundaries for
duration, stable identity, cross-session identity, alert-delivery telemetry
and per-event source attribution.

The report is scanned deterministically for obvious absolute Windows paths,
absolute POSIX paths, database paths, credential-like assignments,
bearer-token patterns and credential-bearing URIs. Detected leakage produces
`PATH_LEAK_DETECTED`.

## 10. Canonicalization

Claims, recommendations, evidence references and limitations are normalized
into stable order. Canonical report JSON uses UTF-8, sorted object keys,
compact separators and finite values. Equivalent logical reports therefore
produce byte-identical canonical JSON.

Validation issues are sorted by a frozen code order and then by path/message.
Repeated validation of the same report/context pair produces identical
canonical validation results.

## 11. Focused Tests

`python -m pytest -q tests/test_safety_report_grounding.py`

Result: `18 passed`.

Coverage includes a fully grounded report, matching and mismatched
fingerprints, unknown fact/metric/event/track/evidence/source references,
numeric match/mismatch, ungrounded findings and risks, recommendation bases,
unavailable-field contradictions, empty/zero-event reports, fabricated
empty-context events, stable error ordering, canonical serialization,
Windows/POSIX path leakage, tracker-scope enforcement and no provider/network
import dependency.

## 12. Full Regression

```text
python -m pytest -q
450 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host.

## 13. Frozen Assets and Governance

| Asset | SHA256 | Result |
| --- | --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

The Charter diff is empty, P8-1 files are unchanged, and both Phase 7 tags
retain their recorded tag objects and target commits.

## 14. Gate Results

| Gate | Status |
| --- | --- |
| P8-2-G1 `phase8-report-v1` schema without provider dependency | PASS |
| P8-2-G2 context fingerprint binding | PASS |
| P8-2-G3 fact/metric/event/track/evidence reference validation | PASS |
| P8-2-G4 exact structured numeric validation | PASS |
| P8-2-G5 ungrounded content fails closed | PASS |
| P8-2-G6 unavailable and privacy boundaries | PASS |
| P8-2-G7 reproducible canonicalization and validation | PASS |
| P8-2-G8 full regression and no-provider checks | PASS |

## 15. Known Limitations

- No provider adapter, provider SDK, retry policy or authentication exists.
- No `TemplateFallback` implementation exists.
- No real LLM-generated report was evaluated; P8-2 uses deterministic test
  fixtures only.
- Grounding validation checks reference integrity and deterministic bounds,
  not the professional quality of a future recommendation.
- Free-text semantic contradiction detection remains intentionally out of
  scope; only structured and mechanically detectable contradictions are
  rejected.

## 16. Final State

`P8-2 IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`

Provider integration, TemplateFallback, Basic Agent and P8-3 remain
unauthorized. No commit, tag or push was created. M-021, M-022 and M-023 remain
`待实现`.
