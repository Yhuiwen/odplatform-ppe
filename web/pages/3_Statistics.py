"""SQLite-backed event statistics page."""

from __future__ import annotations

import streamlit as st

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventQuery, EventStatus
from web.dashboard_support import get_runtime


st.title("Statistics")
runtime = get_runtime(st)
service = runtime.query_service

filter_columns = st.columns(2)
event_type_value = filter_columns[0].selectbox(
    "Event type",
    ("ALL", *(item.value for item in ComplianceEventType)),
)
status_value = filter_columns[1].selectbox(
    "Status",
    ("ALL", *(item.value for item in EventStatus)),
)

statistics = service.statistics(
    EventQuery(
        event_type=None if event_type_value == "ALL" else event_type_value,
        status=None if status_value == "ALL" else status_value,
        limit=1000,
    )
)
type_counts = {key.value: value for key, value in statistics.by_type}
status_counts = {key.value: value for key, value in statistics.by_status}

metric_columns = st.columns(4)
metric_columns[0].metric("Total", statistics.total_count)
metric_columns[1].metric("No helmet", type_counts.get("NO_HELMET", 0))
metric_columns[2].metric("No vest", type_counts.get("NO_VEST", 0))
metric_columns[3].metric("Unknown", type_counts.get("PPE_UNKNOWN", 0))

left, right = st.columns(2)
with left:
    st.subheader("By type")
    if type_counts:
        st.bar_chart(type_counts)
    else:
        st.info("No type statistics are available.")

with right:
    st.subheader("By status")
    if status_counts:
        st.bar_chart(status_counts)
    else:
        st.info("No status statistics are available.")

st.subheader("Daily events")
if statistics.by_day:
    st.bar_chart(dict(statistics.by_day))
else:
    st.info("No daily statistics are available.")

st.subheader("Sources")
if statistics.by_source:
    st.dataframe(
        [
            {"source": source, "event_count": count}
            for source, count in statistics.by_source
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No source statistics are available.")

st.caption(
    "Source query generated at "
    f"{statistics.generated_at}; earliest "
    f"{statistics.earliest_at or 'N/A'}; latest "
    f"{statistics.latest_at or 'N/A'}"
)
