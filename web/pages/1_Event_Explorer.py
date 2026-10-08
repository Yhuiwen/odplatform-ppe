"""Event history and operator handling controls."""

from __future__ import annotations

import streamlit as st

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventStatus
from web.dashboard_support import get_runtime
from web.ui.components import render_empty_state, render_page_header, render_section_header
from web.ui.formatting import available_date_range, format_confidence, format_event_status, format_event_type, format_timestamp, format_source_label, period_from_dates


PAGE_SIZE = 50

render_page_header("事件中心", "检索、筛选并查看已确认的 PPE 合规事件")
runtime = get_runtime(st)
service = runtime.query_service
default_start, default_end = available_date_range(service.statistics())

if "event_explorer_offset" not in st.session_state:
    st.session_state.event_explorer_offset = 0

filter_columns = st.columns(4)
event_type_value = filter_columns[0].selectbox(
    "事件类型",
    ("ALL", *(item.value for item in ComplianceEventType)),
    format_func=lambda value: "全部类型" if value == "ALL" else format_event_type(value),
)
status_value = filter_columns[1].selectbox(
    "处理状态",
    ("ALL", *(item.value for item in EventStatus)),
    format_func=lambda value: "全部状态" if value == "ALL" else format_event_status(value),
)
sources = tuple(sorted({format_source_label(value) for value in service.sources()} - {"其他"}))
source_value = filter_columns[2].selectbox(
    "来源",
    ("ALL", *sources),
    format_func=lambda value: "全部来源" if value == "ALL" else value,
)
track_text = filter_columns[3].text_input("Track ID")

date_columns = st.columns((2, 2, 2, 1))
start_date = date_columns[0].date_input("开始日期（UTC）", value=default_start)
end_date = date_columns[1].date_input("结束日期（UTC）", value=default_end)
sort_order = date_columns[2].selectbox("时间排序", ("desc", "asc"), format_func=lambda value: "最新在前" if value == "desc" else "最早在前")
if date_columns[3].button("重置筛选", use_container_width=True):
    st.session_state.event_explorer_offset = 0
    st.rerun()

track_id: int | None = None
if track_text.strip():
    try:
        track_id = int(track_text.strip())
        if track_id < 0:
            raise ValueError
    except ValueError:
        st.error("Track ID 必须是非负整数。")
        st.stop()

start_at: str | None = None
end_at: str | None = None
if start_date > end_date:
    st.error("开始日期不能晚于结束日期。")
    st.stop()
period = period_from_dates(start_date, end_date)
start_at, end_at = period["start_at"], period["end_at"]

page = service.list_events(
    start_at=start_at,
    end_at=end_at,
    track_id=track_id,
    event_type=None if event_type_value == "ALL" else event_type_value,
    status=None if status_value == "ALL" else status_value,
    source_group=None if source_value == "ALL" else source_value,
    sort_order=sort_order,
    limit=PAGE_SIZE,
    offset=st.session_state.event_explorer_offset,
)

render_section_header("筛选结果")
rows = page.items
if rows:
    row_sources = service.sources_for_events(rows)
    widths = (2, 3, 1, 2, 1, 1, 2, 1)
    headers = ("来源", "发生时间", "Track", "事件类型", "置信度", "证据", "处理状态", "操作")
    for column, label in zip(st.columns(widths), headers):
        column.markdown(f"**{label}**")
    if st.session_state.pop("event_status_error", None):
        st.error("事件状态更新失败，请刷新后重试。")

    def save_status(event_id: str, key: str) -> None:
        try:
            runtime.status_service.set_handled(
                event_id,
                handled=st.session_state[key] == "已处理",
            )
        except Exception:
            st.session_state["event_status_error"] = True

    for event in rows:
        columns = st.columns(widths, vertical_alignment="center")
        columns[0].write(format_source_label(row_sources.get(event.id)))
        columns[1].write(format_timestamp(event.timestamp))
        columns[2].write(str(event.track_id))
        columns[3].write(format_event_type(event.type))
        columns[4].write(format_confidence(event.confidence, event.type))
        columns[5].write("已留证" if event.snapshot else "无证据")
        status_key = f"event_status_{event.id}"
        current_label = "已处理" if event.status in {EventStatus.RESOLVED, EventStatus.DISMISSED} else "待处理"
        if st.session_state.get(status_key) != current_label:
            st.session_state[status_key] = current_label
        columns[6].selectbox(
            "处理状态", ("待处理", "已处理"), key=status_key,
            label_visibility="collapsed", on_change=save_status,
            args=(event.id, status_key),
        )
        if columns[7].button("查看详情", key=f"event_detail_{event.id}"):
            st.session_state["selected_evidence_event_id"] = event.id
            st.switch_page("pages/2_Evidence_Viewer.py")
else:
    render_empty_state("没有匹配的事件", "请调整筛选条件或日期范围")

previous_column, summary_column, next_column = st.columns((1, 4, 1))
if previous_column.button(
    "上一页",
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
    f"第 {offset + 1 if rows else 0}–{offset + len(rows)} 条，共 {page.total_count} 条"
)

if next_column.button(
    "下一页",
    disabled=offset + PAGE_SIZE >= page.total_count,
    use_container_width=True,
):
    st.session_state.event_explorer_offset += PAGE_SIZE
    st.rerun()

st.caption(f"数据更新：{format_timestamp(page.generated_at)}")
