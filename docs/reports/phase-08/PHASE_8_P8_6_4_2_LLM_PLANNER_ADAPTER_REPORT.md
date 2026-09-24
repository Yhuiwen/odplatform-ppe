# Phase 8 P8-6.4.2 LLM Planner Adapter Report

Status: `P8-6.4.2 HUMAN REVIEW PASS`

Date: 2026-09-24

Checkpoint base: `phase-8-provider-pipeline-complete`

## 1. Scope

P8-6.4.2 implements only the provider-independent LLM planner adapter:

```text
LLMPlannerCandidateClient
-> untrusted candidate bytes
-> AgentPlanCandidateParser
-> AgentPlanCandidateValidator
-> phase8-agent-plan-v1
```

The adapter does not execute a tool, call `ToolRegistry.execute`, implement
`AgentService`, run an autonomous loop, add memory, discover dynamic tools,
invoke provider-native tool calling or enter Phase 9. No real provider request
was issued.

## 2. Changed Files

Implementation:

- `core/agent/llm_planner.py`
- `services/llm_planner_adapter.py`
- `core/agent/__init__.py`

Tests:

- `tests/test_llm_planner_adapter.py`
- `tests/unit/test_imports.py`

Documentation:

- `README.md`
- `docs/01_MASTER_PLAN.md`
- `docs/02_CURRENT_STATUS.md`
- `docs/04_CHANGELOG.md`
- `docs/05_TEST_GATES.md`
- `docs/phases/PHASE_08_LLM_AGENT.md`
- `docs/designs/phase-08/PHASE_8_P8_6_4_AGENT_PLANNING_ARCHITECTURE.md`
- `docs/reports/phase-08/PHASE_8_P8_6_4_1_PLAN_VALIDATOR_REPORT.md`
- this report

## 3. Request Boundary

`PlannerCandidateRequestBuilder` builds deterministic
`phase8-agent-planner-request-v1` requests. A request contains:

- normalized user question;
- static `phase8-agent-plan-candidate-v1` field metadata;
- the four frozen tool names and versions with bounded input fields;
- request binding SHA256;
- finite timeout and response-size policy.

The request contains no event rows, audit history, evidence, filesystem or
database path, credential, model artifact or provider-native tool call.
`LLMPlannerCandidateClient` is an injected protocol that returns untrusted
candidate bytes. It contains no network implementation.

The provider-independent adapter does not repurpose or modify the
report-specific `SafetyLLMClient`. The frozen P8-5 report pipeline remains
unchanged.

## 4. Adapter Behavior

`LLMPlannerAdapter` follows this order:

1. normalize the question and run deterministic forbidden-intent precheck;
2. confirm `provider:invoke` through the unchanged permission policy;
3. optionally obtain one candidate through the injected client;
4. pass candidate bytes through the strict P8-6.4.1 parser;
5. pass the parsed candidate through the existing validator;
6. append a bounded planning audit event;
7. return only a new `phase8-agent-plan-v1`.

The adapter never calls a tool handler and never returns a provider object.

## 5. Failure Semantics

| Outcome | Behavior |
| --- | --- |
| Valid candidate | Strictly validated and converted to `AgentPlan`; audited as `PLANNED` |
| Malformed/invalid candidate | Audited as `FAILURE`; deterministic planner fallback |
| Unknown candidate tool | Audited as `UNKNOWN_TOOL` / `TOOL_NOT_FOUND`; deterministic planner fallback |
| Provider failure | Audited as `FAILURE` with bounded provider code; deterministic planner fallback |
| Forbidden capability or unauthorized candidate | Audited as `REFUSED`; no fallback and no privilege escalation |
| Forbidden request before provider | Audited as `REFUSED`; provider client is not called |
| Deterministic fallback cannot plan | Structured `LLMPlannerError`; no tool execution |

Audit events use the unchanged `phase8-agent-audit-v1` contract and retain no
raw question, candidate payload, provider output, path or credential.

## 6. Focused Tests

```text
python -m pytest tests/test_llm_planner_adapter.py tests/test_agent_plan_candidate.py tests/test_agent_planner.py tests/test_agent_audit.py tests/unit/test_imports.py -q
148 passed
```

Coverage includes:

- deterministic request building;
- valid LLM candidate through strict validation;
- malformed candidate fallback;
- forbidden candidate refusal without fallback;
- provider-failure fallback;
- missing `provider:invoke` capability with no client call;
- no `ToolRegistry.execute` call on either path;
- audit metadata generation and payload exclusion;
- deterministic forbidden-request precheck before provider call;
- static checks for no Agent framework, provider SDK, network or system
  execution dependency.

Full repository:

```text
python -m pytest -q
625 passed, 1 skipped
```

`python -m compileall -q .` and `git diff --check` also pass. The skip is the
existing optional Torch evaluation test.

## 7. Frozen Compatibility

| Contract or asset | Result |
| --- | --- |
| `phase8-agent-plan-candidate-v1` | UNCHANGED |
| `phase8-agent-plan-v1` | UNCHANGED |
| `phase8-agent-tool-registry-v1` | UNCHANGED |
| `phase8-agent-policy-v1` | UNCHANGED |
| `phase8-agent-audit-v1` | UNCHANGED |
| `phase8-report-v1` | UNCHANGED |
| `SafetyReportGroundingValidator` | UNCHANGED |
| `TemplateFallback` | UNCHANGED |
| P8-5 provider pipeline | UNCHANGED |
| `phase-8-provider-pipeline-complete` | UNCHANGED |
| Model, dataset, training and inference assets | UNCHANGED |
| Charter protected body | UNCHANGED / EMPTY DIFF |

No real provider request or model load was performed.

## 8. Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-6.4.2-G1 | Planner request builder is bounded, deterministic and tool-call-free | PASS |
| P8-6.4.2-G2 | Candidate client boundary is injected and untrusted | PASS |
| P8-6.4.2-G3 | Candidate output uses the existing strict parser and validator | PASS |
| P8-6.4.2-G4 | Provider access is deny-by-default | PASS |
| P8-6.4.2-G5 | Failure behavior is bounded and non-escalating | PASS |
| P8-6.4.2-G6 | No tool execution or Agent orchestration is added | PASS |
| P8-6.4.2-G7 | Audit metadata is bounded and privacy-preserving | PASS |
| P8-6.4.2-G8 | Frozen contracts, assets and checkpoint remain unchanged | PASS |

## 9. Known Limitations

- No real provider planner call has been executed; the client boundary is
  currently exercised with deterministic injected doubles only.
- Provider quality, latency, cost and availability are not evaluated.
- The adapter does not orchestrate tool execution or synthesize an Agent
  answer.
- Durable audit storage remains unimplemented.
- `AgentService` orchestration was implemented later by P8-6.4.3 and received
  human review PASS; Phase 9 remains not started.
- M-023 remains `待实现`.

## 10. Final State

```text
P8-6.4.1: HUMAN REVIEW PASS
P8-6.4.2: HUMAN REVIEW PASS
AgentService orchestration: HUMAN REVIEW PASS
Tool execution by adapter: NOT IMPLEMENTED
Real provider planning request: NOT RUN
Agent implementation checkpoint: RELEASED
Phase 9: NOT STARTED
```

No commit, tag or push was performed by this slice. P8-6.4.3 was implemented
later and the reviewed Agent implementation was published under tag
`phase-8-controlled-agent-complete`.
