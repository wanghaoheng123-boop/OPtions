import json
import os
from datetime import datetime
from typing import Dict, Any, List

class LocalMemoryStore:
    """
    JSON-based Memory System for preserving Agent decisions, verified backtest records,
    and algorithms learned from GitHub.
    """
    def __init__(self, db_path: str = "memory/agent_memory.json"):
        # Go up one level from this file's folder to ensure correct path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_path)
        self._ensure_db()

    def _ensure_db(self):
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, "w") as f:
                json.dump({"sessions": [], "verified_algorithms": []}, f)

    def load_memory(self) -> Dict[str, Any]:
        with open(self.db_path, "r") as f:
            return json.load(f)

    def save_memory(self, memory_data: Dict[str, Any]):
        with open(self.db_path, "w") as f:
            json.dump(memory_data, f, indent=4)

    def log_session(self, ticker: str, market_data: dict, trader_insight: str, backtest_result: dict, critic_review: str):
        """
        Preserves the entire review and edit loop for future few-shot contextual learning.
        """
        memory = self.load_memory()
        session_log = {
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "market_data": market_data,
            "trader_insight": trader_insight,
            "backtest_result": backtest_result,
            "critic_review": critic_review,
            "status": "APPROVED" if backtest_result.get("verdict") == "PASS" else "REJECTED"
        }
        memory["sessions"].append(session_log)
        self.save_memory(memory)
        return True
