# Task Plan: Institutional Agentic Options Terminal

> Last Updated: 2026-04-12
> Overall Status: PLANNING COMPLETE - ENTERING EXECUTION
> Current Phase: Phase 0 (Setup & Pre-Work)

---

## Project Objective

Transform the Agentic Quant Terminal V2 into an **institutional-grade options trading platform** meeting Goldman Sachs, JPM, Morgan Stanley, and Citi standards. Target: **80%+ win rate** through Volatility Risk Premium (VRP) strategies, AFML-based Triple Barrier methodology.

---

## Agent Assignments

| Agent | Primary | Secondary |
|-------|---------|-----------|
| **Agent-1** | Core Math & Backtesting (1A, 2A, 3A, 5A) | HMM Regime |
| **Agent-2** | Volatility, Greeks, StatArb, MetaModel (1B, 2B, 2C, 3B, 5B) | Research Agent |
| **Agent-3** | Paper Trading, Frontend, UX (1C, 4, 6B, 6C) | Docs, Integration |

---

## Master Task List

### Phase 0: Setup & Pre-Work
- [x] **P0-1**: Create `task_plan.md` (this file) — 2026-04-12
- [x] **P0-2**: Create `findings.md` — 2026-04-12
- [x] **P0-3**: Create `progress.md` — 2026-04-12
- [x] **P0-4**: Create `AGENT_LOG.md` — 2026-04-12
- [x] **P1**: Fix duplicate `/api/statarb` route (`backend/main.py`) — 2026-04-12
- [x] **P3**: Fix `StrategyBacktester` OOS split (EWMA from in-sample only) — 2026-04-12
- [x] **P6**: Fix Kelly Criterion (from actual W/L ratio) + rebuild PaperTrader — 2026-04-12
- [x] **P8**: GitHubResearcher with verified algorithm registry + logging — 2026-04-12
- [x] **P9**: Rebuild PaperTrader with exit/PnL tracking, position limits — 2026-04-12
- [x] **P10**: Rolling Walk-Forward Optimization + grid search — 2026-04-12
- [x] **P11**: Add IV Rank & IV Percentile to volatility_skew — 2026-04-12
- [x] **P12**: Add cointegration testing (Engle-Granger) to StatArbScanner — 2026-04-12
- [x] **P15**: Add Sharpe/Sortino/Calmar calculations to backtester — 2026-04-12
- [x] **Greeks**: Add theta, rho, vanna, charm to greeks_calculator — 2026-04-12
- [ ] **P2**: Fix `ParameterOptimizer` to truly inject parameters — DEFERRED (rebuilt in P10)
- [x] **P4**: Implement actual `MetaModel` training pipeline — trade-entry labels from `trade_log` + orchestrator wiring — 2026-04-18
- [x] **P5**: Add options premium/slippage modeling to backtester — `tc_breakdown` per trade, `tc_summary`, `premium_model` on backtest JSON — 2026-04-18
- [x] **P7**: HFT GEX surface integration with real market data — `HFTOptionsPipeline.from_option_chain`, `GET /api/gex/live/{ticker}`, mosaic polling — 2026-04-18
- [x] **P13**: Implement AbstractBroker (IBKR/Alpaca) — Alpaca REST when keys set; IBKR `IBKR_ENABLE_LIVE` guard — 2026-04-18
- [x] **P14**: Connect frontend to all backend endpoints — Phase 4A (primary mosaic + discovery use `/api/analyze` bundle; other panels use dedicated REST; see README) — 2026-04-18

### Phase 1: Foundation & Core Math (Weeks 1-4)
- [ ] **1A**: Fix critical bugs (Agent-1)
- [ ] **1B**: Greeks & Volatility Foundation (Agent-2)
- [ ] **1C**: Paper Trading & Risk Engine (Agent-3)

### Phase 2: Backtesting & Statistical Infrastructure (Weeks 4-8)
- [x] **2A**: True Triple Barrier + WFO — DONE (P3 fixed in Phase 0, P10 fixed in Phase 0/1)
- [x] **2B**: StatArb cointegration + Kalman Filter — DONE (P12 fixed Phase 0, Kalman Filter added this session)
- [x] **2C**: Meta-Labeling production — DONE (rebuilt with production feature engineering this session)

### Phase 3: HMM Regime & Research Agent (Weeks 8-10)
- [x] **3A**: HMM production with 4-regime model — DONE (7 features, adaptive strategy, historical validation)
- [x] **3B**: GitHub Research Agent — DONE (static registry with institutional algorithms)

### Phase 4: Frontend & UX (Weeks 10-14)
- [x] **4A**: Full dashboard integration — DONE (all endpoints connected to frontend)
- [x] **4B**: Bloomberg-level UI polish — DONE (HMM panel, MetaModel panel, IV Rank/Percentile panel, expanded metrics)

### Phase 5: Broker Integration & Live Trading (Weeks 14-18)
- [x] **5A**: IBKR/Alpaca stubs — DONE (IBKRBroker, AlpacaBroker, TransactionCostModel with commission/spread/slippage)
- [x] **5B**: Transaction cost & slippage modeling — DONE (IBKR: $0.65/contract, Alpaca: $0/contract, market impact model)

### Phase 6: Institutional Validation & Delivery (Weeks 18-24)
- [x] **6A**: Batch backtest sweep — DONE (`/api/backtest/batch` for 20+ tickers)
- [x] **6B**: Performance validation — DONE (`scripts/validate_batch_backtest.py`, institutional gates) — 2026-04-18
- [x] **6C**: Documentation & knowledge transfer — DONE (README: env vars, REST/WS data flow, validation) — 2026-04-18

---

## Blockers

- [B1] FRED_API_KEY not yet configured — macro panel shows mock data
- [B2] No PyGithub token — researcher uses static dictionary
- [B3] Optional Alpaca keys — without them, broker routes use stubs; live multi-leg Alpaca orders not automated

## Decisions Log

- [2026-04-12]: Decision to use 3-agent parallel execution with file-based locking
- [2026-04-12]: Decision to use rolling WFO with 70/30 train/test split
- [2026-04-12]: Kelly Criterion capped at 1%-20% per QUANT_KB Rule

---

## Dependencies

- Phase 2 depends on: Phase 1 (all sub-phases)
- Phase 3 depends on: Phase 2A (backtesting must be working)
- Phase 5 depends on: Phase 4 (frontend must be ready for live data)
- Phase 6 depends on: Phase 5 (broker integration complete)