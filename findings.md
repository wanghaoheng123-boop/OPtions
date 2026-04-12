# Findings: Institutional Agentic Options Terminal

> Last Updated: 2026-04-12

---

## Architecture Decisions

| Date | Finding | Implication |
|------|---------|-------------|
| 2026-04-12 | Duplicate `/api/statarb` route in `backend/main.py` (lines 121 and 130) | FastAPI will only register the second one; first is shadowed |
| 2026-04-12 | `ParameterOptimizer` grid search is mathematically mocked — it runs the same backtest 18 times with no parameter injection | No actual optimization occurs; all grid entries return identical results |
| 2026-04-12 | `StrategyBacktester` uses OOS data for EWMA volatility calculation, then applies those barriers to the same OOS data | Triple Barrier methodology broken — violates AFML Ch. 3 principle |
| 2026-04-12 | `MetaModel` is never trained — `train_meta_model()` is defined but never called from any code path | `get_bet_size()` always falls back to 1.0 |
| 2026-04-12 | `PaperTrader` only logs entry — no exit logic, realized PnL, or position tracking | Cannot evaluate trade performance |
| 2026-04-12 | No cointegration test in `StatArbScanner` — only price ratio Z-score | Will trade spurious correlations that mean-revert permanently |
| 2026-04-12 | HFT GEX uses simulated OI with `random.randint()` — no real market data | Real-time GEX surface is fictional |
| 2026-04-12 | No Sharpe/Sortino/Calmar anywhere in codebase | Cannot properly evaluate risk-adjusted returns |
| 2026-04-12 | `GreeksCalculator` missing theta, rho, vanna, charm | Second-order Greeks referenced but not computed |
| 2026-04-12 | `volatility_skew.py` has no IV Rank or IV Percentile — critical for QUANT_KB Rule 1 | Cannot enforce "never buy premium when IV Rank > 50" |

---

## Technical Discoveries

### Black-Scholes Implementation
- Current `greeks_calculator.py` uses `scipy.stats.norm` correctly for CDF/PDF
- Fixed: missing dividend yield (q) in d1/d2 — affects call/put parity for dividend stocks
- Fixed: Added theta (time decay per day), rho (interest rate sensitivity)
- Fixed: Added vanna (dDelta/dVol) and charm (dDelta/dTime) — second-order cross-Greeks
- Also added: color (dGamma/dTime), speed (d2Gamma/dS2) — third-order Greeks

### Triple Barrier Backtester — REBUILT
- Uses daily OHLCV closes as price series (not tick data)
- Fixed: EWMA volatility from IN-SAMPLE only, applied to OUT-OF-SAMPLE
- Fixed: Added Sharpe, Sortino, Calmar metrics
- Fixed: barrier_hits tracking (PT/SL/Time counts per strategy)
- Added: trained_volatility output for transparency
- Added: walk_forward_optimized flag for WFO verification

### Kelly Criterion — REBUILT
- Formula: `W - ((1-W)/R)` where R = avg_win / avg_loss from backtest stats
- Fixed: was using fixed R=1.0, now derives from actual profit_factor and win_rate
- Half-Kelly cap at 1%-20% per QUANT_KB Rule
- Added: is_reliable flag when trades < 30 (insufficient data warning)

### HMM Regime Detection
- Uses 2 features only: Returns and (High-Low)/Close range proxy
- Should incorporate: VIX, gamma tilt, macro regime, market breadth
- 3 states may not be enough — typical markets have 4+ regimes

### StatArb Pairs Trading — REBUILT
- Fixed: Now includes Engle-Granger two-step cointegration test
- Only trades pairs with ADF p-value < 0.05 (95% confidence)
- Added: half_life calculation for mean reversion duration
- Added: 17 institutional pairs including rates, commodities, international
- Added: backtest_pairs_strategy() for historical validation
- Extended pairs: SPY/QQQ, XLK/XLV, IWM/SPY, XLF/XLE, GLD/SLV + 12 more

### Walk-Forward Optimization — REBUILT
- Fixed: Rolling WFO with expanding or rolling windows
- Grid search over 192 parameter combinations (4 TP x 4 SL x 3 Time x 4 EWMA)
- Proper parameter injection into backtester simulation
- quick_scan() for rapid 70/30 single-split when full WFO too slow

### Paper Trading — REBUILT
- Full entry/exit tracking with Triple Barrier compliance
- Realized and unrealized PnL per position
- Position limits: max 5 concurrent, max 25% portfolio concentration
- Daily loss circuit breaker: stops trading at 5% daily DD
- Kelly sizing with is_reliable flag for insufficient trade counts
- Force close capability for manual intervention
- Research usage logging integrated

### Meta-Labeling — REBUILT (Phase 2)
- Production MetaLabeler with 10 engineered features:
  - z_score_price (Z-score vs 20-day MA)
  - z_score_slow (Z-score vs 60-day MA)
  - plus_dm_ratio / minus_dm_ratio (ADX proxy)
  - ret_5d, ret_10d, ret_20d (momentum features)
  - vol_ratio_10d, vol_ratio_30d (volatility regime)
  - price_vs_ma200 (trend indicator)
  - volume_ratio, distance_from_ma20_pct
- Binary labels: 1 if primary strategy made money, 0 if loss
- Returns probability (0-1) for bet sizing
- Thresholds: prob < 0.50 → REJECT (regime shift detected)
- Training stats: accuracy, precision, recall, F1, AUC-ROC
- Out-of-sample evaluation method
- Model save/load with joblib

