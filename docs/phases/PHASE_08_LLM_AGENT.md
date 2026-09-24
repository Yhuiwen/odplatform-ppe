# Phase 08 — LLM & Agent

## 1. 阶段目标

【LOCKED】LLM Report + Fallback + Basic Agent。

## 2. 进入条件

- Phase 7 Gate 全部 PASS。
- 平台统计查询和事件数据接口稳定。

## 3. 当前子任务

Phase 8-0 Architecture and Contract Freeze 已完成设计并通过人工审核，
`P8-0 DESIGN COMPLETE / HUMAN REVIEW PASS`。P8-1 Deterministic Safety
Analytics and Context 已实现并通过人工审核，状态为
`HUMAN REVIEW PASS`。P8-2 Structured Report Contract and Grounding Validator
已实现并通过人工审核，状态为 `HUMAN REVIEW PASS`。P8-3 Deterministic
Template Fallback 已实现并通过人工审核，状态为 `HUMAN REVIEW PASS`。P8-4
Provider Adapter Boundary and Untrusted Output Parsing 已实现并通过人工审核，
状态为 `HUMAN REVIEW PASS`。P8-5 Real Provider E2E, Grounding Enforcement and
Safe Fallback 已实现并通过人工审核，当前状态为
`COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`。P8-5D Sanitized Provider Schema
Diagnostics 当前状态为 `HUMAN REVIEW PASS`。P8-5P Provider Prompt Schema
Conformance Fix 当前状态为 `HUMAN REVIEW PASS`。
本次授权将 P8-5 重定为 provider E2E，并以 P8-5D 增强失败诊断；P8-5P 仅将
provider prompt 提升为从权威 dataclass/enum 生成的 exact schema
description；Basic Agent 仍未被授权。
冻结与实现路径为：

```text
Event Store
-> SafetyAnalyticsService
-> SafetyContextBuilder
-> SafetyLLMClient
-> StructuredSafetyReport
```

Basic Agent 使用同一只读事实源，只能调用受控工具。单个 OpenAI-compatible
provider transport 与 provider-first fallback orchestration 已实现。人工已
执行一次真实 `deepseek-flash` 请求；provider response 与 message content
已收到，strict JSON syntax 已通过，但该历史请求的 `phase8-report-v1`
构造以 `REPORT_SCHEMA_INVALID` 失败，provider grounding 未到达。该失败及
其后的 `TemplateFallback` grounding PASS 继续作为历史证据保留。P8-5D 为
该失败类别增加有界 sanitized diagnostics，P8-5P 将 provider prompt 升级为
从权威 dataclass/enum 生成的 exact schema description。随后另行授权的人工
真实请求遵循 prompt v2，transport、strict JSON、`phase8-report-v1` 和
provider grounding 全部通过，返回 `PROVIDER_VALIDATED`，且
`generation_path=PROVIDER`、`degraded=false`、fallback 未使用。Agent 业务
代码未开始；M-021、M-022、M-023 仍为 `待实现`。

冻结文档：

- `docs/designs/phase-08/PHASE_8_AGENT_ARCHITECTURE.md`
- `docs/reports/phase-08/PHASE_8_P8_0_ARCHITECTURE_FREEZE_REPORT.md`
- `docs/03_TECHNICAL_DECISIONS.md` ADR-023

子阶段规划：

| Subphase | Scope | Status |
| --- | --- | --- |
| P8-0 | Architecture and contract freeze | DESIGN COMPLETE / HUMAN REVIEW PASS |
| P8-1 | Deterministic analytics and versioned context schema | HUMAN REVIEW PASS |
| P8-2 | Structured report contract and grounding validator | HUMAN REVIEW PASS |
| P8-3 | Deterministic local template fallback | HUMAN REVIEW PASS |
| P8-4 | Provider-independent adapter and strict untrusted output parsing | HUMAN REVIEW PASS |
| P8-5 | Real provider E2E, grounding enforcement and safe fallback | COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED |
| P8-5D | Sanitized provider schema diagnostics | HUMAN REVIEW PASS |
| P8-5P | Provider prompt schema conformance fix | HUMAN REVIEW PASS |
| P8-6 | Integration tests, evaluation and Phase 8 release review | READY / NOT STARTED |

