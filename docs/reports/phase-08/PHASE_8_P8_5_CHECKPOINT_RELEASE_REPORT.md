# Phase 8 P8-5 Interim Release Checkpoint Report

Status: `P8-0 THROUGH P8-5 COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`

Release type: `INTERIM PHASE 8 CHECKPOINT`

This is not the Phase 8 final release.

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- Pre-release HEAD and `origin/main`:
  `47206f5b2425572fd8b186312023767d12730f42`
- Checkpoint commit:
  `ASSIGNED_AT_COMMIT_TIME / RECORDED_IN_FINAL_RELEASE_OUTPUT`
- Annotated tag: `phase-8-provider-pipeline-complete`
- Tag object and peeled target:
  `ASSIGNED_AT_TAG_TIME / RECORDED_IN_FINAL_RELEASE_OUTPUT`

## 2. Scope

This checkpoint records the authorized P8-0 through P8-5 work:

- architecture and contract freeze;
- deterministic safety analytics and canonical `phase8-context-v1` context;
- provider-independent `phase8-report-v1` report construction;
- deterministic grounding validation;
- deterministic `TemplateFallback` and safe `REPORT_UNAVAILABLE` behavior;
- provider-independent request, transport, parsing and error boundaries;
- one OpenAI-compatible chat-completions transport;
- bounded sanitized provider schema diagnostics;
- `phase8-provider-prompt-v2` schema-conformant request construction;
- focused tests, non-secret configuration, reports, phase documentation and
  worklogs.

It does not include Basic Agent implementation, P8-6 integration/evaluation,
Phase 8 final release closure or Phase 9 work.

## 3. Architecture Status

P8-0 is human-reviewed PASS. The authoritative architecture remains
`docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`, and ADR-023 continues
to freeze the read-only downstream boundary:

```text
Event Store
-> SafetyAnalyticsService
-> SafetyContextBuilder
-> SafetyLLMClient
-> StructuredSafetyReport
```

Detection, tracking, association, compliance, event persistence, inference,
training and dataset behavior remain outside the Phase 8 change scope.

## 4. Contract Status

### Deterministic Analytics and Context

P8-1 is human-reviewed PASS. `SafetyAnalyticsService` reads through
`EventQueryService`; `SafetyAnalysisContext` remains versioned
`phase8-context-v1`; canonical context and the method-level context
fingerprint remain unchanged.

### Structured Report and Grounding

P8-2 is human-reviewed PASS. `phase8-report-v1` remains the exact bounded
report contract. `SafetyReportGroundingValidator` remains bound to the
context fingerprint and fails closed on fabricated references, numeric
contradictions, unavailable-field contradictions and path/credential-like
leakage.

### Deterministic Fallback

P8-3 is human-reviewed PASS. `TemplateFallback` remains deterministic and
provider-independent, emits `TEMPLATE_FALLBACK` / `degraded=true`, and passes
the unchanged grounding validator before a report can be returned. Fallback
failure returns `REPORT_UNAVAILABLE` without a report.

### Provider Boundary

P8-4 is human-reviewed PASS. Provider requests are deterministic and bound to
the frozen context fingerprint. Provider responses are untrusted, bounded
UTF-8 JSON and cannot escape unless exact parsing and unchanged grounding
validation both pass.

### Provider E2E and Validation

P8-5 is human-reviewed PASS. One configuration-driven OpenAI-compatible
chat-completions transport exists behind the P8-4 boundary. The final
separately authorized human request used prompt v2 and returned:

```text
provider_ref: openai-compatible
model_ref: deepseek-flash
transport: PASS
strict JSON: PASS
phase8-report-v1: PASS
grounding: VALID
generation_path: PROVIDER
degraded: false
fallback: NOT USED
provider status: PROVIDER_VALIDATED
```

No provider request was issued by this checkpoint-release task.

## 5. Historical Failure Evidence

P8-5R remains preserved as historical evidence:

