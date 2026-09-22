"""Evaluate frozen EXP-001 or replay saved results without running a model."""

import argparse
import json
from pathlib import Path

import yaml

from services.val_service import ValService, replay


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/evaluation/exp001_test.yaml")
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    if args.replay:
        metrics = replay(args.replay)
        print(json.dumps({"replay": "PASS", "overall": metrics["overall"]}, indent=2))
    else:
        config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
        result = ValService().evaluate(config)
        print(json.dumps({"output_path": result["output_path"],
                          "overall": result["metrics"]["overall"]}, indent=2))


if __name__ == "__main__":
    main()