### Kalman Filter Pairs Trading — NEW (Phase 2)
- KalmanFilterPairs: dynamic hedge ratio (time-varying, not static OLS)
- State equation: beta_t = beta_{t-1} + noise (random walk)
- Observation: y_t = alpha + beta_t * x_t + noise
- Adaptive to changing market relationships
- get_signal() returns: NO_SIGNAL / SHORT_SPREAD / LONG_SPREAD / EXIT
- KalmanFilterPairTrader: manages multiple pairs with position tracking
- scan_pairs_kalman() in StatArbScanner integrates Kalman with Z-score signals
- get_institutional_pairs_scan() for 17-pair institutional universe

### Orchestrator — REBUILT (Phase 2)
- Production multi-agent loop with real MetaLabeler integration
- select_strategy() rule-based strategy selection from market conditions
- get_trader_insight() generates reasoning per strategy type
- get_critic_review() with hard constraints (WR>=75%, PF>=1.2, DD<20%) + soft (Sharpe, Sortino, Calmar)
- run_agentic_loop() coordinates: Researcher → Trader → Optimizer → Backtester → MetaModel → Critic → Memory
- run_batch_analysis() for multi-ticker screening
- Full analysis response: strategy, trader insight, researcher context, optimization params, backtest, meta verdict, critic review, recommendation

---

## Lessons Learned

### What Worked
- Black-Scholes d1/d2 formula is correct and numerically stable
- Volatility skew sentiment classification (Extreme Fear/Bullish Greed) is well-designed
- Agent orchestration pattern (Trader → Backtester → Critic → MetaModel) is architecturally sound
- Kelly Criterion position sizing is the right approach for institutional allocation

### What Didn't
- Mock LLM query in orchestrator.py is not replaceable without breaking flow
- Static algorithm dictionary in GitHubResearcher prevents real knowledge growth
- Paper trading has no exit logic — cannot measure performance

### What Needs Research
- True options PnL modeling (not just underlying price moves)
- Real-time GEX from market data providers (Polygon.io, Databento, ThetaData)
- IBKR API for live options execution
- Johansen cointegration test vs Engle-Granger for multivariate relationships

---

## Research References

- Lopez de Prado, "Advances in Financial Machine Learning" (AFML) — Triple Barrier, Meta-Labeling, Dollar Bars
- Thorp, "Kelly Capital Growth Investment" — Kelly Criterion institutional use
- Hamilton, "A New Approach to Economic Analysis of Nonstationary Time Series" (1989) — Markov regime switching
- Gatev et al., "Pairs Trading: Performance of a Relative Value Arbitrage Rule" — cointegration-based pairs trading
- Grinold & Kahn, "Active Portfolio Management" — institutional portfolio construction
- Aldridge, "High-Frequency Trading" — transaction cost modeling

---

## Open Questions

1. **Q1**: Should we use 0DTE options data or stick to standard weekly expirations? → Need to research 0DTE microstructure
2. **Q2**: Real-time GEX data source? Currently simulated → Need to evaluate Polygon.io vs Databento vs ThetaData
3. **Q3**: Should we implement a full options pricing model (Barone-Adesi-Whaley) or stay with Black-Scholes? → AAW for American options
4. **Q4**: Should HMM use VIX as exogenous variable? → Yes, increases regime accuracy
5. **Q5**: Kalman Filter for pairs — what state dimension? → 2D: price ratio + hedge ratio

---

## Next Investigation

- Verify actual yfinance option chain structure (column names may differ by version)
- Test real FRED API access with demo key
- Benchmark `fracdiff` library for fractional differentiation

---

## Phase 3: HMM Regime Detection — COMPLETED

### 4-State Gaussian HMM — Production Implementation
- 4 hidden states: Bull, Bear, High-Vol Bear, Low-Vol Chop
- 7 features: returns, realized_vol, hl_range, volume_change, vix_proxy, trend_signal, mean_reversion
- Strategy mapping per regime:
  - Bull + High Vol → covered_call (TREND_FOLLOWING)
  - Bear + High Vol → wheel / short_put (CASH_SECURED_PUTS)
  - Chop + Low Vol → iron_condor / short_strangle (RANGE_BOUND)
  - High-Vol Bear → defensive covered_call (DEFENSIVE)
- Regime-adaptive strategy override based on GEX and IV Rank
- Historical validation: tests state distribution during VIX > 30 and drawdown periods
- Confidence scoring: STABLE (P > 0.6), TRANSITIONAL (0.4-0.6), UNCERTAIN (<0.4)

---

## Phase 4: Frontend & Backend Integration — COMPLETED

### New API Endpoints (8 added)
- POST /api/backtest — Standalone backtest on ticker/strategy
- POST /api/backtest/optimize — Parameter-optimized backtest
- GET /api/hmm/{ticker} — 4-state HMM regime detection
- GET /api/hmm/{ticker}/validation — Historical VIX/drawdown validation
- GET /api/meta/{ticker} — Meta-labeling bet size from Random Forest
- GET /api/statarb/kalman — Kalman-filtered dynamic hedge ratio pairs
- GET /api/statarb/institutional — Full 17-pair institutional universe scan
- POST /api/portfolio/execute — Paper trade execution

### FastAPI Serialization Fix
- Root cause: numpy.bool_, numpy.integer, numpy.floating not JSON serializable
- Fix: `_sanitize()` function converts all numpy types to native Python before jsonable_encoder
- Applied to all 23 endpoints and WebSocket feed

### TerminalMosaic Updates (9 panels)
- HMM Regime panel: shows state label, recommended strategy, confidence, vol regime, VIX proxy
- MetaModel ML panel: shows bet size, verdict (APPROVE/REJECT), confidence, reason
- IV Rank/Percentile panel: shows rank %, percentile %, verdicts (SELL_PREMIUM/BUY_PREMIUM)
- Expanded backtest metrics: Sharpe, Sortino, Calmar, barrier_hits (PT/SL/Time counts)
- Optimization params displayed per recommendation
- Layout expanded to 12-column grid