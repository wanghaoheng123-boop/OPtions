import sys
sys.path.append('.')
import json
import numpy as np
from skills.backtester_audit import IronCondorBacktester
import pandas as pd

SECTORS = {
    "Technology": ["AAPL", "MSFT", "NVDA", "META", "GOOGL"],
    "Financials": ["JPM", "BAC", "GS", "MS", "V"],
    "Healthcare": ["UNH", "JNJ", "LLY", "ABBV", "MRK"],
    "Consumer_Discretionary": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
    "Consumer_Staples": ["WMT", "KO", "PEP", "PG", "COST"],
    "Energy": ["XOM", "CVX", "COP", "EOG", "SLB"],
    "Industrials": ["BA", "CAT", "GE", "RTX", "UPS"],
}

# Fixed earnings calendar for all major tickers
EARNINGS_CALENDAR = {
    # Technology
    'AAPL': [1, 4, 7, 10], 'MSFT': [2, 5, 8, 11], 'NVDA': [1, 4, 7, 10],
    'META': [1, 4, 7, 10], 'GOOGL': [1, 4, 7, 10],
    # Financials
    'JPM': [1, 4, 7, 10], 'BAC': [1, 4, 7, 10], 'GS': [1, 4, 7, 10],
    'MS': [1, 4, 7, 10], 'V': [1, 4, 7, 10],
    # Healthcare
    'UNH': [1, 4, 7, 10], 'JNJ': [1, 4, 7, 10], 'LLY': [1, 4, 7, 10],
    'ABBV': [1, 4, 7, 10], 'MRK': [1, 4, 7, 10],
    # Consumer Disc
    'AMZN': [1, 4, 7, 10], 'TSLA': [1, 4, 7, 10], 'HD': [1, 4, 7, 10],
    'MCD': [1, 4, 7, 10], 'NKE': [1, 4, 7, 10],
    # Consumer Staples
    'WMT': [2, 5, 8, 11], 'KO': [1, 4, 7, 10], 'PEP': [1, 4, 7, 10],
    'PG': [1, 4, 7, 10], 'COST': [1, 4, 7, 10],
    # Energy
    'XOM': [1, 4, 7, 10], 'CVX': [1, 4, 7, 10], 'COP': [1, 4, 7, 10],
    'EOG': [1, 4, 7, 10], 'SLB': [1, 4, 7, 10],
    # Industrials
    'BA': [1, 4, 7, 10], 'CAT': [1, 4, 7, 10], 'GE': [1, 4, 7, 10],
    'RTX': [1, 4, 7, 10], 'UPS': [1, 4, 7, 10],
}

