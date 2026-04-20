# Findings: Institutional Agentic Options Terminal

> Last Updated: 2026-04-20

---

## Completion Snapshot (2026-04-20)

- Project roadmap phases are complete in code; remaining gates are external credentials/data access, not missing implementation.
- Full validation sweep passed on 2026-04-20:
  - `python -m pytest tests/ -m "not network" -q` -> 4 passed
  - `python -m pytest tests/ -m network -q` -> 4 passed
  - `python scripts/validate_regression.py --tickers SPY,QQQ,IWM --days 400` -> REGRESSION OK
  - `python scripts/validate_batch_backtest.py --basket --days 400` -> VALIDATION OK (institutional_pass 3/3)
  - `cd frontend && npm run test:e2e` -> 5 passed, 1 skipped
- External dependency status:
  - **FRED**: no key -> expected fallback (`FRED_API_KEY_MISSING` + mock macro panel values)
  - **GitHub researcher**: no token -> verified static algorithm registry path remains primary
  - **Alpaca**: keys unlock REST account/contracts; multi-leg order automation intentionally rejected (`ALPACA_MULTI_LEG_NOT_IMPLEMENTED`)

## 15-Phase Program Snapshot (2026-04-20)

- Program artifacts created in `review/PROGRAM15/` covering scope freeze, inventory/contracts, reliability uplift, validation/risk, and closure.
- Critical quant loop hardening delivered:
  - single-position progression and OOS IV-rank alignment in `skills/backtester.py`
  - optimizer cache contamination remediation in `skills/parameter_optimizer.py`
  - orchestrator backtest-key compatibility in `core_agents/orchestrator.py`
- Reliability and CI uplift delivered:
  - macro series shape compatibility in `frontend/src/components/MacroSearchTerminal.tsx`
  - added tests: `tests/test_integrity_quant.py`, `tests/test_contract_expansion.py`
  - strict release-gates CI job in `.github/workflows/ci.yml`
- Validation matrix passed (`pytest` non-network + network, regression, strict batch, frontend e2e).

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

## Skill and data audit (rolling — 2026-04-18)

High-level map for due diligence: each row is a **proxy** with known blind spots; extend when modules change.

| Module / skill | Primary data | Known limits | Tests / gates |
|----------------|--------------|--------------|----------------|
| `market_data_api` | yfinance OHLCV | Not live tape; gaps/revisions | `test_chart_spy_contract` (network) |
| `options_chain_fetcher` | Chain vendor / yfinance | Empty chain on illiquid names | `/api/analyze` contract (network) |
| `gamma_exposure` | OI × model Greeks | OI timing; model vs market IV | GEX live test (network, may skip) |
| `volatility_skew` | Chain IV / history | Proxy IV, lookback quality | Indirect via analyze |
| `backtester` | yfinance bars + BS proxy | Not tick fills; parameter risk | `validate_regression.py`, `test_backtest_spy` |
| `paper_trader` | Simulated execution | Not broker accounting | Manual / API integration |
| `regime_hmm` | Return features | Label instability short samples | HMM panel + analyze payload |
| `meta_model` | Trade / return labels | Fallback label path documented README | pytest where trained |

**Ablation discipline:** when comparing runs (flags, spans, filters), log ticker set, flags, and outcome date in [`progress.md`](progress.md) per README §5c.

---

## Peer review charter (2026-04-18)

**Comment sink (agreed for this repo):**

1. **Primary:** GitHub **Issues** using templates under [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/) (`Bug report`, `Peer review note`). Suggested labels: `review`, `bug`, `quant`, `ui`, `wontfix-data-limit` (create labels in the repo settings if missing).
2. **Secondary / offline:** Append a dated bullet under **Peer review log** in this file with the same fields as the template.

**Minimal repro template (copy into any Issue or log):**

- Environment: local | Vercel | other; Python `x.y`; Node `x.y`; API base URL.
- Steps: numbered list from cold start.
- Expected vs actual: one sentence each.
- Evidence: `curl` snippet or Network tab (status + path); no secrets.
- Class: `data` | `contract` | `logic` (see triage playbook below).

**AdversarialReviewer:** before closing an Issue, verify items in [`AGENTS.md`](AGENTS.md) adversarial checklist apply to the change scope, or document a waiver in the Issue.

---

## UI/API review matrix (manual checklist)

