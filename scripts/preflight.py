"""Read-only checks for the frozen final-demo runtime."""

from __future__ import annotations

import hashlib
import os
import platform
import sys
from importlib.metadata import PackageNotFoundError, distributions, version
from pathlib import Path
from typing import Callable, Mapping
import re

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_SHA256 = "1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61"
INFERENCE_SHA256 = "0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c"
CHECKPOINT_SIZE = 5479891
REQUIRED_PACKAGES = (
    "torch", "torchvision", "ultralytics", "opencv-python", "numpy", "Pillow",
    "streamlit", "pytest", "pyttsx3", "plotly", "PyYAML", "lap",
)
CRITICAL_RUNTIME_PACKAGES = frozenset(name.lower() for name in REQUIRED_PACKAGES)


def _normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _installed_versions() -> dict[str, str]:
    return {
        _normalize_package_name(dist.metadata["Name"]): dist.version
        for dist in distributions()
        if dist.metadata.get("Name")
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _lock_versions(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    entries = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            name, pinned = line.split("==", 1)
            entries[name.lower()] = pinned
    return entries


def check_runtime(
    root: Path = ROOT,
    *,
    package_lookup: Callable[[str], str] = version,
    python_version: tuple[int, int, int] | None = None,
    os_name: str | None = None,
    architecture: str | None = None,
    expected_packages: Mapping[str, str] | None = None,
    installed_packages: Mapping[str, str] | None = None,
    checkpoint_sha256: str = CHECKPOINT_SHA256,
    checkpoint_size: int = CHECKPOINT_SIZE,
    inference_sha256: str = INFERENCE_SHA256,
) -> list[tuple[bool, str]]:
    """Inspect local state without opening devices or changing files."""

    root = Path(root)
    observed_python = python_version or tuple(sys.version_info[:3])
    observed_os = os_name or platform.system()
    observed_arch = architecture or platform.machine()
    lock = root / "locks/FINAL-DEMO-RUNTIME-001/requirements.txt"
    pins = dict(expected_packages) if expected_packages is not None else _lock_versions(lock)
    pins = {_normalize_package_name(name): pin for name, pin in pins.items()}
    installed = (
        {_normalize_package_name(name): pin for name, pin in installed_packages.items()}
        if installed_packages is not None else _installed_versions()
    )
    checks: list[tuple[bool, str]] = [
        (observed_python == (3, 12, 1), f"Python {'.'.join(map(str, observed_python))}"),
        (observed_os == "Windows", f"OS {observed_os}"),
        (observed_arch.lower() in {"amd64", "x86_64"}, f"architecture {observed_arch}"),
        (bool(pins), "FINAL-DEMO-RUNTIME-001 lock present"),
    ]
    for name in REQUIRED_PACKAGES:
        expected = pins.get(_normalize_package_name(name))
        try:
            actual = package_lookup(name)
        except PackageNotFoundError:
            actual = "MISSING"
        checks.append((expected is not None and actual == expected, f"{name} {actual} (expected {expected or 'UNLOCKED'})"))
    for name, expected in sorted(pins.items()):
        actual = installed.get(name)
        checks.append((actual == expected, f"lock {name} {actual or 'MISSING'} (expected {expected})"))
    for name in sorted(CRITICAL_RUNTIME_PACKAGES - pins.keys()):
        if name in installed:
            checks.append((False, f"critical runtime package {name} installed but absent from lock"))

    checkpoint = root / "models/checkpoints/EXP-001/best.pt"
    checks.append((checkpoint.is_file(), "checkpoint exists"))
    if checkpoint.is_file():
        checks.append((checkpoint.stat().st_size == checkpoint_size, "checkpoint size"))
        checks.append((_sha256(checkpoint) == checkpoint_sha256, "checkpoint SHA256"))

    inference = root / "configs/inference.yaml"
    checks.append((inference.is_file(), "inference config exists"))
    if inference.is_file():
        checks.append((_sha256(inference) == inference_sha256, "inference config SHA256"))
        content = inference.read_text(encoding="utf-8")
        checks.append(("policy: cpu_only" in content and "auto_download: false" in content, "CPU-only/no-download policy"))

    database_parent = root / "artifacts/events"
    snapshot_root = database_parent / "snapshots"
    checks.append((database_parent.is_dir() and os.access(database_parent, os.R_OK | os.W_OK), "demo database parent accessible"))
    checks.append((snapshot_root.is_dir() and os.access(snapshot_root, os.R_OK | os.W_OK), "snapshot root accessible"))
    for asset in (
        "artifacts/validation/P4C-1/input/construction-workers-public-domain.jpg",
        "artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4",
    ):
        checks.append(((root / asset).is_file(), f"demo asset {asset}"))
    return checks


def main() -> int:
    checks = check_runtime()
    for passed, label in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {label}")
    passed = all(result for result, _ in checks)
    print(f"FINAL DEMO PREFLIGHT: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
