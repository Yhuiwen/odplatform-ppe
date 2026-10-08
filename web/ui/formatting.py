"""Human-facing labels; persisted values remain unchanged."""

from datetime import date, timedelta
import re


EVENT_TYPES = {"NO_HELMET": "未佩戴安全帽", "NO_VEST": "未穿反光衣", "PPE_UNKNOWN": "PPE 状态未知"}
EVENT_STATUSES = {"open": "待处理", "acknowledged": "已确认", "resolved": "已处理", "dismissed": "已忽略"}


def format_event_type(value):
    return EVENT_TYPES.get(getattr(value, "value", value), str(value))


def format_event_status(value):
    return EVENT_STATUSES.get(getattr(value, "value", value), str(value))


def format_timestamp(value):
    return value.replace("T", " ").replace("Z", " UTC") if value else "—"


def format_confidence(value, event_type=None):
    if value is None or (getattr(event_type, "value", event_type) == "PPE_UNKNOWN" and value == 0):
        return "—"
    return f"{value:.0%}"


def short_event_id(value):
    return value if len(value) <= 16 else f"{value[:12]}..."


def format_source_label(value):
    """Show an input type without exposing file names or RTSP addresses."""
    if not isinstance(value, str):
        return "其他"
    if value.startswith("mp4:"):
        return "mp4"
    if value.startswith("rtsp:"):
        return "rtsp"
    match = re.fullmatch(r"usb:(\d+)", value)
    if match:
        return f"usb{match.group(1)}"
    return "其他"


def source_group_counts(by_source):
    counts = {}
    for source, count in by_source:
        label = format_source_label(source)
        counts[label] = counts.get(label, 0) + count
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def available_date_range(statistics, today=None):
    today = today or date.today()
    if statistics.earliest_at and statistics.latest_at:
        return date.fromisoformat(statistics.earliest_at[:10]), date.fromisoformat(statistics.latest_at[:10])
    return today - timedelta(days=30), today


def period_from_dates(start, end):
    return {"start_at": f"{start.isoformat()}T00:00:00Z", "end_at": f"{end.isoformat()}T23:59:59Z"}
