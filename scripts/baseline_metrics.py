#!/usr/bin/env python3
"""
Print optimization-loop metric commands and optionally run fast pytest.

Usage:
  python scripts/baseline_metrics.py          # print commands only
  python scripts/baseline_metrics.py --quick  # run pytest -m "not network" -q
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--quick",
        action="store_true",
        help="Run pytest -m \"not network\" -q from repo root",
    )
    args = p.parse_args()

    print("Optimization loop - capture baselines (see findings.md)\n")
    print("  python -m pytest tests/ -m \"not network\" -q")
    print("  python -m pytest tests/ -m network -q")
    print("  cd frontend && npm run test:e2e")
    print(
        "  curl -s -o NUL -w \"time_total=%{time_total}\\n\" -X POST "
        'http://127.0.0.1:8005/api/analyze -H "Content-Type: application/json" '
        '-d "{\\"ticker\\":\\"SPY\\",\\"days\\":126}"'
    )
    print("  python scripts/validate_regression.py --tickers SPY,QQQ --days 400")
    print("  python scripts/validate_batch_backtest.py --basket --days 400\n")

    if args.quick:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-m", "not network", "-q"],
            cwd=str(ROOT),
        )
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
