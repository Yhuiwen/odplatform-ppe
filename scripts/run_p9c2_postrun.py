"""Read-only post-long-run SQLite and Dashboard smoke validation."""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    validation = json.loads((run_root / "outputs/validation.json").read_text(encoding="utf-8"))
    expected = validation["events"]
    runtime = build_runtime(
        database_path=run_root / "database/events.sqlite3",
        snapshot_root=run_root / "snapshots",
    )
    pages = {
        "Overview": "0_Overview.py",
        "Event Explorer": "1_Event_Explorer.py",
        "Evidence Viewer": "2_Evidence_Viewer.py",
        "Statistics": "3_Statistics.py",
    }
    output: dict = {"run_root": str(run_root), "events": expected, "pages": {}}
    for name, filename in pages.items():
        app = AppTest.from_file(str(ROOT / "web/pages" / filename), default_timeout=30)
        app.session_state["_odplatform_dashboard_runtime"] = runtime
        started = perf_counter()
        app.run()
        elapsed_ms = (perf_counter() - started) * 1000
        exceptions = [str(item.message) for item in app.exception]
        metrics = {item.label: str(item.value) for item in app.metric}
        if name in {"Overview", "Statistics"}:
            assert str(expected) in metrics.values(), (name, expected, metrics)
        if name == "Evidence Viewer" and expected:
            assert metrics.get("Integrity") == "VERIFIED", metrics
        assert not exceptions, (name, exceptions)
        output["pages"][name] = {"load_ms": elapsed_ms, "exceptions": exceptions, "metrics": metrics}
    target = run_root / "outputs/dashboard-postrun.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run_root": str(run_root), "page_loads_ms": {k: round(v["load_ms"], 1) for k, v in output["pages"].items()}, "exceptions": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
