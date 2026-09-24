# Phase 8 P8-6.4 Architecture Freeze Report

Status: `P8-6.4 ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS`

Date: 2026-09-24

## 1. Repository Identity

- Branch: `main`
- HEAD and `origin/main`: `962ad45880fbc941582235f7177d0af5ad8fb9e1`
- Checkpoint tag: `phase-8-provider-pipeline-complete`
- Tag object: `447e93a5e92a3ede849dfcbd3e3706e79c525b4e`
- Checkpoint commit: `962ad45880fbc941582235f7177d0af5ad8fb9e1`
- Existing P8-6.1 through P8-6.3 work: uncommitted and preserved

## 2. Pre-Read Result

The governance documents, Phase 8 phase document, P8-6 architecture and
reports, Agent schemas/planner/registry/permissions/audit implementation, and
frozen P8-5 contracts were read before this design freeze.

The current review state was accepted as:

```text
P8-6.1: HUMAN REVIEW PASS
P8-6.2: HUMAN REVIEW PASS
P8-6.3: HUMAN REVIEW PASS
```

No governance conflict was found.

## 3. Scope

This freeze defines only:

- the optional LLM-assisted planner boundary;
- the untrusted candidate contract;
- deterministic candidate parsing and validation;
- final `AgentPlan` construction;
- `ToolRegistry` enforcement;
- permission verification;
- append-only audit integration;
- provider failure and invalid-output fallback;
- privacy and security constraints.

This freeze added no planner or provider integration code and issued no
provider request. Separately authorized P8-6.4.1 work subsequently implements
only strict candidate parsing, validation and deterministic `AgentPlan`
construction.

## 4. Frozen Architecture

```text
User request
-> deterministic precheck
-> optional LLM candidate
-> strict candidate parse
-> semantic and argument validation
-> deterministic AgentPlan construction
-> ToolRegistry resolution
-> deny-by-default permission preflight
-> append-only audit
-> final non-executable AgentPlan
```

Execution remains separate:

```text
final AgentPlan
-> ToolRegistry.execute
-> permission recheck
-> static read-only handler
```

The model cannot execute a tool and cannot bypass the registry.

## 5. Contract Decision

The final plan contract remains:

```text
phase8-agent-plan-v1
```

The new, future-only candidate contract is:

```text
phase8-agent-plan-candidate-v1
```

The candidate is untrusted and contains no free-form reasoning. Only bounded
intent, tool identity, arguments and a reason enum may be proposed. The final
`AgentPlan` is constructed only by deterministic project code.

## 6. Validation Decision

The validation order is fail-closed:

1. normalize and bound the request;
2. reject forbidden requests before any provider call;
3. optionally obtain one bounded provider candidate;
4. strictly parse the candidate without repair;
5. validate intent, tool, version, arguments and request binding;
6. preserve a supported deterministic intent or fall back to it;
7. construct the final `AgentPlan`;
8. resolve the tool through the static registry;
9. apply deny-by-default permission policy;
10. append the audit event before releasing a successful plan.

An invalid candidate cannot reach a handler.

## 7. Enforcement and Permissions

The static registry remains the sole execution point and rechecks permissions
and the closed argument allowlist. Dynamic registration, unknown tools,
descriptor changes and version mismatches fail closed.

Planning-provider access uses the existing `provider:invoke` capability and is
disabled by default. Candidate output cannot grant or alter capabilities.
Generated report calls through `generate_safety_report` retain their own
separate provider permission.

## 8. Audit Decision

The append-only contract remains `phase8-agent-audit-v1`. Accepted plans,
refusals, unknown tools, malformed candidates and provider failures use the
existing status vocabulary and bounded safe error codes.

No raw prompt, raw provider response, reasoning transcript, question text,
arguments, event data, credentials or filesystem/database path is retained.
Audit append failure remains fail closed.

## 9. Failure and Privacy Decision

Planner provider failure routes to the deterministic planner or a safe
refusal. It does not use or change the P8-5 report `TemplateFallback`.

