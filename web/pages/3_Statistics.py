"""Read-only event analytics for the safety platform."""

import streamlit as st

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventQuery, EventStatus
from web.dashboard_support import get_runtime
from web.ui.components import render_compact_counts, render_empty_state, render_kpi_card, render_page_header, render_section_header
from web.ui.formatting import available_date_range, format_event_status, format_event_type, format_timestamp, period_from_dates, source_group_counts

render_page_header("安全统计分析", "按事件类型、状态和时间查看 PPE 合规趋势")
service = get_runtime(st).query_service
start_default, end_default = available_date_range(service.statistics())
filters = st.columns(4)
event_type = filters[0].selectbox("事件类型", ("ALL", *(item.value for item in ComplianceEventType)), format_func=lambda value: "全部类型" if value == "ALL" else format_event_type(value))
status = filters[1].selectbox("处理状态", ("ALL", *(item.value for item in EventStatus)), format_func=lambda value: "全部状态" if value == "ALL" else format_event_status(value))
start = filters[2].date_input("开始日期（UTC）", value=start_default)
end = filters[3].date_input("结束日期（UTC）", value=end_default)
if start > end:
    st.error("开始日期不能晚于结束日期。")
    st.stop()
period = period_from_dates(start, end)
statistics = service.statistics(EventQuery(start_at=period["start_at"], end_at=period["end_at"], event_type=None if event_type == "ALL" else event_type, status=None if status == "ALL" else status))
type_counts = {key.value: value for key, value in statistics.by_type}
status_counts = {key.value: value for key, value in statistics.by_status}
for column, item in zip(st.columns(4), (("总事件", statistics.total_count, "筛选范围内"), ("未戴安全帽", type_counts.get("NO_HELMET", 0), "安全帽违规"), ("未穿反光衣", type_counts.get("NO_VEST", 0), "反光衣违规"), ("状态未知", type_counts.get("PPE_UNKNOWN", 0), "PPE 关联未知"))):
    with column:
        render_kpi_card(*item)

left, right = st.columns(2, gap="large")
with left:
    render_section_header("事件类型分布")
    render_compact_counts(type_counts, format_event_type)
with right:
    render_section_header("事件状态分布")
    render_compact_counts(status_counts, format_event_status)

render_section_header("每日事件趋势")
if statistics.by_day:
    import altair as alt
    import pandas as pd
    data = pd.DataFrame([{"日期": day, "事件数": count} for day, count in statistics.by_day])
    st.altair_chart(alt.Chart(data).mark_line(point=alt.OverlayMarkDef(size=90, filled=True), color="#315c89", strokeWidth=3).encode(x=alt.X("日期:N", axis=alt.Axis(labelAngle=0, title=None)), y=alt.Y("事件数:Q", axis=alt.Axis(tickMinStep=1, title=None)), tooltip=["日期:N", "事件数:Q"]).properties(height=220), use_container_width=True)
    if len(data) == 1:
        st.caption("当前仅有 1 个统计日期")
else:
    render_empty_state("暂无每日趋势", "当前日期范围内没有事件")

render_section_header("输入源分布")
source_counts = source_group_counts(statistics.by_source)
if source_counts:
    st.table([{"来源": source, "事件数": count, "占比": f"{count / statistics.total_count:.0%}"} for source, count in source_counts.items()])
else:
    render_empty_state("暂无来源数据", "当前筛选范围内没有事件来源")
st.caption(f"数据更新：{format_timestamp(statistics.generated_at)}")
