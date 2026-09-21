from pathlib import Path

import pytest

from utils.config_loader import ConfigError, load_all_configs, load_yaml


EXPECTED_CONFIGS = {"app", "dataset", "train", "inference", "tracker", "rules"}
EXPECTED_CLASSES = ["person", "hardhat", "no_hardhat", "vest", "no_vest"]


def test_all_six_configs_parse() -> None:
    configs = load_all_configs()
    assert set(configs) == EXPECTED_CONFIGS
    assert all(isinstance(config, dict) for config in configs.values())


def test_v1_classes_are_strict_and_ordered() -> None:
    config = load_all_configs()["dataset"]
    classes = [config["classes"][index] for index in range(5)]
    assert classes == EXPECTED_CLASSES


def test_missing_configuration_has_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="does not exist"):
        load_yaml(tmp_path / "missing.yaml")


def test_invalid_yaml_has_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text("root: [unterminated\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_yaml(path)


def test_empty_or_non_mapping_yaml_is_rejected(tmp_path: Path) -> None:
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ConfigError, match="empty"):
        load_yaml(empty)

    sequence = tmp_path / "sequence.yaml"
    sequence.write_text("- item\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="root must be a mapping"):
        load_yaml(sequence)