Basic Agent remains `NOT AUTHORIZED` and requires a separately assigned
subphase/authorization. The P8-5 row records the authorized provider E2E scope,
not Basic Agent completion.

## 4. 实现设计

Phase 8 严格位于确定性 PPE 系统下游：

```text
Video
-> Detection
-> Tracking
-> PPE Association
-> Compliance Engine
-> Event Store
-> Safety Analytics / Agent
```

Agent 不得检查原始图像来独立判断 PPE、覆盖 detection/tracking/association、
创建或修改权威事件、重训模型或修改 dataset/mapping。Phase 8 的数据读取必须
经过 `EventQueryService`，不得从分析层直接执行 SQL。

`SafetyAnalyticsService` 只做确定性计算，无 LLM 依赖。它通过
`EventQueryService.query_events()` 分页读取详细事件，并通过同一服务的
`statistics()` 获取权威 source 聚合；分析层不直接执行 SQL。`track_id` 是
tracker 作用域标识，不是稳定人员身份；当前 schema 没有违规持续时长和告警
投递遥测，因此这些指标必须记录为 `UNAVAILABLE`，不能推断。

`SafetyAnalysisContext` 版本为 `phase8-context-v1`，明确分离：

```text
observed_facts
calculated_metrics
metadata
unavailable_fields
```

P8-1 已实现 exact totals、type/status/track/day 分布、first/last occurrence、
evidence availability、opaque `SRC-<16 hex>` source grouping 和 deterministic
ordering。Reporting interval 冻结为 inclusive `[start_at, end_at]`；详细事件
顺序为 `timestamp DESC, event_id ASC`。Canonical JSON 使用 UTF-8、sorted
keys、无多余空白和 finite numeric values。

`SafetyContextBuilder.fingerprint(context)` 对 canonical context 计算 SHA256，
仅排除 `metadata.generated_at`。该值作为方法返回，不向冻结 schema 增加
`context_sha256` 字段；如需字段化必须另行审核和 amendment。

`SafetyLLMClient` 使用 provider-independent protocol，概念接口为：

```text
generate_report(context) -> StructuredSafetyReport
```

领域服务不得绑定 OpenAI、DeepSeek、Ollama 或其他 provider。Provider
实现推迟到后续授权子阶段。

`StructuredSafetyReport` 版本为 `phase8-report-v1`，至少包含
`schema_version`、`reporting_period`、`generation`、
`executive_summary`、`key_findings`、`risk_observations`、
`recommendations`、`evidence_references`、`limitations` 和
`grounding_status`。事实、风险观察和建议必须分离。

每个事实性声明必须引用 context 中存在的事实或指标；event ID、track ID、
数值、snapshot 引用和建议依据均需校验。LLM 输出中的伪造 ID、未知引用或不
一致数字必须被拒绝。模板降级遵循相同接地规则，并明确标记
`TEMPLATE_FALLBACK` 和 `degraded=true`。

Provider unavailable、timeout、rate limit、malformed output、schema failure、
空事件集、证据缺失、部分数据库数据和 fallback failure 使用结构化错误码。
外部模型失败不得影响监控主链路；fallback 失败时返回
`REPORT_UNAVAILABLE`，不得伪造报告。

外部 provider 默认禁止接收原始图片/证据字节、绝对路径、数据库文件、带凭据
RTSP URL、人员身份、worker 展示名、日志、环境值或 secrets。API key 只能来自
环境变量或外部 secret manager，不得进入 Git、日志或报告。