```text
REAL PROVIDER EXECUTED
PROVIDER REPORT SCHEMA REJECTED
TEMPLATE FALLBACK PASS
```

That request reached the provider, passed strict JSON syntax, then failed
`phase8-report-v1` construction with `REPORT_SCHEMA_INVALID`; provider
grounding was not reached. P8-5D subsequently added bounded sanitized
diagnostics, and P8-5P added `phase8-provider-prompt-v2`. The final authorized
request followed prompt v2 and passed. Historical reports retain their
original statuses.

## 6. Security Audit

- Real credential values: `NO_MATCH`
- API-key value inspected or printed: `NO`
- Authorization header persisted: `NO`
- Raw provider response persisted: `NO`
- Provider request issued by this release task: `NO`
- `--execute` used by this release task: `NO`
- Credential-bearing `.env` included: `NO`
- Database, MP4, model checkpoint or generated runtime artifact included: `NO`
- Runtime outputs remain ignored: `YES`

The credential-pattern scan had one false-positive line in
`infra/llm/fallback.py`: the identifier `risk-010-dominant-event-type`
contains the substring matched by a broad `sk-...` pattern. No credential
value is present.

## 7. Frozen Contract and Asset Verification

| Asset or contract | SHA256 | Result |
| --- | --- | --- |
| `core/schemas/safety_report.py` | `4aee24b9841bd5a8dc48f82ad93b2feaf51f9336eacbcaca8dd1f4ab0a811d42` | MATCH / UNCHANGED |
| `services/safety_report_grounding_validator.py` | `f014f2245cdf17178ae7c21f8cd6c2597a3810a8420600da3e7906825e8fd399` | MATCH / UNCHANGED |
| `infra/llm/fallback.py` | `1fdba8a8562d9760f6ac695e84b485accd3df4908c9215368dda05bc555d20ac` | MATCH / UNCHANGED |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` | MATCH |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` | MATCH |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` | MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` | MATCH |

- Charter protected-body diff: `EMPTY`
- Prompt version: `phase8-provider-prompt-v2` / UNCHANGED
- Provider trust boundary: UNCHANGED
- Phase 7 tags: UNCHANGED

## 8. Validation

Pre-commit gate:

```text
python -m pytest -q
539 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skipped test is the existing optional Torch evaluation test because Torch
is not installed on this host.

The final pre-commit and post-documentation gate is rerun before publication;
the final response records the observed results.

## 9. Gate Results

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-5-CP-G1 | Only authorized Phase 8 P8-0 through P8-5 work is included | PASS |
| P8-5-CP-G2 | Existing release tags are not moved or overwritten | PASS |
| P8-5-CP-G3 | Frozen report, grounding, fallback and provider contracts remain unchanged | PASS |
| P8-5-CP-G4 | Model, training, inference, dataset and Charter assets remain unchanged | PASS |
| P8-5-CP-G5 | No secret, raw provider response or runtime artifact enters Git | PASS |
| P8-5-CP-G6 | Provider validation is represented without re-execution | PASS |
| P8-5-CP-G7 | Full repository gates pass | PASS |
| P8-5-CP-G8 | Checkpoint and next-phase boundaries remain accurate | PASS |

## 10. Unresolved Phase 8 Work

- P8-6 integration tests, evaluation and Phase 8 release review:
  `READY / NOT STARTED`
- Basic Agent implementation: `NOT STARTED`
- Phase 8 final release closure: `NOT COMPLETE`
- Phase 9 Integration & Delivery: `NOT STARTED`
- M-021, M-022 and M-023: `待实现`

The single successful provider smoke request does not prove provider cost,
latency, rate-limit behavior or long-running stability. Raw provider content
was intentionally not persisted, so validation relies on the recorded
sanitized result and implementation-path audit rather than a packet transcript.

## 11. Final Checkpoint State

```text
Phase 8 P8-0 through P8-5: CHECKPOINT RELEASED
Phase 8: IN PROGRESS
P8-6: READY / NOT STARTED
Phase 9: NOT STARTED
```

Do not start P8-6 automatically.
