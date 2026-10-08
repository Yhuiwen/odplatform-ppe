# P9-D monitoring and event operator flow

Date: 2026-10-07. Targeted UI/service gate: PASS; broader P9-D human review remains open.

## Changes

- Monitoring start/stop now reruns the full page immediately after a successful action, so the opposite button is enabled after one click even for a continuing USB camera session. The processed-frame preview and service lifecycle remain unchanged.
- The monitoring KPI says `告警投递` and explains that one persisted event can have Console, Web and TTS delivery results. The underlying counter remains adapter deliveries; it is not treated as an event count.
- Event Explorer uses Chinese operator controls. Each result has a `查看详情` button that sets the selected event and navigates to Evidence Viewer; the separate lower detail panel is removed. The evidence page selects the requested event, including one without a snapshot.
- The per-event status control offers `待处理` and `已处理`. An explicit `EventStatusService` maps these to existing `OPEN` and `RESOLVED` values, persists through `EventRepository.update_status`, and the page rereads the repository. The read-only `EventQueryService` remains read-only.
- Read-only Streamlit dataframes on Overview, Monitoring and Statistics are static tables, so their English native context menu is absent. Event Explorer provides Chinese action controls instead.

## Verification

The focused AppTest covers one-click USB start and stop, persisted status changes in both directions, event detail selection and Evidence Viewer preselection. Existing page/monitoring tests passed. Full repository regression: **783 passed**. Streamlit was restarted on port 8502 and `/_stcore/health` returned `ok`. No physical USB device was available to this test; the button interaction uses a service fake. The in-app browser control interface was unavailable for a visual click-through, so a live browser visual check and manual camera session remain for review.