P8-2 已实现 `phase8-report-v1` schema 与 `SafetyReportGroundingValidator`。
报告通过 `source_context_sha256` 绑定 P8-1 method-level context fingerprint；
validator 对 fact、metric、event、tracker-scoped track、source、evidence 和
结构化数值引用逐一核对。未知引用、数值不一致、无依据 finding/risk、无效建议
依据、unavailable-field contradiction、绝对路径/数据库路径/credential-like
泄漏均 fail closed，不修复或删除坏 claim。canonical report serialization 对
同一逻辑报告保持稳定。P8-2 不实现 provider adapter 或 fallback。

P8-3 已实现 `TemplateFallback` 与最小 `ReportService` orchestration。
fallback 只接受 `phase8-context-v1`，复用
`SafetyContextBuilder.fingerprint(context)`，输出
`phase8-report-v1`，固定标记 `TEMPLATE_FALLBACK` / `degraded=true`，并且
只引用 context 中已有的 facts、metrics、track IDs 和 available evidence。
所有 unavailable fields 必须按原 field/reason_code 原样写入 limitations。
缺 metric、数值不一致、track/evidence/metric 不匹配时确定性 fail closed。
`ReportService` 使用未修改的 P8-2 validator 校验 fallback 输出，只有通过后
才返回 `grounding_status=VALID`。

P8-4 已实现 provider-independent adapter boundary，不实现真实 provider、
网络 transport 或 provider SDK。`ProviderRequestBuilder` 只发送安全
`phase8-context-v1` payload，移除 `metadata.generated_at`，绑定
`SafetyContextBuilder.fingerprint(context)`，使用固定
`phase8-provider-request-v1` / `phase8-provider-prompt-v1` /
`phase8-report-v1` 版本，要求有限 timeout，并冻结
`262144` bytes response limit。`ProviderTransport` 通过依赖注入隔离 transport；
`SafetyLLMClient` 只返回 strict parse 后的 `unvalidated` candidate。

`ProviderResponseParser` 将 provider bytes 作为不可信输入：先执行大小检查，
再要求 UTF-8、无 BOM、严格 JSON、无重复 key、无 `NaN`/`Infinity`、无未知字段，
并逐层构造既有 `phase8-report-v1` schema。fingerprint mismatch、错误
generation mode/status、malformed nested claim 和 schema 错误均 fail closed。
`ReportService.generate_provider_report()` 将 candidate 交给未修改的 P8-2
validator，返回 candidate + validation wrapper；P8-4 不静默 fallback，也不将
provider 自报的 `valid` 视为 grounding 通过。

P8-5 在未改变的 `ProviderTransport` 边界后增加唯一一个
OpenAI-compatible chat-completions transport。配置只保存环境变量名：
`PPE_LLM_ENDPOINT`、`PPE_LLM_MODEL`、`PPE_LLM_API_KEY`；credential 只从
环境读取，不进入 YAML、请求、日志或报告。transport 使用标准库 HTTP、
有限 timeout、单次尝试、无 retry，并继续遵守 `262144` bytes response
limit。

`ReportService.generate_provider_or_fallback()` 实现 provider-first：
provider candidate 必须先通过未改变的 strict parser 和 P8-2 grounding
validator，才能以 `PROVIDER` / `degraded=false` 返回。malformed、schema
invalid、fingerprint mismatch、伪造 event/track、数值矛盾、path leak 以及
timeout/auth/rate-limit/HTTP/unavailable/empty/oversized 等失败均确定性转入
未改变的 `TemplateFallback`。fallback 仍为
`TEMPLATE_FALLBACK` / `degraded=true` 并通过同一个 validator；fallback
失败返回 `REPORT_UNAVAILABLE`，不暴露无效报告。

Basic Agent 只允许调用受控只读工具，例如 `query_events`、
`get_event_statistics`、`get_event`、`list_sources`、
`get_evidence_metadata` 和 `analyze_period`。禁止任意 SQL、shell、文件系统、
网络副作用和外部动作；超出范围或无证据时返回明确拒绝或数据不足。

