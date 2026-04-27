# Institutional Iron Condor — Sector Deep-Dive Audit

## Agentic Quant Terminal V2 — 35 Tickers, 7 Sectors

Audited backtester: [`skills/backtester_audit.py`](../../skills/backtester_audit.py)

**Generated (UTC):** `2026-04-12T12:07:18.919912+00:00`

---

## Executive Summary

Universe: **35** tickers, **7** sectors (top 5 by liquidity / market cap). Each run: **5 contracts** per trade, **252** calendar days lookback, adaptive wing/DTE/IV Rank, earnings filter on, 50% profit take, 100% credit stop.

- **WORKING** (WR ≥ 75%, PF ≥ 1.2, max DD < 20%): **3/35**
- **MARGINAL** (WR ≥ 60%, PF ≥ 0.8, and not failing on DD/WR/PF rules): **14/35**
- **FAILING** (WR < 60% **or** PF < 0.8 **or** max DD > 20%): **18/35**
- **NO_DATA** (no trades / data error): **0/35**

### Sector rollup

| Sector | Tested | Working | Marginal | Failing | No data | Avg WR% | Avg PF | Sector P&L $ |
|--------|--------|---------|----------|---------|---------|---------|--------|-------------|
| Consumer Discretionary | 5 | 0 | 1 | 4 | 0 | 40.0 | 1.33 | -2465.32 |
| Consumer Staples | 5 | 0 | 1 | 4 | 0 | 46.67 | 0.61 | -4020.13 |
| Energy | 5 | 0 | 1 | 4 | 0 | 26.67 | 1.18 | -10700.68 |
| Financials | 5 | 0 | 3 | 2 | 0 | 53.33 | 2.69 | 12191.1 |
| Healthcare | 5 | 0 | 4 | 1 | 0 | 60.0 | 1.71 | 15432.71 |
| Industrials | 5 | 1 | 1 | 3 | 0 | 46.67 | 21.16 | -8270.23 |
| Technology | 5 | 2 | 3 | 0 | 0 | 80.0 | 43.03 | 39662.59 |

---

## Methodology

- **Engine:** `IronCondorBacktester.run()` — 70/30 in-sample vs out-of-sample split.
- **IV at entry:** 30d realized vol × VOLATILITY_RATIO (1.4); IV Rank from 252d history of realized vol when available.
- **Per-ticker JSON:** IV used range, IV raw range, IV Rank range at entries, avg adaptive wing % and DTE, barrier counts, `trade_sample` (up to 3 trades, scalar fields).

---

## Sector Analysis

### Technology (AAPL, MSFT, NVDA, META, GOOGL)

| Ticker | Class | WR% | PF | Max DD% | Sharpe | Sortino | Calmar | Trades | P&L $ | Avg credit | IV used range | IV Rank range | Avg wing% | Avg DTE | Barriers pt/sl/time/exp/fc |
|--------|-------|-----|-----|---------|--------|---------|--------|--------|--------|------------|---------------|---------------|-----------|---------|---------------------------|
| AAPL | WORKING | 100.0 | 99.99 | 0.0 | 4.36 | 0 | 0 | 3 | 6266.92 | 4.204 | 0.28–0.3824 | 50.0–50.0 | 0.05 | 21.67 | 0/0/0/1/2 |
| MSFT | MARGINAL | 66.67 | 0.99 | 6.92 | 1.27 | 0 | 3.49 | 3 | -100.68 | 7.9589 | 0.2765–0.3816 | 50.0–50.0 | 0.05 | 21.45 | 0/0/0/1/2 |
| NVDA | MARGINAL | 66.67 | 10.28 | 0.54 | 3.64 | 0 | 65.39 | 3 | 5007.38 | 4.9076 | 0.3886–0.5959 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| META | WORKING | 100.0 | 99.99 | 0.4 | 3.82 | 0 | 374.32 | 3 | 21687.2 | 17.7509 | 0.5248–0.6155 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| GOOGL | MARGINAL | 66.67 | 3.9 | 2.35 | 2.89 | 0 | 20.18 | 3 | 6801.77 | 7.4929 | 0.2805–0.5827 | 50.0–50.0 | 0.05 | 21.32 | 0/1/0/0/2 |

