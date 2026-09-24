# Phase 8 P8-1 Deterministic Safety Analytics Report

Status: `P8-1 IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD: `47206f5b2425572fd8b186312023767d12730f42`
- `origin/main`: `47206f5b2425572fd8b186312023767d12730f42`
- Phase 7 final tag: `phase-7-release-freeze-complete`
- Existing Phase 7 base tag: `phase-7-web-alert-platform-complete`
- Phase 7 tags were not moved, recreated or deleted.
- P8-0 Human Review: PASS.

## 2. Pre-Read Result

The P8-1 authorization, AGENTS.md, Master Plan, Current Status, technical
decisions, Changelog, Test Gates, Risk Register, Phase 6 and Phase 7 documents,
Phase 8 phase document, P8-0 architecture and freeze report, Event Store,
`EventQueryService`, repository and query tests were read before hardening the
implementation.

The authoritative read boundary is `EventQueryService`. The persisted event
projection is:

```text
id
timestamp
track_id
type
confidence
snapshot
status
```

The timestamp representation is UTC-normalized ISO 8601 with a trailing `Z`.
`track_id` is tracker-scoped and is not a stable person identity. No direct SQL,
provider SDK, network call or upstream mutation is present in the deterministic
path. No governance conflict was found.

## 3. Files Changed

- `core/schemas/safety.py`
- `services/safety_analytics_service.py`
- `services/safety_context_builder.py`
- `tests/test_safety_analytics.py`
- `docs/reports/phase-08/PHASE_8_P8_1_DETERMINISTIC_ANALYTICS_REPORT.md`
- `docs/worklogs/2026/09/2026-09-24-03-phase8-p8-1-deterministic-analytics.md`
- Required status synchronization in README, Master Plan, Current Status,
  Changelog, Test Gates, the Phase 8 phase document and the P8-0 status tables.

No model, dataset, mapping, training configuration, inference contract,
Phase 5/6/7 implementation, provider placeholder or dependency file was
modified.

## 4. Implemented Architecture

```text
Event Store
-> EventQueryService
-> SafetyAnalyticsService
-> SafetyContextBuilder
-> phase8-context-v1
```

`SafetyAnalyticsService` reads all matching rows through bounded deterministic
pages and rejects duplicate event identities, unsupported records, changing
totals and incomplete pages. Aggregate source counts use the existing
authoritative `EventQueryService.statistics()` method and are checked against
the same detailed event total.

The deterministic modules do not import an LLM/provider boundary, provider SDK,
HTTP client or network module. No provider or LLM is called.

## 5. Authoritative Data Sources

- `EventQueryService.query_events()` for detailed persisted event facts.
- `EventQueryService.statistics()` for authoritative source-count aggregation.
- `PersistedEvent` fields for event identity, timestamp, tracker-scoped
  identifier, event type, confidence, snapshot reference and lifecycle status.
- `SnapshotReference` through the existing event projection only as a relative
  `snapshot_ref`; evidence bytes are never embedded.

## 6. Reporting Interval Semantics

The P8-0 interval contract is preserved:

```text
[start_at, end_at]
```

Both boundaries are inclusive. The repository stores UTC-normalized
timestamps, and no undocumented timezone conversion is added. An interval with
no matching events is a successful result with zero counts and null
first/last occurrence values.

## 7. Ordering Rules

- Detailed facts: `timestamp DESC, event_id ASC`.
- Event types: the frozen `NO_HELMET`, `NO_VEST`, `PPE_UNKNOWN` order.
- Statuses: `open`, `acknowledged`, `resolved`, `dismissed`.
- Track counts: ascending tracker-scoped `track_id`.
- UTC day buckets: ascending `YYYY-MM-DD`.
- Source references: ascending opaque `SRC-<16 hex>` reference.
- Metrics: ascending `metric_id`.
- Unavailable fields: ascending `field`.
- Query filters: ascending filter key.

Database row order cannot change the logical result or canonical context.

## 8. Analytics Schema

The deterministic result contains:

- reporting interval;
- total event count;
- counts by event type and lifecycle status;
- tracker-scoped counts by `track_id`;
- UTC day distribution;
- first and last occurrence;
- evidence-available and evidence-missing counts;
- source counts using opaque local references;
- explicit unavailable fields.

All metrics use the same validated query filters. Detailed facts and
type/status/track/day/evidence metrics are computed from the fully loaded
filtered event set; source counts use the authoritative statistics projection
and must match that detailed total.

## 9. Context Schema

The context version is:

```text
phase8-context-v1
```

The four required top-level sections remain separate:

```text
observed_facts
calculated_metrics
metadata
unavailable_fields
```

Canonical JSON uses UTF-8, sorted keys, no insignificant whitespace and finite
numeric values. The context schema rejects duplicate fact IDs, metric IDs and
unavailable field names. The context does not include raw images, evidence
bytes, absolute paths, database files, credentials, environment secrets, SQL or
internal stack traces.

## 10. Unavailable-Field Handling

The implementation explicitly marks unavailable:

- stable unique-person count;
- cross-session identity;
- violation duration/average duration;
- alert-delivery telemetry;
- per-event source attribution.

Source aggregate counts are available without exposing raw sources, but the
frozen `PersistedEvent` projection does not expose per-event source, so that
linkage is never reconstructed. Values are not silently converted into zero,
compliant, violation or fabricated estimates.

## 11. Track ID Semantics

`track_id` is serialized only as a tracker-scoped reference. Every event fact
carries `track_scope: tracker_scoped`. The implementation does not expose
employee ID, worker identity or stable person identity and rejects unexpected
identity-alias constructor fields.

## 12. Evidence-Reference Behavior

`snapshot_ref` is copied from the persisted relative POSIX path and is `null`
when evidence is absent. `evidence_available` must agree with reference
presence. Source values are reduced to opaque `SRC-<16 hex>` references for
source grouping and filtering. Absolute local paths and raw source labels do
not appear in the canonical context.

## 13. Reproducibility Behavior

For the same event dataset, query interval, analytics configuration and schema
version, canonical context serialization is deterministic. Query-row reversal
does not change the logical result, canonical JSON or fingerprint.

## 14. Context Fingerprint Status

`SafetyContextBuilder.fingerprint(context)` returns a SHA256 over canonical
context content with only `metadata.generated_at` excluded. It is a method
result, not a new context field. This preserves the frozen `phase8-context-v1`
schema while providing deterministic identity for later report and grounding
work.

The same input produces the same fingerprint; material fact changes produce a
different fingerprint; wall-clock generation time does not change it. Adding a
`context_sha256` field remains an unresolved schema-amendment decision and was
not done automatically.

## 15. Tests

Focused P8-1 tests:

```text
python -m pytest -q tests/test_safety_analytics.py
18 passed
```

Coverage includes exact counts, type/status/track/day grouping, source opacity,
inclusive boundaries, empty intervals, invalid interval/timestamp inputs,
first/last occurrence, evidence availability, missing required `track_id`,
unsupported records, duplicate event identities, deterministic ordering,
query-order variation, canonical serialization, context schema validation,
reproducibility, fingerprint stability and change, absolute-path exclusion and
provider/LLM import exclusion.

Full repository gate:

```text
python -m pytest -q
432 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host.

