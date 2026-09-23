"""Read-only event history explorer."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus
from web.dashboard_support import event_rows, get_runtime


PAGE_SIZE = 50

st.title("Event Explorer")
runtime = get_runtime(st)
service = runtime.query_service

if "event_explorer_offset" not in st.session_state:
    st.session_state.event_explorer_offset = 0

filter_columns = st.columns(4)
event_type_value = filter_columns[0].selectbox(
    "Event type",
    ("ALL", *(item.value for item in ComplianceEventType)),
)
status_value = filter_columns[1].selectbox(
    "Status",
    ("ALL", *(item.value for item in EventStatus)),
)
sources = service.sources()
source_value = filter_columns[2].selectbox(
    "Source",
    ("ALL", *sources),
)
track_text = filter_columns[3].text_input("Track ID")

use_date_range = st.checkbox("Use UTC date range")
if use_date_range:
    date_columns = st.columns(2)
    start_date = date_columns[0].date_input(
        "From",
        value=date.today() - timedelta(days=30),
        max_value=date.today(),
    )
    end_date = date_columns[1].date_input(
        "To",
        value=date.today(),
        max_value=date.today(),
    )
else:
    start_date = None
    end_date = None

track_id: int | None = None
if track_text.strip():
    try:
        track_id = int(track_text.strip())
        if track_id < 0:
            raise ValueError
    except ValueError:
        st.error("Track ID must be a non-negative integer.")
        track_id = None

start_at: str | None = None
end_at: str | None = None
if start_date is not None and end_date is not None:
    if start_date > end_date:
        st.error("The start date cannot be after the end date.")
        st.stop()
    start_at = f"{start_date.isoformat()}T00:00:00Z"
    end_at = f"{end_date.isoformat()}T23:59:59Z"

page = service.list_events(
    start_at=start_at,
    end_at=end_at,
    track_id=track_id,
    event_type=None if event_type_value == "ALL" else event_type_value,
    status=None if status_value == "ALL" else status_value,
    source=None if source_value == "ALL" else source_value,
    limit=PAGE_SIZE,
    offset=st.session_state.event_explorer_offset,
)

rows = event_rows(page)
if rows:
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("No events match the current filters.")

previous_column, summary_column, next_column = st.columns((1, 4, 1))
if previous_column.button(
    "Previous",
    disabled=st.session_state.event_explorer_offset <= 0,
    use_container_width=True,
):
    st.session_state.event_explorer_offset = max(
        0,
        st.session_state.event_explorer_offset - PAGE_SIZE,
    )
    st.rerun()

offset = st.session_state.event_explorer_offset
summary_column.caption(
    f"Showing {offset + 1 if rows else 0}-{offset + len(rows)} "
    f"of {page.total_count} events"
)

if next_column.button(
    "Next",
    disabled=offset + PAGE_SIZE >= page.total_count,
    use_container_width=True,
):
    st.session_state.event_explorer_offset += PAGE_SIZE
    st.rerun()

st.caption(f"Source query generated at {page.generated_at}")
