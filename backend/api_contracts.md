# API Contract Surface (First Review Canonical)

## Canonical Endpoints

### `POST /api/analyze`
- Request: `{ ticker: string, days?: number }`
- Response canonical keys:
  - `ticker`, `current_price`, `target_expiry`, `market_structure`, `paper_trade_status`
  - flattened agent keys: `strategy_proposed`, `trader_insight`, `researcher_context`, `optimization`, `backtest`, `meta_model`, `critic_review`, `final_recommendation`
  - nested compatibility alias: `agent_insights` (same payload as flattened agent keys)

### `GET /api/chart/{ticker}`
- Response: `{ data: Array<{time, open, high, low, close}> }`

### `GET /api/portfolio`
- Response: portfolio object with `positions`, `cash_balance`, `total_return`, `win_rate`, `average_kelly_sizing`

### `GET /api/gex/live/{ticker}`
- Response includes: `spot_price`, `call_wall`, `put_wall`, `dealer_tilt`, `total_call_gex_m`, `total_put_gex_m`, `strikes`, `ticker`, `expiry`

### `GET /api/statarb`
- Response: `{ pairs: Array<{pair, z_score, current_spread, action}> }`

## Alias Policy (Backward Compatibility)
- `backtest.max_drawdown` aliases `max_drawdown_percent`
- `backtest.num_trades` aliases `n_trades`
- `backtest.trained_volatility` aliases `trained_iv`
- `researcher_context.name` aliases `researcher_context.algorithm`

## Error Envelope Policy
- Use transport-level status codes.
- Error body should include `detail` string for frontend extraction.
- Critical feed endpoints (`/api/hmm/*`, `/api/meta/*`, `/api/statarb*`, `/api/macro*`, `/api/heatmap`, `/api/screener`) must not return HTTP 200 for runtime failures.
- Degradation metadata should be represented as explicit fields in successful payloads, not hidden in fallback strings.
