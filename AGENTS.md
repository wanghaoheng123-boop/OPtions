# Agent routing and governance

Canonical routing for Cursor / Claude Code / Antigravity. **`CLAUDE.md`** at repo root points here (or duplicates this path for tools that only read `CLAUDE.md`).

## Roles (operational — not separate LLM runtimes)

| Role | Scope | Primary artifacts |
|------|--------|---------------------|
| **Orchestrator** | Sequencing, scope, merge gate | [`task_plan.md`](task_plan.md), [`activeContext.md`](activeContext.md) |
| **ResearchAgent** | External refs, UI precedents, papers | Web search, OpenAlex / CrossRef when used as skills |
| **QuantAgent** | Backtests, metrics, invariants | [`skills/backtester.py`](skills/backtester.py), [`scripts/validate_*.py`](scripts/), [`tests/`](tests/) |
| **UIAgent** | Layout, errors, accessibility | [`frontend/src/`](frontend/src/) |
| **AdversarialReviewer** | Contrarian pass before merge | Checklist below — must be satisfied or documented waiver |
| **Supervisor** | Release sign-off | Updates `activeContext.md` + dated entry in [`progress.md`](progress.md) |

## Sub-agent dispatch rules

1. **Split work** by directory: `skills/` vs `frontend/` vs `backend/`.
2. **Return**: file paths changed, test commands run, remaining risks.
3. **Never** claim fund “intent”; use **observable proxy + hypothesis + uncertainty**.

## Adversarial review checklist (mandatory before “done”)

- [ ] **Data source**: Where does each number come from (yfinance, BS formula, OI field name)?
- [ ] **Failure modes**: Empty chain, rate limit, 404 — does UI show it?
- [ ] **Overfit / leakage**: Train/test separation documented for backtests?
- [ ] **API contract**: Response keys match what the UI reads (`data`, `agent_insights`, etc.)?
- [ ] **No false precision**: Rounded sensibly; no fake decimals on derived metrics?
- [ ] **Security**: No secrets in repo; env vars only in deployment settings?
- [ ] **Methodology surface**: Does `GET /api/methodology/{panel}` stay aligned with code paths when logic changes?
- [ ] **Claims bound to observables**: No “fund intent”; use proxies, hypotheses, and uncertainty labels.
- [ ] **Ablation / regression note**: If behavior changed under a flag or ticker matrix, is it logged (README §5c / `progress.md`)?

Optional cross-checks (not merge blockers): OpenAlex/CrossRef for formula citations; GitHub for comparable implementations — cite as references only.

## Skills (optional hooks)

Use workspace skills when relevant: `free-web-search`, `verify-claims`, `pinescript-quant-analysis` (only if Pine-related), Vercel skills for deploy.

## Peer review program

Issue templates: [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/). Charter, UI/API checklist, triage playbook, and offline log: [`findings.md`](findings.md) (sections **Peer review charter**, **UI/API review matrix**, **Root-cause triage playbook**, **Peer review log**).

## CLI / API tools

- **CI**: GitHub Actions workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs `pytest -m "not network"` on push/PR.
- **Tests**: `python -m pytest tests/ -m "not network"` (fast), `python -m pytest tests/ -m network` (yfinance).
- **Browser E2E**: `cd frontend && npm run test:e2e` (Playwright; see [`README.md`](README.md) §6b).
- **Baseline commands**: `python scripts/baseline_metrics.py` (optional `--quick`).
- **Batch gates**: `python scripts/validate_batch_backtest.py --tickers SPY --days 400`
- **Structure regression**: `python scripts/validate_regression.py --tickers SPY,QQQ --days 400`

## Release gate snapshot (2026-04-20)

- Fast tests: pass (`pytest -m "not network"`).
- Network tests: pass (`pytest -m network`).
- Regression script: pass (`validate_regression.py --tickers SPY,QQQ,IWM --days 400`).
- Batch institutional gates: pass (`validate_batch_backtest.py --basket --days 400`).
- Frontend E2E: pass (`frontend npm run test:e2e`, 1 macOS-only shortcut test skipped on non-macOS).
- Open caveats are external dependency gates only (`FRED_API_KEY`, `GITHUB_TOKEN`, optional Alpaca creds / live broker scope).
