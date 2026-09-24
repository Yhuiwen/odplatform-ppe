# Phase 8 Final Integration Freeze Report

Status: `PHASE 8 FINAL INTEGRATION ARCHITECTURE: FROZEN / HUMAN REVIEW PASS`

Date: 2026-09-24

Repository path: `docs/reports/phase-08/PHASE_8_FINAL_INTEGRATION_FREEZE_REPORT.md`.

This report records the original design-only freeze. It does not itself
authorize a provider request, a model load, commit, tag or push. Subsequent
API, Web and E2E work passed human review and Phase 8 is now `FINAL RELEASED`
under `phase-8-final-integration-complete`.

## 1. Pre-Read Result

The required governance and Phase 8 records were read before editing:

- `AGENTS.md`;
- Charter, Master Plan, Current Status, Technical Decisions, Changelog, Test
  Gates, Risk Register, Open Source Usage and Reference Assets;
- `docs/phases/PHASE_08_LLM_AGENT.md`;
- `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`;
- `docs/designs/phase-08/PHASE_8_P8_6_AGENT_ARCHITECTURE.md`;
- `docs/designs/phase-08/PHASE_8_P8_6_4_AGENT_PLANNING_ARCHITECTURE.md`;
- `docs/reports/phase-08/PHASE_8_AGENT_CHECKPOINT_RELEASE_REPORT.md`;
- the current Agent schemas, registry, permissions, planner adapter, audit
  service, report service, tool service and Streamlit support/page modules.

No governance conflict was found. The work is limited to the two requested
Markdown documents.

## 2. Repository Identity

| Item | Value |
| --- | --- |
| Branch | `main` |
| HEAD | `56c0f49095c7b4ad39f273e0884652daad26a19f` |
| `origin/main` before task | `56c0f49095c7b4ad39f273e0884652daad26a19f` |
| Phase 8 Agent checkpoint tag | `phase-8-controlled-agent-complete` |
| Tag object | `ca46c884b29783892bdaa002e6a40efa491a34e5` |
| Tag target | `56c0f49095c7b4ad39f273e0884652daad26a19f` |
| Working tree before task | CLEAN |

## 3. Design Output

Created:

```text
docs/designs/phase-08/PHASE_8_FINAL_INTEGRATION_ARCHITECTURE.md
docs/reports/phase-08/PHASE_8_FINAL_INTEGRATION_FREEZE_REPORT.md
```

The architecture document freezes:

1. the typed in-process Agent application API boundary;
2. the trusted identity and UI-safe result projection;
3. the Streamlit import and session/rerun boundary;
4. the end-to-end user workflow;
5. a deterministic no-provider demo scenario;
6. API, web, integration and regression tests;
7. deployment and operational constraints;
8. the security review and hard invariants.

The design explicitly keeps planning, permissions, execution, report grounding
and audit inside the existing Agent service graph.

## 4. Frozen Contract Review

The design preserves:

| Contract or asset | Design requirement |
| --- | --- |
| `phase8-context-v1` | UNCHANGED |
| `phase8-report-v1` | UNCHANGED |
| `SafetyReportGroundingValidator` | UNCHANGED |
| `TemplateFallback` | UNCHANGED |
| `phase8-agent-request-v1` | UNCHANGED |
| `phase8-agent-result-v1` | UNCHANGED |
| `phase8-agent-plan-v1` | UNCHANGED |
| `phase8-agent-audit-v1` | UNCHANGED |
| Static four-tool `ToolRegistry` | UNCHANGED |
| Deny-by-default permissions | UNCHANGED |
| `phase-8-controlled-agent-complete` | UNCHANGED |
| Detection, tracking, association and compliance | UNCHANGED |
| Model, dataset and training assets | UNCHANGED |

Current recorded frozen asset hashes:

| Asset | SHA256 |
| --- | --- |
| `core/schemas/safety_report.py` | `4aee24b9841bd5a8dc48f82ad93b2feaf51f9336eacbcaca8dd1f4ab0a811d42` |
| `services/safety_report_grounding_validator.py` | `f014f2245cdf17178ae7c21f8cd6c2597a3810a8420600da3e7906825e8fd399` |
| `infra/llm/fallback.py` | `1fdba8a8562d9760f6ac695e84b485accd3df4908c9215368dda05bc555d20ac` |
| `models/checkpoints/EXP-001/best.pt` | `1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61` |
| `configs/training/exp001_baseline.yaml` | `df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989` |
| `configs/inference.yaml` | `0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c` |
| `data/processed/css-ppe-10-v1/data.yaml` | `45cc271729a71157e548004c2802b7d8ac3294a1c2fac0105129ca2498d2878a` |

The locked Charter body remains unchanged. Historical authorized M-004 and
M-005 status changes remain visible as expected; M-021, M-022 and M-023 remain
`待实现`.

## 5. Interface Freeze Decisions

### 5.1 Agent API

The future `AgentApplicationService`:

