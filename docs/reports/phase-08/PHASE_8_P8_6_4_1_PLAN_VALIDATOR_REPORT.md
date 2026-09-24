# Phase 8 P8-6.4.1 Plan Candidate Validator Report

Status: `P8-6.4.1 HUMAN REVIEW PASS`

Date: 2026-09-24

Checkpoint base: `phase-8-provider-pipeline-complete`

## 1. Scope

P8-6.4.1 implements only the strict parser, semantic validator and
deterministic conversion for the untrusted candidate contract:

```text
phase8-agent-plan-candidate-v1
```

The implemented path is:

```text
bounded UTF-8 JSON bytes
-> strict candidate parser
-> AgentPlanCandidate
-> request binding, intent, tool, argument and permission validation
-> new phase8-agent-plan-v1 AgentPlan
```

No LLM provider request, AgentService orchestration, tool execution,
autonomous reasoning, dynamic tool registration, durable audit storage or
Phase 9 work was added.

## 2. Changed Files

Implementation:

- `core/schemas/agent.py`
- `core/agent/candidate.py`
- `core/agent/__init__.py`

Tests:

- `tests/test_agent_plan_candidate.py`
- `tests/unit/test_imports.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/designs/phase-08/PHASE_8_P8_6_4_AGENT_PLANNING_ARCHITECTURE.md`
- `docs/reports/phase-08/PHASE_8_P8_6_4_ARCHITECTURE_FREEZE_REPORT.md`
- this report

## 3. Candidate Contract

`AgentPlanCandidate` contains only:

```text
schema_version
request_binding_sha256
proposed_intent
proposed_tool_name
proposed_tool_version
proposed_arguments
reason_code
```

The schema version is exactly `phase8-agent-plan-candidate-v1`. The reason
code is a closed enum:

```text
SUMMARY_REQUEST
STATISTICS_REQUEST
EVENT_DETAIL_REQUEST
REPORT_REQUEST
INSUFFICIENT_CONTEXT
```

The candidate is untrusted and is never executable. The final plan contract
remains unchanged at `phase8-agent-plan-v1`.

## 4. Strict Parser

`AgentPlanCandidateParser` accepts bounded raw UTF-8 bytes only and rejects:

- empty input, invalid UTF-8, BOM and oversized input;
- malformed JSON, duplicate keys and non-finite numbers;
- non-object payloads, missing fields, unknown fields and wrong field types;
- unknown schema versions, invalid intent/reason values and malformed hashes;
- excessive nesting, string size, node count and integer range.

Malformed candidate output is never repaired or partially accepted.

## 5. Deterministic Validation and Conversion

`build_agent_plan_request_binding()` produces the deterministic SHA256 binding
for the normalized question and frozen request/plan/registry identity.
`AgentPlanCandidateValidator` performs fail-closed validation in this order:

1. validate the normalized question and request binding;
2. reject unsupported intents;
3. reject forbidden requests identified by the deterministic planner;
4. reject a candidate that conflicts with an explicit deterministic intent;
5. reject forbidden tool, SQL, filesystem, shell and mutation-like fields;
6. resolve the exact tool name and version through the static `ToolRegistry`;
7. enforce the frozen intent-to-tool mapping and read-only effect;
8. apply the deny-by-default `ToolPermissionPolicy`;
9. validate arguments through the existing deterministic planner;
10. construct a new `AgentPlan` from validated fields only.

The validator never calls `ToolRegistry.execute`, never returns a provider
object and does not copy provider prose, reasoning or unknown fields.

## 6. Tests

Focused:

```text
python -m pytest tests/test_agent_plan_candidate.py tests/test_agent_planner.py tests/test_agent_tool_registry.py tests/test_agent_audit.py tests/unit/test_imports.py -q
148 passed
```

Coverage includes:

- valid candidate parsing and conversion;
- malformed JSON, duplicate keys and non-finite values;
- unknown and extra fields;
- unknown, dynamic and forbidden tools;
- invalid arguments, unsupported fields and wrong period shape;
- SQL, filesystem, shell and mutation-like candidate payloads;
- unknown intent and deterministic intent conflict;
- request binding mismatch and unauthorized permissions;
- deterministic repeated conversion;
- proof that `ToolRegistry.execute` is not called.

Full repository:

```text
python -m pytest -q
613 passed, 1 skipped
```

The skipped test is the existing optional Torch evaluation test because Torch
is not installed on this host.

## 7. Frozen Compatibility

| Contract or asset | Result |
| --- | --- |
| `phase8-agent-plan-v1` | UNCHANGED |
| Deterministic planner | UNCHANGED |
| Static four-tool registry | UNCHANGED |
| Deny-by-default permissions | UNCHANGED |
| `phase8-agent-audit-v1` | UNCHANGED |
| `phase8-report-v1` | UNCHANGED |
| `SafetyReportGroundingValidator` | UNCHANGED |
| `TemplateFallback` | UNCHANGED |
| P8-5 provider transport and trust boundary | UNCHANGED |
| `phase-8-provider-pipeline-complete` tag | UNCHANGED |
| Model, dataset, training and inference assets | UNCHANGED |
| Charter protected body | UNCHANGED / EMPTY DIFF |

No provider request or model load was performed.

## 8. Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-6.4.1-G1 | Candidate schema is versioned, immutable and separate from `AgentPlan` | PASS |
| P8-6.4.1-G2 | Parser accepts bounded strict UTF-8 JSON only and repairs nothing | PASS |
| P8-6.4.1-G3 | Intent, tool name, tool version and reason code are validated | PASS |
| P8-6.4.1-G4 | Request binding, deterministic intent conflict and forbidden requests are enforced | PASS |
| P8-6.4.1-G5 | Static registry and deny-by-default permissions are enforced before conversion | PASS |
| P8-6.4.1-G6 | Arguments use the existing deterministic planner validation path | PASS |
| P8-6.4.1-G7 | Candidate conversion is deterministic and has no tool execution side effects | PASS |
| P8-6.4.1-G8 | Frozen P8-5 contracts, assets and checkpoint tag remain unchanged | PASS |

## 9. Known Limitations

- `INSUFFICIENT_CONTEXT` candidates are parsed but cannot produce an
  executable plan; only the four supported intent/reason pairs are converted.
- No provider prompt or provider transport call is implemented in this
  slice.
- `AgentService` orchestration and answer synthesis remain unimplemented.
  P8-6.4.2 subsequently adds the provider-independent planner audit and
  deterministic fallback boundary.
- No real provider candidate or runtime Agent plan has been validated.
- M-023 remains `待实现`.

## 10. Final State

```text
P8-6.1: HUMAN REVIEW PASS
P8-6.2: HUMAN REVIEW PASS
P8-6.3: HUMAN REVIEW PASS
P8-6.4: ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS
P8-6.4.1: HUMAN REVIEW PASS
P8-6.4.2 LLM planner adapter: HUMAN REVIEW PASS
P8-6.4.3 AgentService orchestration: HUMAN REVIEW PASS
Agent implementation checkpoint: RELEASED
Phase 9: NOT STARTED
```

No commit, tag or push was performed by this slice. The later reviewed
implementation is recorded by tag `phase-8-controlled-agent-complete`.