def run_ticker(ticker, sector):
    """Run backtest for a single ticker with the audited parameters."""
    bt = IronCondorBacktester(
        use_adaptive=True,
        earnings_filter=True,
        profit_take_pct=0.50,
        stop_loss_mult=1.0,
        num_contracts=5,
    )
    # Override earnings calendar
    bt.EARNINGS_CALENDAR = EARNINGS_CALENDAR

    r = bt.run(ticker, days=252)

    if 'error' in r and 'No data' in r.get('error', ''):
        return {
            'ticker': ticker, 'sector': sector, 'status': 'NO_DATA',
            'error': r['error']
        }
    elif 'error' in r:
        return {
            'ticker': ticker, 'sector': sector, 'status': 'ERROR',
            'error': r['error']
        }

    wr = r.get('win_rate_percent', 0)
    pf = r.get('profit_factor', 0)
    dd = r.get('max_drawdown_percent', 999)
    sharpe = r.get('sharpe_ratio', 0)

    if wr >= 75 and pf >= 1.2 and dd < 20:
        verdict = 'PASS'
    elif wr >= 60 and pf >= 0.8:
        verdict = 'MARGINAL'
    else:
        verdict = 'FAIL'

    pnls = [t['pnl'] for t in r.get('trade_sample', [])]
    wins = [p for p in pnls if p > 0] if pnls else []
    losses = [p for p in pnls if p <= 0] if pnls else []
    expectancy = (wr/100 * r.get('avg_win', 0) - (1-wr/100) * r.get('avg_loss', 0)) if r.get('avg_win', 0) > 0 else 0

    # Count barrier hits from full run
    barriers = r.get('barrier_hits', {})
    total_trades = r.get('n_trades', 0)

    return {
        'ticker': ticker,
        'sector': sector,
        'status': 'SUCCESS',
        'verdict': verdict,
        'n_trades': total_trades,
        'n_wins': r.get('n_wins', 0),
        'win_rate_percent': wr,
        'profit_factor': pf,
        'max_drawdown_percent': dd,
        'sharpe_ratio': sharpe,
        'sortino_ratio': r.get('sortino_ratio', 0),
        'calmar_ratio': r.get('calmar_ratio', 0),
        'total_net_pnl': r.get('total_net_pnl', 0),
        'avg_win': r.get('avg_win', 0),
        'avg_loss': r.get('avg_loss', 0),
        'avg_credit': r.get('avg_credit', 0),
        'total_return_percent': r.get('total_return_percent', 0),
        'barrier_hits': barriers,
        'trained_iv': r.get('trained_iv', 0),
        'volatility_ratio': r.get('volatility_ratio', 1.4),
        'num_contracts': r.get('num_contracts', 5),
        'trade_sample': r.get('trade_sample', [])[:3],
        'expectancy': expectancy,
        # Breakdown by barrier
        'pt_pct': round(barriers.get('pt', 0) / max(total_trades, 1) * 100, 1),
        'sl_pct': round(barriers.get('sl', 0) / max(total_trades, 1) * 100, 1),
        'time_pct': round(barriers.get('time', 0) / max(total_trades, 1) * 100, 1),
        'exp_pct': round(barriers.get('exp', 0) / max(total_trades, 1) * 100, 1),
        'forced_close_pct': round(barriers.get('forced_close', 0) / max(total_trades, 1) * 100, 1),
    }

def classify_iv_regime(trained_iv):
    """Classify IV regime."""
    if trained_iv < 0.15: return 'LOW'
    elif trained_iv < 0.25: return 'MODERATE'
    elif trained_iv < 0.35: return 'HIGH'
    else: return 'EXTREME'

print("=" * 75)
print("INSTITUTIONAL IRON CONDOR — SECTOR DEEP-DIVE")
print("35 Tickers, 7 Sectors, Audited Backtester")
print("=" * 75)

all_results = []
failed_tickers = []

for sector, tickers in SECTORS.items():
    print(f"\n--- {sector} ---")
    for ticker in tickers:
        result = run_ticker(ticker, sector)
        all_results.append(result)

        if result['status'] == 'SUCCESS':
            v = result['verdict']
            wr = result['win_rate_percent']
            pf = result['profit_factor']
            dd = result['max_drawdown_percent']
            pnl = result['total_net_pnl']
            trades = result['n_trades']
            iv = result['trained_iv']
            print(f"  {ticker:6s}: WR={wr:5.1f}% PF={pf:6.2f} DD={dd:5.1f}% "
                  f"Sharpe={result['sharpe_ratio']:5.1f} P&L=${pnl:8.0f} "
                  f"Trades={trades:2d} IV={iv:.1%} [{v}]")
        elif result['status'] == 'NO_DATA':
            print(f"  {ticker:6s}: NO DATA")
            failed_tickers.append(ticker)
        else:
            print(f"  {ticker:6s}: ERROR - {result.get('error', 'unknown')}")
            failed_tickers.append(ticker)

# ============================================================
# Aggregate results
# ============================================================
print("\n" + "=" * 75)
print("AGGREGATE RESULTS")
print("=" * 75)

successful = [r for r in all_results if r['status'] == 'SUCCESS']
n_success = len(successful)
n_pass = sum(1 for r in successful if r['verdict'] == 'PASS')
n_marginal = sum(1 for r in successful if r['verdict'] == 'MARGINAL')
n_fail = sum(1 for r in successful if r['verdict'] == 'FAIL')

total_pnl = sum(r['total_net_pnl'] for r in successful)
avg_wr = np.mean([r['win_rate_percent'] for r in successful]) if successful else 0
avg_pf = np.mean([r['profit_factor'] for r in successful]) if successful else 0
avg_dd = np.mean([r['max_drawdown_percent'] for r in successful]) if successful else 0
avg_sharpe = np.mean([r['sharpe_ratio'] for r in successful]) if successful else 0
total_trades = sum(r['n_trades'] for r in successful)

