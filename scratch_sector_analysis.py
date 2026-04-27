import sys
sys.path.append('.')
from skills.backtester_audit import IronCondorBacktester, OptionsPricing
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("COMPREHENSIVE SECTOR ANALYSIS — TOP US STOCKS")
print("Iron Condor Strategy — Institutional Audit-Corrected Backtester")
print("=" * 80)

# ============================================================
# SECTOR DEFINITIONS (Top stocks per sector)
# ============================================================
SECTORS = {
    'Technology': {
        'etf': 'XLK',
        'tickers': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'CRM', 'ORCL', 'AMD', 'INTC'],
        'characteristics': 'High IV, earnings-driven, innovation cycles'
    },
    'Healthcare': {
        'etf': 'XLV',
        'tickers': ['UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'LLY', 'ABT', 'BMY'],
        'characteristics': 'Moderate IV, binary events (FDA approvals), defensive'
    },
    'Financials': {
        'etf': 'XLF',
        'tickers': ['JPM', 'BAC', 'GS', 'MS', 'BLK', 'C', 'WFC', 'AXP'],
        'characteristics': 'Interest rate sensitive, earnings cyclical, high-beta'
    },
    'Consumer_Discretionary': {
        'etf': 'XLY',
        'tickers': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW'],
        'characteristics': 'Consumer spending sensitive, high-beta, seasonal'
    },
    'Communication_Services': {
        'etf': 'XLC',
        'tickers': ['META', 'GOOGL', 'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'WBD'],
        'characteristics': 'High IV tech-adjacent, streaming/binary events'
    },
    'Energy': {
        'etf': 'XLE',
        'tickers': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO'],
        'characteristics': 'Commodity price sensitive, high vol, geopolitical risk'
    },
    'Industrials': {
        'etf': 'XLI',
        'tickers': ['CAT', 'HON', 'RTX', 'BA', 'GE', 'DE', 'UPS', 'FDX'],
        'characteristics': 'Moderate IV, economic cycle sensitive, defense stable'
    },
    'Consumer_Staples': {
        'etf': 'XLP',
        'tickers': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'MDLZ', 'CL', 'GIS'],
        'characteristics': 'Low IV, defensive, dividend stable, inelastic demand'
    },
    'Utilities': {
        'etf': 'XLU',
        'tickers': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'SRE', 'EXC', 'XEL'],
        'characteristics': 'Very low IV, rate sensitive, stable but boring'
    },
    'Materials': {
        'etf': 'XLB',
        'tickers': ['LIN', 'APD', 'SHW', 'FCX', 'NEE', 'DOW', 'PPG', 'NEM'],
        'characteristics': 'Commodity price sensitive, moderate IV, global demand'
    },
    'Broad_Market': {
        'etf': 'SPY',
        'tickers': ['SPY', 'QQQ', 'IWM', 'DIA'],
        'characteristics': 'Diversified, baseline market representation'
    }
}

# ============================================================
# PARAMETERS TO TEST
# ============================================================
PARAM_SETS = [
    {'name': 'Standard (50% PT, 1.0x SL)', 'profit_take_pct': 0.50, 'stop_loss_mult': 1.0, 'dte': 30, 'wing': 0.05},
    {'name': 'Aggressive (70% PT, 1.0x SL)', 'profit_take_pct': 0.70, 'stop_loss_mult': 1.0, 'dte': 30, 'wing': 0.05},
    {'name': 'Wide Wing (50% PT, 1.0x SL, 7%)', 'profit_take_pct': 0.50, 'stop_loss_mult': 1.0, 'dte': 30, 'wing': 0.07},
    {'name': 'Short DTE (50% PT, 21 DTE)', 'profit_take_pct': 0.50, 'stop_loss_mult': 1.0, 'dte': 21, 'wing': 0.05},
]

# ============================================================
# RUN BACKTESTS
# ============================================================
ALL_RESULTS = {}
PARAM_RESULTS = {}

