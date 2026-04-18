# Product context

## Problem domain

Options analytics combine **slow** data (daily OHLC, chains via yfinance), **model** outputs (Black–Scholes, simplified barriers), and **ML** overlays (HMM, meta-labels). Users confuse models with markets; the product must **disambiguate**.

## User experience goals

- **Discovery** → pick a ticker → **terminal** with panels (chart, macro, portfolio, GEX, HMM, meta, backtest).
- **Never silent failure**: failed `/api/analyze` or `/api/chart` shows actionable error text.
- **Methodology**: collapsible “how this is computed” per domain (linked to `GET /api/methodology` and README).

## Functional goals

- Same-origin `/api/*` on Vercel Services; dev proxy to local Python.
- GEX: chain-backed REST in production; optional WS mock in dev.