print(f"\nTotal tickers tested: {len(all_results)}")
print(f"Successful: {n_success} | PASS: {n_pass} | MARGINAL: {n_marginal} | FAIL: {n_fail}")
print(f"Total P&L: ${total_pnl:,.2f}")
print(f"Average WR: {avg_wr:.1f}%")
print(f"Average PF: {avg_pf:.2f}")
print(f"Average DD: {avg_dd:.1f}%")
print(f"Average Sharpe: {avg_sharpe:.1f}")
print(f"Total Trades: {total_trades}")

# Per-sector summary
print("\n--- SECTOR SUMMARY ---")
print(f"{'Sector':<25} {'Tickers':>7} {'PASS':>5} {'MARG':>5} {'FAIL':>5} "
      f"{'AvgWR':>7} {'AvgPF':>7} {'AvgDD':>7} {'TotalP&L':>12}")
print("-" * 90)
sector_rows = []
for sector, tickers in SECTORS.items():
    sec_results = [r for r in successful if r['sector'] == sector]
    if sec_results:
        n_t = len(sec_results)
        n_p = sum(1 for r in sec_results if r['verdict'] == 'PASS')
        n_m = sum(1 for r in sec_results if r['verdict'] == 'MARGINAL')
        n_f = sum(1 for r in sec_results if r['verdict'] == 'FAIL')
        avg_w = np.mean([r['win_rate_percent'] for r in sec_results])
        avg_p = np.mean([r['profit_factor'] for r in sec_results])
        avg_d = np.mean([r['max_drawdown_percent'] for r in sec_results])
        sec_pnl = sum(r['total_net_pnl'] for r in sec_results)
        print(f"{sector:<25} {n_t:>7} {n_p:>5} {n_m:>5} {n_f:>5} "
              f"{avg_w:>6.1f}% {avg_p:>7.2f} {avg_d:>6.1f}% ${sec_pnl:>11,.0f}")
        sector_rows.append({
            'sector': sector, 'n_tickers': n_t,
            'pass': n_p, 'marginal': n_m, 'fail': n_f,
            'avg_wr': round(avg_w, 1), 'avg_pf': round(avg_p, 2),
            'avg_dd': round(avg_d, 1), 'total_pnl': round(sec_pnl, 2)
        })

# Per-ticker full results
print("\n--- PER-TICKER RESULTS ---")
print(f"{'Ticker':<8} {'Sector':<25} {'WR%':>6} {'PF':>7} {'DD%':>6} "
      f"{'Sharpe':>7} {'P&L':>10} {'Trades':>7} {'IV':>6} {'Verdict':>8}")
print("-" * 110)
for r in sorted(successful, key=lambda x: x['total_net_pnl'], reverse=True):
    print(f"{r['t\t\t\t\t\t ticker']:<8} {r['sector']:<25} "
          f"{r['win_rate_percent']:>5.1f}% {r['profit_factor']:>7.2f} "
          f"{r['max_drawdown_percent']:>5.1f}% {r['sharpe_ratio']:>7.1f} "
          f"${r['total_net_pnl']:>9,.0f} {r['n_trades']:>7} "
          f"{r['trained_iv']:>5.1%} {r['verdict']:>8}")

# Barrier analysis
print("\n--- BARRIER HIT ANALYSIS ---")
all_pt = sum(r['pt_pct'] for r in successful) / max(n_success, 1)
all_sl = sum(r['sl_pct'] for r in successful) / max(n_success, 1)
all_time = sum(r['time_pct'] for r in successful) / max(n_success, 1)
all_exp = sum(r['exp_pct'] for r in successful) / max(n_success, 1)
all_fc = sum(r['forced_close_pct'] for r in successful) / max(n_success, 1)
print(f"Profit Taking (PT):    {all_pt:.1f}%")
print(f"Stop Loss (SL):        {all_sl:.1f}%")
print(f"Time Exit:             {all_time:.1f}%")
print(f"Expiration:            {all_exp:.1f}%")
print(f"Forced Close:         {all_fc:.1f}%")

