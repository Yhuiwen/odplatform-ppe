"""Execute or replay the frozen EXP-001 checkpoint comparison."""
import argparse
import json
from pathlib import Path

from services.model_comparison_service import replay_comparison, run_comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--config', type=Path, default=Path('configs/evaluation/exp001_comparison.yaml'))
    group.add_argument('--replay', type=Path)
    args = parser.parse_args()
    result = replay_comparison(args.replay) if args.replay else run_comparison(args.config)
    print(json.dumps({'status': result['status'], 'conditions_equal': result['conditions_equal'],
                      'last_minus_best': result['last_minus_best']}, indent=2))


if __name__ == '__main__':
    main()