Human reviewers complete this on each release candidate; attach evidence (screens + status codes) to the GitHub Issue or paste links in the peer review log.

| # | Area | Check | Pass |
|---|------|--------|------|
| 1 | Dev wiring | Backend listens on same port as Vite proxy (default 8005); README curl health succeeds | [ ] |
| 2 | Discovery | `GlobalDiscoveryFeed` loads; selecting a ticker opens terminal | [ ] |
| 3 | Terminal | Analyze strip / portfolio strip / top banner show sensible messages when endpoints fail | [ ] |
| 4 | Partial load | With analyze failing (e.g. bad ticker), chart still loads for valid OHLC ticker if chart API succeeds | [ ] |
| 5 | Chart | Candlesticks render for SPY; Method drawer loads for `chart` panel | [ ] |
| 6 | Command palette | Ctrl/⌘+K opens; health command returns JSON; Esc closes | [ ] |
| 7 | API | `GET /api/health`, `GET /api/methodology`, `GET /api/chart/SPY`, `POST /api/analyze` (SPY) — note status codes | [ ] |
| 8 | Mosaic panels | GEX, stat-arb, macro tiles do not throw blank uncaught errors when data missing | [ ] |

---

## Root-cause triage playbook

1. **Symptom** — from UI, pytest, or `validate_*.py`.
2. **Minimal repro** — smallest ticker / days / endpoint.
3. **Classify**
   - **Data:** rate limit, empty chain, 404 from vendor → document under methodology / `wontfix-data-limit` or retry policy.
   - **Contract:** UI reads wrong key or backend renamed field → fix mapping; add contract test.
   - **Logic:** wrong formula, NaN propagation, leakage → fix code; add invariant or regression test in [`tests/`](tests/).
4. **Link code** — cite `skills/…` or `backend/main.py` route handler.
5. **Close loop** — PR references Issue; AdversarialReviewer checks [`AGENTS.md`](AGENTS.md) list.

### Automated campaign log (baseline — 2026-04-18)

| Run | Outcome | Triage class |
|-----|---------|--------------|
| `pytest -m "not network"` | 4 passed | N/A |
| `pytest -m network` | 4 passed | N/A |
| `validate_regression.py` SPY,QQQ,IWM | REGRESSION OK | N/A |
| `validate_batch_backtest.py --basket` | VALIDATION OK | N/A |

No root-cause tickets required for this batch. When a row fails: open a Bug report Issue, classify per playbook, link `skills/` or `backend/main.py`, add a regression test if logic/contract.

---

## Optimization loop metrics (baseline — 2026-04-18)

**Process:** measure → one scoped change → verify (`pytest`, `validate_*`, `npm run test:e2e`). Log deltas in [`progress.md`](progress.md). Do **not** treat raw backtest win rate as the primary optimization target without PBO / walk-forward controls (see literature table below).

| Metric | How to capture | Command / artifact |
|--------|----------------|---------------------|
| Fast test reliability | Pass/fail | `python -m pytest tests/ -m "not network" -q` |
| Live-data smoke | Pass/fail | `python -m pytest tests/ -m network -q` |
| UI E2E | Pass/fail | `cd frontend && npm run test:e2e` ([`frontend/e2e/`](frontend/e2e/), mocked `/api`) |
| API latency (local) | `time_total` | `curl` timing for `POST /api/analyze` (see [`README.md`](README.md) curl block); use `/dev/null` or `NUL` per OS |
| Backtest structure | Exit code | `python scripts/validate_regression.py --tickers SPY,QQQ,IWM --days 400` |

Helper (prints commands; `--quick` runs fast pytest): [`scripts/baseline_metrics.py`](scripts/baseline_metrics.py).

---

## External OSS landscape (reviewed — 2026-04-18)

Stars are **order-of-magnitude snapshots** (verify on GitHub before relying on for comparisons). **None of these imply profitability**; they are design and engineering references for this repo’s FastAPI + React + `skills/` layout.

