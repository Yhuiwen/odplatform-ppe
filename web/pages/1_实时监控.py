"""Streamlit page for service-owned realtime monitoring."""

from __future__ import annotations

import streamlit as st

from core.schemas.video import SourceType
from services.monitoring_service import (
    MonitoringConfigurationError,
    MonitoringError,
    MonitoringSourceRequest,
)
from web.monitoring_support import get_monitoring_runtime


st.title("Realtime Monitoring")

runtime = get_monitoring_runtime(st)
service = runtime.service

SOURCE_LABELS = {
    "MP4 file": SourceType.MP4,
    "USB Camera": SourceType.USB_CAMERA,
    "RTSP": SourceType.RTSP,
}

source_label = st.selectbox("Input source", tuple(SOURCE_LABELS))
source_type = SOURCE_LABELS[source_label]

location: str | int
if source_type is SourceType.MP4:
    location = st.text_input(
        "MP4 path",
        help="Absolute path or a path relative to the process working directory.",
    )
elif source_type is SourceType.USB_CAMERA:
    location = int(
        st.number_input(
            "Camera device index",
            min_value=0,
            max_value=64,
            value=0,
            step=1,
        )
    )
else:
    location = st.text_input(
        "RTSP URL",
        type="password",
        help="Credentials are not written to monitoring status output.",
    )

current_status = service.status()
start_column, stop_column = st.columns(2)

if start_column.button(
    "Start monitoring",
    type="primary",
    use_container_width=True,
    disabled=current_status.active,
):
    if source_type is not SourceType.USB_CAMERA and not str(location).strip():
        st.error("A source location is required.")
    else:
        try:
            service.start(
                MonitoringSourceRequest(
                    source_type=source_type,
                    location=location,
                )
            )
        except MonitoringConfigurationError as exc:
            st.error(str(exc))
        except MonitoringError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"{type(exc).__name__}: {exc}")
        else:
            st.success("Monitoring session started.")

if stop_column.button(
    "Stop monitoring",
    use_container_width=True,
    disabled=not current_status.active,
):
    status = service.stop()
    if status.error_code == "MONITORING_STOP_TIMEOUT":
        st.error(status.error_message or "Monitoring did not stop in time.")
    else:
        st.success("Monitoring stop requested.")


@st.fragment(run_every=1.0)
def render_live_status() -> None:
    status = service.status()

    state_column, frames_column, detections_column, tracks_column, events_column = (
        st.columns(5)
    )
    state_column.metric("State", status.state.value.upper())
    frames_column.metric("Frames", status.frames_processed)
    detections_column.metric("Detections", status.detections)
    tracks_column.metric("Tracks", status.tracks)
    events_column.metric("Events", status.events_generated)

    alert_columns = st.columns(3)
    alert_columns[0].metric("Delivered alerts", status.alerts_delivered)
    alert_columns[1].metric("Failed alerts", status.alerts_failed)
    alert_columns[2].metric("Unknown associations", status.unknown_associations)

    source_name = status.display_name or status.source_id or "No active source"
    st.caption(
        f"Source: {source_name} | "
        f"Latest frame: {status.latest_frame_id if status.latest_frame_id is not None else 'N/A'}"
    )

    if status.error_message:
        st.error(f"{status.error_code or 'MONITORING_ERROR'}: {status.error_message}")

    preview_column, event_column = st.columns((3, 2))
    with preview_column:
        st.subheader("Detection preview")
        if status.latest_frame is not None:
            st.image(
                status.latest_frame,
                channels="BGR",
                caption="Latest processed frame",
                use_container_width=True,
            )
        else:
            st.info("No processed frame is available yet.")

    with event_column:
        st.subheader("Recent events")
        if status.recent_events:
            st.dataframe(
                [
                    {
                        "event_id": item["event_id"],
                        "type": item["type"],
                        "track_id": item["track_id"],
                        "confidence": item["confidence"],
                        "frame_id": item["frame_id"],
                        "snapshot": item["snapshot"],
                        "alerts": ", ".join(
                            f"{result['adapter']}:{result['status']}"
                            for result in item["alerts"]
                        ),
                    }
                    for item in status.recent_events
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No events are available for this session.")

    if status.started_at:
        st.caption(
            f"Started: {status.started_at} | Stopped: {status.stopped_at or 'N/A'}"
        )


render_live_status()
