# Phase 1 Scope Freeze - 15-Phase Institutional Program

Date: 2026-04-20

## Objective

Lock scope, ownership, and mandatory gate policy before any phase promotion.

## Ownership Matrix

- Orchestrator: sequencing, gate approvals, artifact integrity.
- Quant Lead: `skills/` algorithms, backtest integrity, optimizer correctness.
- Backend Lead: `backend/main.py` contracts, failure-path hardening.
- Frontend Lead: `frontend/src/` contract alignment and resilience UX.
- QA Lead: tests, scripts, CI gate enforcement and evidence packaging.
- Proxy Review Board:
  - Quant Reviewer
  - Risk Reviewer
  - Product Reviewer

## In-Scope Work

1. Complete critical algorithm/function correctness in quant stack.
2. Expand endpoint and regression test coverage to program gate requirements.
3. Harden API/UI contract behavior and failure semantics.
4. Run phased validation loops with no-skip promotion rules.
5. Perform midpoint and pre-release proxy institutional reviews.
6. Publish final closure dossier with evidence and residual risk.

## Out of Scope

1. External paid market data vendor migration in this cycle.
2. Real external institutional client engagement (replaced by proxy board process).
3. Full broker-side multi-leg automation beyond current documented baseline.

## Mandatory Program Gates

No phase promotion unless all required checks for that phase pass.

Program-wide minimum checks:

- `python -m pytest tests/ -m "not network"`
- `python -m pytest tests/ -m network`
- `python scripts/validate_regression.py --tickers SPY,QQQ,IWM --days 400`
- `python scripts/validate_batch_backtest.py --basket --days 400 --strict`
- `cd frontend && npm run test:e2e`

## Evidence Requirements per Phase

- Files changed.
- Commands executed.
- Test outcomes.
- Open risks and mitigations.
- Reviewer decision (pass/block/waiver with rationale).