for param_set in PARAM_SETS:
    print("\n" + "=" * 80)
    print("PARAMETER SET: {} | PT={:.0%} | SL={:.1f}x | DTE={} | Wing={:.0%}".format(
        param_set['name'], param_set['profit_take_pct'], param_set['stop_loss_mult'],
        param_set['dte'], param_set['wing']))
    print("=" * 80)

    sector_results = {}
    param_key = param_set['name']

    for sector_name, sector_data in SECTORS.items():
        print("\n--- {} ({}) ---".format(sector_name, sector_data['etf']))

        ticker_results = []
        failed = []

        for ticker in sector_data['tickers']:
            bt = IronCondorBacktester(
                iv_rank_min=50.0,
                dte_entry=param_set['dte'],
                max_hold_days=param_set['dte'] - 5,
                profit_take_pct=param_set['profit_take_pct'],
                stop_loss_mult=param_set['stop_loss_mult'],
                wing_pct=param_set['wing'],
                num_contracts=1,
                use_adaptive=True,
                earnings_filter=True
            )

            r = bt.run(ticker, days=252)

            if 'error' not in r:
                r['ticker'] = ticker
                r['sector'] = sector_name
                ticker_results.append(r)

                verdict = "PASS" if (r['win_rate_percent'] >= 75 and
                                    r['profit_factor'] >= 1.2 and
                                    r['max_drawdown_percent'] < 20) else "FAIL"
                print("  {}: WR={:.0f}% PF={:.1f} DD={:.1f}% Sharpe={:.1f} P&L=${:.0f} ({}) {}".format(
                    ticker, r['win_rate_percent'], r['profit_factor'],
                    r['max_drawdown_percent'], r['sharpe_ratio'],
                    r['total_net_pnl'], r['n_trades'], verdict))
            else:
                failed.append((ticker, r.get('error')))
                print("  {}: ERROR - {}".format(ticker, r.get('error')))

        # Sector summary
        if ticker_results:
            n = len(ticker_results)
            avg_wr = np.mean([r['win_rate_percent'] for r in ticker_results])
            avg_pf = np.mean([r['profit_factor'] for r in ticker_results])
            avg_dd = np.mean([r['max_drawdown_percent'] for r in ticker_results])
            avg_sharpe = np.mean([r['sharpe_ratio'] for r in ticker_results])
            total_pnl = sum(r['total_net_pnl'] for r in ticker_results)
            passed = sum(1 for r in ticker_results if r['win_rate_percent'] >= 75 and
                         r['profit_factor'] >= 1.2 and r['max_drawdown_percent'] < 20)
            avg_trades = np.mean([r['n_trades'] for r in ticker_results])

            sector_results[sector_name] = {
                'tickers_tested': n,
                'tickers_failed': len(failed),
                'passed': passed,
                'pass_rate': passed / n * 100 if n > 0 else 0,
                'avg_win_rate': avg_wr,
                'avg_profit_factor': avg_pf,
                'avg_max_dd': avg_dd,
                'avg_sharpe': avg_sharpe,
                'total_pnl': total_pnl,
                'avg_trades': avg_trades,
                'results': ticker_results,
                'characteristics': sector_data['characteristics']
            }

            print("  >> {}: {}/{} PASS | WR={:.0f}% | PF={:.1f} | DD={:.1f}% | Sharpe={:.1f} | P&L=${:.0f}".format(
                sector_name, passed, n, avg_wr, avg_pf, avg_dd, avg_sharpe, total_pnl))
        else:
            sector_results[sector_name] = {
                'tickers_tested': 0,
                'passed': 0,
                'pass_rate': 0,
                'error': 'No valid tickers'
            }

        if failed:
            print("  Failed: {}".format([t for t, e in failed]))

    PARAM_RESULTS[param_key] = sector_results

# ============================================================
# BEST PARAMETER SET PER SECTOR
# ============================================================
print("\n" + "=" * 80)
print("BEST PARAMETER SET PER SECTOR")
print("=" * 80)

best_params = {}
for sector_name in SECTORS.keys():
    best_param = None
    best_score = -999

    for param_name, sector_results in PARAM_RESULTS.items():
        if sector_name in sector_results:
            sr = sector_results[sector_name]
            if sr['tickers_tested'] > 0:
                # Score: WR (40%) + PF (30%) + (100-DD) (20%) + Sharpe (10%)
                score = (
                    sr['avg_win_rate'] / 100 * 40 +
                    min(sr['avg_profit_factor'], 10) / 10 * 30 +
                    (100 - min(sr['avg_max_dd'], 100)) / 100 * 20 +
                    min(max(sr['avg_sharpe'], 0), 5) / 5 * 10
                )
                if score > best_score:
                    best_score = score
                    best_param = param_name

    best_params[sector_name] = best_param
    print("{}: Best = {} (score={:.1f})".format(sector_name, best_param, best_score))

# ============================================================
# GENERATE MARKDOWN REPORT
# ============================================================
print("\n" + "=" * 80)
print("GENERATING REPORT...")
print("=" * 80)

# Save detailed results
import json
results_summary = {}
for param_name, sector_results in PARAM_RESULTS.items():
    for sector_name, sr in sector_results.items():
        if 'results' in sr:
            for r in sr['results']:
                ticker = r['ticker']
                if ticker not in results_summary:
                    results_summary[ticker] = {}
                results_summary[ticker][param_name] = {
                    'wr': r['win_rate_percent'],
                    'pf': r['profit_factor'],
                    'dd': r['max_drawdown_percent'],
                    'sharpe': r['sharpe_ratio'],
                    'pnl': r['total_net_pnl'],
                    'n': r['n_trades'],
                    'verdict': 'PASS' if r['win_rate_percent'] >= 75 and r['profit_factor'] >= 1.2 and r['max_drawdown_percent'] < 20 else 'FAIL'
                }

# Save JSON for AI agents
with open('sector_analysis_results.json', 'w') as f:
    json.dump(results_summary, f, indent=2)
print("Saved sector_analysis_results.json")

print("\nAnalysis complete! Run the report generator next.")