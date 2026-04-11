import json
import os
from datetime import datetime

class PaperTrader:
    """
    Virtual Sandbox for the AI Agents. Tracks 'executed' positions, simulated PnL,
    and mimics PolyBot paper-trading integrations for strategy evaluation.
    """
    def __init__(self, db_path: str = "memory/paper_portfolio.json"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_path)
        self._ensure_db()

    def _ensure_db(self):
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "w") as f:
                json.dump({
                    "cash_balance": 100000.0,
                    "positions": [],
                    "pnl_history": []
                }, f)

    def execute_trade(self, ticker: str, spot_price: float, strategy: str, critic_approved: bool, backtest_stats: dict):
        if not critic_approved:
            return {"status": "rejected_by_critic"}
            
        with open(self.db_path, "r") as f:
            portfolio = json.load(f)
            
        # Mathematical Kelly Criterion Sizing
        # Formula: Kelly % = W - ((1 - W) / R)
        w = backtest_stats.get("win_rate_percent", 50.0) / 100.0
        
        # Approximate Risk/Reward (R). Using empirical drawdown as risk proxy.
        # If strategy is profitable, assume R = 1.0 (baseline) for simplicity if actual R is infinite or indeterminate.
        r = 1.0 
        
        # Calculate Full Kelly
        full_kelly = w - ((1.0 - w) / r)
        
        # Mitigate risk with Half Kelly (institutional standard)
        half_kelly = full_kelly / 2.0
        
        # Cap max allocation at 20%, minimum at 1%
        optimal_allocation_pct = max(0.01, min(half_kelly, 0.20))
        
        allocation = portfolio["cash_balance"] * optimal_allocation_pct
        shares = allocation / spot_price if spot_price > 0 else 0
        
        trade = {
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "strategy": strategy,
            "entry_price": spot_price,
            "shares_or_contracts": round(shares, 2),
            "capital_allocated": round(allocation, 2),
            "kelly_percentage": round(optimal_allocation_pct * 100, 2),
            "status": "OPEN"
        }
        
        portfolio["cash_balance"] -= allocation
        portfolio["positions"].append(trade)
        
        with open(self.db_path, "w") as f:
            json.dump(portfolio, f, indent=4)
            
        return trade
        
    def get_portfolio(self):
        with open(self.db_path, "r") as f:
            return json.load(f)

paper_broker = PaperTrader()
