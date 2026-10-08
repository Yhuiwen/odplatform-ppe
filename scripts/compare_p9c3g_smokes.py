"""Require four one-cycle business signatures to match before long controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def signature(result: dict) -> dict:
    keys = ("cycles", "frames", "detections", "tracks", "associations",
            "unknown_associations", "events", "snapshot_files_verified",
            "alerts_delivered", "alerts_failed", "semantic_events")
    return {key: result[key] for key in keys}


def compare(roots: list[Path]) -> dict:
    results = [json.loads((root / "outputs/validation.json").read_text(encoding="utf-8")) for root in roots]
    if len(results) != 4 or {item["cell"] for item in results} != {"PP", "PR", "RP", "RR"}:
        raise AssertionError("four unique matrix smoke cells required")
    if not all(item["mode"] == "smoke" and item["pass"] for item in results):
        raise AssertionError("all smoke validations must pass")
    signatures = {item["cell"]: signature(item) for item in results}
    baseline = signatures["PP"]
    if not all(value == baseline for value in signatures.values()):
        raise AssertionError(f"matrix smoke semantic mismatch: {signatures}")
    if baseline["cycles"] != 1 or baseline["frames"] != 47:
        raise AssertionError("matrix smoke must be one complete real-frame cycle")
    return {"pass": True, "signatures": signatures}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_roots", nargs=4, type=Path)
    args = parser.parse_args()
    result = compare([path.resolve() for path in args.run_roots])
    target = Path(__file__).resolve().parents[1] / "artifacts/p9c3g/semantic-gate.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"pass": True, "signature": result["signatures"]["PP"]}))


if __name__ == "__main__":
    main()
