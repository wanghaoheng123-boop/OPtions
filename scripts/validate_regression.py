#!/usr/bin/env python3
"""
Structural regression for StrategyBacktester (no FastAPI).

Runs iron-condor backtest per ticker and asserts required JSON keys exist.
Uses live yfinance data — expect occasional failures from rate limits; retry
or reduce the ticker list.

Usage:
  python scripts/validate_regression.py
  python scripts/validate_regression.py --tickers SPY --days 400
"""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

REQUIRED_KEYS = (
    "ticker",
    "win_rate_percent",
    "profit_factor",
    "max_drawdown",
    "max_drawdown_percent",
    "trade_log",
    "tc_summary",
    "premium_model",
    "barrier_hits",
)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--tickers", default="SPY,QQQ", help="Comma-separated symbols")
    p.add_argument("--days", type=int, default=400)
    args = p.parse_args()

    from skills.backtester import StrategyBacktester

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    failed = []
    for t in tickers:
        try:
            out = StrategyBacktester.run_historical_backtest(
                t, "iron_condor", days=args.days
            )
        except Exception as e:
            failed.append((t, f"exception: {e}"))
            continue
        if out.get("error"):
            failed.append((t, out["error"]))
            continue
        missing = [k for k in REQUIRED_KEYS if k not in out]
        if missing:
            failed.append((t, f"missing keys: {missing}"))
            continue
        if not isinstance(out["trade_log"], list):
            failed.append((t, "trade_log not a list"))
            continue
        if not out["trade_log"]:
            failed.append((t, "empty trade_log"))
            continue
        tc = out.get("tc_summary") or {}
        if "total_cost" not in tc:
            failed.append((t, "tc_summary.total_cost missing"))
            continue
        print(f"OK {t} trades={len(out['trade_log'])} wr={out['win_rate_percent']}%")

    if failed:
        for t, msg in failed:
            print(f"FAIL {t}: {msg}", file=sys.stderr)
        raise SystemExit(1)
    print("REGRESSION OK")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