P8-5D 仅为 `REPORT_SCHEMA_INVALID` 增加有界、确定性的 sanitized
diagnostics。每条诊断只包含 safe JSON path、项目自有错误类别、expected
type/constraint 和 actual JSON type；最多 20 条并提供 `truncated` 标记。
provider raw value、未知字段名、raw response、prompt、context payload、
authorization header 或 API key 不进入诊断。public failure code 仍为
`REPORT_SCHEMA_INVALID`，不修复、不部分接受无效报告，也不修改
`phase8-report-v1`、`SafetyReportGroundingValidator` 或
`TemplateFallback` 行为。

P8-5P 将 provider request 中的 loose prose 替换为从
`core/schemas/safety_report.py` 权威 dataclass/enum 派生的 compact schema
description。`PROVIDER_PROMPT_VERSION` 更新为
`phase8-provider-prompt-v2`，提示中明确全部 top-level 与 nested required
字段、exact enum、nullable-but-required、closed-object、empty-array 和
provider candidate constants。它不新增第二份手写报告 schema，不修改
parser、grounding、fallback、context 或 fingerprint；prompt 合规也不是
security boundary。P8-5P 本身未执行真实 provider 请求，因此没有在自身范围
内证明 `PROVIDER_VALIDATED`；随后另行授权的人工请求遵循 prompt v2 并完成
了真实 provider validation PASS。

P8-0 不引入 LangChain、LlamaIndex 或新的 Agent framework，也不安装或调用
provider SDK。

## 5. 测试要求

- 报告数据范围、来源和降级状态测试。
- LLM 超时、异常、未配置时的 fallback 测试。
- Agent 查询、分析、越权拒绝和无法验证回答测试。
- 确定性 analytics 计数、排序、空数据集和 unavailable fields 测试。
- context canonical serialization 与重复构建测试。
- hallucinated event/track ID、未知数值和无效引用拒绝测试。
- provider/fallback failure isolation 与 deterministic mock LLM 测试。

## 6. Gate

| Gate | Requirement |
| --- | --- |
| P8-G1 | LLM 报告不编造平台数据且结论可追溯 |
| P8-G2 | LLM 不可用时自动生成本地模板报告 |
| P8-G3 | Agent 可受控查询和分析内部数据 |

P8-0 design gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-0-G1 | Authoritative Phase 8 scope and repository status are audited | PASS |
| P8-0-G2 | Downstream read-only trust boundary is frozen | PASS |
| P8-0-G3 | Deterministic analytics and versioned context contracts are defined | PASS |
| P8-0-G4 | Provider-independent report and fallback contracts are defined | PASS |
| P8-0-G5 | Grounding and evidence-reference policy is defined | PASS |
| P8-0-G6 | Failure, privacy, secret and Basic Agent tool boundaries are defined | PASS |
| P8-0-G7 | Future deterministic and mock-based evaluation strategy is defined | PASS |
| P8-0-G8 | No implementation, external call, dependency, frozen-asset change, commit, tag or push is included | PASS |

P8-1 implementation gates:

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

P8-2 implementation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-2-G1 | `phase8-report-v1` structured schema implemented without provider dependency | PASS |
| P8-2-G2 | Report is cryptographically bound to the supplied deterministic P8-1 context fingerprint | PASS |
| P8-2-G3 | Fact, metric, event, track and evidence references are validated against authoritative context | PASS |
| P8-2-G4 | Numeric structured claims cannot contradict deterministic analytics | PASS |
| P8-2-G5 | Ungrounded or fabricated factual content fails closed | PASS |
| P8-2-G6 | Unavailable fields and privacy boundaries cannot be bypassed through structured report fields | PASS |
| P8-2-G7 | Canonicalization and validation behavior are reproducible | PASS |
| P8-2-G8 | Full repository regression, frozen-asset, governance and no-provider checks pass | PASS |

