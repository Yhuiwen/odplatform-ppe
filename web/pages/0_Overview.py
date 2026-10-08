"""Operational overview derived from persisted PPE events."""

from html import escape

import streamlit as st

from web.dashboard_support import get_runtime
from web.ui.components import (
    event_table_rows,
    render_compact_counts,
    render_empty_state,
    render_kpi_card,
    render_page_header,
    render_section_header,
)
from web.ui.formatting import format_event_type, format_timestamp, source_group_counts


runtime = get_runtime(st)
service = runtime.query_service
statistics = service.statistics()
status_counts = {key.value: value for key, value in statistics.by_status}
type_counts = {key.value: value for key, value in statistics.by_type}
pending = status_counts.get("open", 0) + status_counts.get("acknowledged", 0)
handled = status_counts.get("resolved", 0) + status_counts.get("dismissed", 0)
source_counts = source_group_counts(statistics.by_source)

render_page_header("安全运营总览", "从已记录的事件了解当前待办、违规类型和变化趋势")
headline = "需要处理的事件" if pending else "当前没有待处理事件"
detail = (
    f"已有 {handled} 起事件标记为已处理；请持续核查新事件。"
    if pending else "打开实时监控可查看处理后的检测画面。"
)
st.markdown(
    f'<div class="overview-hero"><div><span class="overview-eyebrow">工地 PPE 安全态势</span>'
    f'<h2>{escape(headline)}</h2><p>{escape(detail)}</p></div>'
    f'<div class="overview-hero-number"><strong>{pending}</strong><span>待处理事件</span></div></div>',
    unsafe_allow_html=True,
)
action_columns = st.columns(3)
if action_columns[0].button("查看事件中心", icon=":material/assignment:", use_container_width=True):
    st.switch_page("pages/1_Event_Explorer.py")
if action_columns[1].button("打开实时监控", icon=":material/live_tv:", use_container_width=True):
    st.switch_page("pages/1_实时监控.py")
if action_columns[2].button("查看统计分析", icon=":material/monitoring:", use_container_width=True):
    st.switch_page("pages/3_Statistics.py")

for column, item in zip(st.columns(4), (
    ("累计事件", statistics.total_count, "已持久化记录", "◉", "blue"),
    ("待处理", pending, "待人工复核", "!", "red"),
    ("未佩戴安全帽", type_counts.get("NO_HELMET", 0), "安全帽违规", "▣", "amber"),
    ("未穿反光衣", type_counts.get("NO_VEST", 0), "反光衣违规", "▥", "amber"),
)):
    with column:
        render_kpi_card(*item)

left, right = st.columns((7, 4), gap="large")
with left:
    render_section_header("事件时间趋势", "按 UTC 日期统计已记录事件")
    if statistics.by_day:
        import altair as alt
        import pandas as pd

        trend = pd.DataFrame(
            [{"日期": day, "事件数": count} for day, count in statistics.by_day]
        )
        chart = alt.Chart(trend).mark_line(
            point=alt.OverlayMarkDef(size=75, filled=True),
            color="#315c89", strokeWidth=3,
        ).encode(
            x=alt.X("日期:N", axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y("事件数:Q", axis=alt.Axis(tickMinStep=1, title=None)),
            tooltip=["日期:N", "事件数:Q"],
        ).properties(height=260)
        st.altair_chart(chart, use_container_width=True)
    else:
        render_empty_state("暂无趋势数据", "监控产生事件后将在这里形成时间趋势")
with right:
    render_section_header("违规类型", "以已确认事件为口径")
    render_compact_counts(type_counts, format_event_type, height=260)
    if type_counts.get("PPE_UNKNOWN", 0):
        st.caption(f"另有 {type_counts['PPE_UNKNOWN']} 起 PPE 状态未知事件，建议人工核查证据。")

render_section_header("近期事件", "按发生时间查看；来源仅显示输入类型")
sort_order = st.selectbox(
    "时间排序", ("desc", "asc"),
    format_func=lambda value: "最新在前" if value == "desc" else "最早在前",
    key="overview_time_sort",
)
recent = service.list_events(limit=8, sort_order=sort_order)
if recent.items:
    sources = service.sources_for_events(recent.items)
    st.table(event_table_rows(recent.items, include_source=True, sources=sources))
    if st.button("查看全部事件", icon=":material/arrow_forward:"):
        st.switch_page("pages/1_Event_Explorer.py")
else:
    render_empty_state("暂无安全事件", "监控产生的已确认事件将在这里显示")

lower_left, lower_right = st.columns(2, gap="large")
with lower_left:
    render_section_header("输入源分布", "按 mp4、USB 编号和 rtsp 汇总")
    render_compact_counts(source_counts, height=200)
with lower_right:
    render_section_header("处理进度", "基于事件状态，不代表现场安全评分")
    if statistics.total_count:
        st.progress(handled / statistics.total_count, text=f"已处理 {handled} / {statistics.total_count}")
        st.caption(f"待处理 {pending} 起；状态未知 {type_counts.get('PPE_UNKNOWN', 0)} 起。")
    else:
        render_empty_state("暂无处理进度", "先完成一次检测并确认事件")

st.caption(f"数据更新：{format_timestamp(statistics.generated_at)} · 所有指标来自持久化事件")
