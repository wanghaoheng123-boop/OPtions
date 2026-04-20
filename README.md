# 🚀 Institutional Agentic Options Terminal

An advanced, open-source quantitative trading terminal featuring high-frequency Gamma Exposure (GEX) mapping, mathematical regime detection via Hidden Markov Models (HMM), and a dynamic mosaic React dashboard. Designed strictly for high-performance option analytics and automated market-maker profiling.

---

## 🌟 Elite Features

*   **1-Second Tick Gamma Micro-structure:** Runs Black-Scholes equations dynamically over massive options chains to isolate the precise institutional Call Walls (Max Resistance) and Put Walls (Max Support).
*   **Hidden Markov Model (HMM) Regime Detection:** Mathematical extraction of market regimes (Sustained Bull, Volatile Bear, Consolidation Chop) through multi-dimensional Unsupervised Learning pipelines.
*   **Deep Reinforcement Learning Pivot:** Features proxy framework architecture mapped for Proximal Policy Optimization (PPO) via FinRL, enabling dynamic capital allocation across risk thresholds.
*   **Mosaic React Layout:** Built strictly on `react-grid-layout`, the frontend operates like Bloomberg/Symphony displays, allowing full drag/drop and maximization of specific analytical widgets.
*   **Market Data Aggregation:** Includes native hooks into the FRED (Federal Reserve) database and statistical arbitrage Z-score tracking mapping massive ETF pairs mathematically.

## 🛠️ Architecture
*   **Backend:** FastAPI (Python), `hmmlearn`, `scikit-learn`, `stable-baselines3`, `asyncio` WebSockets.
*   **Frontend:** React (TypeScript), Vite, `react-grid-layout`, `lucide-react`, `lightweight-charts`.

---

## 📥 Installation

This application requires both Python 3.10+ and Node.js.

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Setup the Python Backend
The backend houses the ML Models and the FastAPI server.
```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate
# Activate it (Mac/Linux)
source venv/bin/activate

# Install backend dependencies (recommended)
pip install -r backend/requirements.txt
```

### 3. Environment variables (`.env` in project root)

