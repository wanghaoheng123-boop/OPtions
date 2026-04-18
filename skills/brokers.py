from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime
import os
import numpy as np


class AbstractBroker(ABC):
    """
    Institutional Live Execution API Architecture.

    All broker integrations (IBKR, Alpaca, Tradier) must conform to this schema
    to ensure seamless integration with the AI Orchestrator execution loop.

    Phase 5 Implementation: IBKR and Alpaca stub implementations added.
    """

    @abstractmethod
    def fetch_account_metrics(self) -> dict:
        """Returns Cash Balance, Net Liquidity, Margin Utilization."""
        pass

    @abstractmethod
    def submit_complex_order(self, ticker: str, strategy_type: str, dte: int,
                              sizing_pct: float, strikes: dict = None) -> dict:
        """
        Executes a multi-leg option strategy (e.g. Iron Condor, Wheel, Covered Call).
        Returns the fill confirmation and execution IDs.
        """
        pass

    @abstractmethod
    def close_position(self, position_id: str) -> bool:
        """Gracefully exits a running position based on Triple Barrier breach."""
        pass

    @abstractmethod
    def get_option_chain(self, ticker: str, expiration: str = None) -> dict:
        """Fetch live option chain for ticker."""
        pass


# ============================================================
# TRANSACTION COST & SLIPPAGE MODEL
# ============================================================

class TransactionCostModel:
    """
    Institutional-grade transaction cost modeling.

    Components:
    1. Commission: per-contract fees (IBKR: $0.65/contract, Alpaca: $0/contract)
    2. Bid-Ask Spread: market orders pay half the spread
    3. Slippage: price impact based on order size and liquidity

    Based on Aldridge, "High-Frequency Trading" — Chapter on transaction cost modeling.
    """

    BROKER_CONFIGS = {
        "IBKR": {
            "commission_per_contract": 0.65,
            "min_commission": 1.0,
            "base_spread_bps": 2.0,  # Base spread in basis points
        },
        "ALPACA": {
            "commission_per_contract": 0.0,
            "min_commission": 0.0,
            "base_spread_bps": 3.0,  # Alpaca has slightly wider spreads
        },
        "PAPER": {
            "commission_per_contract": 0.0,
            "min_commission": 0.0,
            "base_spread_bps": 1.0,  # Simulated tight spreads for paper
        }
    }

    def __init__(self, broker: str = "PAPER"):
        self.config = self.BROKER_CONFIGS.get(broker, self.BROKER_CONFIGS["PAPER"])
        self.broker = broker

    def calculate_commission(self, num_contracts: int, premium: float) -> float:
        """Calculate commission cost for a trade."""
        commission = self.config["commission_per_contract"] * num_contracts
        return max(commission, self.config["min_commission"])

    def calculate_spread_cost(self, num_contracts: int, mid_price: float,
                               order_type: str = "market") -> float:
        """
        Calculate bid-ask spread cost.

        Args:
            num_contracts: Number of contracts
            mid_price: Midpoint price of the option
            order_type: 'market' (pays half spread) or 'limit' (no spread cost assumed)
        """
        if order_type == "limit":
            return 0.0

        spread_bps = self.config["base_spread_bps"]
        # Market orders pay approximately half the spread
        spread_cost_per_contract = mid_price * (spread_bps / 10000) * 0.5
        return spread_cost_per_contract * num_contracts

    def calculate_slippage(self, num_contracts: int, mid_price: float,
                           market_impact_factor: float = 0.1) -> float:
        """
        Estimate slippage based on order size and market impact.

        Uses a simple square-root market impact model:
        slippage = market_impact_factor * sqrt(num_contracts) * mid_price

        Args:
            num_contracts: Number of contracts
            mid_price: Option mid price
            market_impact_factor: Liquidity coefficient (higher for illiquid options)
        """
        if num_contracts <= 5:
            return 0.0  # Small orders have minimal market impact

        slippage = market_impact_factor * np.sqrt(num_contracts) * mid_price * 0.001
        return min(slippage, mid_price * 0.01)  # Cap at 1% of price

    def total_cost(self, num_contracts: int, mid_price: float,
                   order_type: str = "market",
                   market_impact_factor: float = 0.1) -> dict:
        """
        Calculate total transaction cost breakdown.

        Returns detailed cost components for transparency.
        """
        commission = self.calculate_commission(num_contracts, mid_price)
        spread_cost = self.calculate_spread_cost(num_contracts, mid_price, order_type)
        slippage = self.calculate_slippage(num_contracts, mid_price, market_impact_factor)
        total = commission + spread_cost + slippage

        # Cost as percentage of notional
        notional = num_contracts * mid_price * 100  # 100 shares per contract
        total_cost_bps = (total / notional * 10000) if notional > 0 else 0

        return {
            "broker": self.broker,
            "num_contracts": num_contracts,
            "commission": round(commission, 2),
            "spread_cost": round(spread_cost, 2),
            "slippage": round(slippage, 2),
            "total_cost": round(total, 2),
            "total_cost_bps": round(total_cost_bps, 2),
            "notional": round(notional, 2),
            "order_type": order_type
        }


