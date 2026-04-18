#!/usr/bin/env python3
"""
Phase 6B: drive POST /api/backtest/batch and enforce institutional gates.

Gates match backend batch summary / critic-style thresholds:
  - win_rate_percent >= 75
  - profit_factor >= 1.2
  - max_drawdown < 20  (percent; uses max_drawdown alias from StrategyBacktester)

Usage (no server; in-process FastAPI TestClient):
  python scripts/validate_batch_backtest.py --tickers SPY --days 400

With running API (e.g. uvicorn main:app in backend/):
  python scripts/validate_batch_backtest.py --url http://127.0.0.1:8000 --tickers SPY,QQQ

Exit code 0 if at least --min-pass tickers pass all gates; else 1.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GATES = {
    "win_rate_percent": 75.0,
    "profit_factor": 1.2,
    "max_drawdown": 20.0,
}


def passes_institutional(row: Dict[str, Any]) -> bool:
    if not row or row.get("error"):
        return False
    wr = float(row.get("win_rate_percent") or 0)
    pf = float(row.get("profit_factor") or 0)
    dd = row.get("max_drawdown")
    if dd is None:
        dd = row.get("max_drawdown_percent")
    if dd is None:
        return False
    dd = float(dd)
    return wr >= GATES["win_rate_percent"] and pf >= GATES["profit_factor"] and dd < GATES["max_drawdown"]


def _batch_in_process(payload: Dict[str, Any]) -> Dict[str, Any]:
    backend_dir = os.path.join(ROOT, "backend")
    prev_cwd = os.getcwd()
    try:
        os.chdir(backend_dir)
        from fastapi.testclient import TestClient

        import importlib.util

        main_path = os.path.join(backend_dir, "main.py")
        spec = importlib.util.spec_from_file_location("terminal_main", main_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        client = TestClient(mod.app)
        resp = client.post("/api/backtest/batch", json=payload)
        resp.raise_for_status()
        return resp.json()
    finally:
        os.chdir(prev_cwd)


def _batch_http(base_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/backtest/batch"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {body}") from e


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate batch backtest institutional gates.")
    parser.add_argument(
        "--tickers",
        default="SPY",
        help="Comma-separated tickers (need enough --days for OOS, e.g. 400+).",
    )
    parser.add_argument("--strategy", default="iron_condor")
    parser.add_argument("--days", type=int, default=400)
    parser.add_argument(
        "--min-pass",
        type=int,
        default=1,
        help="Minimum number of tickers that must pass all gates (default 1).",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Base URL of running API; if omitted, uses in-process TestClient.",
    )
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    payload = {"tickers": tickers, "strategy": args.strategy, "days": args.days}

    if args.url:
        data = _batch_http(args.url, payload)
    else:
        data = _batch_in_process(payload)

    results: List[Dict[str, Any]] = data.get("results") or []
    summary: Dict[str, Any] = data.get("summary") or {}

    print(
        f"{'Ticker':<8} {'WR%':>8} {'PF':>7} {'MaxDD%':>8} "
        f"{'Verdict':>8} {'Gates':>6}"
    )
    for row in results:
        t = row.get("_ticker", "?")
        wr = row.get("win_rate_percent")
        pf = row.get("profit_factor")
        dd = row.get("max_drawdown", row.get("max_drawdown_percent"))
        verdict = row.get("verdict", "")
        gate = "PASS" if passes_institutional(row) else "FAIL"
        wr_s = f"{wr:.1f}" if isinstance(wr, (int, float)) else str(wr)
        pf_s = f"{pf:.2f}" if isinstance(pf, (int, float)) else str(pf)
        dd_s = f"{dd:.2f}" if isinstance(dd, (int, float)) else str(dd)
        print(f"{t:<8} {wr_s:>8} {pf_s:>7} {dd_s:>8} {str(verdict):>8} {gate:>6}")

    print("summary:", summary)

    n_pass = sum(1 for row in results if passes_institutional(row))
    print(
        f"institutional_pass: {n_pass}/{len(results)} "
        f"(required >= {args.min_pass}; gates WR>={GATES['win_rate_percent']}, "
        f"PF>={GATES['profit_factor']}, MaxDD<{GATES['max_drawdown']})"
    )

    if n_pass < args.min_pass:
        print("VALIDATION FAILED", file=sys.stderr)
        raise SystemExit(1)
    print("VALIDATION OK")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
