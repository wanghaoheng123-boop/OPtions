# Phase 2-3 Inventory and Contract Matrix

Date: 2026-04-20

## Repository Inventory Summary

- Quant/algorithm modules under `skills/`: 20+ classes/modules spanning pricing, GEX, stat-arb, HMM, meta-modeling, backtesting, and brokers.
- API surface in `backend/main.py`: 28 routes (HTTP + WebSocket).
- Frontend client: React terminal dashboard under `frontend/src`.
- Validation stack:
  - Python tests in `tests/`
  - Playwright E2E in `frontend/e2e`
  - Validation scripts in `scripts/`

## API Endpoint Matrix (Phase 3 Baseline)

| Endpoint | Method | Test Status |
|---|---|---|
| `/api/analyze` | POST | Covered (network smoke) |
| `/api/backtest` | POST | Covered (network smoke) |
| `/api/backtest/optimize` | POST | Missing dedicated contract test |
| `/api/backtest/batch` | POST | Covered by script; add direct contract test |
| `/api/hmm/{ticker}` | GET | Missing direct contract test |
| `/api/hmm/{ticker}/validation` | GET | Missing direct contract test |
| `/api/meta/{ticker}` | GET | Missing direct contract test |
| `/api/statarb/kalman` | GET | Missing direct contract test |
| `/api/statarb/institutional` | GET | Missing direct contract test |
| `/api/methodology` | GET | Covered |
| `/api/methodology/{panel_id}` | GET | Covered |
| `/api/chart/{ticker}` | GET | Covered (network) |
| `/api/macro` | GET | Missing direct contract test |
| `/api/macro/search` | GET | Missing direct contract test |
| `/api/macro/series/{series_id}` | GET | Missing direct contract test |
| `/api/heatmap` | GET | Missing direct contract test |
| `/api/portfolio` | GET | Missing direct contract test |
| `/api/portfolio/execute` | POST | Missing direct contract test |
| `/api/statarb` | GET | Missing direct contract test |
| `/api/screener` | GET | Missing direct contract test |
| `/api/broker/order` | POST | Missing direct contract test |
| `/api/broker/positions/{broker_name}` | GET | Missing direct contract test |
| `/api/broker/account/{broker_name}` | GET | Missing direct contract test |
| `/api/broker/tc/{broker_name}` | GET | Missing direct contract test |
| `/api/gex/live/{ticker}` | GET | Covered (network) |
| `/ws/gex` | WS | Missing WS test |
| `/api/ws/gex` | WS | Missing WS test |
| `/api/health` | GET | Covered |

## Priority Function Risk Targets for Phase 4

1. `skills/backtester.py`
   - overlapping trade realism and position gating
   - index/time alignment for IV rank and OOS features
2. `skills/parameter_optimizer.py`
   - cache contamination across windows and tickers
3. `core_agents/orchestrator.py`
   - backtest key contract mismatch (`num_trades` vs `n_trades`, volatility key)
4. `frontend/src/components/MacroSearchTerminal.tsx`
   - macro series shape mismatch with candlestick chart expectations
