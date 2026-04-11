import sys
import os

# Ensure the app folder is in the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core_agents.orchestrator import MarketExpertTeam
from skills.backtester import StrategyBacktester

try:
    print("--- DIRECT QUANT RAG TEST ---")
    insight = MarketExpertTeam.run_agentic_loop("SPY", {"total_net_gex": 100, "volatility_skew": {"sentiment": "Extreme Fear"}})
    print("\n[Traders Insight]:", insight["trader_insight"])
    print("[Critic Review]:", insight["critic_review"])
    print("\n[Backtest Results]:")
    for k, v in insight["backtest"].items():
        print(f"  {k}: {v}")
except Exception as e:
    import traceback
    traceback.print_exc()
