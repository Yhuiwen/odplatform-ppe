"""Streamlit entry point for the read-only Safety Agent assistant."""

from __future__ import annotations

import streamlit as st

from web.agent_support import (
    ask_safety_question,
    get_agent_runtime,
    latest_agent_projection,
    render_agent_projection,
    agent_date_range,
    agent_period,
    render_agent_header,
    render_agent_empty,
    render_agent_section,
)


render_agent_header("安全助手", "通过只读安全 Agent 查询事件统计、证据与安全概况")
runtime = get_agent_runtime(st)
if runtime.assistant_provider_configured:
    st.caption("大模型接口已配置，可理解安全问题并整理平台查询结果。")
else:
    st.caption("大模型接口未配置或配置无效；当前使用本地安全查询。")
default_start, default_end = agent_date_range(st)
render_agent_section("快捷问题")
quick_questions = ("今日有哪些 PPE 违规？", "统计最近的安全事件", "有哪些未戴安全帽事件？", "总结当前安全风险")
for column, prompt in zip(st.columns(4), quick_questions):
    if column.button(prompt, use_container_width=True):
        st.session_state["assistant_question"] = prompt

with st.form("agent_question_form"):
    question = st.text_area(
        "向安全助手提问",
        placeholder="例如：统计最近的安全事件",
        key="assistant_question",
    )
    with st.expander("高级筛选 · UTC 日期范围"):
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
        "询问安全助手",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if not question.strip():
        st.warning("请输入安全相关问题后再提交。")
    elif start_date > end_date:
        st.error("开始日期不能晚于结束日期。")
    else:
        try:
            with st.spinner("正在查询数据并整理回复..."):
                ask_safety_question(
                    st,
                    question=question,
                    requested_period=agent_period(start_date, end_date),
                )
        except Exception:
            st.error("助手暂时无法回答，请稍后重试。")

projection = latest_agent_projection(st, operation="ask")
if projection is None:
    render_agent_empty("尚无助手回复", "选择快捷问题或输入安全相关问题")
else:
    render_agent_section("安全助手回复")
    render_agent_projection(st, projection)
