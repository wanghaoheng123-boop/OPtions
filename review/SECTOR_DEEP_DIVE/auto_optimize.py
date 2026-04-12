"""
Automated parameter search over the audited iron condor backtester (35-ticker universe).

Grid-search small, safe ranges for:
  volatility_ratio, profit_take_pct, stop_loss_mult, min_credit_pct_of_risk

Picks the combo that lexicographically maximizes:
  (WORKING count, MARGINAL count, int(total P&L))

Writes:
  AUTO_OPTIMIZE_GRID.json   — all evaluated combinations + per-combo aggregates
  AUTO_OPTIMIZE_BEST.json   — winning parameters + metrics
  recommended_params.json   — optional input for run_sector_deep_dive.py

Usage (repo root):
  python review/SECTOR_DEEP_DIVE/auto_optimize.py
  python review/SECTOR_DEEP_DIVE/auto_optimize.py --quick
  python review/SECTOR_DEEP_DIVE/auto_optimize.py --no-write-recommended
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from itertools import product
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from skills.backtester_audit import IronCondorBacktester

HERE = os.path.dirname(os.path.abspath(__file__))

SECTORS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "META", "GOOGL"],
    "Financials": ["JPM", "BAC", "GS", "MS", "V"],
    "Healthcare": ["UNH", "JNJ", "LLY", "ABBV", "MRK"],
    "Consumer_Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
    "Consumer_Staples": ["WMT", "KO", "PEP", "PG", "COST"],
    "Energy": ["XOM", "CVX", "COP", "EOG", "SLB"],
    "Industrials": ["BA", "CAT", "GE", "RTX", "UPS"],
}

DAYS = 252
NUM_CONTRACTS = 5


def classify(wr: float, pf: float, dd: float, n_trades: int) -> str:
    if n_trades == 0:
        return "NO_DATA"
    if wr >= 75 and pf >= 1.2 and dd < 20:
        return "WORKING"
    if wr < 60 or pf < 0.8 or dd > 20:
        return "FAILING"
    if wr >= 60 and pf >= 0.8:
        return "MARGINAL"
    return "FAILING"


def evaluate_combo(params: dict[str, Any]) -> dict[str, Any]:
    """Run all tickers with identical params; return aggregate metrics."""
    working = marginal = failing = no_data = 0
    total_pnl = 0.0
    dds: list[float] = []
    sharpes: list[float] = []

    for sector, tickers in SECTORS.items():
        for t in tickers:
            bt = IronCondorBacktester(
                use_adaptive=True,
                earnings_filter=True,
                num_contracts=NUM_CONTRACTS,
                **params,
            )
            r = bt.run(t, days=DAYS)
            if "error" in r:
                no_data += 1
                continue
            total_pnl += float(r.get("total_net_pnl") or 0)
            dds.append(float(r.get("max_drawdown_percent") or 0))
            sharpes.append(float(r.get("sharpe_ratio") or 0))
            c = classify(
                float(r["win_rate_percent"]),
                float(r["profit_factor"]),
                float(r["max_drawdown_percent"]),
                int(r["n_trades"]),
            )
            if c == "WORKING":
                working += 1
            elif c == "MARGINAL":
                marginal += 1
            elif c == "FAILING":
                failing += 1
            else:
                no_data += 1

    mean_dd = sum(dds) / len(dds) if dds else 0.0
    mean_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0.0
    return {
        "params": params,
        "working": working,
        "marginal": marginal,
        "failing": failing,
        "no_data": no_data,
        "total_pnl": round(total_pnl, 2),
        "mean_max_drawdown_pct": round(mean_dd, 2),
        "mean_sharpe": round(mean_sharpe, 3),
        "sort_key": (working, marginal, int(round(total_pnl))),
    }


def grids(quick: bool) -> list[dict[str, Any]]:
    if quick:
        vols = [1.3, 1.5]
        pts = [0.45, 0.55]
        sls = [1.0]
        mcs = [0.10]
    else:
        vols = [1.25, 1.4, 1.55]
        pts = [0.45, 0.5, 0.55]
        sls = [1.0, 1.25]
        mcs = [0.08, 0.10]
    out = []
    for vol, pt, sl, mc in product(vols, pts, sls, mcs):
        out.append(
            {
                "profit_take_pct": pt,
                "stop_loss_mult": sl,
                "volatility_ratio": vol,
                "min_credit_pct_of_risk": mc,
            }
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="smaller grid (faster)")
    ap.add_argument(
        "--no-write-recommended",
        action="store_true",
        help="do not write recommended_params.json",
    )
    args = ap.parse_args()

    combos = grids(args.quick)
    rows = []
    for i, params in enumerate(combos):
        print(f"[{i+1}/{len(combos)}] evaluating {params} ...")
        rows.append(evaluate_combo(params))

    best = max(rows, key=lambda r: r["sort_key"])
    ts = datetime.now(timezone.utc).isoformat()

    grid_path = os.path.join(HERE, "AUTO_OPTIMIZE_GRID.json")
    best_path = os.path.join(HERE, "AUTO_OPTIMIZE_BEST.json")
    rec_path = os.path.join(HERE, "recommended_params.json")

    with open(grid_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_utc": ts,
                "quick": args.quick,
                "universe": "35_tickers_7_sectors",
                "days": DAYS,
                "num_contracts": NUM_CONTRACTS,
                "rows": rows,
            },
            f,
            indent=2,
        )

    best_payload = {
        "generated_utc": ts,
        "sort_key": best["sort_key"],
        "metrics": {k: best[k] for k in ("working", "marginal", "failing", "no_data", "total_pnl", "mean_max_drawdown_pct", "mean_sharpe")},
        "recommended_params": best["params"],
    }
    with open(best_path, "w", encoding="utf-8") as f:
        json.dump(best_payload, f, indent=2)

    if not args.no_write_recommended:
        rec = dict(best["params"])
        rec["_meta"] = {
            "source": "auto_optimize.py",
            "generated_utc": ts,
            "sort_key": list(best["sort_key"]),
        }
        with open(rec_path, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)

    print("\nBest combo:", best["params"])
    print("Metrics:", best_payload["metrics"])
    print("Wrote:", grid_path, best_path)
    if not args.no_write_recommended:
        print("Wrote:", rec_path, "(run_sector_deep_dive.py loads this if present)")


if __name__ == "__main__":
    main()
