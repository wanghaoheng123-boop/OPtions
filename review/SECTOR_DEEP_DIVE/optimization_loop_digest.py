"""
Read latest sector deep-dive JSON and emit persona-tagged review items + priorities.

Usage (from repo root):
  python review/SECTOR_DEEP_DIVE/optimization_loop_digest.py
"""
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TICKER_JSON = os.path.join(HERE, "TICKER_RESULTS.json")
SECTOR_JSON = os.path.join(HERE, "SECTOR_SUMMARY.json")
OUT_JSON = os.path.join(HERE, "OPTIMIZATION_LOOP_DIGEST.json")


def load():
    with open(TICKER_JSON, encoding="utf-8") as f:
        tickers = json.load(f)
    sectors = {}
    if os.path.isfile(SECTOR_JSON):
        with open(SECTOR_JSON, encoding="utf-8") as f:
            sectors = json.load(f)
    return tickers, sectors


def barrier_sl_ratio(row):
    bh = row.get("barrier_hits") or {}
    n = row.get("n_trades") or 0
    if not n:
        return None
    return (bh.get("sl") or 0) / n


def build_digest(tickers, sectors):
    by_class = defaultdict(list)
    by_sector_fail = defaultdict(list)
    low_sample = []
    high_sl = []

    for r in tickers:
        c = r.get("classification", "?")
        by_class[c].append(r.get("ticker"))
        if "error" in r:
            continue
        nt = r.get("n_trades") or 0
        if nt > 0 and nt < 5:
            low_sample.append(
                {
                    "ticker": r["ticker"],
                    "sector": r["sector"],
                    "n_trades": nt,
                    "tag": "quant",
                }
            )
        rsl = barrier_sl_ratio(r)
        if rsl is not None and rsl >= 0.34 and c == "FAILING":
            high_sl.append(
                {
                    "ticker": r["ticker"],
                    "sector": r["sector"],
                    "sl_share": round(rsl, 2),
                    "tag": "trader_mm",
                }
            )
        if c == "FAILING":
            by_sector_fail[r["sector"]].append(r["ticker"])

    persona_items = []

    # PM: sector PnL and concentration
    for sec, meta in sorted(sectors.items()):
        pnl = meta.get("total_pnl_sector")
        aw = meta.get("avg_win_rate")
        if pnl is not None and pnl < 0 and (aw is None or aw < 55):
            persona_items.append(
                {
                    "persona": "portfolio_manager",
                    "priority": "P1",
                    "item": f"Sector {sec}: negative P&L ({pnl}) and weak avg WR ({aw}); cap or exclude until next engine iteration.",
                }
            )
        if meta.get("failing", 0) >= 4:
            persona_items.append(
                {
                    "persona": "portfolio_manager",
                    "priority": "P1",
                    "item": f"Sector {sec}: {meta['failing']}/5 FAILING - default stance: no sleeve expansion.",
                }
            )

    # Quant: sample size
    for x in low_sample:
        persona_items.append(
            {
                "persona": "quant_analyst",
                "priority": "P2",
                "item": f"{x['ticker']} ({x['sector']}): only {x['n_trades']} OOS trades - do not promote on ratios alone; extend window or walk-forward.",
            }
        )

    # Trader / MM: stop-loss dominated failures
    for x in high_sl:
        persona_items.append(
            {
                "persona": "trader_market_maker",
                "priority": "P2",
                "item": f"{x['ticker']} ({x['sector']}): high SL share (~{x['sl_share']*100:.0f}% of exits) - review wing width, DTE, or vol entry gate.",
            }
        )

    working = [r for r in tickers if r.get("classification") == "WORKING"]
    if len(working) >= 2:
        tick_names = [w["ticker"] for w in working]
        persona_items.append(
            {
                "persona": "portfolio_manager",
                "priority": "P2",
                "item": f"Multiple WORKING names ({', '.join(tick_names)}) - correlation cluster risk; enforce per-name and basket notional caps.",
            }
        )

    persona_items.append(
        {
            "persona": "programmer",
            "priority": "P3",
            "item": "Any change to `backtester_audit.py`: add regression check (golden subset or deterministic fixture) before merging.",
        }
    )

    digest = {
        "source_files": {"tickers": TICKER_JSON, "sectors": SECTOR_JSON},
        "counts_by_classification": {k: len(v) for k, v in sorted(by_class.items())},
        "failing_tickers_by_sector": {k: v for k, v in sorted(by_sector_fail.items()) if v},
        "low_sample_trades": low_sample,
        "high_sl_failing": high_sl,
        "persona_backlog": sorted(persona_items, key=lambda x: (x["priority"], x["persona"])),
    }
    return digest


def main():
    if not os.path.isfile(TICKER_JSON):
        raise SystemExit(f"Missing {TICKER_JSON}; run run_sector_deep_dive.py first.")
    tickers, sectors = load()
    digest = build_digest(tickers, sectors)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(digest, f, indent=2)
    print("Wrote", OUT_JSON)
    print("\n--- Persona backlog (preview) ---")
    for it in digest["persona_backlog"][:20]:
        print(f"[{it['priority']}] {it['persona']}: {it['item']}")
    if len(digest["persona_backlog"]) > 20:
        print(f"... and {len(digest['persona_backlog']) - 20} more in JSON")


if __name__ == "__main__":
    main()
