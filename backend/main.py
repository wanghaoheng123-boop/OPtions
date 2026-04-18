from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
import sys
import os
import asyncio
from typing import List, Optional
import numpy as np

# Add parent path so we can import from skills
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _sanitize(obj):
    """Convert numpy and non-serializable types to native Python for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize(x) for x in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (set, frozenset)):
        return list(obj)
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        try:
            return float(obj)
        except Exception:
            return str(obj)


def sanitized_response(data: dict):
    """Wrap FastAPI response with sanitization for numpy types."""
    return jsonable_encoder(_sanitize(data))


from skills.options_chain_fetcher import OptionsFetcher
from skills.greeks_calculator import GreeksCalculator
from skills.gamma_exposure import MarketStructureAnalyzer
from skills.volatility_skew import VolatilitySkewAnalyzer
from core_agents.orchestrator import MarketExpertTeam
from skills.macro_fetcher import macro_client
from skills.market_data_api import MarketDataAPI
from skills.paper_trader import paper_broker
from skills.statarb_scanner import StatArbScanner
from skills.global_screener import GlobalScreener
from skills.hft_options_pipeline import HFTOptionsPipeline
from skills.regime_hmm import RegimeDetectorHMM
from skills.brokers import get_broker, TransactionCostModel, IBKRBroker, AlpacaBroker

app = FastAPI(title="Agentic Quant Terminal API V2 - Institutional Grade")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    ticker: str
    days: Optional[int] = 252

class BacktestRequest(BaseModel):
    ticker: str
    strategy: str
    days: Optional[int] = 252

class BatchBacktestRequest(BaseModel):
    tickers: List[str]
    strategy: str = "iron_condor"
    days: Optional[int] = 252

class BrokerOrderRequest(BaseModel):
    ticker: str
    strategy: str
    dte: int = 30
    sizing_pct: float = 0.1
    broker: Optional[str] = "PAPER"
    strikes: Optional[dict] = None

@app.post("/api/analyze")
def analyze_ticker(request: AnalysisRequest):
    """
    Full agentic analysis endpoint.
    Coordinates: Researcher → Trader → Optimizer → Backtester → MetaModel → Critic → Memory
    """
    ticker = request.ticker.upper()
    days = request.days or 252

    current_price = OptionsFetcher.get_current_price(ticker)
    if current_price == 0.0:
        raise HTTPException(status_code=404, detail="Ticker not found or failed to fetch.")

    expirations = OptionsFetcher.get_options_expiration_dates(ticker)
    if not expirations:
        raise HTTPException(status_code=404, detail="No options data available for this ticker.")

    target_expiry = expirations[0]

    data = OptionsFetcher.get_options_chain(ticker, target_expiry)
    if not data:
        raise HTTPException(status_code=500, detail="Failed to load options chain.")

    calls = data["calls"]
    puts = data["puts"]
    r_rf = 0.045
    T = 7.0 / 365.0

    calls_greeks = GreeksCalculator.attach_greeks_to_chain(calls, current_price, r_rf, T, 'call')
    puts_greeks = GreeksCalculator.attach_greeks_to_chain(puts, current_price, r_rf, T, 'put')

    market_structure = MarketStructureAnalyzer.calculate_gamma_exposure(calls_greeks, puts_greeks, current_price)
    volatility_skew = VolatilitySkewAnalyzer.calculate_skew(calls_greeks, puts_greeks, current_price)
    market_structure["volatility_skew"] = volatility_skew

    iv_rank_data = VolatilitySkewAnalyzer.get_iv_rank(ticker, lookback_days=252)
    market_structure["iv_rank"] = iv_rank_data

    iv_pct_data = VolatilitySkewAnalyzer.get_iv_percentile(ticker, lookback_days=252)
    market_structure["iv_percentile"] = iv_pct_data

    full_vol = VolatilitySkewAnalyzer.full_volatility_analysis(calls_greeks, puts_greeks, current_price, ticker)
    market_structure["full_volatility_analysis"] = full_vol

    agent_result = MarketExpertTeam.run_agentic_loop(
        ticker=ticker,
        market_data=market_structure,
        days=days,
        use_meta_model=True,
        use_optimization=True
    )

    critic_verdict = agent_result.get("critic_review", {}).get("verdict", "REJECTED")
    is_approved = critic_verdict == "APPROVED"
    strategy = agent_result.get("strategy_proposed", "unknown")
    backtest_stats = agent_result.get("backtest", {})

    trade_executed = paper_broker.execute_trade(
        ticker=ticker,
        spot_price=current_price,
        strategy=strategy,
        critic_approved=is_approved,
        backtest_stats=backtest_stats
    )

    response = {
        "ticker": ticker,
        "current_price": round(current_price, 2),
        "target_expiry": target_expiry,
        "market_structure": market_structure,
        **agent_result,
        "paper_trade_status": trade_executed
    }
    return sanitized_response(response)

# ============================================================
# BACKTESTING ENDPOINTS
# ============================================================

@app.post("/api/backtest")
def run_backtest(request: BacktestRequest):
    from skills.backtester import StrategyBacktester
    ticker = request.ticker.upper()
    result = StrategyBacktester.run_historical_backtest(ticker, request.strategy, days=request.days or 252)
    return sanitized_response(result)

@app.post("/api/backtest/optimize")
def run_optimized_backtest(request: BacktestRequest):
    from skills.parameter_optimizer import ParameterOptimizer
    ticker = request.ticker.upper()
    result = ParameterOptimizer.quick_scan(ticker, request.strategy, days=min(request.days or 252, 252))
    return sanitized_response(result)


@app.post("/api/backtest/batch")
def run_batch_backtest(request: BatchBacktestRequest):
    """
    Run backtest across multiple tickers for institutional validation.
    Returns sorted results: best WR/PF first.
    """
    from skills.backtester import StrategyBacktester

    results = []
    for ticker in request.tickers:
        ticker = ticker.upper()
        try:
            result = StrategyBacktester.run_historical_backtest(
                ticker, request.strategy, days=request.days or 252
            )
            if "error" not in result:
                result["_ticker"] = ticker
                results.append(result)
        except Exception:
            continue

    # Sort by institutional metrics: WR desc, then PF desc
    def score(r):
        wr = r.get("win_rate_percent", 0)
        pf = r.get("profit_factor", 0)
        dd = r.get("max_drawdown", 100)
        sharpe = r.get("sharpe_ratio", 0)
        # Score: WR weighted 30%, PF 30%, Sharpe 25%, low DD 15%
        score_val = (wr / 100 * 0.30) + (min(pf, 3) / 3 * 0.30) + (min(max(sharpe, 0), 3) / 3 * 0.25) + ((100 - min(dd, 100)) / 100 * 0.15)
        return score_val

    results.sort(key=score, reverse=True)

    # Summary stats
    if results:
        avg_wr = np.mean([r.get("win_rate_percent", 0) for r in results])
        avg_pf = np.mean([r.get("profit_factor", 0) for r in results])
        avg_dd = np.mean([r.get("max_drawdown", 0) for r in results])
        avg_sharpe = np.mean([r.get("sharpe_ratio", 0) for r in results])
        summary = {
            "n_tickers": len(results),
            "avg_win_rate": round(avg_wr, 2),
            "avg_profit_factor": round(avg_pf, 2),
            "avg_drawdown": round(avg_dd, 2),
            "avg_sharpe": round(avg_sharpe, 2),
            "passed_institutional": sum(1 for r in results if r.get("win_rate_percent", 0) >= 75 and r.get("profit_factor", 0) >= 1.2 and r.get("max_drawdown", 100) < 20)
        }
    else:
        summary = {"error": "No valid results"}

    return sanitized_response({"results": results, "summary": summary})

# ============================================================
# HMM REGIME DETECTION ENDPOINT
# ============================================================

@app.get("/api/hmm/{ticker}")
def get_hmm_regime(ticker: str):
    try:
        hmm = RegimeDetectorHMM(ticker.upper(), n_components=4)
        result = hmm.fit_predict()
        adaptive = hmm.get_adaptive_strategy()
        result["adaptive_strategy"] = adaptive.get("final_strategy", result["recommended_strategy"])
        return sanitized_response(result)
    except Exception as e:
        return sanitized_response({"error": str(e), "ticker": ticker.upper()})

@app.get("/api/hmm/{ticker}/validation")
def get_hmm_validation(ticker: str):
    try:
        hmm = RegimeDetectorHMM(ticker.upper(), n_components=4)
        validation = hmm.validate_against_historical_events()
        return sanitized_response(validation)
    except Exception as e:
        return sanitized_response({"error": str(e)})

# ============================================================
# META-MODEL ENDPOINT
# ============================================================

@app.get("/api/meta/{ticker}")
def get_meta_label(ticker: str):
    from skills.meta_model import MetaLabeler
    try:
        meta = MetaLabeler()
        features = meta.build_features(ticker.upper(), lookback_days=252)
        if features is None or len(features) < 30:
            return sanitized_response({
                "bet_size": 1.0,
                "verdict": "APPROVE",
                "confidence": "low",
                "reason": "Insufficient data for meta-model — fallback to neutral sizing"
            })
        current_features = features.iloc[-1][meta._feature_names].values
        result = meta.get_bet_size(current_features)
        return sanitized_response(result)
    except Exception as e:
        return sanitized_response({"error": str(e), "ticker": ticker.upper()})

# ============================================================
# KALMAN FILTER PAIRS ENDPOINT
# ============================================================

@app.get("/api/statarb/kalman")
async def get_kalman_statarb():
    try:
        pairs = StatArbScanner.scan_pairs_kalman(days=90)
        return sanitized_response({"pairs": pairs})
    except Exception as e:
        return sanitized_response({"error": str(e)})

@app.get("/api/statarb/institutional")
async def get_institutional_statarb():
    try:
        pairs = StatArbScanner.get_institutional_pairs_scan(days=90)
        return sanitized_response({"pairs": pairs})
    except Exception as e:
        return sanitized_response({"error": str(e)})

# ============================================================
# ORIGINAL ENDPOINTS (Preserved)
# ============================================================

@app.get("/api/chart/{ticker}")
def get_chart_data(ticker: str):
    data = MarketDataAPI.get_ohlcv(ticker.upper())
    if not data:
        raise HTTPException(status_code=404, detail="Chart data not found.")
    return sanitized_response({"data": data})

@app.get("/api/macro")
def get_macro_data():
    return sanitized_response(macro_client.get_latest_macro_indicators())

@app.get("/api/macro/search")
def search_macro(query: str):
    data = macro_client.search_macro_database(query)
    return sanitized_response({"results": data})

@app.get("/api/macro/series/{series_id}")
def get_macro_series(series_id: str):
    data = macro_client.get_historical_series(series_id)
    return sanitized_response({"data": data})

@app.get("/api/heatmap")
def get_heatmap_data():
    return sanitized_response(MarketDataAPI.get_sector_heatmap())

@app.get("/api/portfolio")
def get_portfolio():
    return sanitized_response(paper_broker.get_portfolio())

@app.post("/api/portfolio/execute")
def execute_portfolio_trade(request: AnalysisRequest):
    ticker = request.ticker.upper()
    result = paper_broker.execute_trade(
        ticker=ticker,
        spot_price=OptionsFetcher.get_current_price(ticker),
        strategy="iron_condor",
        critic_approved=True,
        backtest_stats={"win_rate_percent": 75, "profit_factor": 1.5, "num_trades": 50}
    )
    return sanitized_response(result)

@app.get("/api/statarb")
async def get_statarb_heatmap():
    try:
        heatmap = StatArbScanner.scan_pairs(days=90)
        return sanitized_response({"pairs": heatmap})
    except Exception as e:
        return sanitized_response({"error": str(e)})

@app.get("/api/screener")
async def get_global_screener():
    try:
        return sanitized_response(GlobalScreener.run_daily_sweep())
    except Exception as e:
        return sanitized_response({"error": str(e)})

# ============================================================
# BROKER ENDPOINTS
# ============================================================

@app.post("/api/broker/order")
def submit_broker_order(request: BrokerOrderRequest):
    """
    Submit a live/paper trade through IBKR or Alpaca broker.
    """
    try:
        broker = get_broker(request.broker.upper(), paper=True)
        result = broker.submit_complex_order(
            ticker=request.ticker.upper(),
            strategy_type=request.strategy,
            dte=request.dte,
            sizing_pct=request.sizing_pct,
            strikes=request.strikes
        )
        return sanitized_response(result)
    except Exception as e:
        return sanitized_response({"error": str(e)})


@app.get("/api/broker/positions/{broker_name}")
def get_broker_positions(broker_name: str):
    """Get open positions from a specific broker."""
    try:
        broker = get_broker(broker_name.upper(), paper=True)
        positions = broker.get_positions()
        return sanitized_response({"positions": positions})
    except Exception as e:
        return sanitized_response({"error": str(e)})


@app.get("/api/broker/account/{broker_name}")
def get_broker_account(broker_name: str):
    """Get account metrics from a specific broker."""
    try:
        broker = get_broker(broker_name.upper(), paper=True)
        metrics = broker.fetch_account_metrics()
        return sanitized_response(metrics)
    except Exception as e:
        return sanitized_response({"error": str(e)})


@app.get("/api/broker/tc/{broker_name}")
def get_tc_estimate(broker_name: str, num_contracts: int = 10,
                    mid_price: float = 2.50, order_type: str = "market"):
    """Get transaction cost estimate for a broker."""
    try:
        broker = broker_name.upper()
        if broker not in ["IBKR", "ALPACA", "PAPER"]:
            return sanitized_response({"error": f"Unknown broker: {broker_name}"})
        tcm = TransactionCostModel(broker)
        cost = tcm.total_cost(
            num_contracts=num_contracts,
            mid_price=mid_price,
            order_type=order_type
        )
        return sanitized_response(cost)
    except Exception as e:
        return sanitized_response({"error": str(e)})


# ============================================================
# LIVE GEX (chain-backed JSON for polling / serverless)
# ============================================================

@app.get("/api/gex/live/{ticker}")
def get_gex_live(ticker: str):
    """Gamma exposure from live option chain (same pipeline as /api/analyze GEX)."""
    t = ticker.upper()
    try:
        current_price = OptionsFetcher.get_current_price(t)
        if current_price == 0.0:
            return sanitized_response({"error": "Ticker not found", "ticker": t})
        expirations = OptionsFetcher.get_options_expiration_dates(t)
        if not expirations:
            return sanitized_response({"error": "No options data", "ticker": t})
        target_expiry = expirations[0]
        data = OptionsFetcher.get_options_chain(t, target_expiry)
        if not data:
            return sanitized_response({"error": "Failed to load chain", "ticker": t})
        calls = data["calls"]
        puts = data["puts"]
        r_rf = 0.045
        T = 7.0 / 365.0
        calls_g = GreeksCalculator.attach_greeks_to_chain(calls, current_price, r_rf, T, "call")
        puts_g = GreeksCalculator.attach_greeks_to_chain(puts, current_price, r_rf, T, "put")
        surface = HFTOptionsPipeline.from_option_chain(calls_g, puts_g, current_price)
        surface["ticker"] = t
        surface["expiry"] = target_expiry
        return sanitized_response(surface)
    except Exception as e:
        return sanitized_response({"error": str(e), "ticker": t})


async def _gex_websocket_loop(websocket: WebSocket):
    await websocket.accept()
    base_spot = 500.0
    try:
        while True:
            base_spot += __import__("random").uniform(-0.10, 0.10)
            gex_surface = HFTOptionsPipeline.generate_live_gex_surface(spot_price=base_spot)
            await websocket.send_json(_sanitize(gex_surface))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        print("HFT GEX Feed Disconnected.")


# ============================================================
# WEBSOCKET: Real-time GEX Feed (local dev: /ws/gex; behind /api: /api/ws/gex)
# ============================================================

@app.websocket("/ws/gex")
async def websocket_gex_feed(websocket: WebSocket):
    await _gex_websocket_loop(websocket)


@app.websocket("/api/ws/gex")
async def websocket_gex_feed_api_prefix(websocket: WebSocket):
    await _gex_websocket_loop(websocket)

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "OPERATIONAL",
        "tier": "INSTITUTIONAL",
        "version": "2.0",
        "endpoints": {
            "analyze": "/api/analyze [POST]",
            "backtest": "/api/backtest [POST]",
            "backtest_batch": "/api/backtest/batch [POST]",
            "optimize": "/api/backtest/optimize [POST]",
            "hmm": "/api/hmm/{ticker} [GET]",
            "meta": "/api/meta/{ticker} [GET]",
            "statarb_kalman": "/api/statarb/kalman [GET]",
            "statarb_inst": "/api/statarb/institutional [GET]",
            "broker_order": "/api/broker/order [POST]",
            "broker_positions": "/api/broker/positions/{broker} [GET]",
            "broker_account": "/api/broker/account/{broker} [GET]",
            "broker_tc": "/api/broker/tc/{broker} [GET]",
            "portfolio": "/api/portfolio [GET]",
            "macro": "/api/macro [GET]",
            "heatmap": "/api/heatmap [GET]",
            "screener": "/api/screener [GET]",
            "gex_live": "/api/gex/live/{ticker} [GET]",
            "ws_gex": "/ws/gex [WS]",
            "ws_gex_api": "/api/ws/gex [WS]",
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