P8-3 implementation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-3-G1 | `TemplateFallback` is typed, deterministic and provider-independent | PASS |
| P8-3-G2 | Output is `phase8-report-v1` bound to the supplied context fingerprint | PASS |
| P8-3-G3 | Claims use only context facts, metrics, tracks and available evidence | PASS |
| P8-3-G4 | Unavailable fields and recommended actions preserve frozen boundaries | PASS |
| P8-3-G5 | Empty, tied and malformed-metric cases are deterministic and fail closed | PASS |
| P8-3-G6 | `ReportService` validates fallback output and marks it `VALID` only after PASS | PASS |
| P8-3-G7 | No provider, network, model, dataset or upstream pipeline dependency is introduced | PASS |
| P8-3-G8 | Full regression and frozen-asset checks pass | PASS |

P8-4 implementation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-4-G1 | Provider-independent `SafetyLLMClient` and injectable transport boundary implemented | PASS |
| P8-4-G2 | Provider request construction is deterministic, safe and bound to the P8-1 context fingerprint | PASS |
| P8-4-G3 | Provider response is treated as untrusted and requires strict `phase8-report-v1` parsing | PASS |
| P8-4-G4 | All accepted provider candidates pass the unchanged P8-2 grounding validator | PASS |
| P8-4-G5 | Malformed, oversized, invalid, fabricated or contradictory output fails closed | PASS |
| P8-4-G6 | Timeout/auth/rate-limit/provider failures use deterministic safe errors without secret leakage | PASS |
| P8-4-G7 | Mock transport and focused tests perform zero real network/provider access | PASS |
| P8-4-G8 | Full regression, frozen contracts/assets, governance and Phase 7 tag checks pass | PASS |

P8-5 implementation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-5-G1 | Exactly one real provider transport is implemented behind the frozen P8-4 abstraction | PASS |
| P8-5-G2 | Provider candidates escape only after strict parsing and unchanged P8-2 grounding validation | PASS |
| P8-5-G3 | Semantic provider failures deterministically route to `TemplateFallback` | PASS |
| P8-5-G4 | Operational provider failures deterministically route to `TemplateFallback` | PASS |
| P8-5-G5 | Fallback output passes the unchanged validator and retains degraded identity | PASS |
| P8-5-G6 | Fallback failure terminates as `REPORT_UNAVAILABLE` without exposing an invalid report | PASS |
| P8-5-G7 | Real provider evidence is recorded accurately and separately from fallback; secrets are not persisted | PASS / REAL PROVIDER VALIDATED |
| P8-5-G8 | Full regression, frozen contracts/assets, governance and Phase 7 tag checks pass | PASS / final validation audit `539 passed, 1 skipped` |

P8-5D implementation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-5D-G1 | Bounded diagnostic model exposes only safe paths, project categories and JSON type information | PASS |
| P8-5D-G2 | Schema failures map to bounded project-owned diagnostic categories | PASS |
| P8-5D-G3 | `REPORT_SCHEMA_INVALID` remains the public failure code and invalid output is never repaired or partially accepted | PASS |
| P8-5D-G4 | Diagnostics are deterministic, capped at 20 and report `truncated=true` when more failures exist | PASS |
| P8-5D-G5 | Raw values, unknown field names, raw responses, prompts, context payloads and credentials are excluded | PASS |
| P8-5D-G6 | Service and CLI propagate sanitized diagnostics while provider failure still routes to unchanged fallback | PASS |
| P8-5D-G7 | `phase8-report-v1`, GroundingValidator and TemplateFallback behavior remain unchanged | PASS |
| P8-5D-G8 | Full regression, frozen assets, locked governance and zero real-network checks pass | PASS |

P8-5P implementation gates:

