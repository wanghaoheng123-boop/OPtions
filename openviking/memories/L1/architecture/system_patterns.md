# System Patterns (L1 Architecture)

## Core architecture

- Backend: FastAPI in `backend/main.py`.
- Quant and execution logic: `skills/`.
- Orchestration: `core_agents/orchestrator.py`.
- Frontend: Vite + React in `frontend/`, axios calls to `/api`.
- Deployment: Vercel services with frontend root and backend `/api`.

## Dependency map (logical)

```text
App.tsx -> /api/analyze, /api/chart/{ticker}, /api/portfolio
MarketDataAPI.get_ohlcv -> yfinance -> OHLC rows
MarketExpertTeam -> StrategyBacktester + MetaLabeler + ParameterOptimizer
```

## Design rules

- Sanitize API responses for JSON-safe scalar output.
- Keep OHLC numeric fields as native floats before serialization.
- Use lightweight-charts v5 API (`addSeries(CandlestickSeries, opts)`).
- Preserve route and payload compatibility when evolving modules.

## Anti-patterns

- Silent API failures in UI.
- Output claims that imply hidden institutional intent.
- Untracked contract changes between backend and frontend panels.