- **Working:** AAPL, META
- **Marginal:** MSFT, NVDA, GOOGL
- **Failing:** —
- **No data:** —

**What works / what fails in this sector:**
- Selective: only some names pass; use whitelist within sector rather than sector-wide automation.

### Financials (JPM, BAC, GS, MS, V)

| Ticker | Class | WR% | PF | Max DD% | Sharpe | Sortino | Calmar | Trades | P&L $ | Avg credit | IV used range | IV Rank range | Avg wing% | Avg DTE | Barriers pt/sl/time/exp/fc |
|--------|-------|-----|-----|---------|--------|---------|--------|--------|--------|------------|---------------|---------------|-----------|---------|---------------------------|
| JPM | MARGINAL | 66.67 | 7.89 | 0.59 | 2.98 | 0 | 50.61 | 3 | 4035.37 | 6.9732 | 0.2418–0.5289 | 50.0–50.0 | 0.05 | 22.61 | 0/0/0/1/2 |
| BAC | FAILING | 33.33 | 0.17 | 1.42 | -1.77 | -1.02 | -2.36 | 3 | -965.46 | 0.9808 | 0.3126–0.3487 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| GS | MARGINAL | 66.67 | 1.65 | 8.4 | 1.6 | 0.96 | 6.79 | 3 | 5416.58 | 21.4805 | 0.3061–0.5355 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| MS | FAILING | 33.33 | 1.07 | 1.25 | 1.21 | 1.3 | 5.27 | 3 | 123.16 | 3.6348 | 0.2723–0.4289 | 50.0–50.0 | 0.05 | 21.59 | 0/0/0/1/2 |
| V | MARGINAL | 66.67 | 2.69 | 2.11 | 2.51 | 0 | 13.27 | 3 | 3581.45 | 6.687 | 0.2464–0.4558 | 50.0–50.0 | 0.05 | 22.45 | 0/0/0/1/2 |

- **Working:** —
- **Marginal:** JPM, GS, V
- **Failing:** BAC, MS
- **No data:** —

**What works / what fails in this sector:**
- Broad short-vol profile is weak here under current wings/stops; widen wings, reduce size, or skip sector.

### Healthcare (UNH, JNJ, LLY, ABBV, MRK)

| Ticker | Class | WR% | PF | Max DD% | Sharpe | Sortino | Calmar | Trades | P&L $ | Avg credit | IV used range | IV Rank range | Avg wing% | Avg DTE | Barriers pt/sl/time/exp/fc |
|--------|-------|-----|-----|---------|--------|---------|--------|--------|--------|------------|---------------|---------------|-----------|---------|---------------------------|
| UNH | FAILING | 33.33 | 0.14 | 7.26 | -1.87 | -1.86 | -2.92 | 3 | -5012.75 | 9.1709 | 0.5305–0.8616 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| JNJ | MARGINAL | 66.67 | 1.49 | 5.1 | 0.39 | 0.47 | 0.69 | 3 | 1503.13 | 4.3614 | 0.341–0.3612 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| LLY | MARGINAL | 66.67 | 2.43 | 10.34 | 2.54 | 0 | 14.87 | 3 | 14761.2 | 32.0202 | 0.6012–0.816 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| ABBV | MARGINAL | 66.67 | 1.87 | 2.69 | 2.41 | 0 | 10.09 | 3 | 2355.27 | 5.5962 | 0.3156–0.5306 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| MRK | MARGINAL | 66.67 | 2.61 | 1.14 | 2.46 | 0 | 11.42 | 3 | 1825.86 | 3.031 | 0.3906–0.5585 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |

- **Working:** —
- **Marginal:** JNJ, LLY, ABBV, MRK
- **Failing:** UNH
- **No data:** —

**What works / what fails in this sector:**
- Broad short-vol profile is weak here under current wings/stops; widen wings, reduce size, or skip sector.

### Consumer Discretionary (AMZN, TSLA, HD, MCD, NKE)

