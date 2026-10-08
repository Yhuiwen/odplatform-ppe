"""Streamlit navigation entrypoint for the Phase 7 dashboard."""

from __future__ import annotations


def main() -> None:
    import streamlit as st
    import importlib
    from infra.llm import chat_transport
    if getattr(chat_transport, "CHAT_BUDGET_VERSION", 0) != 2:
        importlib.reload(chat_transport)
    from services import configured_report_service
    if getattr(configured_report_service, "REPORT_CONFIG_VERSION", 0) != 3:
        importlib.reload(configured_report_service)
    from infra.llm import assistant_client

    # Upgrade cached modules once when an existing credential-bearing process
    # loads the new assistant feature. Normal reruns do not reload modules.
    if getattr(assistant_client, "ASSISTANT_CLIENT_VERSION", 0) != 2:
        importlib.reload(assistant_client)
    from services import configured_assistant_service
    if getattr(configured_assistant_service, "ASSISTANT_SERVICE_VERSION", 0) != 1:
        importlib.reload(configured_assistant_service)
    from web import agent_support
    if getattr(agent_support, "ASSISTANT_RUNTIME_VERSION", 0) != 4:
        importlib.reload(agent_support)

    from web.ui.theme import configure_page, inject_global_styles

    configure_page()
    inject_global_styles()
    st.sidebar.markdown('<div class="brand"><strong>智慧工地 PPE 安全运营平台</strong><small>PPE Safety Operations</small></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-status">系统状态<br>● 本地演示环境</div>', unsafe_allow_html=True)
    navigation = st.navigation(
        (
            st.Page(
                "pages/0_Overview.py",
                title="安全总览",
                icon=":material/dashboard:",
                default=True,
            ),
            st.Page(
                "pages/1_Event_Explorer.py",
                title="事件中心",
                icon=":material/search:",
            ),
            st.Page(
                "pages/1_实时监控.py",
                title="实时监控",
                url_path="Monitoring",
                icon=":material/live_tv:",
            ),
            st.Page(
                "pages/2_Evidence_Viewer.py",
                title="证据中心",
                icon=":material/image:",
            ),
            st.Page(
                "pages/3_Statistics.py",
                title="统计分析",
                icon=":material/monitoring:",
            ),
            st.Page(
                "pages/6_AI报告.py",
                title="AI 安全报告",
                url_path="AI_Report",
                icon=":material/summarize:",
            ),
            st.Page(
                "pages/7_AI助手.py",
                title="安全助手",
                url_path="AI_Assistant",
                icon=":material/smart_toy:",
            ),
        )
    )
    navigation.run()
    st.sidebar.markdown('<div class="sidebar-foot">YOLO11 · ByteTrack · Streamlit</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
