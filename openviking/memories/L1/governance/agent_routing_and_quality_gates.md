# L1 Agent Routing and Quality Gates (Warm Context)
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
## Purpose
Operational governance for orchestrator/specialist review flow.

## Canonical Sources
- `AGENTS.md`
- `CLAUDE.md`
- `findings.md`

## Routing Policy
- Split work by subsystem (`backend/`, `skills/`, `frontend/`) where possible.
- Require file-level change summaries and explicit risk notes from each execution stream.
- Preserve observability-first language: proxy + hypothesis + uncertainty framing.

## Mandatory Pre-Completion Checks
- Data-source lineage for major metrics is traceable.
- Failure modes are visible in API/UI surfaces.
- Overfit/leakage risks are explicitly bounded in optimization/backtest changes.
- API contract keys remain aligned with frontend usage.
- No false precision in displayed metrics.
- Methodology surfaces stay synchronized with implementation.

## Release Validation Baseline
- Fast tests, network tests, regression scripts, batch validation, and frontend E2E where relevant.
- External credentials are treated as dependency gates, not hidden assumptions.