| Ticker | Class | WR% | PF | Max DD% | Sharpe | Sortino | Calmar | Trades | P&L $ | Avg credit | IV used range | IV Rank range | Avg wing% | Avg DTE | Barriers pt/sl/time/exp/fc |
|--------|-------|-----|-----|---------|--------|---------|--------|--------|--------|------------|---------------|---------------|-----------|---------|---------------------------|
| AMZN | FAILING | 33.33 | 0.35 | 3.33 | -0.66 | -1.24 | -1.88 | 3 | -3575.89 | 5.3554 | 0.4626–0.4811 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| TSLA | FAILING | 33.33 | 3.64 | 2.17 | 2.62 | 5.54 | 25.08 | 3 | 5718.34 | 14.2383 | 0.6236–0.8734 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| HD | FAILING | 33.33 | 0.33 | 11.86 | -2.27 | -1.24 | -2.56 | 3 | -6086.44 | 7.9684 | 0.3372–0.4593 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| MCD | MARGINAL | 66.67 | 1.58 | 3.12 | 1.84 | 0 | 6.36 | 3 | 1817.71 | 5.4929 | 0.2465–0.374 | 50.0–50.0 | 0.05 | 22.45 | 0/0/0/1/2 |
| NKE | FAILING | 33.33 | 0.77 | 1.54 | -0.03 | -0.02 | -0.08 | 3 | -339.04 | 2.0401 | 0.3784–0.9463 | 50.0–50.0 | 0.05 | 21.0 | 0/1/0/0/2 |

- **Working:** —
- **Marginal:** MCD
- **Failing:** AMZN, TSLA, HD, NKE
- **No data:** —

**What works / what fails in this sector:**
- Broad short-vol profile is weak here under current wings/stops; widen wings, reduce size, or skip sector.

### Consumer Staples (WMT, KO, PEP, PG, COST)

| Ticker | Class | WR% | PF | Max DD% | Sharpe | Sortino | Calmar | Trades | P&L $ | Avg credit | IV used range | IV Rank range | Avg wing% | Avg DTE | Barriers pt/sl/time/exp/fc |
|--------|-------|-----|-----|---------|--------|---------|--------|--------|--------|------------|---------------|---------------|-----------|---------|---------------------------|
| WMT | FAILING | 33.33 | 0.26 | 4.27 | -2.62 | -1.41 | -2.96 | 3 | -2415.29 | 2.5092 | 0.2687–0.4097 | 50.0–50.0 | 0.05 | 21.71 | 0/0/0/1/2 |
| KO | FAILING | 66.67 | 0.67 | 2.16 | -0.98 | -0.57 | -1.6 | 3 | -482.55 | 1.0376 | 0.2225–0.2572 | 50.0–50.0 | 0.05 | 25.44 | 0/0/0/1/2 |
| PEP | FAILING | 33.33 | 0.62 | 3.38 | -0.88 | -1.24 | -1.73 | 3 | -1136.53 | 2.975 | 0.3419–0.4531 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| PG | FAILING | 33.33 | 0.22 | 4.54 | -1.95 | -2.12 | -2.93 | 3 | -3358.08 | 2.7841 | 0.2452–0.3989 | 50.0–50.0 | 0.05 | 22.49 | 0/0/0/1/2 |
| COST | MARGINAL | 66.67 | 1.27 | 18.32 | 0.63 | 0.43 | 1.05 | 3 | 3372.32 | 18.031 | 0.233–0.4038 | 50.0–50.0 | 0.05 | 22.9 | 0/0/0/1/2 |

- **Working:** —
- **Marginal:** COST
- **Failing:** WMT, KO, PEP, PG
- **No data:** —

**What works / what fails in this sector:**
- Broad short-vol profile is weak here under current wings/stops; widen wings, reduce size, or skip sector.

### Energy (XOM, CVX, COP, EOG, SLB)

