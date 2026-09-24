"""Streamlit navigation entrypoint for the Phase 7 dashboard."""

from __future__ import annotations


def main() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="PPE Safety Operations",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    navigation = st.navigation(
        (
            st.Page(
                "pages/0_Overview.py",
                title="Overview",
                icon=":material/dashboard:",
                default=True,
            ),
            st.Page(
                "pages/1_Event_Explorer.py",
                title="Event Explorer",
                icon=":material/search:",
            ),
            st.Page(
                "pages/1_实时监控.py",
                title="Realtime Monitoring",
                icon=":material/live_tv:",
            ),
            st.Page(
                "pages/2_Evidence_Viewer.py",
                title="Evidence Viewer",
                icon=":material/image:",
            ),
            st.Page(
                "pages/3_Statistics.py",
                title="Statistics",
                icon=":material/monitoring:",
            ),
        )
    )
    navigation.run()


if __name__ == "__main__":
    main()
