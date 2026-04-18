# Project brief — Institutional Agentic Options Terminal

## Mandate

Deliver a **factual**, **source-grounded** quantitative options terminal: backtests, Greeks/GEX proxies, regime tools, and paper-style execution—without claiming hidden knowledge of fund intentions.

## Audience

Developers and advanced retail / small-team quants who need transparent methodology and reproducible checks.

## Primary objectives

1. **Reliable data paths**: API errors visible in UI; charts render from validated OHLC payloads.
2. **Transparency**: Every major metric documents inputs, formulas (references to code), and limitations.
3. **Validation**: Automated regression (pytest + scripts) before releases.
4. **Governance**: Peer-review and adversarial checklists in `AGENTS.md`; handoff state in `activeContext.md`.

## Non-goals

- Guaranteed profitability or “reading” undisclosed institutional plans.
- Outputs presented as facts when they are models, proxies, or hypotheses.
