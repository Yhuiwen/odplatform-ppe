"""Verified evidence viewer for persisted events."""

from __future__ import annotations

import streamlit as st

from web.dashboard_support import get_runtime


st.title("Evidence Viewer")
runtime = get_runtime(st)
service = runtime.query_service

events = service.snapshot_events()
if not events:
    st.info("No evidence snapshots are available.")
    st.stop()

labels = {
    event.id: (
        f"{event.timestamp} | {event.type.value} | "
        f"track {event.track_id} | {event.id}"
    )
    for event in events
}
event_id = st.selectbox(
    "Event",
    tuple(labels),
    format_func=labels.get,
)
evidence = service.evidence(event_id)

if evidence is None:
    st.error("The selected event no longer exists.")
    st.stop()

metadata_columns = st.columns(4)
metadata_columns[0].metric("Event", evidence.event.id)
metadata_columns[1].metric("Track", evidence.event.track_id)
metadata_columns[2].metric("Confidence", f"{evidence.event.confidence:.2f}")
metadata_columns[3].metric(
    "Integrity",
    "VERIFIED" if evidence.verified else "FAILED",
)

if evidence.file_path is not None:
    st.image(
        str(evidence.file_path),
        caption=f"{evidence.event.type.value} evidence",
        use_container_width=True,
    )
else:
    st.warning("Evidence file is unavailable.")

if evidence.error_message:
    st.error(evidence.error_message)
if evidence.snapshot is not None:
    st.json(evidence.snapshot.to_dict())
