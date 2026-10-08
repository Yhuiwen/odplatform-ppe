"""Isolated synthetic history benchmark for the real SQLite/query/page APIs."""

from __future__ import annotations

import json
import hashlib
import io
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter_ns

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.schemas.compliance import ComplianceEventType
from core.schemas.events import EventQuery, SnapshotReference, StoredEvent
from infra.database.database import Database
from infra.database.repository import EventRepository
from infra.database.snapshot_repository import SnapshotRepository
from web.dashboard_support import build_runtime


def stats(values: list[float]) -> dict:
    sorted_values = sorted(values)
    def pct(p: float) -> float:
        rank = (len(sorted_values) - 1) * p
        lo = int(rank)
        hi = min(lo + 1, len(sorted_values) - 1)
        return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (rank - lo)
    return {"n": len(values), "mean_ms": statistics.mean(values), "p50_ms": pct(.5), "p95_ms": pct(.95), "min_ms": sorted_values[0], "max_ms": sorted_values[-1]}


def measure(action):
    start = perf_counter_ns()
    result = action()
    return result, (perf_counter_ns() - start) / 1_000_000


def main() -> int:
    root = ROOT / "artifacts/p9c/synthetic-database"
    root.mkdir(parents=True, exist_ok=True)
    output: dict = {"label": "SYNTHETIC PERFORMANCE DATA", "scales": []}
    base = datetime(2026, 9, 25, tzinfo=timezone.utc)
    image_buffer = io.BytesIO()
    Image.new("RGB", (640, 480), (80, 80, 80)).save(image_buffer, format="JPEG")
    image_bytes = image_buffer.getvalue()
    image_sha256 = hashlib.sha256(image_bytes).hexdigest()
    for count in (100, 1000, 5000):
        db = Database(root / f"events-{count}.sqlite3")
        events = EventRepository(db)
        snapshots = SnapshotRepository(db)
        inserts: list[float] = []
        snapshot_inserts: list[float] = []
        for i in range(count):
            event_id = f"SYN-P9C-{count:05d}-{i:05d}"
            timestamp = (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z")
            event = StoredEvent(id=event_id, timestamp=timestamp, track_id=i % 100, type=ComplianceEventType.NO_HELMET if i % 2 else ComplianceEventType.NO_VEST, confidence=.8, source_timestamp=float(i), source="synthetic:p9c", frame_id=i)
            _, ms = measure(lambda: events.insert(event))
            inserts.append(ms)
            relative_path = f"synthetic/{event_id}.jpg"
            target = root / "snapshots" / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(image_bytes)
            reference = SnapshotReference(snapshot_id=f"SNP-{event_id}", event_id=event_id, relative_path=relative_path, sha256=image_sha256, width=640, height=480, mime_type="image/jpeg", captured_at=timestamp)
            _, ms = measure(lambda: snapshots.insert(reference))
            snapshot_inserts.append(ms)
        query_times: list[float] = []
        detail_times: list[float] = []
        snapshot_times: list[float] = []
        stats_times: list[float] = []
        for i in range(50):
            page, ms = measure(lambda: events.query(EventQuery(limit=100, offset=(i * 17) % count)))
            assert page.total_count == count
            query_times.append(ms)
            event_id = f"SYN-P9C-{count:05d}-{(i * 97) % count:05d}"
            event, ms = measure(lambda: events.get(event_id))
            assert event and event.id == event_id
            detail_times.append(ms)
            snapshot, ms = measure(lambda: snapshots.get_by_event(event_id))
            assert snapshot and snapshot.event_id == event_id
            snapshot_times.append(ms)
            aggregate, ms = measure(lambda: events.statistics(EventQuery()))
            assert aggregate.total_count == count
            stats_times.append(ms)
        # The dashboard uses this same service graph; time its read path with
        # the isolated DB. AppTest page imports are measured separately below.
        runtime = build_runtime(database_path=db.path, snapshot_root=root / "snapshots")
        page, dashboard_ms = measure(lambda: runtime.query_service.list_events(limit=100))
        assert page.total_count == count
        output["scales"].append({"events": count, "insert": stats(inserts), "snapshot_metadata_insert": stats(snapshot_inserts), "list_query": stats(query_times), "detail_query": stats(detail_times), "snapshot_join_query": stats(snapshot_times), "statistics_query": stats(stats_times), "dashboard_query_ms": dashboard_ms, "database_bytes": db.path.stat().st_size})
        print(f"synthetic {count}: list p95={stats(query_times)['p95_ms']:.3f} ms, stats p95={stats(stats_times)['p95_ms']:.3f} ms", flush=True)
    target = root / "database-benchmark.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
