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
| `VITE_WS_URL` | No | Base URL for the **Live GEX** WebSocket in the mosaic (see below). Defaults to `ws://localhost:8005` |

Live broker API keys are not read from the environment by the FastAPI app today; `skills/brokers.py` ships **IBKR/Alpaca stubs** for paper-style flows and transaction-cost math. Configure keys when you wire real execution.

### 4. Data flow (REST vs WebSocket)

- **Discovery:** `GET /api/screener` → ticker list; choosing a symbol loads the terminal.
- **Terminal analyze:** `POST /api/analyze` runs the full agentic pipeline (options chain, GEX/skew, `MarketExpertTeam`, paper trade) and returns data for the mosaic (HMM, meta-model, backtest, critic, etc. in one payload).
- **Other panels:** dedicated REST calls, for example `GET /api/statarb`, `GET /api/heatmap`, `GET /api/macro*`, `GET /api/portfolio`, `POST /api/portfolio/execute`, `POST /api/broker/*`, `GET /api/hmm/{ticker}`, `GET /api/meta/{ticker}`.
- **Live GEX tile:** the React component opens **`ws://.../ws/gex`** (see `frontend/src/components/LiveGammaExposure.tsx`). That stream is **separate** from the GEX snapshot embedded in `/api/analyze`; run a compatible WebSocket feed on the same host/port or set `VITE_WS_URL`.

### 5. Performance validation (Phase 6B)

With Python dependencies installed (`pip install -r backend/requirements.txt`):

```bash
python scripts/validate_batch_backtest.py --tickers SPY --days 400
```

Uses `POST /api/backtest/batch` in-process (no server) unless you pass `--url http://127.0.0.1:8005`. Exit code **1** if fewer than `--min-pass` tickers meet institutional gates (win rate ≥ 75%, profit factor ≥ 1.2, max drawdown < 20%).

### 6. Setup the React Frontend
The frontend houses the Vite compilation and the Mosaic UI terminal.
```bash
cd frontend
npm install
```

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

Navigate your browser to: `http://localhost:5173/` and prepare for proactive institutional discovery.

## 🤝 Contribution Guidelines
Pull Requests addressing specific High-Frequency latency offsets or premium Tick-Data vendor hooks (ThetaData / Databento) are highly encouraged!
