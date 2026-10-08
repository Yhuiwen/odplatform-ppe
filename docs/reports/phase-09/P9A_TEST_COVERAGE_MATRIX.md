# P9-A Test Coverage Matrix

Date: 2026-09-25. Inventory: 76 `test_*.py` files; 38 under `tests/unit`,
5 under `tests/integration`, none under `tests/e2e` or `tests/regression`.
The rest are top-level test files. `tests/fixtures` contains 17 files.

| Stage | Evidence | Coverage judgment |
| --- | --- | --- |
| Input | MP4 and USB actual runtime; local RTSP open/read/close | REAL RUNTIME, short only |
| Detection | real image and MP4 frozen YOLO run | REAL RUNTIME, short only |
| Tracking | person-only ByteTrack in P7-5 MP4 | REAL RUNTIME, complex scenes missing |
| Association | P7-5 MP4 plus unit tests | REAL RUNTIME, ambiguity scenes missing |
| Compliance | unit tests and one P7-5 unknown event | UNIT / SHORT SMOKE |
| Temporal Event | unit tests, one integrated event | UNIT / SHORT SMOKE |
| SQLite | integration restart and idempotency tests; P7-5 | INTEGRATION / REAL RUNTIME |
| Snapshot | atomic storage tests and P7-5 file | INTEGRATION / REAL RUNTIME |
| Alert | Console/Web actual path, native TTS call | SHORT SMOKE; delivery duration missing |
| Dashboard | real SQLite queries and browser page validation | REAL RUNTIME, small data |
| Analytics | deterministic tests over persisted events | UNIT / INTEGRATION |
| Report | grounded fallback and provider validation separately | UNIT / INTEGRATION; no upstream full E2E |
| Agent | fixture-driven Web/API/registry/audit/UI path | E2E of Agent slice only |

P8-FI's E2E fixture covers `AgentWebAdapter -> AgentApplicationService ->
AgentService -> ToolRegistry -> AgentAuditService -> AgentUiProjection`. It
does not exercise camera/MP4, YOLO, ByteTrack or the full PPE platform.

P9-B must use a real MP4 to generate persisted events, then query the same
database through Dashboard, Analytics, Report and Agent; record event IDs and
timestamps across boundaries. USB and remote RTSP are separate acceptance
scenarios, not substitutes for this MP4 chain.
