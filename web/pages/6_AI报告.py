"""Streamlit entry point for grounded safety report generation."""

from __future__ import annotations

import streamlit as st

from web.agent_support import (
    generate_safety_report,
    get_agent_runtime,
    latest_agent_projection,
    render_agent_projection,
    agent_date_range,
    agent_period,
    agent_event_count,
    render_agent_header,
    render_agent_empty,
    render_agent_section,
)


render_agent_header("AI 安全报告", "基于已确认的安全事件生成可追溯分析与整改建议")
runtime = get_agent_runtime(st)
if runtime.report_provider_configured:
    st.caption("大模型接口已配置；生成报告时调用，调用失败将自动使用本地模板。")
else:
    st.caption("大模型接口未配置或配置无效；当前使用本地模板。")
st.markdown('<div class="note-card">报告仅分析已持久化事件，不会修改检测、跟踪或事件结果。</div>', unsafe_allow_html=True)
default_start, default_end = agent_date_range(st)

with st.form("agent_report_form"):
    date_columns = st.columns(2)
    start_date = date_columns[0].date_input(
        "开始日期（UTC）",
        value=default_start,
    )
    end_date = date_columns[1].date_input(
        "结束日期（UTC）",
        value=default_end,
    )
    submitted = st.form_submit_button(
        "生成安全报告",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if start_date > end_date:
        st.error("开始日期不能晚于结束日期。")
    else:
        period = agent_period(start_date, end_date)
        if agent_event_count(st, period) == 0:
            render_agent_empty("该时间范围暂无安全事件", "调整日期范围后重新生成")
        else:
            try:
                with st.spinner("正在生成安全报告..."):
                    generate_safety_report(st, requested_period=period)
            except Exception:
                st.error("报告生成暂不可用，请稍后重试。")

projection = latest_agent_projection(st, operation="report")
if projection is None:
    render_agent_empty("尚未生成报告", "选择日期范围后生成安全分析")
else:
    render_agent_section("报告结果")
    render_agent_projection(st, projection)
