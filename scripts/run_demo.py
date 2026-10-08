"""Safe final-demo entry point: validate, then print the launch command."""

from __future__ import annotations

import argparse

try:
    from scripts.preflight import main as run_preflight
except ModuleNotFoundError:
    from preflight import main as run_preflight


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate final-demo readiness")
    parser.add_argument("--check", action="store_true", help="preflight only")
    args = parser.parse_args()
    result = run_preflight()
    if result != 0:
        return result
    if not args.check:
        print("Launch: .venv-final-demo\\Scripts\\python.exe -m streamlit run web/Home.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
