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

# Install dependencies (If requirements.txt exists or manually below)
pip install fastapi uvicorn yfinance fredapi scikit-learn hmmlearn stable-baselines3 shimmy gymnasium
```

*Note: You must create a `.env` file in the root directory and add `FRED_API_KEY=your_key_here` for the Macro database to function.*

### 3. Setup the React Frontend
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
