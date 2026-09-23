from pathlib import Path

from scripts.run_tracking_association_validation import (
    _configuration,
    _validate_frozen_contract,
    preflight,
)


def test_p5_3_validation_config_uses_frozen_assets_and_is_disabled() -> None:
    config_path = Path("configs/p5_3_validation.yaml")

    validation = _configuration(config_path)
    configs, paths = _validate_frozen_contract(validation)

    assert validation["execution_enabled"] is False
    assert validation["status"] == "PREPARED_NOT_EXECUTED"
    assert configs["inference"]["execution_enabled"] is False
    assert configs["tracker"]["implementation"]["version"] == "8.4.157"
    assert configs["association"]["thresholds"]["min_containment_ratio"] == 0.5
    assert set(paths) == {
        "inference_config",
        "tracker_config",
        "association_config",
    }


def test_p5_3_preflight_does_not_load_model_or_execute_inference() -> None:
    payload = preflight(Path("configs/p5_3_validation.yaml"))

    assert payload["validation_id"] == "P5-3"
    assert payload["execution_enabled"] is False
    assert payload["model_loaded"] is False
    assert payload["inference_executed"] is False
    assert payload["checkpoint_sha256"] == (
        "1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61"
    )
    assert payload["video_sha256"] == (
        "b630d851f9441aaaac23f75d8be3fa9307cc87201d1bb0972f4508356125b852"
    )