The planner provider may receive only the bounded normalized question and
static allowlisted tool/argument schema metadata. It receives no events,
evidence, audit history, filesystem data, model data or credentials.

Provider output is untrusted. Unknown fields and prose are discarded; invalid
output is never repaired or partially accepted.

## 10. Frozen Compatibility

| Contract or asset | Result |
| --- | --- |
| `core/schemas/agent.py` deterministic final plan | UNCHANGED |
| `core/agent/tool_registry.py` static registry | UNCHANGED |
| `core/agent/permissions.py` deny-by-default policy | UNCHANGED |
| `core/agent/planner.py` deterministic planner | UNCHANGED |
| `phase8-agent-audit-v1` | UNCHANGED |
| `core/schemas/safety_report.py` | SHA256 MATCH |
| `services/safety_report_grounding_validator.py` | SHA256 MATCH |
| `infra/llm/fallback.py` | SHA256 MATCH |
| `models/checkpoints/EXP-001/best.pt` | SHA256 MATCH |
| `configs/training/exp001_baseline.yaml` | SHA256 MATCH |
| `configs/inference.yaml` | SHA256 MATCH |
| `data/processed/css-ppe-10-v1/data.yaml` | SHA256 MATCH |
| `phase-8-provider-pipeline-complete` | UNCHANGED |
| Charter protected body | UNCHANGED / EMPTY DIFF |

## 11. Validation

Design-only validation:

```text
python -m pytest -q
589 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host.

No provider request, model load, training, evaluation, dataset change or Phase
9 work was performed.

## 12. Gate Results

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-6.4-AF-G1 | LLM planner boundary and deterministic authority are frozen | PASS |
| P8-6.4-AF-G2 | Candidate and final `AgentPlan` contracts are separated | PASS |
| P8-6.4-AF-G3 | Plan parsing, validation and fallback order are frozen | PASS |
| P8-6.4-AF-G4 | Static `ToolRegistry` remains the only execution enforcement point | PASS |
| P8-6.4-AF-G5 | Deny-by-default permission and provider-access boundaries are frozen | PASS |
| P8-6.4-AF-G6 | Append-only audit integration preserves `phase8-agent-audit-v1` | PASS |
| P8-6.4-AF-G7 | Provider failure, invalid output and privacy boundaries are frozen | PASS |
| P8-6.4-AF-G8 | No implementation, provider request, dependency, frozen-contract or tag change is included | PASS |

## 13. Known Limitations

- The freeze itself is design only; full provider-assisted planning and
  AgentService orchestration are not implemented.
- The candidate contract and validation pipeline have unit evidence, but no
  real provider or Agent runtime evidence yet.
- Provider quality, latency, cost and long-term availability are not
  evaluated.
- The deterministic planner remains the only planner behavior available in
  the current repository.
- Durable audit storage remains unimplemented. AgentService orchestration was
  implemented later by P8-6.4.3 and received human review PASS.
- P8-6.4 has passed human review. P8-6.4.1 and P8-6.4.2 implementations
  passed human review; P8-6.4.3 was implemented later and also passed review.
- The locked Charter M-023 remains `待实现`.

## 14. Final State

```text
P8-6.1: HUMAN REVIEW PASS
P8-6.2: HUMAN REVIEW PASS
P8-6.3: HUMAN REVIEW PASS
P8-6.4: ARCHITECTURE FREEZE COMPLETE / HUMAN REVIEW PASS
P8-6.4.1: HUMAN REVIEW PASS
P8-6.4.2: HUMAN REVIEW PASS
AgentService orchestration: HUMAN REVIEW PASS
Agent implementation checkpoint: RELEASED
Phase 9: NOT STARTED
```

The freeze itself performed no code implementation, provider request, commit,
tag or push. P8-6.4.1 implementation followed under separate authorization;
it still performed no provider request, commit, tag or push. P8-6.4.2 then
implemented the provider-independent adapter boundary without a real provider
request, commit, tag or push. P8-6.4.3 was subsequently implemented and
reviewed; the later checkpoint release task published the reviewed Agent
implementation under tag `phase-8-controlled-agent-complete`.
