"""Project path discovery without import-time directory creation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def find_project_root(start: str | Path | None = None) -> Path:
    """Return the nearest parent containing the project markers."""

    candidate = Path(start) if start is not None else Path(__file__)
    candidate = candidate.expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent

    markers = ("pyproject.toml", "docs/00_PROJECT_CHARTER.md")
    for directory in (candidate, *candidate.parents):
        if all((directory / marker).is_file() for marker in markers):
            return directory

    raise FileNotFoundError(
        f"Could not locate ODPlatform-PPE project root from {candidate}"
    )


PROJECT_ROOT = find_project_root()
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
LOGS_DIR = ARTIFACTS_DIR / "logs"
EVENTS_DIR = ARTIFACTS_DIR / "events"


def config_path(name: str, *, must_exist: bool = False) -> Path:
    """Resolve a YAML file under ``configs/``."""

    path = Path(name)
    if path.suffix.lower() not in {".yaml", ".yml"}:
        path = path.with_suffix(".yaml")
    resolved = path if path.is_absolute() else CONFIGS_DIR / path
    if must_exist and not resolved.is_file():
        raise FileNotFoundError(resolved)
    return resolved


def ensure_directory(path: str | Path) -> Path:
    """Create and return one directory when explicitly requested."""

    resolved = Path(path).expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_directories(paths: Iterable[str | Path]) -> tuple[Path, ...]:
    """Create and return several directories when explicitly requested."""

    return tuple(ensure_directory(path) for path in paths)


def ensure_project_directories() -> tuple[Path, ...]:
    """Create the runtime directories required by the project."""

    return ensure_directories(
        (
            DATA_DIR,
            MODELS_DIR,
            ARTIFACTS_DIR,
            EVENTS_DIR / "snapshots",
            EVENTS_DIR / "videos",
            LOGS_DIR,
        )
    )
