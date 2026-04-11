from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import asyncio
from typing import List

# Add parent path so we can import from skills
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from skills.options_chain_fetcher import OptionsFetcher
from skills.greeks_calculator import GreeksCalculator
from skills.gamma_exposure import MarketStructureAnalyzer
from core_agents.orchestrator import MarketExpertTeam
from skills.macro_fetcher import macro_client
from skills.market_data_api import MarketDataAPI
from skills.paper_trader import paper_broker
from skills.volatility_skew import VolatilitySkewAnalyzer
from skills.statarb_scanner import StatArbScanner
from skills.global_screener import GlobalScreener
from skills.hft_options_pipeline import HFTOptionsPipeline

app = FastAPI(title="Options Quant Terminal API V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    ticker: str

@app.post("/api/analyze")
def analyze_ticker(request: AnalysisRequest):
    ticker = request.ticker.upper()
    
    # 1. Fetch live data
    current_price = OptionsFetcher.get_current_price(ticker)
    if current_price == 0.0:
        raise HTTPException(status_code=404, detail="Ticker not found or failed to fetch.")
        
    expirations = OptionsFetcher.get_options_expiration_dates(ticker)
    if not expirations:
        raise HTTPException(status_code=404, detail="No options data available for this ticker.")
        
    target_expiry = expirations[0] # Just grab the nearest term for now
    
    data = OptionsFetcher.get_options_chain(ticker, target_expiry)
    if not data:
        raise HTTPException(status_code=500, detail="Failed to load options chain.")
        
    calls = data["calls"]
    puts = data["puts"]
    
    # 2. Add Rigorous Greeks Calculation (Quant Agent Skill Execution)
    # Assume 4.5% risk free rate for approximation
    r_rf = 0.045
    # Simplistic exact DT expiration calculation 
    # To do strict Black Scholes T we need hours to expiry, but for demo we approximate to 7 days if unknown.
    days_to_expiry = 7.0 
    T = days_to_expiry / 365.0
    
    calls_greeks = GreeksCalculator.attach_greeks_to_chain(calls, current_price, r_rf, T, 'call')
    puts_greeks = GreeksCalculator.attach_greeks_to_chain(puts, current_price, r_rf, T, 'put')
    
    # 3. Market Structure (Risk / AP Specialist Loop)
    market_structure = MarketStructureAnalyzer.calculate_gamma_exposure(calls_greeks, puts_greeks, current_price)
    
    # Phase 5: IV Skew Architecture
    volatility_skew = VolatilitySkewAnalyzer.calculate_skew(calls_greeks, puts_greeks, current_price)
    market_structure["volatility_skew"] = volatility_skew
    
    # 4. Agentic Analysis (Trader & Critic Loop via Phase 2 Integration)
    agent_insights = MarketExpertTeam.run_agentic_loop(ticker, market_structure)
    
    # 5. Execute Paper Trade based on Critic's boolean evaluation
    critic_verdict = "APPROVED" in agent_insights["critic_review"].upper()
    trade_executed = paper_broker.execute_trade(ticker, current_price, agent_insights["backtest"]["strategy_tested"], critic_verdict, agent_insights["backtest"])
    
    return {
        "ticker": ticker,
        "current_price": current_price,
        "target_expiry": target_expiry,
        "market_structure": market_structure,
        "agent_insights": agent_insights,
        "paper_trade_status": trade_executed
    }

@app.get("/api/chart/{ticker}")
def get_chart_data(ticker: str):
    data = MarketDataAPI.get_ohlcv(ticker.upper())
    if not data:
        raise HTTPException(status_code=404, detail="Chart data not found.")
    return {"data": data}

@app.get("/api/macro")
def get_macro_data():
    return macro_client.get_latest_macro_indicators()
    
@app.get("/api/macro/search")
def search_macro(query: str):
    data = macro_client.search_macro_database(query)
    return {"results": data}

@app.get("/api/macro/series/{series_id}")
def get_macro_series(series_id: str):
    data = macro_client.get_historical_series(series_id)
    return {"data": data}

@app.get("/api/heatmap")
def get_heatmap_data():
    return MarketDataAPI.get_sector_heatmap()

@app.get("/api/portfolio")
def get_portfolio():
    return paper_broker.get_portfolio()

@app.get("/api/statarb")
async def get_statarb_heatmap():
    """Returns the ETF pairs Z-Score mapping."""
    try:
        heatmap = StatArbScanner.scan_pairs(days=90)
        return {"pairs": heatmap}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/statarb")
async def get_statarb_heatmap():
    """Returns the ETF pairs Z-Score mapping."""
    try:
        heatmap = StatArbScanner.scan_pairs(days=90)
        return {"pairs": heatmap}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/screener")
async def get_global_screener():
    """Returns the absolute best market edges autonomously found."""
    try:
        return GlobalScreener.run_daily_sweep()
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws/gex")
async def websocket_gex_feed(websocket: WebSocket):
    """
    Phase 11: Real-Time High-Frequency Gamma Exposure Feed.
    Pushes updated Call/Put walls and Strike metrics every 1.0 seconds natively.
    """
    await websocket.accept()
    base_spot = 500.0
    try:
        while True:
            # Simulate slight tick movement in Spot Price to force math recalculation
            base_spot += __import__("random").uniform(-0.10, 0.10)
            
            # Execute Phase 11 HFT Pipeline
            gex_surface = HFTOptionsPipeline.generate_live_gex_surface(spot_price=base_spot)
            
            await websocket.send_json(gex_surface)
            await asyncio.sleep(1.0) # Absolute 1-second refresh rate mandate
    except WebSocketDisconnect:
        print("HFT Feed Disconnected.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
