from abc import ABC, abstractmethod

class AbstractBroker(ABC):
    """
    Phase 10 Institutional Engine: Live Execution API Architecture.
    All broker integrations (IBKR, Alpaca, PaperTrader) must conform to this schema
    to ensure seamless integration with the AI Orchestrator execution loop.
    """
    @abstractmethod
    def fetch_account_metrics(self) -> dict:
        """Returns Cash Balance, Net Liquidity, Margin Utilization."""
        pass
        
    @abstractmethod
    def submit_complex_order(self, ticker: str, strategy_type: str, dte: int, sizing_pct: float) -> dict:
        """
        Executes a multi-leg option strategy (e.g. Iron Condor).
        Returns the fill confirmation and execution IDs.
        """
        pass
        
    @abstractmethod
    def close_position(self, position_id: str) -> bool:
        """Gracefully exits a running position based on Triple Barrier breach."""
        pass