- accepts an application request without caller-selected tool, role,
  capability, principal, provider or audit identities;
- obtains identity only from `TrustedIdentityProvider`;
- constructs the existing `AgentRequest`;
- calls `AgentService.execute()` once;
- projects `AgentResult` into a bounded UI-safe view.

It does not plan, authorize, dispatch or generate reports itself.

### 5.2 Web

The future Streamlit pages:

- call `web/agent_support.py` only;
- use the existing service graph;
- execute only on explicit user action;
- render structured, grounded fields;
- display report path, degradation, grounding and audit ID;
- never query SQLite, call a provider, invoke a tool handler or import Agent
  internals directly.

The existing AI pages remain placeholders in this task.

### 5.3 End-to-End Flow

```text
UI request
-> trusted identity
-> AgentApplicationService
-> AgentRequest
-> LLMPlannerAdapter with deterministic fallback
-> validated phase8-agent-plan-v1
-> ToolRegistry
-> existing read-only service
-> append-only audit
-> AgentResult
-> UI-safe projection
```

There is no alternate path around `ToolRegistry`.

## 6. Demo and Test Freeze

The standard demo uses a persisted event fixture, a fixed UTC period,
provider-disabled report generation, summary/statistics/detail questions and a
forbidden mutation request. It must show `TEMPLATE_FALLBACK` accurately and
must not require a real provider, model, dataset download or Phase 9 work.

The future integration suite must cover:

- trusted identity and privilege separation;
- all four read-only intents through the registry;
- unknown and forbidden request refusal;
- provider-disabled fallback and provider-failure fallback;
- invalid provider output rejection;
- audit append and fail-closed behavior;
- deterministic API projection and serialization;
- web import isolation and Streamlit rerun behavior;
- event, evidence and audit identity preservation;
- zero model/provider/network calls in the standard suite.

## 7. Security Review Result

The freeze explicitly covers:

- prompt injection through user text;
- forged role or capability claims;
- tool and dynamic-tool selection by a caller or provider;
- arbitrary SQL, filesystem access and shell execution;
- event mutation, evidence deletion, alert action and compliance override;
- provider output leakage, raw response retention and secret exposure;
- absolute path and evidence-byte leakage;
- Streamlit rerun duplication;
- process-local audit and fail-closed success release.

No design gap blocking the freeze was found. Production authentication and
durable audit storage remain explicitly deferred.

## 8. Freeze Gates

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-FI-AF-G1 | Agent API boundary and trusted identity are frozen | PASS |
| P8-FI-AF-G2 | UI-safe projection and all Agent outcomes are mapped | PASS |
| P8-FI-AF-G3 | Web pages are restricted to the service facade | PASS |
| P8-FI-AF-G4 | End-to-end flow preserves the existing Agent execution path | PASS |
| P8-FI-AF-G5 | Demo is deterministic and provider-independent by default | PASS |
| P8-FI-AF-G6 | API, web, integration and regression tests are defined | PASS |
| P8-FI-AF-G7 | Deployment, configuration and failure isolation are defined | PASS |
| P8-FI-AF-G8 | Security review and hard invariants are frozen | PASS |
| P8-FI-AF-G9 | Frozen P8-5/P8-6 contracts and four-tool registry are preserved | PASS |
| P8-FI-AF-G10 | No implementation, provider request, model load or Phase 9 work is included | PASS |

## 9. Validation

Design-task validation is recorded at completion:

```text
python -m pytest -q
632 passed, 1 skipped

python -m compileall -q .
PASS

git diff --check
PASS
```

The skip is the existing optional Torch evaluation test because Torch is not
installed on this host. The standard suite makes no real provider request.

## 10. Known Limitations

- This document records the original architecture freeze; implementation and
  deterministic E2E validation were subsequently completed and reviewed.
- The Agent audit store is process/session-local.
- Production authentication is not implemented by this design.
- A remote Agent API is not part of V1 scope.
- Phase 8 final integration has since been accepted; Phase 9 delivery remains
  not started.
- M-021, M-022 and M-023 remain `待实现` in the locked Charter.

## 11. Final State

```text
Phase 8 Agent checkpoint:
RELEASED

Phase 8 final integration architecture:
FROZEN / HUMAN REVIEW PASS

Agent API boundary:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

Web integration boundary:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

Deterministic E2E demo:
IMPLEMENTATION COMPLETE / HUMAN REVIEW PASS

Phase 8:
FINAL RELEASED

Release tag:
phase-8-final-integration-complete

Commit:
NOT CREATED BY THE FREEZE TASK

Tag:
NOT CREATED BY THE FREEZE TASK

Push:
NOT PERFORMED BY THE FREEZE TASK

Phase 9:
NOT STARTED
```

Next allowed step: human review of the deterministic E2E demo and its evidence.
The API, Web and E2E boundaries have passed human review, and Phase 8 final
integration is released. Durable audit storage, memory, autonomous loops, real
provider planning calls and Phase 9 remain outside this freeze.
