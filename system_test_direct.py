import sys
import os
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from skills.statarb_scanner import StatArbScanner
from skills.macro_fetcher import macro_client
from core_agents.orchestrator import MarketExpertTeam

def print_header(title):
    print(f"\n{'='*50}\n[TEST] {title}\n{'='*50}")

def test_statarb():
    print_header("Statistical Arbitrage Scanner")
    data = StatArbScanner.scan_pairs(days=30)
    if data and hasattr(data, '__len__') and len(data) > 0 and 'error' not in data[0]:
        print(f"SUCCESS: Analyzed {len(data)} correlated pairs.")
        print(f"Top Divergence: {data[0]['pair']} -> Z-Score: {data[0].get('z_score')}")
        return True
    print("FAILED STATARB:", data)
    return False

def test_macro():
    print_header("FRED Macro API")
    data = macro_client.get_latest_macro_indicators()
    if 'CPIAUCSL_YoY' in data or 'CPIAUCSL' in data:
        print(f"SUCCESS: Fetched Macro Data.")
        return True
    print("FAILED MACRO:", data)
    return False

def test_analyze(ticker):
    print_header(f"Agentic Quantum Loop: {ticker}")
    start = time.time()
    
    # Mock some data structure 
    market_structure = {
        "total_net_gex": 100,
        "call_wall_strike": 500,
        "put_wall_strike": 400,
        "dealer_position_tilt": "Long Gamma",
        "volatility_skew": {
            "volatility_skew_index": -1.5,
            "sentiment": "Fear",
            "otm_call_iv": 15,
            "otm_put_iv": 25
        }
    }
    
    try:
        insights = MarketExpertTeam.run_agentic_loop(ticker, market_structure)
        bkt = insights.get('backtest', {})
        
        print(f"Execution Time: {time.time() - start:.2f}s")
        print(f"Trader Decision:  {insights.get('trader_insight')}")
        print("\n[Backtester]")
        print("Raw Backtest Output:", bkt)
        print(f"Verdict: {bkt.get('verdict')}")
        print(f"Critic Review:    {insights.get('critic_review')}")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

def main():
    checks = []
    checks.append(test_statarb())
    # Macro API takes actual HTTP calls, we mock it or run it
    checks.append(test_macro())
    checks.append(test_analyze("SPY"))
    
    print_header("TEST SUMMARY")
    if all(checks):
        print("COMMAND CENTER: ALL SYSTEMS PASSED. V2 TERMINAL READY.")
    else:
        print("COMMAND CENTER: ERRORS DETECTED.")

if __name__ == "__main__":
    main()