| Project | Language | Why it matters here | Borrow | Avoid / caution |
|---------|----------|---------------------|--------|------------------|
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | Python | Data provider composition, CLI density, agent/MCP patterns | Modular provider interfaces; UX density ideas | Different deploy model; do not copy proprietary data terms |
| [microsoft/qlib](https://github.com/microsoft/qlib) | Python | Pipeline for research → backtest with experiment tracking | Dataset versioning, model zoo patterns | Heavy stack; most alpha claims need independent evaluation |
| [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | Python | Fast vectorized backtests, parameter scans | Vectorized metrics for sweeps; visualization of equity | API shape differs from current `StrategyBacktester` |
| [kernc/backtesting.py](https://github.com/kernc/backtesting.py) | Python | Simple strategy API on OHLCV | Minimal API ergonomics for indicators | Single-threaded assumptions |
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | Python | Live/paper execution discipline, config-driven runs | Risk config patterns, dry-run workflows | Crypto-centric; adapt cautiously to options |
| [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded) | Python | Zipline-class event-driven backtests, bundles, calendars | Pipeline structure for daily equity backtests | Different from options path in this repo; integration is non-trivial |
| [quantopian/empyrical](https://github.com/quantopian/empyrical) | Python | Classic return / risk ratios (Sharpe, Sortino, max drawdown) | Reuse metric definitions for reporting parity | Repository archived; prefer maintained forks for new deps |
| [stefan-jansen/machine-learning-for-trading](https://github.com/stefan-jansen/machine-learning-for-trading) | Python / notebooks | End-to-end ML for trading **book code** | Feature engineering examples next to code | Book edition vs your stack versions |

---

## Selected literature (DOI) — evaluation, labeling, costs

Curated for **this** codebase (triple-barrier style backtests, meta-modeling, execution realism). Use for methodology and **honest** evaluation—not as performance guarantees.

| Work | DOI / ID | One-line takeaway | Applicability |
|------|-----------|-------------------|---------------|
| Bailey, Borwein, López de Prado, Zhu — *The Probability of Backtest Overfitting* | [10.2139/ssrn.2326253](https://doi.org/10.2139/ssrn.2326253) | CSCV / PBO framing for strategy selection bias | **High** — justify why raw WR is not the KPI; add PBO/walk-forward where feasible |
| López de Prado — *Advances in Financial Machine Learning* (Wiley, 2018) | ISBN 978-1-119-48208-6 | Triple barrier labeling, sample weights, meta-labeling | **High** — align `skills/backtester.py` / meta pipeline with documented assumptions |
| Easley et al. — flow / “toxicity” microstructure (classical reference) | multiple venue DOIs — use venue copy | Order flow can be informative but mostly **not** in public retail APIs | **Partial** — do not imply you observe full order flow with yfinance |
| Almgren & Chriss — optimal execution (foundational TCA) | standard journal copies | Explains why slippage / impact models matter | **Partial** — compare to [`TransactionCostModel`](skills/brokers.py) assumptions |
| Cont — empirical properties of asset returns | e.g. Quantitative Finance streams | Stylized facts for vol clustering / fat tails | **Medium** — informs vol proxy limitations in BS-style engines |

OpenAlex broad search is noisy; prefer **known DOIs / ISBN** and library copies for deep reading.

---

## Research backlog (prioritized — create GitHub Issues)

Suggested Issue titles (labels: `research`, `quant`, or `ui`). Triage: data available? testable? copy-safe?

1. **PBO / CSCV spike** — prototype minimal PBO estimate on existing backtest sweep outputs (tie to Bailey et al. DOI above).
2. **Execution model audit** — map `TransactionCostModel` to published TCA assumptions; document gaps in methodology catalog.
3. **Provider abstraction** — sketch interface to swap yfinance for paid OHLC / IV (OpenBB-style), without changing UI contracts.
4. **Playwright coverage** — extend [`frontend/e2e/`](frontend/e2e/) for terminal mosaic panels with broader API mocks (`/api/statarb`, `/api/heatmap`).
5. **Sector heatmap double-path** — investigate Vite log `/api/api/heatmap` when preview runs terminal (possible URL bug in a component).

---

## Peer review log (offline append-only)

_Use dated bullets here if not using GitHub Issues._

- *(none yet)*

### TerminalMosaic Updates (9 panels)
- HMM Regime panel: shows state label, recommended strategy, confidence, vol regime, VIX proxy
- MetaModel ML panel: shows bet size, verdict (APPROVE/REJECT), confidence, reason
- IV Rank/Percentile panel: shows rank %, percentile %, verdicts (SELL_PREMIUM/BUY_PREMIUM)
- Expanded backtest metrics: Sharpe, Sortino, Calmar, barrier_hits (PT/SL/Time counts)
- Optimization params displayed per recommendation
- Layout expanded to 12-column grid