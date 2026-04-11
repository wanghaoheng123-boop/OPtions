import requests
import json
import time

print("--- INITIATING PHASE 6 END-TO-END LIVE QUANT TEST ---")
print("Target: SPY")
print("Sending request to Orchestrator API...")
start = time.time()
try:
    res = requests.post("http://127.0.0.1:8001/api/analyze", json={"ticker": "SPY"}, timeout=30)
    print(f"Request completed in {time.time() - start:.2f} seconds")
    
    if res.status_code == 200:
        data = res.json()
        print("\n=== SYSTEM RESPONSE OK ===")
        print(f"Volatility Skew Metric: {data['market_structure'].get('volatility_skew', {}).get('volatility_skew_index', 'MISSING')}")
        
        print("\n=== AGENT INSIGHTS ===")
        print(f"Trader Proposal: {data['agent_insights'].get('trader_insight', 'ERROR')}")
        
        print("\n=== VERIFICATION BACKTEST MATRIX ===")
        backtest = data['agent_insights'].get('backtest', {})
        print(f"Strategy: {backtest.get('strategy_tested')}")
        print(f"Win Rate: {backtest.get('win_rate_percent', 'ERROR')}%")
        print(f"Profit Factor: {backtest.get('profit_factor', 'ERROR')}")
        print(f"Max Drawdown: {backtest.get('max_drawdown', 'ERROR')}%")
        print(f"Out of Sample Verified: {backtest.get('out_of_sample_verified', False)}")
        print(f"Verdict: {backtest.get('verdict', 'ERROR')}")
        
        print("\n=== CRITIC REVIEW ===")
        print(f"Review: {data['agent_insights'].get('critic_review', 'ERROR')}")
        
        print("\n=== LIVE PAPER EXECUTION ===")
        print(f"Trade Executed Status: {data.get('trade_executed', 'ERROR')}")
    else:
        print(f"FAILED WITH HTTP {res.status_code}")
        print(res.text)

except Exception as e:
    print(f"CONNECTION ERROR: {e}")
