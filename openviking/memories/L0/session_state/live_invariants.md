# Live Invariants (L0)

## Contract and output invariants

- Preserve frontend/backend contract keys used by UI panels (`data`, `agent_insights`, `market_structure`, portfolio fields, and chart payload shape).
- Keep JSON payloads serialization-safe (native scalar types, no raw numpy objects).
- Never silently swallow API errors; surface actionable error text in UI.

## Quant and optimization invariants

- Treat model output as observables/proxies/hypotheses, not hidden market intent.
- Keep train/test separation explicit for backtests and optimization loops.
- Apply institutional gates to strategy recommendations (win rate, profit factor, max drawdown).
- Record failed parameter signatures in episodic memory and do not repeat them unless explicit override is documented.

## Routing and governance invariants

- Query routing order:
  1. L0 session state
  2. L1 architecture/governance
  3. GraphRAG for dependency impact
  4. Episodic SQLite for optimization retrospection
  5. Vector RAG for heavy references
- Keep methodology docs synchronized when behavior, formulas, or API contracts change.
- Avoid token bloat by reading targeted layer files instead of broad historical documents by default.

## Security and process invariants

- Never hardcode secrets.
- Never read or expose `.env` values.
- Keep state continuity artifacts in repo memory layers and `workspace/`.