## 16. Frozen Asset Verification

| Asset | SHA256 | Result |
| --- | --- | --- |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

The Charter diff is empty. Both Phase 7 annotated tags retain their recorded
tag objects and target commits. No provider dependency, credential or runtime
artifact was added to Git.

## 17. Gate Results

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-1-G1 | Authoritative event query boundary reused without upstream mutation | PASS |
| P8-1-G2 | Deterministic analytics produce correct counts and distributions | PASS |
| P8-1-G3 | Reporting interval and ordering semantics are deterministic | PASS |
| P8-1-G4 | `phase8-context-v1` is generated strictly from supported authoritative data | PASS |
| P8-1-G5 | Unsupported and unavailable information remains explicit and is never fabricated | PASS |
| P8-1-G6 | Empty and partial-data cases behave according to contract | PASS |
| P8-1-G7 | Reproducibility and schema-validation tests pass | PASS |
| P8-1-G8 | Full repository regression and frozen-asset checks pass | PASS |

## 18. Known Limitations and Unresolved Decisions

- Report schema construction, report grounding validation and provider
  adaptation are deferred to P8-2.
- Provider selection, authentication, context-size limits, retention and
  fallback wording remain unresolved.
- `context_sha256` is not present in the frozen context schema; only the
  method-level fingerprint is authorized.
- Source aggregates are opaque and safe for context, but per-event source
  attribution remains unavailable without a future schema change.
- Stable person identity, violation duration and alert-delivery telemetry
  remain unavailable under the current authoritative schema.
- M-021, M-022 and M-023 remain `待实现`.

## 19. Final State

`P8-1 IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS`

The report originally recorded `HUMAN REVIEW PENDING`; the subsequent P8-2
authorization confirms that P8-1 passed human review. P8-2 then completed the
structured report contract and grounding validator while remaining
`IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`. No commit, tag or push was
created for either uncommitted Phase 8 change set.
