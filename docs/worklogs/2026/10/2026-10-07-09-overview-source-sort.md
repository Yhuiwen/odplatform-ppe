# 2026-10-07 — Overview and event table cleanup

Changed: Reworked safety Overview; removed visible event IDs from tables; added database-backed time ordering; grouped source filters/statistics and labels as mp4, usb{id}, rtsp; added focused tests.

Reason: The user requested a clearer overview and simpler table presentation without raw source filenames or addresses.

Validation: Populated Overview AppTest, source/group/order repository tests and full pytest (786 passed). Restarted Streamlit on port 8502; health endpoint returned `ok`.

Evidence: `docs/reports/phase-09/P9D_OVERVIEW_SOURCE_SORT_REPORT.md`, `tests/test_dashboard_source_sort.py`, `web/pages/0_Overview.py`.

Risk: The redesigned page needs manual narrow-screen review. Unknown legacy source formats display as `其他` without changing stored metadata.

Not Verified: Manual browser visual layout (browser control interface unavailable) and camera/RTSP presentation on real hardware.

Next Step: Review the restarted Overview at narrow and wide viewport sizes and adjust spacing if needed.
