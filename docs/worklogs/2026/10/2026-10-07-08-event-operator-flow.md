# 2026-10-07 — Monitoring and event operator flow

Changed: One-click monitoring button refresh; clarified alert-delivery KPI; Chinese event row actions and status controls; direct Evidence Viewer selection; persistent status write service; static read-only tables; focused tests.

Reason: User-reported double-click USB controls, ambiguous alert count, English table menu and redundant event details.

Validation: Focused AppTests cover one-click start/stop, both status transitions, navigation selection and evidence preselection. Full pytest: 783 passed. Restarted Streamlit on port 8502; health endpoint returned `ok`.

Evidence: `docs/reports/phase-09/P9D_EVENT_OPERATOR_FLOW_REPORT.md`, `tests/e2e/test_monitoring_control_refresh.py`, `tests/e2e/test_event_operator_flow.py`.

Risk: Rows with many columns need manual narrow-viewport review. Physical USB capture and browser navigation were not exercised by the test suite.

Not Verified: Physical USB camera interaction, manual responsive display (browser control interface unavailable) and concurrent multi-operator status edits.

Next Step: Open the restarted local app, confirm the result-row layout and test one physical camera session.
