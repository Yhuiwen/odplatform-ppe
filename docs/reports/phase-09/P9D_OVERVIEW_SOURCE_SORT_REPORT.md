# P9-D overview, source labels and time ordering

Date: 2026-10-07. Targeted UI/data gate: PASS; manual browser review remains open.

## Design

The safety overview now leads with a pending-event banner, persistent-event KPIs and quick navigation, followed by a UTC daily trend, violation-type chart, recent events, source distribution and handling progress. All counts derive from the existing event repository. The layout takes only the general chart/event-grid information structure from the open-source Worksite Safety Monitor reference; no third-party code or assets were copied. A synthetic safety score and unsupported person identity are deliberately absent.

Visible event tables no longer include an event ID column. The Event Explorer still keeps IDs internally for status edits and exact evidence navigation. Recent-event time selectors use database-side `asc`/`desc` ordering before pagination; the monitoring session's recent list is sorted in memory. Raw source values remain in SQLite, while UI labels are limited to `mp4`, `usb{id}` and `rtsp` for supported inputs. The Event Explorer groups its source filter by these labels, and Statistics aggregates counts across distinct MP4 files or RTSP addresses.

## Verification

- Repository tests cover ascending/descending pagination and grouped MP4, USB and RTSP filtering.
- A populated Overview AppTest confirms the trend renders, no event ID column appears, and an MP4 filename is shown only as `mp4`.
- Focused tests: 13 passed. Full repository suite: **786 passed**.
- Current local database source summary, with raw values suppressed: `mp4: 35 events`, `usb0: 13 events`.
- Streamlit was restarted on port 8502; `/_stcore/health` returned `ok`. The in-app browser control interface remained unavailable, so no screenshot-based responsive review was recorded.

Manual responsive browser inspection and physical camera input were not part of this run. The existing persisted event and source schemas are unchanged.
