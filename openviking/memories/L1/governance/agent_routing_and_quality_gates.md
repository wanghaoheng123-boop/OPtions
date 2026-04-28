# Agent Routing and Quality Gates (L1 Governance)

## Roles

| Role | Scope | Primary artifacts |
|------|-------|-------------------|
| Orchestrator | Sequencing, scope, merge gate | `task_plan.md`, `activeContext.md` |
| ResearchAgent | External refs, UI precedents, papers | web sources, verified citations |
| QuantAgent | Backtests, metrics, invariants | `skills/`, `scripts/validate_*.py`, `tests/` |
| UIAgent | Frontend layout, data rendering, accessibility | `frontend/src/` |
| AdversarialReviewer | Contrarian review before done-state | checklist below |
| Supervisor | Release sign-off and continuity | `progress.md`, L0 updates |

## Sub-agent dispatch rules

1. Split work by subsystem (`skills/`, `frontend/`, `backend/`).
2. Return: files changed, tests run, residual risks.
3. Use observables/proxies/hypotheses language; avoid intent claims.

## Mandatory adversarial review checklist

- Data source lineage clear for each metric.
- Failure modes visible (empty chain, rate limits, external provider outages).
- Overfit/leakage controls documented for backtests.
- API response keys aligned with UI reads.
- No false precision in reported metrics.
- No secrets committed; env vars only.
- Methodology endpoint remains synchronized with computation paths.
- Behavior deltas logged in progress/history artifacts.

## Release gate baseline

- Fast tests: `python -m pytest tests/ -m "not network"`
- Network tests: `python -m pytest tests/ -m network`
- Regression script: `python scripts/validate_regression.py --tickers SPY,QQQ --days 400`
- Batch gates: `python scripts/validate_batch_backtest.py --tickers SPY --days 400`
- Frontend e2e: `cd frontend && npm run test:e2e`

## External dependency caveats

- FRED (`FRED_API_KEY`) and GitHub token are external data gates.
- Alpaca credentials are optional and multi-leg automation remains intentionally out of scope.
