"""UTF-8 YAML configuration loading with explicit failures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from utils.paths import config_path


class ConfigError(ValueError):
    """Raised when a configuration file cannot be loaded safely."""


def _resolve_config_path(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    if candidate.is_absolute() or candidate.parent != Path("."):
        return candidate.resolve()
    return config_path(candidate.name)


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load one UTF-8 YAML mapping and raise ``ConfigError`` on failure."""

    resolved = _resolve_config_path(path)
    if not resolved.is_file():
        raise ConfigError(f"Configuration file does not exist: {resolved}")

    try:
        with resolved.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except UnicodeDecodeError as exc:
        raise ConfigError(f"Configuration is not valid UTF-8: {resolved}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in configuration: {resolved}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read configuration: {resolved}: {exc}") from exc

    if data is None:
        raise ConfigError(f"Configuration is empty: {resolved}")
    if not isinstance(data, dict):
        raise ConfigError(
            f"Configuration root must be a mapping: {resolved}"
        )
    return data


def load_config(name_or_path: str | Path) -> dict[str, Any]:
    """Load a config by filename, stem, or explicit filesystem path."""

    return load_yaml(name_or_path)


def load_all_configs() -> dict[str, dict[str, Any]]:
    """Load all six Phase 0 YAML configuration files."""

    names = ("app", "dataset", "train", "inference", "tracker", "rules")
    return {name: load_config(name) for name in names}
