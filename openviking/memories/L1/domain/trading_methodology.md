# L1 Trading Methodology (Warm Context)
# Trading Methodology (L1 Domain)

## Mandate

Build a factual, source-grounded options terminal for backtesting, Greeks/GEX proxies, regime logic, and paper execution while explicitly avoiding hidden-intent narratives.

## Audience

Advanced retail and small-team quant developers who need transparent methodology and reproducible validation.

## Product goals

- Discovery flow to ticker-specific terminal analysis.
- No silent failure paths; user-visible API error handling.
- Per-panel methodology traceability (`/api/methodology`).
- Reproducible validations with pytest + validation scripts.

## Quant methodology pillars

- Options chain + Greeks computations for structure diagnostics.
- Volatility skew with IV rank/percentile context.
- Triple-barrier style backtesting with risk metrics.
- Parameter optimization with walk-forward loops.
- HMM regime classification and meta-model overlays.
- Portfolio sizing controls and execution safeguards.

## Non-goals

- Guaranteed profitability claims.
- Presenting proxy/model outputs as market facts.
## Purpose
Domain-level strategy and modeling summary for recurrent retrieval.

## Canonical Sources
- `projectbrief.md`
- `productContext.md`
- `techContext.md`
- `findings.md`
- `task_plan.md`

## Methodology Principles
- Factual, source-grounded outputs over narrative claims.
- Transparent quant pipeline with inspectable assumptions.
- Risk-adjusted evaluation prioritized over raw hit-rate storytelling.

## Core Analytical Components
- Options chain retrieval and derived Greeks/GEX style structure metrics.
- Volatility regime and skew proxies (including rank/percentile style diagnostics).
- Backtesting with barrier and transaction-cost aware metrics.
- Meta-labeling and critic gating for recommendation filtering.

## Execution Principles
- Paper and broker pathways are explicit and bounded by available credentials/integrations.
- Position sizing uses constrained risk controls and portfolio-level limits.
- All recommendation outputs require a documented risk context.

## Known Boundaries
- Data quality and live feed fidelity depend on external providers.
- Some live broker capabilities remain intentionally scoped or gated.
