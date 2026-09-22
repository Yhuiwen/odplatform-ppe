import json
from pathlib import Path

import pytest
import yaml
from PIL import Image

from services.val_service import CLASS_NAMES, ValService, replay, sha256
from utils.evaluation_metrics import average_precision, calculate_metrics, iou, match_boxes
from utils.paths import PROJECT_ROOT


def box(cid=0, confidence=None, xyxy=None):
    value = {"class_id": cid, "box": xyxy or [0.1, 0.1, 0.3, 0.3]}
    if confidence is not None:
        value["confidence"] = confidence
    return value


def record(truth, predictions, name="fixture.jpg"):
    return {"image": name, "truth": truth, "predictions": predictions}


def test_perfect_prediction_and_absent_classes():
    metrics = calculate_metrics([record([box()], [box(confidence=0.9)])], CLASS_NAMES)
    assert metrics["overall"]["precision"] == 1
    assert metrics["overall"]["recall"] == 1
    # 101-point envelope/trapezoid policy matches Ultralytics' 0.995 endpoint.
    assert metrics["overall"]["mAP50"] == pytest.approx(0.995)
    assert metrics["overall"]["mAP50-95"] == pytest.approx(0.995)
    assert [r["name"] for r in metrics["per_class"]] == CLASS_NAMES
    assert metrics["per_class"][1]["AP50"] is None
    assert metrics["confusion_matrix"]["counts"][0][0] == 1


def test_false_positive_before_true_positive_ap_regression():
    assert average_precision([False, True], 1) == pytest.approx(0.4975)
    assert average_precision([], 1) == 0
    assert average_precision([], 0) is None
    assert average_precision([True], 2) == pytest.approx(0.495)


def test_duplicate_prediction_is_not_a_second_true_positive():
    predictions = [box(confidence=0.9), box(confidence=0.8)]
    assert len(match_boxes([box()], predictions, 0.5)) == 1
    metrics = calculate_metrics([record([box()], predictions)], CLASS_NAMES)
    assert metrics["per_class"][0]["precision"] == 0.5
    assert metrics["per_class"][0]["recall"] == 1
    assert metrics["per_image"][0]["fp"] == 1
    assert metrics["error_counts"]["duplicate_or_unmatched_overlap"] == 1


def test_wrong_class_and_empty_images_have_correct_background_axes():
    metrics = calculate_metrics([
        record([box(0)], [box(1, 0.9)], "confusion.jpg"),
        record([], [box(2, 0.8)], "empty.jpg"),
        record([box(3)], [], "missed.jpg"),
    ], CLASS_NAMES)
    cm = metrics["confusion_matrix"]["counts"]
    assert cm[1][0] == 1
    assert cm[2][7] == 1
    assert cm[7][3] == 1
    assert metrics["overall"]["mAP50"] == 0
    assert metrics["per_class"][0]["fn"] == 1
    assert metrics["per_class"][1]["fp"] == 1


def test_operating_threshold_does_not_remove_predictions_from_ap():
    metrics = calculate_metrics([record([box()], [box(confidence=0.2)])], CLASS_NAMES)
    assert metrics["overall"]["mAP50"] == pytest.approx(0.995)
    assert metrics["overall"]["recall"] == 0
    assert metrics["error_counts"] == {"missed_ground_truth": 1}


def test_iou_threshold_sweep_and_small_object_recall():
    truth = box(xyxy=[0.1, 0.1, 0.15, 0.15])
    pred = box(confidence=0.9, xyxy=[0.1, 0.1, 0.14, 0.15])
    assert iou(truth["box"], pred["box"]) == pytest.approx(0.8)
    metrics = calculate_metrics([record([truth], [pred])], CLASS_NAMES)
    assert metrics["overall"]["mAP50"] > metrics["overall"]["mAP50-95"]
    assert metrics["small_object_recall"]["small"] == {"targets": 1, "tp": 1, "recall": 1}


@pytest.mark.parametrize("bad", [
    box(7, 0.9), box(0, float("nan")), box(0, 0.9, [0, 0, 0, 1]),
])
def test_malformed_predictions_rejected(bad):
    with pytest.raises(ValueError):
        calculate_metrics([record([], [bad])], CLASS_NAMES)


def test_duplicate_records_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        calculate_metrics([record([], []), record([], [])], CLASS_NAMES)


