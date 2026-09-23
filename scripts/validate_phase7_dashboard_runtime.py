"""Execute the four Streamlit dashboard pages against one P7-5 run."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from streamlit.testing.v1 import AppTest

from web.dashboard_support import build_runtime

__all__ = ["main", "validate_dashboard_runtime"]

PAGES = (
    ("Overview", "web/pages/0_Overview.py"),
    ("Event Explorer", "web/pages/1_Event_Explorer.py"),
    ("Evidence Viewer", "web/pages/2_Evidence_Viewer.py"),
    ("Statistics", "web/pages/3_Statistics.py"),
)


def _exception_text(element: Any) -> str:
    value = getattr(element, "value", element)
    return str(value)


def validate_dashboard_runtime(
    *,
    runtime_validation_path: str | Path,
) -> dict[str, Any]:
    """Run each page with AppTest and persist structured results."""

    summary_path = Path(runtime_validation_path).expanduser().resolve()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    run_root = Path(summary["artifacts"]["run_root"]).expanduser().resolve()
    database_path = Path(summary["persistence"]["database"]).expanduser().resolve()
    snapshot_root = run_root / "snapshots"
    if not database_path.is_file():
        raise FileNotFoundError(f"runtime database does not exist: {database_path}")
    if not snapshot_root.is_dir():
        raise FileNotFoundError(f"snapshot root does not exist: {snapshot_root}")

    runtime = build_runtime(
        database_path=database_path,
        snapshot_root=snapshot_root,
    )
    results: list[dict[str, Any]] = []
    for page_name, relative_path in PAGES:
        page_path = Path(relative_path).expanduser().resolve()
        app = AppTest.from_file(str(page_path), default_timeout=30)
        app.session_state["_odplatform_dashboard_runtime"] = runtime
        app.run()
        exceptions = [_exception_text(item) for item in app.exception]
        titles = [str(item.value) for item in app.title]
        results.append(
            {
                "page": page_name,
                "path": relative_path,
                "status": "PASS" if not exceptions else "FAILED",
                "title": titles[0] if titles else None,
                "exceptions": exceptions,
            }
        )

    payload = {
        "validation_id": "P7-5-DASHBOARD",
        "validated_at": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "runtime_validation": str(summary_path),
        "database": summary["persistence"]["database"],
        "snapshot_root": f"{summary['artifacts']['run_root']}/snapshots",
        "pages": results,
        "status": (
            "PASS"
            if len(results) == len(PAGES)
            and all(item["status"] == "PASS" for item in results)
            else "FAILED"
        ),
    }
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    latest_path = summary_path.parent / "dashboard_validation.json"
    run_path = run_root / "dashboard_validation.json"
    latest_path.write_text(serialized + "\n", encoding="utf-8")
    run_path.write_text(serialized + "\n", encoding="utf-8")
    return payload


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the Phase 7 Streamlit pages with AppTest."
    )
    parser.add_argument(
        "--runtime-validation",
        default="artifacts/validation/P7-5/runtime_validation.json",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    payload = validate_dashboard_runtime(
        runtime_validation_path=args.runtime_validation,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
