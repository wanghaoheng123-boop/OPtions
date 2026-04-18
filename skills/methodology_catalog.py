"""Static methodology copy for `/api/methodology/*` — data lineage and limits (no inferential 'intent')."""

from __future__ import annotations

METHODOLOGY_PANELS: dict[str, dict] = {
    "chart": {
        "title": "Live OHLC chart",
        "inputs": [
            "Ticker from search",
            "yfinance `Ticker.history(period='3mo', interval='1d')`",
        ],
        "method": [
            "Server maps each row to `{ time, open, high, low, close, value }` for lightweight-charts.",
            "OHLC coerced to float; non-finite values become 0.0 for JSON safety.",
        ],
        "limits": [
            "Not an exchange consolidated tape; subject to Yahoo/yfinance delays and gaps.",
            "Empty history returns HTTP 404 from `/api/chart/{ticker}`.",
        ],
        "code_paths": ["skills/market_data_api.py:MarketDataAPI.get_ohlcv", "backend/main.py:get_chart_data"],
    },
    "analyze": {
        "title": "Terminal analyze pipeline",
        "inputs": ["POST body `{ ticker, days? }`", "Options chain + spot where available"],
        "method": [
            "`POST /api/analyze` runs orchestration (GEX/skew, agents, optional paper actions).",
            "Outputs are model and data conditioned — treat narrative fields as hypotheses unless tied to a cited series.",
        ],
        "limits": [
            "Chain/OI quality varies by symbol; some panels may be sparse on illiquid names.",
            "No access to proprietary order flow; 'walls' are chain-derived proxies, not confirmed liquidity.",
        ],
        "code_paths": ["backend/main.py (analyze route)", "core_agents/orchestrator.py"],
    },
    "macro": {
        "title": "FED macro database",
        "inputs": ["FRED API key when set; else mock/cached series per `macro_fetcher`"],
        "method": ["Search and series endpoints aggregate macro indicators for display only."],
        "limits": ["Revisions, release calendars, and key availability follow FRED (or mock) behavior."],
        "code_paths": ["skills/macro_fetcher.py", "backend/main.py `/api/macro*`"],
    },
    "portfolio": {
        "title": "AI paper portfolio",
        "inputs": ["In-memory / persisted paper broker state"],
        "method": ["`GET /api/portfolio` returns positions and summary metrics from the paper engine."],
        "limits": ["Simulated fills and sizing — not live brokerage accounting."],
        "code_paths": ["skills/paper_trader.py", "backend/main.py `/api/portfolio`"],
    },
    "hmm_regime": {
        "title": "HMM regime label",
        "inputs": ["Return series and proxies built in the analyze pipeline"],
        "method": ["Gaussian HMM fit on engineered features; regime label is a model output."],
        "limits": ["Regime labels are not facts about future returns; unstable with short samples."],
        "code_paths": ["skills/regime_hmm.py", "agent outputs in analyze payload"],
    },
}


def list_panel_ids() -> list[str]:
    return sorted(METHODOLOGY_PANELS.keys())


def get_panel(panel_id: str) -> dict | None:
    return METHODOLOGY_PANELS.get(panel_id.strip().lower())