@pytest.fixture
def evaluation_project(tmp_path):
    root = tmp_path
    dataset = root / "data/processed/fixture"
    (dataset / "test/images").mkdir(parents=True)
    (dataset / "test/labels").mkdir(parents=True)
    (dataset / "metadata").mkdir()
    Image.new("RGB", (32, 32)).save(dataset / "test/images/one.png")
    (dataset / "test/labels/one.txt").write_text("0 0.2 0.2 0.2 0.2\n")
    (dataset / "data.yaml").write_text(yaml.safe_dump({"names": dict(enumerate(CLASS_NAMES))}))
    (dataset / "metadata/class_mapping.json").write_text("{}")
    for name in ("best.pt", "training.yaml", "mapping.yaml", "contract.yaml"):
        (root / name).write_text("synthetic test fixture")

    def identity(path):
        return {"path": path.relative_to(root).as_posix(), "sha256": sha256(path)}

    entries = [p for p in dataset.rglob("*") if p.is_file()]
    checksums = dataset / "metadata/checksums.sha256"
    checksums.write_text("".join(f"{sha256(p)}  {p.relative_to(dataset).as_posix()}\n" for p in entries))
    manifest = {"experiment_id": "EXP-001", "best_checkpoint": identity(root / "best.pt"),
                "configuration": identity(root / "training.yaml"), "dataset": {
                    "classes": CLASS_NAMES, "splits": {"test": 1},
                    "processed_data_yaml": identity(dataset / "data.yaml"),
                    "mapping_contract": identity(root / "mapping.yaml"),
                    "training_contract": identity(root / "contract.yaml"),
                    "class_mapping": identity(dataset / "metadata/class_mapping.json"),
                    "fingerprint": {"processed_manifest_sha256": sha256(checksums)}}}
    (root / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    config = yaml.safe_load((PROJECT_ROOT / "configs/evaluation/exp001_test.yaml").read_text())
    config.update(model_manifest="manifest.yaml", dataset_root="data/processed/fixture", expected_images=1)
    return root, config


class FixturePredictor:
    names = CLASS_NAMES
    runtime = {"backend": "synthetic-test-fixture"}

    def __init__(self, checkpoint, config, output):
        pass

    def __call__(self, image):
        return [box(confidence=0.9)]


def test_pipeline_preserves_inputs_replays_and_refuses_overwrite(evaluation_project, monkeypatch):
    root, config = evaluation_project
    # Plot rendering is covered by the real run; this test exercises integrity/replay.
    monkeypatch.setattr("services.val_service.render_confusion", lambda *args: None)
    result = ValService().evaluate(config, project_root=root, predictor_factory=FixturePredictor)
    assert result["run_record"]["integrity_unchanged"]
    assert replay(result["output_path"])["overall"]["recall"] == 1
    with pytest.raises(ValueError, match="new directory"):
        ValService().evaluate(config, project_root=root, predictor_factory=FixturePredictor)
    predictions = Path(result["output_path"]) / "predictions.json"
    predictions.write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        replay(result["output_path"])


@pytest.mark.parametrize("target", ["best.pt", "data/processed/fixture/test/labels/one.txt"])
def test_tampered_inputs_abort_before_loading_model(evaluation_project, target):
    root, config = evaluation_project
    (root / target).write_text("tampered")
    with pytest.raises(ValueError, match="mismatch"):
        ValService().evaluate(config, project_root=root, predictor_factory=lambda *args: pytest.fail("model loaded"))
    assert not (root / config["output_path"]).exists()


@pytest.mark.parametrize("path", ["data/processed/fixture/output", "experiments/runs/EXP-001", "../escape"])
def test_output_cannot_overwrite_protected_locations(evaluation_project, path):
    root, config = evaluation_project
    config["output_path"] = path
    with pytest.raises(ValueError, match="new directory"):
        ValService().evaluate(config, project_root=root)


def test_failure_is_recorded_and_does_not_claim_completed(evaluation_project):
    root, config = evaluation_project
    def fail(*args):
        raise RuntimeError("fixture backend failed")
    with pytest.raises(RuntimeError, match="fixture backend failed"):
        ValService().evaluate(config, project_root=root, predictor_factory=fail)
    context = json.loads((root / config["output_path"] / "run_record.json").read_text())
    assert context["status"] == "FAILED"
    assert context["integrity_unchanged"] is True


def test_empty_config_fails_explicitly():
    with pytest.raises(ValueError, match="Missing evaluation fields"):
        ValService().evaluate({})


def test_last_checkpoint_selection_and_tampering(evaluation_project, monkeypatch):
    root, config = evaluation_project
    last = root / 'last.pt'
    last.write_text('synthetic last checkpoint')
    manifest_path = root / config['model_manifest']
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest['artifact_inventory'] = [{'path': 'last.pt', 'sha256': sha256(last)}]
    manifest_path.write_text(yaml.safe_dump(manifest))
    config['checkpoint_role'] = 'last'
    monkeypatch.setattr('services.val_service.render_confusion', lambda *args: None)
    def factory(checkpoint, config, output):
        assert checkpoint == last
        return FixturePredictor(checkpoint, config, output)
    result = ValService().evaluate(config, project_root=root, predictor_factory=factory)
    assert result['run_record']['checkpoint_sha256'] == sha256(last)
    config['output_path'] += '-tampered'
    last.write_text('tampered')
    with pytest.raises(ValueError, match='Frozen identity mismatch'):
        ValService().evaluate(config, project_root=root, predictor_factory=factory)


def test_ap_matches_pinned_ultralytics_reference_when_available(tmp_path, monkeypatch):
    monkeypatch.setenv('YOLO_CONFIG_DIR', str(tmp_path))
    pytest.importorskip('torch')
    metrics_module = pytest.importorskip('ultralytics.utils.metrics')
    import numpy as np
    for flags, targets in [([True], 2), ([False, True], 1), ([True, False, True], 3),
                           ([False, False], 2), ([True, True], 2)]:
        tp = np.cumsum(flags, dtype=float)
        precision = tp / np.arange(1, len(flags) + 1)
        recall = tp / targets
        reference, _, _ = metrics_module.compute_ap(recall, precision)
        assert average_precision(flags, targets) == pytest.approx(reference, abs=1e-12)


def test_mutating_backend_marks_run_failed_integrity(evaluation_project):
    root, config = evaluation_project
    def mutate(checkpoint, config, output):
        checkpoint.write_text("changed by synthetic bad backend")
        raise RuntimeError("synthetic failure")
    with pytest.raises(RuntimeError, match="changed protected"):
        ValService().evaluate(config, project_root=root, predictor_factory=mutate)
    context = json.loads((root / config["output_path"] / "run_record.json").read_text())
    assert context["status"] == "FAILED_INTEGRITY"
    assert context["integrity_unchanged"] is False


def test_class_order_mismatch_refuses_inference(evaluation_project):
    root, config = evaluation_project
    class WrongNames(FixturePredictor):
        names = list(reversed(CLASS_NAMES))
        def __call__(self, image):
            pytest.fail("Inference should not start")
    with pytest.raises(ValueError, match="class order"):
        ValService().evaluate(config, project_root=root, predictor_factory=WrongNames)
