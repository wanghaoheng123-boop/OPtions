# L1 System Patterns (Warm Context)
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
## Purpose
Canonical architecture and dependency reference for design-time retrieval.

## Canonical Sources
- `systemPatterns.md`
- `backend/main.py`
- `core_agents/orchestrator.py`
- `skills/`
- `frontend/`
- `vercel.json`

## Architecture Summary
- Backend control plane is implemented in `backend/main.py` (FastAPI).
- Domain logic is delegated to quantitative and execution modules under `skills/`.
- Multi-step recommendation assembly is orchestrated in `core_agents/orchestrator.py`.
- Frontend is a Vite + React terminal using `/api/*` contracts and dedicated panels.

## Critical Domain Routes
- API integration layer: market data, options chain, charting, and analytics endpoints.
- Execution logic layer: strategy recommendation, paper execution, broker abstraction.
- Optimization loop layer: parameter scans, walk-forward or split evaluation, gate filtering.
- User data stream layer: portfolio state, panel-level metrics, and live/near-live feeds.

## Design Rules
1. Preserve contract shape between backend responses and frontend readers.
2. Keep quant assumptions explicit and inspectable.
3. Keep model outputs clearly marked as model/proxy, not ground truth.
4. Enforce regression checks before promoting behavior changes.