| Variable | Required | Purpose |
|----------|----------|---------|
| `FRED_API_KEY` | No (macro falls back to mock series) | [FRED](https://fred.stlouisfed.org/) macro indicators and search in `/api/macro*` |
| `GITHUB_TOKEN` | No | Enables live GitHub lookup in `GitHubResearcher`; without it, a static verified-algorithm registry is used |
| `VITE_API_URL` | No | Axios base URL for production split-host deploys; use **origin only** (no trailing `/api`) so `/api/...` paths resolve correctly (see §6b) |
| `PAPER_PORTFOLIO_PATH` | No | Absolute path for paper portfolio JSON; on **Vercel** the app defaults to `/tmp/paper_portfolio.json` (writable). Set explicitly if you need a durable volume |
| `VITE_WS_URL` | No | Base URL for the **Live GEX** WebSocket in local dev (path `/ws/gex` or `/api/ws/gex`). Production builds **poll** `GET /api/gex/live/{ticker}` instead |
| `VITE_GEX_POLL` | No | Set to `1` to force REST polling in dev (same as production behavior) |
| `ALPACA_API_KEY` / `ALPACA_API_SECRET` | No | When both are set (non-`PAPER`), [`get_broker("ALPACA")`](skills/brokers.py) uses **Alpaca REST** for account metrics and `/v2/options/contracts`; multi-leg order submission is not automated |
| `ALPACA_PAPER` | No | Default `true` — paper-api host; set `false` for live trading host |
| `IBKR_ENABLE_LIVE` | No | If `1` / `true`, IBKR broker methods return a structured error explaining that **TWS / IB Gateway + ib_insync** is required (no retail REST in this repo) |

With Alpaca keys unset, `skills/brokers.py` uses **stubs** for paper-style flows and transaction-cost math.

### 3b. External dependency gates (completion runbook)

These are the only remaining credential-dependent capabilities after the code completion sweep:

- **FRED (`FRED_API_KEY`)**: without key, `/api/macro*` returns fallback data and `FRED_API_KEY_MISSING`.
- **GitHub (`GITHUB_TOKEN`)**: without token, researcher uses the in-repo verified algorithm registry.
- **Alpaca (`ALPACA_API_KEY` / `ALPACA_API_SECRET`)**: enables live account/contracts REST paths; multi-leg strategy order automation is intentionally not implemented.

Quick verification commands:

```bash
curl -s http://127.0.0.1:8005/api/macro
curl -s "http://127.0.0.1:8005/api/macro/search?query=GDP"
curl -s http://127.0.0.1:8005/api/broker/account/ALPACA
curl -s "http://127.0.0.1:8005/api/broker/tc/ALPACA?num_contracts=10&mid_price=2.5&order_type=market"
```

Expected behavior:

- Missing FRED key -> payload contains `FRED_API_KEY_MISSING` (graceful fallback).
- Missing Alpaca keys -> broker endpoint returns paper/stub metrics.
- Alpaca keys present -> broker endpoint returns `source: "alpaca_rest"` on live REST account/contract paths.

### 4. Data flow (REST vs WebSocket)

- **Discovery:** `GET /api/screener` → ticker list; choosing a symbol loads the terminal.
- **Terminal analyze:** `POST /api/analyze` runs the full agentic pipeline (options chain, GEX/skew, `MarketExpertTeam`, paper trade) and returns data for the mosaic (HMM, meta-model, backtest, critic, etc. in one payload).
- **Other panels:** dedicated REST calls, for example `GET /api/statarb`, `GET /api/heatmap`, `GET /api/macro*`, `GET /api/portfolio`, `GET /api/methodology/{panel}`, `POST /api/portfolio/execute`, `POST /api/broker/*`, `GET /api/hmm/{ticker}`, `GET /api/meta/{ticker}`.
- **Live GEX tile:** in **development**, the mosaic can use a **WebSocket** mock feed (`/ws/gex` on the Python port). In **production** (e.g. Vite `build`), the UI **polls** [`GET /api/gex/live/{ticker}`](backend/main.py) for chain-backed gamma (serverless-friendly). Optional duplicate WS route: `/api/ws/gex`.

### 5. Performance validation (Phase 6B)

With Python dependencies installed (`pip install -r backend/requirements.txt`):

```bash
python scripts/validate_batch_backtest.py --tickers SPY --days 400
```

Uses `POST /api/backtest/batch` in-process (no server) unless you pass `--url http://127.0.0.1:8005`. Exit code **1** if fewer than `--min-pass` tickers meet institutional gates (win rate ≥ 75%, profit factor ≥ 1.2, max drawdown < 20%).

Flags:

- **`--basket`** — fixed ETF basket `SPY,QQQ,IWM` (good for a quick multi-name sweep).
- **`--strict`** — every requested symbol must return a result **and** pass all gates (stricter than `--min-pass`).

Additional checks:

```bash
python scripts/validate_regression.py --tickers SPY,QQQ --days 400
python -m pytest tests/ -m "not network"   # fast: health, methodology, structure (no yfinance)
python -m pytest tests/ -m network         # needs yfinance + options data
```

### 5b. Backtest accuracy and limitations (read this)

Results are **research-grade simulations**, not guaranteed future performance:

- **Prices** come from **yfinance** (adjusted/historical quirks, possible rate limits). Retry failed validations or use a smaller `--tickers` list if you see download errors.
- **Options** in the iron-condor engine use **Black–Scholes** with a **realized-vol × volatility-premium** proxy, not exchange-reported IV surfaces or tick-level fills.
- **Transaction costs** use [`TransactionCostModel`](skills/brokers.py) (commission / spread / slippage rules), not actual broker rebates or queue position.
- **Meta-labeling** prefers labels from **`trade_log`** (per-trade win/loss on entry dates); if too few trades exist, it falls back to a **next-day return** proxy (see [`skills/meta_model.py`](skills/meta_model.py)).

Use the scripts above for **regression** (structure + gates), not for proving live edge.

### 5c. Regression matrix, strict mode, and ablations

| Check | Command | Notes |
|--------|---------|--------|
| Fast API smoke | `python -m pytest tests/ -m "not network"` | Health, methodology index/detail, structure without yfinance |
| Live data / chart | `python -m pytest tests/ -m network` | Includes `GET /api/chart/SPY` OHLC contract and optional chain-backed GEX |
| Multi-ticker structure | `python scripts/validate_regression.py --tickers SPY,QQQ,IWM --days 400` | Widen the ticker list for a larger matrix; yfinance may rate-limit |
| Batch gates | `python scripts/validate_batch_backtest.py --basket --days 400` | Add `--strict` so every symbol must pass gates (release-style) |

**Ablations:** toggles such as alternate EWMA spans or event filters should be recorded with the flag set and date in `progress.md` so comparisons stay attributable.

**Optional external validation:** OpenAlex/CrossRef or GitHub search can sanity-check formulas and UI patterns; treat hits as **design references**, not proof of live edge.

### 6. Setup the React Frontend
The frontend houses the Vite compilation and the Mosaic UI terminal.
```bash
cd frontend
npm install
```

### 6b. Browser E2E (Playwright)

Headless smoke tests mock `/api` so they run **without** the Python server (CI-friendly).

```bash
cd frontend
npx playwright install chromium   # once per machine
npm run test:e2e                  # build + vite preview on :4173 + run e2e/
```

Optional: `npm run test:e2e:ui` for the Playwright UI debugger. See [`frontend/playwright.config.ts`](frontend/playwright.config.ts).

Set **`PLAYWRIGHT_BASE_URL`** (e.g. `http://127.0.0.1:4173`) if you run `vite preview` on a non-default host/port and want tests to skip the auto-started `webServer` (set **`PW_NO_WEBSERVER=1`** in that case so Playwright does not spawn a second preview).

**`VITE_API_URL` (production):** set to the **API origin only** (e.g. `https://your-deployment.example.com`), **without** a trailing `/api`, because the app already requests paths like `/api/health`. A value ending in `/api` can produce double `/api/api/...` URLs depending on how paths are joined.

---

## ⚡ Running the Terminal

You need to run both servers simultaneously.

**Launch Backend:**
Open terminal at the root directory:
```bash
.\venv\Scripts\python.exe -m uvicorn backend.main:app --port 8005 --reload
```

**Launch Frontend:**
Open a second terminal inside the `/frontend` directory:
```bash
npm run dev
```

Navigate your browser to: `http://localhost:5173/`.

### Local API wiring and quick checks

The Vite dev server proxies browser requests from **`/api/*`** to **`http://127.0.0.1:8005`** (see [`frontend/vite.config.ts`](frontend/vite.config.ts)). If the UI shows empty charts or repeated errors, confirm the backend is listening on the **same port** as the proxy (default **8005**).

**Sanity checks (PowerShell or bash):**

```bash
curl -s http://127.0.0.1:8005/api/health
curl -s http://127.0.0.1:8005/api/chart/SPY | head -c 400
curl -s -X POST http://127.0.0.1:8005/api/analyze -H "Content-Type: application/json" -d "{\"ticker\":\"SPY\",\"days\":126}"
```

If these fail from the host but the SPA is open on port **5173**, the problem is backend/port/proxy—not the chart library.

**Vercel / split deployments:** a static frontend build that calls **`/api/...`** only works when the **same origin** serves FastAPI (e.g. Vercel experimental services per [`vercel.json`](vercel.json)). Hosting the SPA on one URL and the API on another requires configuring the frontend base URL (not enabled in this repo by default).

## Vercel (Services: Vite + FastAPI)

This repo includes [`vercel.json`](vercel.json) with **experimentalServices**: Vite on `/`, FastAPI on `/api` (entrypoint [`backend/main.py`](backend/main.py), `maxDuration` 120s, 1024 MB). Root [`pyproject.toml`](pyproject.toml) exposes the FastAPI app via `[project.scripts] app = "backend.main:app"`. Python dependencies are listed in [`requirements.txt`](requirements.txt) at the repo root (and [`backend/requirements.txt`](backend/requirements.txt) for local backend-only installs).

1. Connect the GitHub repo in the Vercel dashboard (enable **Services** / polyglot detection if prompted).
2. Set environment variables (FRED, GitHub, Alpaca, etc.) in Project Settings.
3. Deploy; open the production URL — API calls use relative `/api/...` from the browser.

Use [`vercel dev -L`](https://vercel.com/docs/cli/dev) locally to run both services together (CLI 48.1.8+).

## 🤝 Contribution Guidelines
Pull Requests addressing specific High-Frequency latency offsets or premium Tick-Data vendor hooks (ThetaData / Databento) are highly encouraged!
