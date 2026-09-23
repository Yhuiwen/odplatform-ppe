# Phase 7 Risk Register

Date: 2026-09-23

Status values: `OPEN`, `MITIGATED`, `MONITORING`, `CLOSED`.

This report supplements `docs/08_RISK_REGISTER.md`; the central register is
authoritative.

| ID | Risk | Probability | Impact | Trigger / evidence | Mitigation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| RISK-020 | SQLite schema or migration drift makes event history unreadable | Medium | High | A deployed database cannot be upgraded from the recorded schema version, or repository code and schema disagree | Use versioned migrations, `schema_migrations`, foreign keys, a pre-migration backup, additive upgrades by default and a migration test before P7 release | OPEN |
| RISK-021 | Streamlit rerun/session behavior couples UI lifecycle to long-running inference | High | High | Browser rerun starts duplicate processing, loses stop state or blocks other users | Freeze a service-owned monitoring session with explicit state, one active source per session and idempotent stop; UI only renders query/session results | OPEN |
| RISK-022 | USB Camera or RTSP source stalls, disconnects or returns stale frames | High | High | Open/read timeout, frozen frame sequence, credential failure or stream EOF | Keep source lifecycle behind `VideoSource`; expose observable failure states, bounded reconnect policy and no fabricated frames; validate with a real source before final acceptance | OPEN |
| RISK-023 | Evidence snapshots consume unbounded disk or lose their database reference | Medium | High | Evidence root growth, missing file referenced by SQLite, orphan files after failed writes | Use date partitions, SHA256 metadata, file/database reconciliation, disk monitoring and a documented retention/archive policy; do not silently delete evidence | OPEN |
| RISK-024 | Web, Console or TTS delivery failure blocks or corrupts the event main path | Medium | High | Alert adapter timeout or exception prevents SQLite event persistence | Persist event and snapshot first; dispatch alerts through isolated adapters with bounded failures and idempotency by `event_id`; record alert failure without inventing success | OPEN |
| RISK-025 | Phase 6 event identity is lost or remapped inconsistently at the Phase 7 boundary | Medium | High | JSONL has no `event_id`; duplicate or mismatched history records appear | Persist the in-memory `event_id` at ingestion, freeze the mapping contract and use `event_id` as the database primary key and alert idempotency key | OPEN |
| RISK-026 | Dashboard statistics diverge from event history | Medium | Medium | Dashboard counts differ from SQLite queries or stale materialized statistics | Treat `events` as source of truth; make `statistics` rebuildable cache data with deterministic aggregation tests and visible refresh time | OPEN |

## Cross-Phase Dependencies

| Dependency | Current state | Required before |
| --- | --- | --- |
| Real detector/inference/ByteTrack runtime evidence | Historical `P5-3-G5 BLOCKED / NOT RUN` | Phase 7-5 final integrated validation |
| Real Camera or RTSP source | Not selected or validated | Phase 7-4/7-5 acceptance for M-008 |
| Annotated video output | Not implemented | Phase 7-4/7-5 acceptance for M-007 |
| Frozen checkpoint and runtime identity | Recorded | Any real integrated inference validation |
| Phase 6 JSONL event evidence | Implemented and offline-tested | SQLite ingestion and compatibility tests |

## Risk Result

All Phase 7 architecture risks are recorded. None is an architecture-freeze
blocker, but RISK-020 through RISK-026 must remain visible in the phase gates
and final release report.
