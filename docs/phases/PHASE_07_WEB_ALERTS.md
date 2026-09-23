# Phase 07 — Web & Alerts

## 1. 阶段目标

【LOCKED】SQLite + Snapshot + TTS + Streamlit。

## 2. 进入条件

- Phase 6 Gate 全部 PASS。
- 事件对象和截图触发点已稳定定义。

## 3. 当前子任务

未开始。计划实现持久化、截图留证、TTS、实时监控、历史查询和数据大屏。


### Deferred MUST delivery ownership (ADR-019)

Phase 7 owns M-007 annotated video rendering through video page/service
integration and M-008 live-input integration for real-time monitoring.
These are deferred MUST implementations from Phase 4, not Extensions.
Deliver and verify them before accepting the corresponding page integrations;
retain the Charter's Camera OR RTSP criterion and observable failure behavior.
Phase 9 performs final full-Charter acceptance. This allocation does not change
this phase's locked goal or current not-started status.

## 4. 实现设计

Repository 隔离数据库访问；事件与截图文件保持一致引用；TTS 失败不阻塞
事件写入；Streamlit 页面只调用服务层，不内嵌业务算法。

## 5. 测试要求

- SQLite 创建、写入、读取、重启持久化和查询过滤测试。
- 截图路径与事件记录一致性测试。
- TTS 成功/失败隔离测试。
- 页面服务交互、空状态、断流和停止行为测试。

## 6. Gate

| Gate | Requirement |
| --- | --- |
| P7-G1 | SQLite 事件持久化与历史查询通过 |
| P7-G2 | 截图留证可追踪且文件真实存在 |
| P7-G3 | TTS 实时告警有冷却且失败不破坏主流程 |
| P7-G4 | 实时监控、历史查询和数据大屏满足验收 |

## 7. 已知问题

并发写入、证据清理和长期运行稳定性尚待设计验证。

## 8. 开发记录

- 2026-09-21: 计划建立，未开始实现。
