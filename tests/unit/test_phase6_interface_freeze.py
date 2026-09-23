from utils.config_loader import load_config


def test_phase6_rules_are_frozen_and_single_frame_safe() -> None:
    rules = load_config("rules")["rules"]

    assert rules["phase"] == 6
    assert rules["subphase"] == "6-0"
    assert rules["status"] == "frozen"
    assert rules["execution_enabled"] is True
    assert rules["event_types"] == [
        "NO_HELMET",
        "NO_VEST",
        "PPE_UNKNOWN",
    ]
    assert rules["temporal_confirmation"] == {
        "enabled": True,
        "min_consecutive_frames": 5,
        "min_duration_seconds": 1.0,
    }
    assert rules["recovery"]["compliant_frames"] == 5
    assert rules["cooldown"]["seconds"] == 30
    assert rules["errors"]["single_frame_confirmation"] is False
    assert rules["errors"]["forced_unknown_assignment"] is False


def test_phase6_output_contract_is_frozen() -> None:
    rules = load_config("rules")["rules"]

    assert rules["output"] == {
        "schema": "core/schemas/compliance.py",
        "result_type": "ComplianceResult",
        "event_type": "ComplianceEvent",
        "wire_fields": ["type", "track_id", "confidence", "timestamp"],
    }
