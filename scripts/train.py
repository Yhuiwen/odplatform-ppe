"""Authorization-gated entry point for EXP-001 YOLO11 training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.train_service import TrainService
from utils.config_loader import load_yaml


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute one authorized ODPlatform-PPE training run."
    )
    parser.add_argument(
        "--config",
        default="configs/training/exp001_baseline.yaml",
        help="Frozen canonical training configuration.",
    )
    parser.add_argument(
        "--authorization",
        default="configs/training/exp001_authorization.yaml",
        help="One-run authorization record.",
    )
    parser.add_argument(
        "--data-yaml",
        help="Execution-host data.yaml; defaults to the authorization record.",
    )
    parser.add_argument(
        "--weights",
        help="Execution-host weight path; defaults to the authorization record.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    result = TrainService().train(
        config,
        config_path=config_path,
        authorization_path=args.authorization,
        data_yaml_path=args.data_yaml,
        weights_path=args.weights,
    )
    print(
        json.dumps(
            {
                "experiment_id": result.experiment_id,
                "run_dir": str(result.run_dir),
                "log_path": str(result.log_path),
                "report_path": str(result.report_path),
                "best_checkpoint": (
                    str(result.best_checkpoint)
                    if result.best_checkpoint
                    else None
                ),
                "last_checkpoint": (
                    str(result.last_checkpoint)
                    if result.last_checkpoint
                    else None
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
