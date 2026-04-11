import os
import sys

# Ensure imports work from the root of the project
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from skills.options_chain_fetcher import OptionsFetcher
from skills.greeks_calculator import GreeksCalculator
from skills.gamma_exposure import MarketStructureAnalyzer
from skills.backtester import StrategyBacktester
from skills.researcher_skill import GitHubResearcher
from core_agents.orchestrator import MarketExpertTeam
from memory.db_setup import LocalMemoryStore

def run_tests():
    print("--- [1] Testing OptionsFetcher ---")
    ticker = "SPY"
    print(f"Fetching current price for {ticker}...")
    price = OptionsFetcher.get_current_price(ticker)
    print(f"Price: {price}")
    
    print(f"Fetching expirations...")
    expirations = OptionsFetcher.get_options_expiration_dates(ticker)
    if not expirations:
        print("FAIL: No expirations found.")
        return
    
    target_expiry = expirations[0]
    print(f"Fetching chain for {target_expiry}...")
    data = OptionsFetcher.get_options_chain(ticker, target_expiry)
    if not data or data['calls'].empty or data['puts'].empty:
        print("FAIL: Options chain empty or failed to parse.")
        return
    print(f"SUCCESS: Fetched {len(data['calls'])} calls and {len(data['puts'])} puts.")

    print("\n--- [2] Testing GreeksCalculator ---")
    calls = data["calls"]
    puts = data["puts"]
    
    r_rf = 0.045
    T = 7.0 / 365.0
    print("Calculating call Greeks...")
    calls_greeks = GreeksCalculator.attach_greeks_to_chain(calls, price, r_rf, T, 'call')
    print("Calculating put Greeks...")
    puts_greeks = GreeksCalculator.attach_greeks_to_chain(puts, price, r_rf, T, 'put')
    
    if 'calc_gamma' not in calls_greeks.columns or 'calc_gamma' not in puts_greeks.columns:
        print("FAIL: Greeks failed to attach.")
        return
    print("SUCCESS: Greeks calculated and attached. Sample call gamma:", calls_greeks['calc_gamma'].iloc[0])

    print("\n--- [3] Testing MarketStructureAnalyzer ---")
    market_structure = MarketStructureAnalyzer.calculate_gamma_exposure(calls_greeks, puts_greeks, price)
    if "error" in market_structure:
        print(f"FAIL: Market structure error: {market_structure['error']}")
    else:
        print("SUCCESS: Market structure calculated:", market_structure)

    print("\n--- [4] Testing Backtester ---")
    print("Testing 'long_gamma' backtest for 30 days...")
    backtest = StrategyBacktester.run_historical_backtest(ticker, 'long_gamma', 30)
    print("Backtest Result:", backtest)
    if "error" in backtest:
        print("FAIL: Backtest failed.")
    else:
        print("SUCCESS: Backtest completed.")

    print("\n--- [5] Testing Orchestrator & Memory ---")
    try:
        agent_insights = MarketExpertTeam.run_agentic_loop(ticker, market_structure)
        print("SUCCESS: Orchestrator ran seamlessly. Output:")
        print(agent_insights)
    except Exception as e:
        print(f"FAIL: Orchestrator failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_tests()
