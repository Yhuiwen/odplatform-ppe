"""Verified evidence viewer for persisted events."""

from __future__ import annotations

import streamlit as st

from web.dashboard_support import get_runtime
from web.ui.components import render_empty_state, render_kpi_card, render_page_header, render_section_header, render_status_badge
from web.ui.formatting import format_confidence, format_event_type, format_timestamp, short_event_id


render_page_header("事件证据中心", "查看违规现场截图及完整性校验信息")
runtime = get_runtime(st)
service = runtime.query_service

events = list(service.snapshot_events())
requested_id = st.session_state.get("selected_evidence_event_id")
if requested_id and all(item.id != requested_id for item in events):
    requested_event = service.get_event(requested_id)
    if requested_event is not None:
        events.insert(0, requested_event)
if not events:
    render_empty_state("暂无证据", "有截图的事件将在这里显示")
    st.stop()

labels = {
    event.id: (
        f"{format_timestamp(event.timestamp)} · {format_event_type(event.type)} · Track {event.track_id}"
    )
    for event in events
}
event_id = st.selectbox(
    "选择事件",
    tuple(labels),
    format_func=labels.get,
    index=list(labels).index(requested_id) if requested_id in labels else 0,
)
st.session_state["selected_evidence_event_id"] = event_id
evidence = service.evidence(event_id)

if evidence is None:
    st.error("所选事件已不存在。")
    st.stop()

metadata_columns = st.columns(4)
for column, data in zip(metadata_columns, (
    ("事件", short_event_id(evidence.event.id), "事件标识"),
    ("Track", evidence.event.track_id, "人员轨迹"),
    ("置信度", format_confidence(evidence.event.confidence, evidence.event.type), "检测结果"),
    ("完整性", "已验证" if evidence.verified else "待核查", "SHA256 与尺寸校验"),
)):
    with column:
        render_kpi_card(*data, tone="green" if data[0] == "完整性" and evidence.verified else "blue")

left, right = st.columns((7, 3), gap="large")
with left:
    render_section_header("现场截图")
    if evidence.file_path is not None:
        st.image(str(evidence.file_path), caption=format_event_type(evidence.event.type), width=850)
    else:
        render_empty_state("证据图片不可用", "请核查证据文件完整性")
with right:
    render_section_header("证据详情")
    render_status_badge("完整性已验证" if evidence.verified else "完整性待核查", "green" if evidence.verified else "red")
    st.write(f"**事件类型**　{format_event_type(evidence.event.type)}")
    st.write(f"**发生时间**　{format_timestamp(evidence.event.timestamp)}")
    st.write(f"**文件状态**　{'可用' if evidence.file_path else '不可用'}")
    if evidence.snapshot is not None:
        st.write(f"**图片尺寸**　{evidence.snapshot.width} × {evidence.snapshot.height}")
        st.write(f"**MIME**　{evidence.snapshot.mime_type}")
        digest = evidence.snapshot.sha256
        st.write(f"**SHA256**　`{digest[:12]}...{digest[-8:]}`")
        with st.expander("复制完整 SHA256"):
            st.code(digest)

if evidence.error_message:
    st.error("证据完整性校验未通过，请联系管理员核查。")
if evidence.snapshot is not None:
    with st.expander("查看原始证据元数据"):
        st.json(evidence.snapshot.to_dict())
