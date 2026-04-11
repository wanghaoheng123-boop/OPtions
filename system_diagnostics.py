import requests
import time
import sys

PORT = 8002
BASE_URL = f"http://127.0.0.1:{PORT}"

def print_header(title):
    print(f"\n{'='*50}\n[TEST] {title}\n{'='*50}")

def test_statarb():
    print_header("Statistical Arbitrage Scanner")
    res = requests.get(f"{BASE_URL}/api/statarb", timeout=15)
    if res.status_code == 200:
        data = res.json()
        if 'error' in data:
            print("FAILED:", data['error'])
            return False
        print(f"SUCCESS: Loaded {len(data['pairs'])} cointegrated pairs.")
        print(f"Top Divergence: {data['pairs'][0]['pair']} -> Z-Score: {data['pairs'][0]['z_score']}")
        return True
    print("FAILED: HTTP", res.status_code)
    return False

def test_macro():
    print_header("FRED Macro API")
    res = requests.get(f"{BASE_URL}/api/macro", timeout=15)
    if res.status_code == 200:
        data = res.json()
        print(f"SUCCESS: Fetched indicators. CPI: {data.get('CPIAUCSL', 'N/A')}")
        return True
    print("FAILED: HTTP", res.status_code)
    return False

def test_analyze(ticker):
    print_header(f"Agentic Quantum Loop: {ticker}")
    start = time.time()
    res = requests.post(f"{BASE_URL}/api/analyze", json={"ticker": ticker}, timeout=60)
    print(f"Execution Time: {time.time() - start:.2f}s")
    
    if res.status_code == 200:
        data = res.json()
        insights = data.get('agent_insights', {})
        bkt = insights.get('backtest', {})
        trade = data.get('paper_trade_status', {})
        
        print(f"IV Skew Status:   {data.get('market_structure', {}).get('volatility_skew', {}).get('sentiment')}")
        print(f"Trader Decision:  {insights.get('trader_insight')}")
        print(f"Critic Review:    {insights.get('critic_review')}")
        print("\n[Backtester]")
        print(f"Strategy: {bkt.get('strategy_tested')} | Win Rate: {bkt.get('win_rate_percent')}% | Profit Factor: {bkt.get('profit_factor')}")
        print(f"Verdict: {bkt.get('verdict')}")
        
        print("\n[Paper Broker]")
        print(f"Trade Execution:  {trade.get('status')} | Capital: ${trade.get('trade_log', {}).get('capital_allocated', 0)}")
        return True
    else:
        print("FAILED: HTTP", res.status_code)
        try:
            print(res.json())
        except:
            print(res.text)
        return False

def main():
    print("Waiting 3s for fastAPI to boot...")
    time.sleep(3)
    
    checks = []
    checks.append(test_statarb())
    checks.append(test_macro())
    checks.append(test_analyze("SPY"))
    checks.append(test_analyze("TSLA")) # High volatility test
    
    print_header("TEST SUMMARY")
    if all(checks):
        print("ALL SYSTEMS PASSED. INSTITUTIONAL ENGINE VERIFIED.")
    else:
        print("ERRORS DETECTED IN PIPELINE.")

if __name__ == "__main__":
    main()