# ============================================================
# Save JSON results
# ============================================================
ticker_results_json = []
for r in successful:
    ticker_results_json.append({
        'ticker': r['ticker'],
        'sector': r['sector'],
        'verdict': r['verdict'],
        'n_trades': r['n_trades'],
        'win_rate_percent': r['win_rate_percent'],
        'profit_factor': r['profit_factor'],
        'max_drawdown_percent': r['max_drawdown_percent'],
        'sharpe_ratio': r['sharpe_ratio'],
        'sortino_ratio': r['sortino_ratio'],
        'calmar_ratio': r['calmar_ratio'],
        'total_net_pnl': r['total_net_pnl'],
        'avg_win': r['avg_win'],
        'avg_loss': r['avg_loss'],
        'avg_credit': r['avg_credit'],
        'total_return_percent': r['total_return_percent'],
        'barrier_hits': r['barrier_hits'],
        'trained_iv': r['trained_iv'],
        'volatility_ratio': r['volatility_ratio'],
        'num_contracts': r['num_contracts'],
        'expectancy': r['expectancy'],
        'pt_pct': r['pt_pct'],
        'sl_pct': r['sl_pct'],
        'time_pct': r['time_pct'],
        'exp_pct': r['exp_pct'],
        'forced_close_pct': r['forced_close_pct'],
    })

with open('review/SECTOR_DEEP_DIVE/TICKER_RESULTS.json', 'w') as f:
    json.dump(ticker_results_json, f, indent=2)

with open('review/SECTOR_DEEP_DIVE/SECTOR_SUMMARY.json', 'w') as f:
    json.dump({
        'total_tickers': len(all_results),
        'successful': n_success,
        'passed': n_pass,
        'marginal': n_marginal,
        'failed': n_fail,
        'pass_rate': round(n_pass / max(n_success, 1) * 100, 1),
        'total_pnl': round(total_pnl, 2),
        'avg_win_rate': round(avg_wr, 2),
        'avg_profit_factor': round(avg_pf, 2),
        'avg_max_drawdown': round(avg_dd, 2),
        'avg_sharpe': round(avg_sharpe, 2),
        'total_trades': total_trades,
        'sectors': sector_rows,
        'failed_tickers': failed_tickers,
        'barrier_analysis': {
            'profit_taking_pct': round(all_pt, 1),
            'stop_loss_pct': round(all_sl, 1),
            'time_exit_pct': round(all_time, 1),
            'expiration_pct': round(all_exp, 1),
            'forced_close_pct': round(all_fc, 1),
        }
    }, f, indent=2)

print("\nJSON files saved.")

# ============================================================
# Best conditions analysis
# ============================================================
passing = [r for r in successful if r['verdict'] == 'PASS']
passing_ivs = [r['trained_iv'] for r in passing]
passing_wrs = [r['win_rate_percent'] for r in passing]
passing_pfs = [r['profit_factor'] for r in passing]

best_conditions = {
    'avg_iv_for_passing': round(np.mean(passing_ivs), 4) if passing_ivs else None,
    'iv_range_for_pass': {
        'min': round(min(passing_ivs), 4) if passing_ivs else None,
        'max': round(max(passing_ivs), 4) if passing_ivs else None,
    },
    'avg_wr_for_passing': round(np.mean(passing_wrs), 1) if passing_wrs else None,
    'avg_pf_for_passing': round(np.mean(passing_pfs), 2) if passing_pfs else None,
    'best_tickers': sorted(passing, key=lambda x: x['sharpe_ratio'], reverse=True)[:5],
    'worst_tickers': sorted(successful, key=lambda x: x['win_rate_percent'])[:5],
    'highest_pnl_tickers': sorted(successful, key=lambda x: x['total_net_pnl'], reverse=True)[:5],
}

with open('review/SECTOR_DEEP_DIVE/BEST_CONDITIONS.json', 'w') as f:
    json.dump(best_conditions, f, indent=2)

print("\nBest conditions saved.")
print("\n=== DATA COLLECTION COMPLETE ===")
print("Ready to generate SECTOR_DEEP_DIVE_REPORT.md")