| Gate | Requirement | Status |
| --- | --- | --- |
| P8-5P-G1 | Prompt schema is derived from the authoritative report implementation | PASS |
| P8-5P-G2 | Every top-level and nested required field is represented | PASS |
| P8-5P-G3 | Nullable, enum, closed-object and empty-array semantics are explicit | PASS |
| P8-5P-G4 | Provider candidate constants and fingerprint binding are clear | PASS |
| P8-5P-G5 | Prompt behavior remains deterministic and strictly fails closed | PASS |
| P8-5P-G6 | Frozen report, parser, grounding and fallback behavior remain unchanged | PASS |
| P8-5P-G7 | Focused and full tests pass without a real provider request | PASS |
| P8-5P-G8 | Frozen assets, governance and Phase 7 tags remain unchanged | PASS |

## 7. 已知问题

实际 provider vendor、endpoint、model、credential、API 成本、context-size
限制、报告保留、Agent planning strategy、隐私和网络稳定性待后续子阶段评估。
P8-5R 的真实 provider 请求已执行并收到响应，但当时 `phase8-report-v1`
构造因 `REPORT_SCHEMA_INVALID` 被拒，provider grounding 未到达；该历史
fallback grounding PASS 不表述为 provider validation PASS。P8-5D 使该
失败类别具备有界、可审计的 sanitized diagnostics，P8-5P 使后续 provider
prompt 显式表达完整 frozen schema。随后另行授权的人工请求遵循 prompt v2，
transport、strict JSON、`phase8-report-v1` 和 grounding 全部通过，返回
`PROVIDER_VALIDATED`。原始 provider response 未持久化，因此验证依据是人工
提供的 sanitized result 与实现路径审计，不包含 packet-level transcript。
当前历史 schema 无法提供稳定人员身份、违规持续时长或告警投递统计，P8 不得
自行推断。该成功验证覆盖本次授权 smoke request，不代表所有未来 provider
响应、成本、延迟、rate-limit 或长期稳定性均已验证。

## 8. 开发记录

- 2026-09-24: Published the authorized P8-0 through P8-5 interim release
  checkpoint under annotated tag `phase-8-provider-pipeline-complete`. This
  is `P8-0 THROUGH P8-5 COMPLETE / HUMAN REVIEW PASS / CHECKPOINTED`, not the
  final Phase 8 release. P8-6 is `READY / NOT STARTED`; Basic Agent and Phase
  9 are not started. The release task issued no provider request, did not use
  `--execute`, preserved the historical schema-rejection evidence and left
  M-021, M-022 and M-023 as `待实现`.
- 2026-09-24: Completed the P8-5 final real provider validation audit. The
  separately authorized manual request followed prompt v2 and returned
  `PROVIDER_VALIDATED`: transport PASS, strict JSON PASS,
  `phase8-report-v1` PASS, provider grounding VALID, `PROVIDER`,
  `degraded=false`, no safe error, no schema diagnostics and fallback not
  used. The audit verified the implementation path, issued no provider
  request, did not use `--execute`, did not inspect or print the API-key value
  and retained no raw provider response or authorization header. The earlier
  schema-rejection evidence remains historically preserved. Full regression
  passed (`539 passed, 1 skipped`); frozen assets, the current Charter diff and
  Phase 7 tags were verified. The validation audit itself performed no
  commit, tag or push; checkpoint publication is recorded separately above.
- 2026-09-24: Completed P8-5P provider prompt schema conformance fix. Added
  a compact schema description generated from the authoritative report
  dataclasses/enums, embedded it in the provider system message, and upgraded
  the prompt version to `phase8-provider-prompt-v2`. The prompt now states all
  required nested fields, enum values, nullable-required fields,
  closed-object policy, empty-array behavior and provider success constants.
  No report schema, parser, grounding validator, fallback behavior, context
  contract or fingerprint algorithm changed. Focused tests passed (`80
  passed`) and the full repository gate passed (`539 passed, 1 skipped`); no
  real provider request, `--execute`, commit, tag or push was performed.
  P8-5P subsequently received `HUMAN REVIEW PASS`.
