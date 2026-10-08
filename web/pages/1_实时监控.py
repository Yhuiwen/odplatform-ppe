"""Streamlit page for service-owned realtime monitoring."""

from __future__ import annotations

from html import escape

import streamlit as st

from core.schemas.video import SourceType
from services.monitoring_service import (
    MonitoringConfigurationError,
    MonitoringError,
    MonitoringSourceRequest,
)
from web.monitoring_support import get_monitoring_runtime
from web.ui.components import render_empty_state, render_kpi_card, render_page_header, render_section_header, render_status_badge
from web.ui.formatting import format_event_type, format_source_label, format_timestamp


render_page_header("实时安全监控", "实时执行人员检测、PPE 关联、违规确认和事件告警")

runtime = get_monitoring_runtime(st)
service = runtime.service

SOURCE_LABELS = {
    "MP4 视频": SourceType.MP4,
    "USB 摄像头": SourceType.USB_CAMERA,
    "RTSP 流": SourceType.RTSP,
}

render_section_header("监控控制台")
source_label = st.selectbox("输入源", tuple(SOURCE_LABELS))
source_type = SOURCE_LABELS[source_label]

location: str | int
if source_type is SourceType.MP4:
    location = st.text_input(
        "视频文件路径",
        placeholder="选择已存在的 MP4 文件路径",
        help="可填写项目目录下已有 MP4 文件的相对路径。",
    )
elif source_type is SourceType.USB_CAMERA:
    location = int(
        st.number_input(
            "摄像头编号",
            min_value=0,
            max_value=64,
            value=0,
            step=1,
        )
    )
else:
    location = st.text_input(
        "RTSP 地址",
        type="password",
        help="连接信息仅用于建立视频流。",
    )

current_status = service.status()
start_column, stop_column = st.columns(2)

if start_column.button(
    "开始监控",
    type="primary",
    use_container_width=True,
    disabled=current_status.active or (source_type is not SourceType.USB_CAMERA and not str(location).strip()),
):
    if source_type is not SourceType.USB_CAMERA and not str(location).strip():
        st.error("请填写有效的输入源。")
    else:
        try:
            service.start(
                MonitoringSourceRequest(
                    source_type=source_type,
                    location=location,
                )
            )
        except (MonitoringConfigurationError, MonitoringError):
            st.error("输入源或监控配置不可用，请核查后重试。")
        except Exception:
            st.error("监控启动失败，请检查输入源和模型环境。")
        else:
            st.rerun()

if stop_column.button(
    "停止监控",
    use_container_width=True,
    disabled=not current_status.active,
):
    status = service.stop()
    if status.error_code == "MONITORING_STOP_TIMEOUT":
        st.error("停止监控超时，请稍后查看状态。")
    else:
        st.rerun()

render_section_header("实时检测画面")
st.markdown(
    f'<img src="{escape(runtime.preview_url, quote=True)}" '
    'alt="实时处理后的检测画面" '
    'style="display:block;width:100%;aspect-ratio:16/9;object-fit:contain;'
    'background:#17283b;border-radius:10px">',
    unsafe_allow_html=True,
)
st.caption("检测框由处理完成的帧直接回显；首帧处理完成后自动显示。")


@st.fragment(run_every=0.3)
def render_live_status() -> None:
    status = service.status()

    state_labels = {"idle": ("空闲", "gray"), "starting": ("启动中", "amber"), "running": ("监控中", "green"), "stopping": ("停止中", "amber"), "stopped": ("已停止", "gray"), "completed": ("已完成", "green"), "failed": ("异常", "red")}
    label, tone = state_labels.get(status.state.value, ("状态未知", "gray"))
    render_status_badge(label, tone)
    for column, item in zip(st.columns(6), (("已处理帧", status.frames_processed, "视频帧"), ("检测目标", status.detections, "目标"), ("人员轨迹", status.tracks, "Track"), ("违规事件", status.events_generated, "已确认"), ("告警投递", status.alerts_delivered, "各通道送达次数"), ("关联未知", status.unknown_associations, "需核查"))):
        with column:
            render_kpi_card(*item)
    st.caption("一条违规事件可分别向控制台、网页和语音投递告警，因此告警投递次数可能大于事件数。")

    if status.error_message:
        code = status.error_code or ""
        message = "监控运行失败，请检查输入源和模型环境。"
        if "RTSP" in code:
            message = "RTSP 连接失败，请检查流地址。"
        elif "CAMERA" in code:
            message = "无法连接摄像头。"
        elif "SOURCE" in code or "VIDEO" in code:
            message = "无法打开视频文件。"
        st.error(message)

    render_section_header("最新事件 / 告警")
    if status.recent_events:
        recent_sort = st.selectbox("时间排序", ("desc", "asc"), format_func=lambda value: "最新在前" if value == "desc" else "最早在前", key="monitoring_recent_sort")
        recent_rows = sorted(status.recent_events, key=lambda item: item.get("timestamp", ""), reverse=recent_sort == "desc")[:8]
        st.table(
            [
                {"时间": format_timestamp(item.get("timestamp")), "事件类型": format_event_type(item.get("type")), "Track": item.get("track_id", "—"), "状态": "已告警" if item.get("alerts") else "已确认"}
                for item in recent_rows
            ],
        )
    else:
        render_empty_state("当前会话暂无事件", "确认的违规事件将在这里显示")

    st.caption(f"输入源：{format_source_label(status.source_id) if status.source_id else '未选择'}　·　源状态：{status.state.value}　·　当前帧：{status.latest_frame_id if status.latest_frame_id is not None else '—'}")


render_live_status()
