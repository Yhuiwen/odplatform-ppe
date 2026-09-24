"""Streamlit entry point for grounded safety report generation."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from web.agent_support import (
    generate_safety_report,
    get_agent_runtime,
    latest_agent_projection,
    render_agent_projection,
)


st.title("AI Safety Report")
runtime = get_agent_runtime(st)
if runtime.identity_mode == "LOCAL_DEMO_READ_ONLY":
    st.caption("Local read-only demo identity")

with st.form("agent_report_form"):
    date_columns = st.columns(2)
    start_date = date_columns[0].date_input(
        "From",
        value=date.today() - timedelta(days=7),
        max_value=date.today(),
    )
    end_date = date_columns[1].date_input(
        "To",
        value=date.today(),
        max_value=date.today(),
    )
    submitted = st.form_submit_button(
        "Generate report",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if start_date > end_date:
        st.error("The start date cannot be after the end date.")
    else:
        try:
            generate_safety_report(
                st,
                requested_period={
                    "start_at": f"{start_date.isoformat()}T00:00:00Z",
                    "end_at": f"{end_date.isoformat()}T23:59:59Z",
                },
            )
        except Exception:
            st.error("The report request could not be completed safely.")

projection = latest_agent_projection(st)
if projection is None:
    st.info("No report has been generated in this session.")
else:
    render_agent_projection(st, projection)
