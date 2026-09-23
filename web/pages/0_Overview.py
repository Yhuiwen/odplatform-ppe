"""Safety operations overview page."""

from __future__ import annotations

import streamlit as st

from web.dashboard_support import event_rows, get_runtime


st.title("Safety Overview")
runtime = get_runtime(st)
query_service = runtime.query_service

statistics = query_service.statistics()
recent = query_service.list_events(limit=8)
status_counts = {key.value: value for key, value in statistics.by_status}
type_counts = {key.value: value for key, value in statistics.by_type}

metric_columns = st.columns(4)
metric_columns[0].metric("Total events", statistics.total_count)
metric_columns[1].metric("Open events", status_counts.get("open", 0))
metric_columns[2].metric(
    "No helmet",
    type_counts.get("NO_HELMET", 0),
)
metric_columns[3].metric(
    "Unknown PPE",
    type_counts.get("PPE_UNKNOWN", 0),
)

left, right = st.columns((3, 2))
with left:
    st.subheader("Recent events")
    rows = event_rows(recent)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No events are available.")

with right:
    st.subheader("Event mix")
    if type_counts:
        st.bar_chart(type_counts)
    else:
        st.info("No event statistics are available.")

    st.subheader("Web alerts")
    web_alerts = runtime.web_alerts.history()
    if web_alerts:
        st.dataframe(
            [item.to_dict() for item in web_alerts],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No web alerts in this session.")

st.caption(f"Source query generated at {statistics.generated_at}")
