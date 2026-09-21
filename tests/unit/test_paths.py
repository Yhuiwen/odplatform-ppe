from pathlib import Path

from utils.paths import (
    ARTIFACTS_DIR,
    CONFIGS_DIR,
    DATA_DIR,
    LOGS_DIR,
    MODELS_DIR,
    PROJECT_ROOT,
    config_path,
    ensure_directory,
    find_project_root,
)


def test_project_root_can_be_detected_from_module_location() -> None:
    assert find_project_root(__file__) == PROJECT_ROOT
    assert PROJECT_ROOT.name == "odplatform-ppe"
    assert (PROJECT_ROOT / "pyproject.toml").is_file()


def test_standard_directories_are_exposed() -> None:
    assert CONFIGS_DIR == PROJECT_ROOT / "configs"
    assert DATA_DIR == PROJECT_ROOT / "data"
    assert MODELS_DIR == PROJECT_ROOT / "models"
    assert ARTIFACTS_DIR == PROJECT_ROOT / "artifacts"
    assert LOGS_DIR == ARTIFACTS_DIR / "logs"


def test_config_path_supports_stem_and_filename() -> None:
    assert config_path("app") == CONFIGS_DIR / "app.yaml"
    assert config_path("app.yaml") == CONFIGS_DIR / "app.yaml"


def test_ensure_directory_is_explicit(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "directory"
    assert not target.exists()
    assert ensure_directory(target) == target.resolve()
    assert target.is_dir()
