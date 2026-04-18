# System patterns

## Architecture

- **Backend**: FastAPI in [`backend/main.py`](backend/main.py); skills in [`skills/`](skills/); orchestration in [`core_agents/orchestrator.py`](core_agents/orchestrator.py).
- **Frontend**: Vite + React in [`frontend/`](frontend/); axios to `/api`.
- **Deploy**: Vercel experimental Services — Vite `/`, FastAPI `/api` ([`vercel.json`](vercel.json)).

## Dependency map (logical)

```
App.tsx → /api/analyze, /api/chart/{t}, /api/portfolio
MarketDataAPI.get_ohlcv → yfinance → list[{time, open, high, low, close}]
MarketExpertTeam → StrategyBacktester, MetaLabeler, ParameterOptimizer
```

## Design rules

- **Sanitize** API responses for JSON (`sanitized_response` in FastAPI).
- **Numeric** OHLC must be native floats before JSON (see `MarketDataAPI`).
- **Charts**: lightweight-charts **v5** uses `addSeries(CandlestickSeries, opts)` — not `addCandlestickSeries`.

## Anti-patterns (forbidden)

- Swallowing axios errors without UI feedback.
- Presenting model outputs as “what hedge funds will do” without data lineage.
