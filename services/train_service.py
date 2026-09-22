"""Authorization-gated YOLO11 training service."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from utils.paths import PROJECT_ROOT


class TrainingAuthorizationError(PermissionError):
    """Raised when no valid one-run authorization is present."""


class TrainingConfigurationError(ValueError):
    """Raised when frozen training inputs are missing or inconsistent."""


@dataclass(frozen=True)
class TrainingResult:
    """Paths and status produced by one training invocation."""

    experiment_id: str
    run_dir: Path
    log_path: Path
    report_path: Path
    best_checkpoint: Path | None
    last_checkpoint: Path | None


Runner = Callable[[dict[str, Any]], Any]


_REQUIRED_FIELDS = {
    "experiment_id",
    "dataset",
    "dataset_contract",
    "processed_dataset",
    "model",
    "model_version",
    "weights",
    "class_count",
    "classes",
    "epochs",
    "imgsz",
    "batch",
    "optimizer",
    "learning_rate",
    "lr_strategy",
    "lr_final_fraction",
    "weight_decay",
    "warmup_epochs",
    "patience",
    "augmentation",
    "seed",
    "device",
    "workers",
    "deterministic",
    "amp",
    "cache",
    "output_path",
    "logs_path",
    "reports_path",
    "checkpoint_path",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml_mapping(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise TrainingConfigurationError(f"{label} does not exist: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise TrainingConfigurationError(
            f"Could not parse {label}: {path}"
        ) from exc
    if not isinstance(data, dict):
        raise TrainingConfigurationError(f"{label} must be a YAML mapping")
    return data


def _resolve_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def _require_empty_destination(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise TrainingConfigurationError(
            f"Output destination is not empty: {path}"
        )


def _extract_class_names(data: dict[str, Any]) -> list[str]:
    names = data.get("names")
    if isinstance(names, dict):
        ordered = [names[key] for key in sorted(names, key=int)]
    elif isinstance(names, list):
        ordered = names
    else:
        raise TrainingConfigurationError("data.yaml must define names")
    return [str(name) for name in ordered]


class TrainService:
    """Execute one configuration-bound training run after explicit approval."""

    def train(
        self,
        config: dict[str, Any],
        *,
        config_path: str | Path | None = None,
        authorization_path: str | Path | None = None,
        data_yaml_path: str | Path | None = None,
        weights_path: str | Path | None = None,
        runner: Runner | None = None,
    ) -> TrainingResult:
        missing = sorted(_REQUIRED_FIELDS.difference(config))
        if missing:
            raise TrainingConfigurationError(
                f"Training config is missing required fields: {missing}"
            )

        resolved_config_path = _resolve_path(
            config_path or "configs/training/exp001_baseline.yaml"
        )
        resolved_authorization = _resolve_path(
            authorization_path
            or "configs/training/exp001_authorization.yaml"
        )
        authorization = _load_yaml_mapping(
            resolved_authorization,
            "training authorization",
        )

        if authorization.get("status") != "GRANTED":
            raise TrainingAuthorizationError(
                "Training authorization is not GRANTED"
            )
        if authorization.get("training_execution_enabled") is not True:
            raise TrainingAuthorizationError(
                "Training execution is not enabled by the authorization record"
            )
        if authorization.get("experiment_id") != config["experiment_id"]:
            raise TrainingAuthorizationError(
                "Training authorization experiment ID does not match config"
            )

        config_sha256 = _sha256_file(resolved_config_path)
        if authorization.get("configuration_sha256") != config_sha256:
            raise TrainingAuthorizationError(
                "Canonical configuration hash does not match authorization"
            )
        if config.get("status") != "CONFIGURATION_FROZEN":
            raise TrainingConfigurationError(
                "Canonical training configuration is not frozen"
            )

        resolved_data_yaml = _resolve_path(
            data_yaml_path or authorization.get("data_yaml_path", "")
        )
        if not resolved_data_yaml.is_file():
            raise TrainingConfigurationError(
                f"Processed data.yaml does not exist: {resolved_data_yaml}"
            )
        dataset = _load_yaml_mapping(resolved_data_yaml, "processed data.yaml")
        dataset_classes = _extract_class_names(dataset)
        expected_classes = [str(value) for value in config["classes"]]
        if dataset_classes != expected_classes:
            raise TrainingConfigurationError(
                "Processed data.yaml class order does not match frozen config"
            )
        if int(dataset.get("nc", -1)) != int(config["class_count"]):
            raise TrainingConfigurationError(
                "Processed data.yaml class count does not match frozen config"
            )

        resolved_weights = _resolve_path(
            weights_path or authorization.get("weight_path", "")
        )
        if not resolved_weights.is_file():
            raise TrainingConfigurationError(
                f"Initialization weight does not exist: {resolved_weights}"
            )
        expected_weight_sha256 = authorization.get("weight_sha256")
        if expected_weight_sha256 != _sha256_file(resolved_weights):
            raise TrainingAuthorizationError(
                "Initialization weight SHA256 does not match authorization"
            )

        augmentation = _load_yaml_mapping(
            _resolve_path(config["augmentation"]),
            "augmentation config",
        )
        augmentation_parameters = augmentation.get("augmentation", {}).get(
            "parameters",
            {},
        )
        if not isinstance(augmentation_parameters, dict):
            raise TrainingConfigurationError(
                "Augmentation parameters must be a mapping"
            )
        color_jitter = augmentation_parameters.get("color_jitter")
        if color_jitter is None:
            raise TrainingConfigurationError(
                "Augmentation config must define color_jitter"
            )

        run_dir = _resolve_path(config["output_path"])
        log_dir = _resolve_path(config["logs_path"])
        report_dir = _resolve_path(config["reports_path"])
        checkpoint_dir = _resolve_path(config["checkpoint_path"])
        for destination in (run_dir, log_dir, report_dir, checkpoint_dir):
            _require_empty_destination(destination)

        log_dir.mkdir(parents=True, exist_ok=True)
        report_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(timezone.utc).isoformat()
        log_path = log_dir / "training.log"
        report_path = report_dir / "run_record.yaml"

        context = {
            "schema_version": "training-execution-context-v1",
            "status": "STARTED",
            "experiment_id": config["experiment_id"],
            "started_at_utc": started_at,
            "configuration_path": str(resolved_config_path),
            "configuration_sha256": config_sha256,
            "authorization_path": str(resolved_authorization),
            "data_yaml_path": str(resolved_data_yaml),
            "weights_path": str(resolved_weights),
            "weights_sha256": expected_weight_sha256,
            "run_dir": str(run_dir),
            "log_path": str(log_path),
        }
        report_path.write_text(
            yaml.safe_dump(context, sort_keys=False),
            encoding="utf-8",
        )

        params: dict[str, Any] = {
            "data": str(resolved_data_yaml),
            "epochs": config["epochs"],
            "imgsz": config["imgsz"],
            "batch": config["batch"],
            "optimizer": config["optimizer"],
            "lr0": config["learning_rate"],
            "lrf": config["lr_final_fraction"],
            "cos_lr": config["lr_strategy"] == "cosine",
            "weight_decay": config["weight_decay"],
            "warmup_epochs": config["warmup_epochs"],
            "patience": config["patience"],
            "seed": config["seed"],
            "deterministic": config["deterministic"],
            "device": config["device"],
            "workers": config["workers"],
            "amp": config["amp"],
            "cache": config["cache"],
            "project": str(run_dir.parent),
            "name": run_dir.name,
            "exist_ok": False,
            "pretrained": True,
            "plots": True,
            "save": True,
            "val": True,
            "scale": augmentation_parameters.get("image_scale"),
            "translate": augmentation_parameters.get("translation"),
            "fliplr": augmentation_parameters.get("horizontal_flip"),
            # Ultralytics exposes color jitter as separate HSV gains.
            "hsv_h": color_jitter,
            "hsv_s": color_jitter,
            "hsv_v": color_jitter,
            "mosaic": augmentation_parameters.get("mosaic"),
            "close_mosaic": augmentation_parameters.get("close_mosaic"),
        }

        active_runner = runner or _run_ultralytics
        try:
            active_runner(
                {
                    "weights": str(resolved_weights),
                    "params": params,
                }
            )
        except Exception as exc:
            context["status"] = "FAILED"
            context["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            context["error"] = f"{type(exc).__name__}: {exc}"
            report_path.write_text(
                yaml.safe_dump(context, sort_keys=False),
                encoding="utf-8",
            )
            raise

        if not run_dir.is_dir():
            raise TrainingConfigurationError(
                f"Training runner did not create run directory: {run_dir}"
            )

        config_snapshot = run_dir / "exp001_baseline.frozen.yaml"
        shutil.copy2(resolved_config_path, config_snapshot)
        context["status"] = "COMPLETED"
        context["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        context["configuration_snapshot"] = str(config_snapshot)
        report_path.write_text(
            yaml.safe_dump(context, sort_keys=False),
            encoding="utf-8",
        )

        best_source = run_dir / "weights" / "best.pt"
        last_source = run_dir / "weights" / "last.pt"
        best_checkpoint = None
        last_checkpoint = None
        if best_source.is_file():
            best_checkpoint = checkpoint_dir / "best.pt"
            shutil.copy2(best_source, best_checkpoint)
        if last_source.is_file():
            last_checkpoint = checkpoint_dir / "last.pt"
            shutil.copy2(last_source, last_checkpoint)

        return TrainingResult(
            experiment_id=str(config["experiment_id"]),
            run_dir=run_dir,
            log_path=log_path,
            report_path=report_path,
            best_checkpoint=best_checkpoint,
            last_checkpoint=last_checkpoint,
        )


def _run_ultralytics(payload: dict[str, Any]) -> Any:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise TrainingConfigurationError(
            "ultralytics is required to execute training"
        ) from exc

    model = YOLO(payload["weights"])
    return model.train(**payload["params"])
