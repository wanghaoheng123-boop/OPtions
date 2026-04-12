"""
Sector Deep-Dive: run audited iron condor backtest on top 5 names per key US sector.
Outputs TICKER_RESULTS.json, SECTOR_SUMMARY.json, BEST_CONDITIONS.json, SECTOR_DEEP_DIVE_REPORT.md

Protocol matches plan: 5 contracts, adaptive + earnings, 252 days, institutional thresholds.
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from skills.backtester_audit import IronCondorBacktester

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RECOMMENDED_JSON = os.path.join(OUT_DIR, "recommended_params.json")


def load_recommended_bt_kwargs():
    """Optional overrides from `auto_optimize.py` (same directory)."""
    if not os.path.isfile(RECOMMENDED_JSON):
        return {}
    with open(RECOMMENDED_JSON, encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if k != "_meta"}


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
    """Plan-aligned: WORKING / MARGINAL / FAILING / NO_DATA."""
    if n_trades == 0:
        return "NO_DATA"
    if wr >= 75 and pf >= 1.2 and dd < 20:
        return "WORKING"
    if wr < 60 or pf < 0.8 or dd > 20:
        return "FAILING"
    if wr >= 60 and pf >= 0.8:
        return "MARGINAL"
    return "FAILING"


def expectancy(wr: float, avg_win: float, avg_loss: float) -> float:
    wrf = wr / 100.0
    return (wrf * avg_win) - ((1 - wrf) * avg_loss)


def slim_trades(sample):
    """Scalars only for JSON (drop full strike dicts)."""
    out = []
    for t in sample or []:
        row = {
            k: t[k]
            for k in (
                "entry_price",
                "entry_credit",
                "pnl",
                "barrier",
                "exit_day",
                "iv_rank",
                "iv_used",
                "iv_raw",
                "wing_pct",
                "dte",
                "iv_rank_min",
            )
            if k in t
        }
        sk = t.get("strikes") or {}
        if sk.get("wing_width") is not None:
            row["wing_width"] = sk["wing_width"]
        out.append(row)
    return out


def run_all():
    results = []
    bt_kwargs = {
        "use_adaptive": True,
        "earnings_filter": True,
        "profit_take_pct": 0.50,
        "stop_loss_mult": 1.0,
        "num_contracts": NUM_CONTRACTS,
    }
    bt_kwargs.update(load_recommended_bt_kwargs())
    for sector, tickers in SECTORS.items():
        for t in tickers:
            bt = IronCondorBacktester(**bt_kwargs)
            r = bt.run(t, days=DAYS)
            row = {
                "sector": sector,
                "ticker": t,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            if "error" in r:
                row["error"] = r["error"]
                row["verdict"] = "NO_DATA"
                row["classification"] = "NO_DATA"
            else:
                row.update(
                    {
                        "n_trades": r["n_trades"],
                        "n_wins": r["n_wins"],
                        "win_rate_percent": r["win_rate_percent"],
                        "profit_factor": r["profit_factor"],
                        "total_net_pnl": r["total_net_pnl"],
                        "avg_win": r["avg_win"],
                        "avg_loss": r["avg_loss"],
                        "max_drawdown_percent": r["max_drawdown_percent"],
                        "max_drawdown_dollars": r["max_drawdown_dollars"],
                        "sharpe_ratio": r["sharpe_ratio"],
                        "sortino_ratio": r["sortino_ratio"],
                        "calmar_ratio": r["calmar_ratio"],
                        "total_return_percent": r["total_return_percent"],
                        "trained_iv": r["trained_iv"],
                        "volatility_ratio": r["volatility_ratio"],
                        "avg_credit": r["avg_credit"],
                        "avg_capital_per_trade": r["avg_capital_per_trade"],
                        "num_contracts": r["num_contracts"],
                        "barrier_hits": r["barrier_hits"],
                        "verdict": r["verdict"],
                        "iv_used_range": r.get("iv_used_range"),
                        "iv_raw_range": r.get("iv_raw_range"),
                        "iv_rank_range": r.get("iv_rank_range"),
                        "avg_adaptive_wing_pct": r.get("avg_adaptive_wing_pct"),
                        "avg_adaptive_dte": r.get("avg_adaptive_dte"),
                        "trade_sample": slim_trades(r.get("trade_sample")),
                    }
                )
                row["classification"] = classify(
                    r["win_rate_percent"],
                    r["profit_factor"],
                    r["max_drawdown_percent"],
                    r["n_trades"],
                )
                row["expectancy_dollars"] = round(
                    expectancy(
                        r["win_rate_percent"],
                        r["avg_win"],
                        r["avg_loss"],
                    ),
                    2,
                )
            results.append(row)
    return results


def sector_summary(results):
    by = {}
    for r in results:
        s = r["sector"]
        by.setdefault(s, []).append(r)
    summary = {}
    for sector, rows in by.items():
        ok = [x for x in rows if x.get("classification") == "WORKING"]
        marg = [x for x in rows if x.get("classification") == "MARGINAL"]
        fail = [x for x in rows if x.get("classification") == "FAILING"]
        nod = [x for x in rows if x.get("classification") == "NO_DATA"]
        wrs = [x["win_rate_percent"] for x in rows if "win_rate_percent" in x]
        pfs = [x["profit_factor"] for x in rows if "profit_factor" in x]
        pnls = [x["total_net_pnl"] for x in rows if "total_net_pnl" in x]
        summary[sector] = {
            "tickers_tested": len(rows),
            "working": len(ok),
            "marginal": len(marg),
            "failing": len(fail),
            "no_data": len(nod),
            "avg_win_rate": round(sum(wrs) / len(wrs), 2) if wrs else None,
            "avg_profit_factor": round(sum(pfs) / len(pfs), 2) if pfs else None,
            "total_pnl_sector": round(sum(pnls), 2) if pnls else None,
            "working_tickers": [x["ticker"] for x in ok],
            "marginal_tickers": [x["ticker"] for x in marg],
            "failing_tickers": [x["ticker"] for x in fail],
            "no_data_tickers": [x["ticker"] for x in nod],
        }
    return summary


def best_conditions(results):
    working = [r for r in results if r.get("classification") == "WORKING"]
    marginal = [r for r in results if r.get("classification") == "MARGINAL"]
    failing = [r for r in results if r.get("classification") == "FAILING"]
    high_bar = [
        r
        for r in results
        if r.get("n_trades")
        and r.get("win_rate_percent", 0) > 80
        and r.get("profit_factor", 0) > 2.0
    ]
    cfg_kw = {
        "use_adaptive": True,
        "earnings_filter": True,
        "profit_take_pct": 0.5,
        "stop_loss_mult": 1.0,
        "num_contracts": NUM_CONTRACTS,
    }
    cfg_kw.update(load_recommended_bt_kwargs())
    ref_bt = IronCondorBacktester(**cfg_kw)
    return {
        "institutional_thresholds": {
            "win_rate_min_pct": 75,
            "profit_factor_min": 1.2,
            "max_drawdown_max_pct": 20,
        },
        "marginal_thresholds": {
            "win_rate_min_pct": 60,
            "profit_factor_min": 0.8,
            "note": "MARGINAL when WR and PF meet these and not FAILING (DD<=20%, WR>=60, PF>=0.8).",
        },
        "failing_rules": {
            "any_of": [
                "win_rate_percent < 60",
                "profit_factor < 0.8",
                "max_drawdown_percent > 20",
            ]
        },
        "backtest_config": {
            "strategy": "iron_condor_audited",
            "days": DAYS,
            "use_adaptive": ref_bt.use_adaptive,
            "earnings_filter": ref_bt.earnings_filter,
            "profit_take_pct": ref_bt.profit_take_pct,
            "stop_loss_mult": ref_bt.stop_loss_mult,
            "num_contracts": ref_bt.num_contracts,
            "volatility_ratio": ref_bt.volatility_ratio,
            "min_credit_pct_of_risk": ref_bt.min_credit_pct_of_risk,
            "recommended_params_loaded": os.path.isfile(RECOMMENDED_JSON),
        },
        "counts": {
            "working": len(working),
            "marginal": len(marginal),
            "failing": len(failing),
            "no_data": len([r for r in results if r.get("classification") == "NO_DATA"]),
        },
        "working_list": [{"ticker": r["ticker"], "sector": r["sector"]} for r in working],
        "tickers_wr_gt_80_pf_gt_2": [
            {"ticker": r["ticker"], "sector": r["sector"], "wr": r["win_rate_percent"], "pf": r["profit_factor"]}
            for r in sorted(high_bar, key=lambda x: (-x["profit_factor"], -x["win_rate_percent"]))
        ],
        "interpretation": {
            "when_works_best": [
                "Large-cap liquid names with moderate realized vol and IV Rank above adaptive floor",
                "Fewer gap-driven single-name events than high-beta discretionary",
                "Sufficient credit vs wing width (passes min credit filter)",
            ],
            "when_fails": [
                "High-beta names with frequent large daily moves vs wing width",
                "Max drawdown > 20% fails deployment even if win rate is high",
                "Binary event risk not fully removed by coarse earnings calendar",
            ],
        },
    }


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def build_markdown(results, sector_sum, best):
    lines = []
    lines.append("# Institutional Iron Condor — Sector Deep-Dive Audit")
    lines.append("")
    lines.append("## Agentic Quant Terminal V2 — 35 Tickers, 7 Sectors")
    lines.append("")
    lines.append("Audited backtester: [`skills/backtester_audit.py`](../../skills/backtester_audit.py)")
    lines.append("")
    lines.append(f"**Generated (UTC):** `{datetime.now(timezone.utc).isoformat()}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    total = len(results)
    w = sum(1 for r in results if r.get("classification") == "WORKING")
    m = sum(1 for r in results if r.get("classification") == "MARGINAL")
    f = sum(1 for r in results if r.get("classification") == "FAILING")
    nd = sum(1 for r in results if r.get("classification") == "NO_DATA")
    lines.append(
        f"Universe: **{total}** tickers, **{len(SECTORS)}** sectors (top 5 by liquidity / market cap). "
        f"Each run: **{NUM_CONTRACTS} contracts** per trade, **{DAYS}** calendar days lookback, adaptive wing/DTE/IV Rank, "
        "earnings filter on, 50% profit take, 100% credit stop."
    )
    lines.append("")
    lines.append(f"- **WORKING** (WR ≥ 75%, PF ≥ 1.2, max DD < 20%): **{w}/{total}**")
    lines.append(f"- **MARGINAL** (WR ≥ 60%, PF ≥ 0.8, and not failing on DD/WR/PF rules): **{m}/{total}**")
    lines.append(f"- **FAILING** (WR < 60% **or** PF < 0.8 **or** max DD > 20%): **{f}/{total}**")
    lines.append(f"- **NO_DATA** (no trades / data error): **{nd}/{total}**")
    lines.append("")
    lines.append("### Sector rollup")
    lines.append("")
    lines.append("| Sector | Tested | Working | Marginal | Failing | No data | Avg WR% | Avg PF | Sector P&L $ |")
    lines.append("|--------|--------|---------|----------|---------|---------|---------|--------|-------------|")
    for sec, s in sorted(sector_sum.items()):
        lines.append(
            f"| {sec.replace('_', ' ')} | {s['tickers_tested']} | {s['working']} | {s['marginal']} | "
            f"{s['failing']} | {s['no_data']} | {s['avg_win_rate'] or '—'} | "
            f"{s['avg_profit_factor'] or '—'} | {s['total_pnl_sector'] or '—'} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("- **Engine:** `IronCondorBacktester.run()` — 70/30 in-sample vs out-of-sample split.")
    lines.append("- **IV at entry:** 30d realized vol × VOLATILITY_RATIO (1.4); IV Rank from 252d history of realized vol when available.")
    lines.append("- **Per-ticker JSON:** IV used range, IV raw range, IV Rank range at entries, avg adaptive wing % and DTE, barrier counts, `trade_sample` (up to 3 trades, scalar fields).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Sector Analysis")
    lines.append("")

    for sector, tickers in SECTORS.items():
        tick_str = ", ".join(tickers)
        lines.append(f"### {sector.replace('_', ' ')} ({tick_str})")
        lines.append("")
        rows = [r for r in results if r["sector"] == sector]
        lines.append(
            "| Ticker | Class | WR% | PF | Max DD% | Sharpe | Sortino | Calmar | Trades | P&L $ | "
            "Avg credit | IV used range | IV Rank range | Avg wing% | Avg DTE | Barriers pt/sl/time/exp/fc |"
        )
        lines.append(
            "|--------|-------|-----|-----|---------|--------|---------|--------|--------|--------|"
            "------------|---------------|---------------|-----------|---------|---------------------------|"
        )
        for r in rows:
            if "error" in r:
                lines.append(
                    f"| {r['ticker']} | NO_DATA | — | — | — | — | — | — | 0 | — | — | — | — | — | — | {str(r.get('error', ''))[:32]} |"
                )
                continue
            bh = r.get("barrier_hits", {})
            bhs = "/".join(str(bh.get(k, 0)) for k in ("pt", "sl", "time", "exp", "forced_close"))
            ivu = r.get("iv_used_range")
            ivu_s = f"{ivu[0]}–{ivu[1]}" if ivu else "—"
            irr = r.get("iv_rank_range")
            irr_s = f"{irr[0]}–{irr[1]}" if irr else "—"
            aw = r.get("avg_adaptive_wing_pct")
            ad = r.get("avg_adaptive_dte")
            lines.append(
                f"| {r['ticker']} | {r['classification']} | {r['win_rate_percent']} | {r['profit_factor']} | "
                f"{r['max_drawdown_percent']} | {r['sharpe_ratio']} | {r['sortino_ratio']} | {r['calmar_ratio']} | "
                f"{r['n_trades']} | {r['total_net_pnl']} | {r['avg_credit']} | {ivu_s} | {irr_s} | "
                f"{aw if aw is not None else '—'} | {ad if ad is not None else '—'} | {bhs} |"
            )
        s = sector_sum[sector]
        lines.append("")
        lines.append(f"- **Working:** {', '.join(s['working_tickers']) or '—'}")
        lines.append(f"- **Marginal:** {', '.join(s['marginal_tickers']) or '—'}")
        lines.append(f"- **Failing:** {', '.join(s['failing_tickers']) or '—'}")
        lines.append(f"- **No data:** {', '.join(s['no_data_tickers']) or '—'}")
        lines.append("")
        lines.append("**What works / what fails in this sector:**")
        if s["working"] >= 3:
            lines.append("- Several names cleared institutional gates; sector is a candidate for deployment with per-name risk caps.")
        elif s["working"] >= 1:
            lines.append("- Selective: only some names pass; use whitelist within sector rather than sector-wide automation.")
        else:
            lines.append("- Broad short-vol profile is weak here under current wings/stops; widen wings, reduce size, or skip sector.")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Best Conditions for Strategy Success")
    lines.append("")
    lines.append("Institutional **PASS** in-engine: WR ≥ 75%, PF ≥ 1.2, max DD < 20%.")
    lines.append("")
    lines.append("### Observed: WR > 80% and PF > 2.0")
    lines.append("")
    hb = best.get("tickers_wr_gt_80_pf_gt_2") or []
    if hb:
        for x in hb:
            lines.append(f"- **{x['ticker']}** ({x['sector']}): WR {x['wr']}%, PF {x['pf']}")
    else:
        lines.append("- No tickers met this stricter discretionary bar in this run.")
    lines.append("")
    lines.append("### General patterns")
    lines.append("")
    for item in best["interpretation"]["when_works_best"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Failure Modes and Risk Patterns")
    lines.append("")
    for item in best["interpretation"]["when_fails"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### Tickers flagged FAILING or NO_DATA")
    lines.append("")
    fail_rows = [r for r in results if r.get("classification") in ("FAILING", "NO_DATA")]
    for r in sorted(fail_rows, key=lambda x: x["ticker"]):
        if r.get("classification") == "NO_DATA":
            lines.append(f"- **{r['ticker']}** ({r['sector']}): {r.get('error', 'NO_DATA')}")
        else:
            lines.append(
                f"- **{r['ticker']}** ({r['sector']}): WR {r['win_rate_percent']}%, PF {r['profit_factor']}, "
                f"DD {r['max_drawdown_percent']}%, barriers {r.get('barrier_hits')}"
            )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## AI Agent Optimization Recommendations")
    lines.append("")
    lines.append("1. **IV source:** Swap realized×1.4 for options-chain ATM IV or IV Rank from a vendor; align `adaptive_iv_rank_min` with real IV Rank.")
    lines.append("2. **Drawdown gate:** Treat `max_drawdown_percent > 20` as hard FAIL for promotion even if PF is high (see plan failing rules).")
    lines.append("3. **High-beta discretionary:** Down-weight or block when 20d realized vol exceeds sector-specific threshold; many fails cluster there.")
    lines.append("4. **Wing / DTE:** For high `sl` share, raise `adaptive_wing` floor or shorten DTE; re-run sector basket after each change.")
    lines.append("5. **Sample size:** OOS often yields few trades; require minimum N and walk-forward windows before live capital.")
    lines.append("6. **Margin realism:** With **5 contracts**, scale Reg-T/SPAN estimates in reporting; `avg_capital_per_trade` is wing-based proxy only.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Final Recommendations")
    lines.append("")
    wl = best["working_list"]
    if wl:
        lines.append(
            "**Deploy-first watchlist (WORKING this run):** "
            + ", ".join(f"{x['ticker']} ({x['sector']})" for x in wl)
            + "."
        )
    else:
        lines.append("No ticker met full WORKING criteria; do not scale capital until filters or universe are revised.")
    lines.append("")
    lines.append("**Sectors:** Prefer follow-up sizing on sectors with multiple WORKING names; treat Energy and broad Staples as suspect until structural edge improves.")
    lines.append("")
    lines.append("**Parameters:** Keep `profit_take_pct=0.50`, `stop_loss_mult=1.0`, `earnings_filter=True`, `use_adaptive=True`, `num_contracts=5` for comparability to this audit.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Machine-Readable Outputs")
    lines.append("")
    lines.append("- [`TICKER_RESULTS.json`](./TICKER_RESULTS.json)")
    lines.append("- [`SECTOR_SUMMARY.json`](./SECTOR_SUMMARY.json)")
    lines.append("- [`BEST_CONDITIONS.json`](./BEST_CONDITIONS.json)")
    lines.append("")
    return "\n".join(lines)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    results = run_all()
    ssum = sector_summary(results)
    best = best_conditions(results)
    write_json(os.path.join(OUT_DIR, "TICKER_RESULTS.json"), results)
    write_json(os.path.join(OUT_DIR, "SECTOR_SUMMARY.json"), ssum)
    write_json(os.path.join(OUT_DIR, "BEST_CONDITIONS.json"), best)
    md = build_markdown(results, ssum, best)
    with open(os.path.join(OUT_DIR, "SECTOR_DEEP_DIVE_REPORT.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print("Wrote:", OUT_DIR)
    print("  TICKER_RESULTS.json")
    print("  SECTOR_SUMMARY.json")
    print("  BEST_CONDITIONS.json")
    print("  SECTOR_DEEP_DIVE_REPORT.md")


if __name__ == "__main__":
    main()
