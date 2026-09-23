import hashlib
from pathlib import Path

import pytest

from services.train_service import TrainService, TrainingAuthorizationError
from utils.config_loader import load_yaml
from utils.paths import PROJECT_ROOT


REPORT_PATH = (
    PROJECT_ROOT / "docs" / "reports" / "EXP-001_TRAINING_EXECUTION_REPORT.md"
)
AUTHORIZATION_PATH = (
    PROJECT_ROOT / "configs" / "training" / "exp001_authorization.yaml"
)
CONFIG_PATH = PROJECT_ROOT / "configs" / "training" / "exp001_baseline.yaml"
CHARTER_PATH = PROJECT_ROOT / "docs" / "00_PROJECT_CHARTER.md"
CURRENT_STATUS_PATH = PROJECT_ROOT / "docs" / "02_CURRENT_STATUS.md"
TEST_GATES_PATH = PROJECT_ROOT / "docs" / "05_TEST_GATES.md"
TRAINING_STRATEGY_PATH = PROJECT_ROOT / "docs" / "18_TRAINING_STRATEGY.md"

BEST_CHECKPOINT = (
    PROJECT_ROOT / "models" / "checkpoints" / "EXP-001" / "best.pt"
)
LAST_CHECKPOINT = (
    PROJECT_ROOT / "models" / "checkpoints" / "EXP-001" / "last.pt"
)
BEST_SHA256 = (
    "1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61"
)
LAST_SHA256 = (
    "acdd89c00cde096d609b596577572d7f4ed5bbcc7104babf0a1691c6cd8aba88"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_exp001_execution_report_records_complete_evidence() -> None:
    assert REPORT_PATH.is_file()
    report = REPORT_PATH.read_text(encoding="utf-8")
    required_fragments = [
        "Status: COMPLETED",
        "Experiment | `EXP-001`",
        "Configuration SHA256 | "
        "`df6c55ae6deb4697493a2c1e49ac171bff5c38edfd73ad968aa5e1e2cacff989`",
        "Weight SHA256 | "
        "`0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`",
        "Best epoch | `75`",
        "Stop reason | Early stopping after `20` epochs without improvement",
        "| all | 0.899 | 0.649 | 0.767 | 0.480 |",
        "`1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61`",
        "M-004 is satisfied",
        "M-005 remains `待实现`",
        "one-time, not used for training",
    ]
    for fragment in required_fragments:
        assert fragment in report, fragment


def test_exp001_authorization_is_consumed_and_cannot_run_again() -> None:
    authorization = load_yaml(AUTHORIZATION_PATH)
    assert authorization["status"] == "CONSUMED"
    assert authorization["training_execution_enabled"] is False
    assert authorization["authorization_status_at_execution"] == "GRANTED"
    assert authorization["authorization_consumed"] is True

    with pytest.raises(TrainingAuthorizationError):
        TrainService().train(
            load_yaml(CONFIG_PATH),
            config_path=CONFIG_PATH,
            authorization_path=AUTHORIZATION_PATH,
        )


def test_m004_and_m005_are_implemented() -> None:
    charter = CHARTER_PATH.read_text(encoding="utf-8")
    status = CURRENT_STATUS_PATH.read_text(encoding="utf-8")
    gates = TEST_GATES_PATH.read_text(encoding="utf-8")
    strategy = TRAINING_STRATEGY_PATH.read_text(encoding="utf-8")

    expected_m004 = (
        "| M-004 | YOLO11n 至少完成一轮可复现训练 | "
        "固定配置、数据和随机种子后至少完成一轮训练；产出权重、日志、配置快照"
        "和复现实验命令 | 已经实现 |"
    )
    assert expected_m004 in charter
    assert "M-004：已经实现" in status
    assert "M-005：已经实现" in status
    assert "P2-5.5-G9" in gates
    assert "EXP-001 TRAINING COMPLETED" in strategy


def test_local_exp001_checkpoints_match_recorded_hashes_when_present() -> None:
    if not BEST_CHECKPOINT.is_file() or not LAST_CHECKPOINT.is_file():
        pytest.skip("training checkpoints are Git-ignored and not present")

    assert BEST_CHECKPOINT.stat().st_size == 5_479_891
    assert LAST_CHECKPOINT.stat().st_size == 5_479_891
    assert _sha256(BEST_CHECKPOINT) == BEST_SHA256
    assert _sha256(LAST_CHECKPOINT) == LAST_SHA256
