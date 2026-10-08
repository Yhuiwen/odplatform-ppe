"""Regenerate the local 416px OpenVINO graph from the frozen PPE checkpoint."""

from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.paths import PROJECT_ROOT


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    config_path = PROJECT_ROOT / "configs/inference_cpu_fast.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    inference = config["inference"]
    source = PROJECT_ROOT / inference["model"]["path"]
    target = PROJECT_ROOT / inference["model"]["export_path"]
    if not source.is_file() or sha256(source) != inference["model"]["sha256"]:
        raise RuntimeError("Frozen source checkpoint is missing or has a different SHA256")
    if target.exists():
        raise RuntimeError(f"Export already exists; preserve it or move it first: {target}")

    from ultralytics import YOLO

    with tempfile.TemporaryDirectory(prefix="ppe-openvino-export-") as directory:
        temporary_checkpoint = Path(directory) / "best.pt"
        shutil.copy2(source, temporary_checkpoint)
        exported = Path(YOLO(str(temporary_checkpoint), task="detect").export(
            format="openvino", imgsz=416, half=False, dynamic=False,
            nms=False, device="cpu",
        ))
        if exported.name != "best_openvino_model":
            raise RuntimeError(f"Unexpected export directory: {exported}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(exported, target)

    names = ("best.bin", "best.xml", "metadata.yaml")
    inference["model"]["export_sha256"] = {name: sha256(target / name) for name in names}
    config_path.write_text(
        "# Realtime CPU profile derived from the frozen checkpoint; see ADR-025.\n"
        + yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Exported {target} and updated its three file hashes in {config_path}")


if __name__ == "__main__":
    main()