| Ticker | Class | WR% | PF | Max DD% | Sharpe | Sortino | Calmar | Trades | P&L $ | Avg credit | IV used range | IV Rank range | Avg wing% | Avg DTE | Barriers pt/sl/time/exp/fc |
|--------|-------|-----|-----|---------|--------|---------|--------|--------|--------|------------|---------------|---------------|-----------|---------|---------------------------|
| XOM | FAILING | 0.0 | 0.0 | 2.9 | -2.48 | -4.42 | -3.72 | 3 | -3047.38 | 2.8678 | 0.2628–0.4752 | 50.0–50.0 | 0.05 | 21.91 | 0/0/0/1/2 |
| CVX | FAILING | 0.0 | 0.0 | 6.05 | -3.24 | -2.46 | -3.55 | 3 | -6089.87 | 4.1161 | 0.2557–0.5458 | 50.0–50.0 | 0.05 | 22.14 | 0/0/0/1/2 |
| COP | FAILING | 33.33 | 0.35 | 1.68 | -0.72 | -0.92 | -1.53 | 3 | -1400.89 | 2.9088 | 0.3014–0.6762 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| EOG | FAILING | 33.33 | 0.4 | 2.54 | -1.18 | -0.61 | -1.79 | 3 | -1401.23 | 2.7585 | 0.2775–0.5302 | 50.0–50.0 | 0.05 | 21.42 | 0/0/0/1/2 |
| SLB | MARGINAL | 66.67 | 5.17 | 0.35 | 2.46 | 2.84 | 16.43 | 3 | 1238.69 | 1.5185 | 0.4313–0.8216 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |

- **Working:** —
- **Marginal:** SLB
- **Failing:** XOM, CVX, COP, EOG
- **No data:** —

**What works / what fails in this sector:**
- Broad short-vol profile is weak here under current wings/stops; widen wings, reduce size, or skip sector.

### Industrials (BA, CAT, GE, RTX, UPS)

| Ticker | Class | WR% | PF | Max DD% | Sharpe | Sortino | Calmar | Trades | P&L $ | Avg credit | IV used range | IV Rank range | Avg wing% | Avg DTE | Barriers pt/sl/time/exp/fc |
|--------|-------|-----|-----|---------|--------|---------|--------|--------|--------|------------|---------------|---------------|-----------|---------|---------------------------|
| BA | FAILING | 33.33 | 0.78 | 5.37 | 0.18 | 0.11 | 0.26 | 3 | -1095.15 | 6.6293 | 0.3471–0.7664 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| CAT | FAILING | 0.0 | 0.0 | 16.86 | -3.53 | -3.15 | -3.03 | 3 | -15356.73 | 18.7902 | 0.3133–0.7054 | 50.0–50.0 | 0.05 | 21.0 | 0/1/0/0/2 |
| GE | WORKING | 100.0 | 99.99 | 0.0 | 3.74 | 0 | 0 | 3 | 6560.61 | 8.0031 | 0.3336–0.5923 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |
| RTX | MARGINAL | 66.67 | 4.49 | 1.2 | 2.33 | 3.75 | 12.62 | 3 | 2925.94 | 4.1347 | 0.2814–0.4656 | 50.0–50.0 | 0.05 | 21.29 | 0/0/0/1/2 |
| UPS | FAILING | 33.33 | 0.53 | 4.13 | -1.31 | -3.95 | -1.8 | 3 | -1304.9 | 2.8227 | 0.4435–0.5588 | 50.0–50.0 | 0.05 | 21.0 | 0/0/0/1/2 |

- **Working:** GE
- **Marginal:** RTX
- **Failing:** BA, CAT, UPS
- **No data:** —

**What works / what fails in this sector:**
- Selective: only some names pass; use whitelist within sector rather than sector-wide automation.

---

## Best Conditions for Strategy Success

Institutional **PASS** in-engine: WR ≥ 75%, PF ≥ 1.2, max DD < 20%.

### Observed: WR > 80% and PF > 2.0

- **AAPL** (Technology): WR 100.0%, PF 99.99
- **META** (Technology): WR 100.0%, PF 99.99
- **GE** (Industrials): WR 100.0%, PF 99.99

### General patterns