# ============================================================
# IBKR STUB IMPLEMENTATION
# ============================================================

class IBKRBroker(AbstractBroker):
    """
    Interactive Brokers REST API integration stub.

    In production:
    - Use `ib_insync` library for the Trader Workstation (TWS) API
    - Or use IBKR REST API with OAuth/JWT authentication
    - Connect to paper trading account first (paper=1 parameter)

    Commission Structure (approximate):
    - $0.65 per contract
    - $1.00 minimum per order
    """

    def __init__(self, account_id: str = "PAPER", paper: bool = True):
        self.account_id = account_id
        self.paper = paper
        self.broker_name = "IBKR"
        self.tcm = TransactionCostModel("IBKR")
        self._positions = {}
        self._orders = {}
        self._order_counter = 1000

    def _live_requested_response(self, method: str) -> Optional[dict]:
        """If user opts into live IBKR via env, explain that TWS/Gateway is required."""
        flag = os.getenv("IBKR_ENABLE_LIVE", "").lower()
        if flag not in ("1", "true", "yes"):
            return None
        return {
            "broker": self.broker_name,
            "error": "IBKR_REQUIRES_TWS_OR_GATEWAY",
            "message": (
                "Live IBKR is not wired in this repo. Use Trader Workstation or "
                "IB Gateway with ib_insync, or set ALPACA_API_KEY / ALPACA_API_SECRET "
                "for Alpaca REST."
            ),
            "method": method,
            "is_paper": self.paper,
            "timestamp": datetime.now().isoformat(),
        }

    def fetch_account_metrics(self) -> dict:
        """
        Fetch account balance and margin metrics.

        In production: GET /v1/portfolio/{accountId}/positions
        with IBKR REST API.
        """
        blocked = self._live_requested_response("fetch_account_metrics")
        if blocked:
            return blocked
        # Stub: return simulated account data
        return {
            "broker": self.broker_name,
            "account_id": self.account_id,
            "cash_balance": 100000.0,
            "net_liquidation": 100000.0,
            "buying_power": 400000.0,  # Reg-T margin = 50%
            "margin_utilization": 0.0,
            "is_paper": self.paper,
            "timestamp": datetime.now().isoformat()
        }

    def get_option_chain(self, ticker: str, expiration: str = None) -> dict:
        """
        Fetch live option chain from IBKR.

        In production: GET /v1/secdef/searches with type=OPT
        """
        blocked = self._live_requested_response("get_option_chain")
        if blocked:
            return blocked
        # Stub: delegate to yfinance
        import yfinance as yf
        try:
            opt = yf.Ticker(ticker)
            if expiration:
                return opt.option_chain(expiration)
            else:
                expirations = opt.options
                if expirations:
                    return opt.option_chain(expirations[0])
                return {}
        except Exception:
            return {}

    def submit_complex_order(self, ticker: str, strategy_type: str, dte: int,
                              sizing_pct: float, strikes: dict = None) -> dict:
        """
        Submit a multi-leg options order.

        Strategy types: 'iron_condor', 'wheel', 'covered_call', 'long_gamma',
                        'short_put', 'bull_call_spread', 'bear_put_spread'

        In production: POST /v1/orders
        """
        blocked = self._live_requested_response("submit_complex_order")
        if blocked:
            return {**blocked, "status": "REJECTED"}
        import random

        self._order_counter += 1
        order_id = f"IBKR_{self._order_counter}"

        # Simulate order fill
        fill_price = random.uniform(1.50, 3.50)  # Simulated premium
        num_contracts = max(1, int(sizing_pct * 100))

        # Calculate costs
        cost_breakdown = self.tcm.total_cost(
            num_contracts=num_contracts,
            mid_price=fill_price,
            order_type="market",
            market_impact_factor=0.1
        )

        position_id = f"POS_{self._order_counter}"
        self._positions[position_id] = {
            "order_id": order_id,
            "ticker": ticker,
            "strategy": strategy_type,
            "dte": dte,
            "num_contracts": num_contracts,
            "entry_premium": fill_price,
            "entry_date": datetime.now().isoformat(),
            "status": "OPEN",
            "cost_breakdown": cost_breakdown,
            "strikes": strikes or {}
        }

        return {
            "order_id": order_id,
            "position_id": position_id,
            "status": "FILLED",
            "fill_price": fill_price,
            "num_contracts": num_contracts,
            "cost_breakdown": cost_breakdown,
            "broker": self.broker_name,
            "is_paper": self.paper,
            "message": f"Paper order filled: {strategy_type} on {ticker}"
        }

    def close_position(self, position_id: str) -> bool:
        """Close an open position."""
        if position_id in self._positions:
            pos = self._positions[position_id]
            pos["status"] = "CLOSED"
            pos["exit_date"] = datetime.now().isoformat()
            return True
        return False

    def get_positions(self) -> List[dict]:
        """Get all open positions."""
        return [p for p in self._positions.values() if p["status"] == "OPEN"]


