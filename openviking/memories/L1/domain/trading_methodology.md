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