- Large-cap liquid names with moderate realized vol and IV Rank above adaptive floor
- Fewer gap-driven single-name events than high-beta discretionary
- Sufficient credit vs wing width (passes min credit filter)

---

## Failure Modes and Risk Patterns

- High-beta names with frequent large daily moves vs wing width
- Max drawdown > 20% fails deployment even if win rate is high
- Binary event risk not fully removed by coarse earnings calendar

### Tickers flagged FAILING or NO_DATA

- **AMZN** (Consumer_Discretionary): WR 33.33%, PF 0.35, DD 3.33%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **BA** (Industrials): WR 33.33%, PF 0.78, DD 5.37%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **BAC** (Financials): WR 33.33%, PF 0.17, DD 1.42%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **CAT** (Industrials): WR 0.0%, PF 0.0, DD 16.86%, barriers {'pt': 0, 'sl': 1, 'time': 0, 'exp': 0, 'forced_close': 2}
- **COP** (Energy): WR 33.33%, PF 0.35, DD 1.68%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **CVX** (Energy): WR 0.0%, PF 0.0, DD 6.05%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **EOG** (Energy): WR 33.33%, PF 0.4, DD 2.54%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **HD** (Consumer_Discretionary): WR 33.33%, PF 0.33, DD 11.86%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **KO** (Consumer_Staples): WR 66.67%, PF 0.67, DD 2.16%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **MS** (Financials): WR 33.33%, PF 1.07, DD 1.25%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **NKE** (Consumer_Discretionary): WR 33.33%, PF 0.77, DD 1.54%, barriers {'pt': 0, 'sl': 1, 'time': 0, 'exp': 0, 'forced_close': 2}
- **PEP** (Consumer_Staples): WR 33.33%, PF 0.62, DD 3.38%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **PG** (Consumer_Staples): WR 33.33%, PF 0.22, DD 4.54%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **TSLA** (Consumer_Discretionary): WR 33.33%, PF 3.64, DD 2.17%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **UNH** (Healthcare): WR 33.33%, PF 0.14, DD 7.26%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **UPS** (Industrials): WR 33.33%, PF 0.53, DD 4.13%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **WMT** (Consumer_Staples): WR 33.33%, PF 0.26, DD 4.27%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}
- **XOM** (Energy): WR 0.0%, PF 0.0, DD 2.9%, barriers {'pt': 0, 'sl': 0, 'time': 0, 'exp': 1, 'forced_close': 2}

---

## AI Agent Optimization Recommendations

1. **IV source:** Swap realized×1.4 for options-chain ATM IV or IV Rank from a vendor; align `adaptive_iv_rank_min` with real IV Rank.
2. **Drawdown gate:** Treat `max_drawdown_percent > 20` as hard FAIL for promotion even if PF is high (see plan failing rules).
3. **High-beta discretionary:** Down-weight or block when 20d realized vol exceeds sector-specific threshold; many fails cluster there.
4. **Wing / DTE:** For high `sl` share, raise `adaptive_wing` floor or shorten DTE; re-run sector basket after each change.
5. **Sample size:** OOS often yields few trades; require minimum N and walk-forward windows before live capital.
6. **Margin realism:** With **5 contracts**, scale Reg-T/SPAN estimates in reporting; `avg_capital_per_trade` is wing-based proxy only.

---

## Final Recommendations

**Deploy-first watchlist (WORKING this run):** AAPL (Technology), META (Technology), GE (Industrials).

**Sectors:** Prefer follow-up sizing on sectors with multiple WORKING names; treat Energy and broad Staples as suspect until structural edge improves.

**Parameters:** Keep `profit_take_pct=0.50`, `stop_loss_mult=1.0`, `earnings_filter=True`, `use_adaptive=True`, `num_contracts=5` for comparability to this audit.

---

## Machine-Readable Outputs

- [`TICKER_RESULTS.json`](./TICKER_RESULTS.json)
- [`SECTOR_SUMMARY.json`](./SECTOR_SUMMARY.json)
- [`BEST_CONDITIONS.json`](./BEST_CONDITIONS.json)