- 2026-09-24: Completed P8-5D sanitized provider schema diagnostics. The
  strict parser now returns `REPORT_SCHEMA_INVALID` with at most 20
  deterministic, sanitized path/category/type diagnostics and a truncation
  flag. No raw value, unknown field name, raw response, prompt, context body,
  credential or authorization header is exposed. Service/CLI propagation is
  metadata-only, fallback behavior is unchanged, and no real provider request
  or `--execute` was used. P8-5D subsequently received `HUMAN REVIEW PASS`.
- 2026-09-24: P8-5R real provider post-execution audit completed. The human
  operator executed one OpenAI-compatible request against
  `https://api.deepseek.com/chat/completions` with model `deepseek-flash`.
  The provider response envelope and message content were received, and strict
  JSON parsing succeeded. `phase8-report-v1` construction failed with
  `REPORT_SCHEMA_INVALID`, so provider grounding was not reached. The unchanged
  `TemplateFallback` passed grounding and remained degraded; that historical
  result is not `PROVIDER_VALIDATED`. This audit issued no additional provider
  request. At that historical point P8-5 was `IMPLEMENTATION COMPLETE / REAL
  PROVIDER EXECUTED / PROVIDER REPORT SCHEMA REJECTED / TEMPLATE FALLBACK PASS
  / HUMAN REVIEW PENDING`.
- 2026-09-24: Completed P8-5 real-provider E2E wiring and safe fallback.
  Added one configuration-driven OpenAI-compatible transport, environment-only
  credential resolution, bounded single-attempt HTTP, provider-first
  orchestration, strict grounding enforcement, deterministic fallback and
  `REPORT_UNAVAILABLE`. Added transport/E2E tests and an explicitly gated
  smoke CLI. Existing P8-1 through P8-4 contracts were not weakened. At the
  implementation point, no endpoint/model/credential was configured and the
  smoke was not executed. The later human execution is recorded above; Basic
  Agent remains unauthorized.
- 2026-09-24: Completed P8-4 provider adapter boundary and untrusted output
  parsing. Added the provider-independent request/transport/error contracts,
  deterministic request builder, strict bounded JSON parser,
  `SafetyLLMClient`, and candidate-plus-validation orchestration. Added
  focused zero-network tests and synchronized Phase 8 status. No real
  provider, network call, SDK, API key, model, dataset or upstream pipeline
  was changed. P8-4 subsequently passed human review.
- 2026-09-24: Completed P8-3 deterministic template fallback. Replaced the
  fallback/report-service placeholders with typed implementations over
  `phase8-context-v1`, added focused deterministic/grounding/fail-closed tests,
  and synchronized Phase 8 status. No provider, network call, real LLM,
  Basic Agent, model, dataset or upstream pipeline was changed. P8-3 is
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`.
- 2026-09-24: Completed P8-2 structured report contract and grounding
  validator. Added `core/schemas/safety_report.py`,
  `services/safety_report_grounding_validator.py` and focused tests. Added
  context fingerprint binding, strict reference and numeric validation,
  limitation consistency, deterministic validation ordering, canonical report
  serialization and privacy/path checks. No provider, network, LLM, fallback,
  Agent or upstream pipeline implementation was added. P8-2 is
  `IMPLEMENTATION COMPLETE / HUMAN REVIEW PENDING`.
- 2026-09-24: Completed and hardened P8-1 deterministic analytics/context
  implementation. Added `core/schemas/safety.py`,
  `services/safety_analytics_service.py`,
  `services/safety_context_builder.py` and focused tests. P8-1 is
  `HUMAN REVIEW PASS`; no provider, network call,
  report service, Agent tool or upstream phase implementation was changed.
- 2026-09-24: Completed P8-0 architecture and contract freeze design. Added
  ADR-023 and the Phase 8 architecture/freeze reports. No provider, API,
  dependency, model, dataset, training or upstream Phase 0 through Phase 7
  implementation was changed. P8-0 subsequently passed human review. M-021
  through M-023 remain `待实现`.
- 2026-09-21: 计划建立，未开始实现。