# ============================================================
# ALPACA STUB IMPLEMENTATION
# ============================================================

class AlpacaBroker(AbstractBroker):
    """
    Alpaca Trading API integration stub.

    Commission: $0 per trade (commission-free options)
    Spread: Generally wider than IBKR

    In production:
    - Use `alpaca-trade-api` library
    - API key/secret from alpaca.markets
    - Paper trading at paper.alpacapi.com
    """

    def __init__(self, api_key: str = "PAPER", api_secret: str = "PAPER", paper: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper
        self.broker_name = "ALPACA"
        self.tcm = TransactionCostModel("ALPACA")
        self._positions = {}
        self._orders = {}
        self._order_counter = 2000

    def fetch_account_metrics(self) -> dict:
        """
        Fetch account from Alpaca.

        In production: GET /account
        """
        return {
            "broker": self.broker_name,
            "account_id": self.api_key[:8] + "...",
            "cash_balance": 100000.0,
            "net_liquidation": 100000.0,
            "buying_power": 400000.0,
            "margin_utilization": 0.0,
            "is_paper": self.paper,
            "timestamp": datetime.now().isoformat()
        }

    def get_option_chain(self, ticker: str, expiration: str = None) -> dict:
        """Fetch option chain from Alpaca."""
        import yfinance as yf
        try:
            opt = yf.Ticker(ticker)
            if expiration:
                return opt.option_chain(expiration)
            else:
                expirations = opt.options
                if expirations:
                    return opt.option_chain(expirations[0])
                return {}
        except Exception:
            return {}

    def submit_complex_order(self, ticker: str, strategy_type: str, dte: int,
                              sizing_pct: float, strikes: dict = None) -> dict:
        """
        Submit order to Alpaca.

        In production: POST /v2/orders
        """
        import random

        self._order_counter += 1
        order_id = f"ALP_{self._order_counter}"

        fill_price = random.uniform(1.50, 3.50)
        num_contracts = max(1, int(sizing_pct * 100))

        cost_breakdown = self.tcm.total_cost(
            num_contracts=num_contracts,
            mid_price=fill_price,
            order_type="market"
        )

        position_id = f"APOS_{self._order_counter}"
        self._positions[position_id] = {
            "order_id": order_id,
            "ticker": ticker,
            "strategy": strategy_type,
            "dte": dte,
            "num_contracts": num_contracts,
            "entry_premium": fill_price,
            "entry_date": datetime.now().isoformat(),
            "status": "OPEN",
            "cost_breakdown": cost_breakdown,
            "strikes": strikes or {}
        }

        return {
            "order_id": order_id,
            "position_id": position_id,
            "status": "FILLED",
            "fill_price": fill_price,
            "num_contracts": num_contracts,
            "cost_breakdown": cost_breakdown,
            "broker": self.broker_name,
            "is_paper": self.paper,
            "message": f"Paper order filled: {strategy_type} on {ticker}"
        }

    def close_position(self, position_id: str) -> bool:
        """Close an open position."""
        if position_id in self._positions:
            self._positions[position_id]["status"] = "CLOSED"
            self._positions[position_id]["exit_date"] = datetime.now().isoformat()
            return True
        return False

    def get_positions(self) -> List[dict]:
        """Get all open positions."""
        return [p for p in self._positions.values() if p["status"] == "OPEN"]


# ============================================================
# ALPACA REST (env: ALPACA_API_KEY, ALPACA_API_SECRET, optional ALPACA_PAPER)
# ============================================================


class AlpacaRESTBroker(AlpacaBroker):
    """Live Alpaca Trading API for account and option contracts (httpx)."""

    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        super().__init__(api_key=api_key, api_secret=api_secret, paper=paper)
        self._trade_base = (
            "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        )

    def _headers(self) -> dict:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

    def fetch_account_metrics(self) -> dict:
        try:
            import httpx

            with httpx.Client(timeout=25.0) as client:
                r = client.get(f"{self._trade_base}/v2/account", headers=self._headers())
                if r.status_code != 200:
                    return {
                        "broker": self.broker_name,
                        "error": "ALPACA_ACCOUNT_HTTP_ERROR",
                        "status_code": r.status_code,
                        "body": r.text[:500],
                        "source": "alpaca_rest",
                    }
                j = r.json()
            cash = float(j.get("cash", 0) or 0)
            pv = float(j.get("portfolio_value", cash) or cash)
            bp = float(j.get("buying_power", 0) or 0)
            return {
                "broker": self.broker_name,
                "account_id": j.get("account_number", self.api_key[:8] + "..."),
                "cash_balance": cash,
                "net_liquidation": pv,
                "buying_power": bp,
                "margin_utilization": 0.0,
                "is_paper": self.paper,
                "timestamp": datetime.now().isoformat(),
                "source": "alpaca_rest",
            }
        except Exception as e:
            return {"broker": self.broker_name, "error": str(e), "source": "alpaca_rest"}

    def get_option_chain(self, ticker: str, expiration: str = None) -> dict:
        try:
            import httpx

            params: Dict = {
                "underlying_symbols": ticker.upper(),
                "status": "active",
                "limit": 500,
            }
            if expiration:
                params["expiration_date"] = expiration
            with httpx.Client(timeout=30.0) as client:
                r = client.get(
                    f"{self._trade_base}/v2/options/contracts",
                    headers=self._headers(),
                    params=params,
                )
                if r.status_code != 200:
                    return {
                        "error": "ALPACA_CONTRACTS_HTTP_ERROR",
                        "status_code": r.status_code,
                        "body": r.text[:400],
                    }
                data = r.json()
            return {**data, "source": "alpaca_rest", "underlying": ticker.upper()}
        except Exception as e:
            return {"error": str(e), "source": "alpaca_rest"}

    def submit_complex_order(
        self,
        ticker: str,
        strategy_type: str,
        dte: int,
        sizing_pct: float,
        strikes: dict = None,
    ) -> dict:
        return {
            "status": "REJECTED",
            "broker": self.broker_name,
            "error": "ALPACA_MULTI_LEG_NOT_IMPLEMENTED",
            "message": (
                "Map strategy legs to OCC option symbols and POST /v2/orders; "
                "not automated in this codebase."
            ),
            "source": "alpaca_rest",
        }


# ============================================================
# BROKER FACTORY
# ============================================================

def get_broker(broker_name: str = "PAPER", **kwargs) -> AbstractBroker:
    """
    Factory function to get a broker instance.

    Usage:
        broker = get_broker("IBKR", account_id="U123456", paper=True)
        broker = get_broker("ALPACA", api_key="PK...", api_secret="...", paper=True)
        broker = get_broker("PAPER")  # Default paper broker
    """
    brokers = {
        "IBKR": IBKRBroker,
        "ALPACA": AlpacaBroker,
        "PAPER": IBKRBroker,  # Paper uses IBKR stub
    }

    broker_class = brokers.get(broker_name.upper())
    if not broker_class:
        raise ValueError(f"Unknown broker: {broker_name}. Available: {list(brokers.keys())}")

    name = broker_name.upper()
    if name == "PAPER":
        return IBKRBroker(account_id="PAPER", paper=True)

    if name == "ALPACA":
        key = os.getenv("ALPACA_API_KEY") or kwargs.get("api_key")
        secret = os.getenv("ALPACA_API_SECRET") or kwargs.get("api_secret")
        paper_raw = os.getenv("ALPACA_PAPER", "true")
        paper = str(paper_raw).lower() in ("1", "true", "yes")
        if kwargs.get("paper") is not None:
            paper = bool(kwargs.get("paper"))
        if key and secret and key != "PAPER" and secret != "PAPER":
            return AlpacaRESTBroker(
                api_key=str(key),
                api_secret=str(secret),
                paper=paper,
            )
        return broker_class(
            api_key=kwargs.get("api_key", "PAPER"),
            api_secret=kwargs.get("api_secret", "PAPER"),
            paper=kwargs.get("paper", True),
        )

    return broker_class(**kwargs)


# Global stubs
ibkr_broker = IBKRBroker(paper=True)
alpaca_broker = AlpacaBroker(paper=True)
paper_broker_legacy = ibkr_broker  # Alias for backwards compatibility