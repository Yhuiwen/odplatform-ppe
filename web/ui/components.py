"""Small shared Streamlit presentation components."""

from html import escape

import streamlit as st

from web.ui.formatting import format_confidence, format_event_status, format_event_type, format_timestamp, format_source_label


def render_page_header(title, subtitle):
    st.markdown(f'<div class="page-kicker">PPE SAFETY OPERATIONS</div><h1 class="page-title">{escape(title)}</h1><p class="page-subtitle">{escape(subtitle)}</p>', unsafe_allow_html=True)


def render_section_header(title, caption=None):
    st.markdown(f'<h3 class="section-title">{escape(title)}</h3>' + (f'<p class="section-caption">{escape(caption)}</p>' if caption else ""), unsafe_allow_html=True)


def render_kpi_card(label, value, detail="", icon="●", tone="blue"):
    st.markdown(f'<div class="kpi-card {escape(tone)}"><div class="kpi-top"><span>{escape(label)}</span><span>{escape(icon)}</span></div><div class="kpi-value">{escape(str(value))}</div><div class="kpi-detail">{escape(detail)}</div></div>', unsafe_allow_html=True)


def render_status_badge(label, tone="gray"):
    st.markdown(f'<span class="status-badge {escape(tone)}">● {escape(label)}</span>', unsafe_allow_html=True)


def render_empty_state(title, description, icon="○"):
    st.markdown(f'<div class="empty-state"><span class="empty-icon">{escape(icon)}</span><strong>{escape(title)}</strong><small>{escape(description)}</small></div>', unsafe_allow_html=True)


def event_table_rows(events, *, sources=None, include_source=False):
    rows = []
    sources = sources or {}
    for event in events:
        row = {"发生时间": format_timestamp(event.timestamp), "人员 Track": event.track_id, "事件类型": format_event_type(event.type), "置信度": format_confidence(event.confidence, event.type), "证据": "已留证" if event.snapshot else "无证据", "状态": format_event_status(event.status)}
        if include_source:
            row["来源"] = format_source_label(sources.get(event.id))
        rows.append(row)
    return rows


def render_compact_counts(counts, formatter=lambda value: value, height=280):
    if not counts:
        render_empty_state("暂无统计数据", "当前筛选范围没有可展示的事件")
        return
    import altair as alt
    import pandas as pd

    data = pd.DataFrame([{"类别": formatter(key), "事件数": count} for key, count in counts.items()])
    chart = alt.Chart(data).mark_bar(cornerRadiusEnd=5, color="#315c89", size=24).encode(
        x=alt.X("事件数:Q", axis=alt.Axis(tickMinStep=1, title=None)),
        y=alt.Y("类别:N", sort="-x", axis=alt.Axis(title=None, labelLimit=130)),
        tooltip=["类别:N", "事件数:Q"],
    ).properties(height=min(height, max(90, len(data) * 48)))
    st.altair_chart(chart, use_container_width=True)
