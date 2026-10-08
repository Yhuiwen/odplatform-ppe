"""Final-demo installation contract without installing packages during tests."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_package_metadata_declares_lock_as_full_runtime_entry() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    metadata = tomllib.loads(text)
    assert metadata["project"]["dependencies"] == []
    assert "pip install .` alone is not a complete application installation" in text
    assert (ROOT / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt").is_file()


def test_root_requirements_agree_with_frozen_opencv() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "opencv-python==5.0.0.93" in requirements.splitlines()


def test_project_packages_import_after_install() -> None:
    for name in ("core", "infra", "services", "utils", "web"):
        assert importlib.import_module(name) is not None
