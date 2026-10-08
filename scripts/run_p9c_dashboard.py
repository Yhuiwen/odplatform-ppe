"""Time existing Streamlit pages against isolated synthetic P9-C history."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.dashboard_support import build_runtime


def main() -> int:
    root = ROOT / "artifacts/p9c/synthetic-database"
    pages = {
        "Overview": "0_Overview.py",
        "Event Explorer": "1_Event_Explorer.py",
        "Evidence Viewer": "2_Evidence_Viewer.py",
        "Statistics": "3_Statistics.py",
    }
    result = {"label": "SYNTHETIC PERFORMANCE DATA", "scales": []}
    for count in (100, 1000, 5000):
        runtime = build_runtime(
            database_path=root / f"events-{count}.sqlite3",
            snapshot_root=root / "snapshots",
        )
        row = {"events": count, "pages": {}}
        for name, filename in pages.items():
            page_path = ROOT / "web/pages" / filename
            start = perf_counter()
            app = AppTest.from_file(str(page_path), default_timeout=30)
            app.session_state["_odplatform_dashboard_runtime"] = runtime
            app.run()
            elapsed_ms = (perf_counter() - start) * 1000
            exceptions = [str(item.message) for item in app.exception]
            assert not exceptions, (name, count, exceptions)
            metrics = {item.label: str(item.value) for item in app.metric}
            if name in {"Overview", "Statistics"}:
                assert str(count) in metrics.values(), (name, count, metrics)
            elif name == "Evidence Viewer":
                assert metrics.get("Integrity") == "VERIFIED", (name, count, metrics)
            row["pages"][name] = {
                "load_ms": elapsed_ms,
                "exceptions": exceptions,
                "metrics": metrics,
            }
        result["scales"].append(row)
        print(f"dashboard {count}: " + ", ".join(
            f"{name}={entry['load_ms']:.1f} ms"
            for name, entry in row["pages"].items()
        ), flush=True)
    target = root / "dashboard-benchmark.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
