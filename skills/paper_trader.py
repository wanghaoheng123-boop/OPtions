import json
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

class PaperTrader:
    """
    Institutional-grade virtual sandbox for AI agents.
    Implements proper Kelly Criterion position sizing derived from actual historical
    win/loss ratios, full exit tracking, realized/unrealized PnL, and Triple Barrier compliance.

    Kelly Criterion: Kelly% = W - ((1 - W) / R)
    Where W = win rate, R = win/loss ratio (avg_win / avg_loss)
    Capped at 1%-20% per trade, max 5 concurrent positions.
    """

    DEFAULT_CONFIG = {
        "initial_balance": 100000.0,
        "max_positions": 5,
        "min_allocation_pct": 0.01,   # 1% minimum
        "max_allocation_pct": 0.20,    # 20% maximum (Kelly cap)
        "max_portfolio_concentration": 0.25,  # Max 25% in single position
        "daily_loss_limit": 0.05,      # Stop trading if 5% daily drawdown
        "slippage_bps": 5,             # 5 basis points slippage
    }

    @staticmethod
    def _resolved_db_path(explicit: Optional[str]) -> str:
        """Writable path: env override, serverless /tmp, or repo memory/."""
        if explicit:
            return explicit if os.path.isabs(explicit) else os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), explicit
            )
        env_path = os.environ.get("PAPER_PORTFOLIO_PATH")
        if env_path:
            return env_path
        if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
            return os.path.join(tempfile.gettempdir(), "paper_portfolio.json")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "memory", "paper_portfolio.json")

    def __init__(self, db_path: Optional[str] = None, config: dict = None):
        self.db_path = self._resolved_db_path(db_path)
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._ensure_db()

    def _ensure_db(self):
        if os.path.exists(self.db_path):
            return
        try:
            parent = os.path.dirname(self.db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            self._init_portfolio()
        except OSError:
            # Read-only bundle (e.g. serverless) — fall back to /tmp
            self.db_path = os.path.join(tempfile.gettempdir(), "paper_portfolio.json")
            if not os.path.exists(self.db_path):
                self._init_portfolio()

    def _init_portfolio(self):
        portfolio = {
            "cash_balance": self.config["initial_balance"],
            "starting_balance": self.config["initial_balance"],
            "positions": [],
            "closed_trades": [],
            "daily_pnl": [],
            "stats": {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_wins": 0.0,
                "total_losses": 0.0,
            }
        }
        with open(self.db_path, "w") as f:
            json.dump(portfolio, f, indent=2)

    def _load_portfolio(self) -> dict:
        """Load portfolio, migrating old format if needed."""
        with open(self.db_path, "r") as f:
            old_portfolio = json.load(f)

        old_portfolio.setdefault("positions", [])
        old_portfolio.setdefault("closed_trades", [])
        old_portfolio.setdefault("daily_pnl", [])
        old_portfolio.setdefault("cash_balance", self.config["initial_balance"])

        # Migrate old format (without new fields) to new format
        if "starting_balance" not in old_portfolio:
            old_portfolio["starting_balance"] = old_portfolio.get("cash_balance", self.config["initial_balance"])
            old_portfolio["closed_trades"] = old_portfolio.get("closed_trades", [])
            old_portfolio["daily_pnl"] = old_portfolio.get("daily_pnl", [])
            old_portfolio["stats"] = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_wins": 0.0,
                "total_losses": 0.0,
            }

        stats = old_portfolio.get("stats") or {}
        for key, default in (
            ("total_trades", 0),
            ("winning_trades", 0),
            ("losing_trades", 0),
            ("total_wins", 0.0),
            ("total_losses", 0.0),
        ):
            stats.setdefault(key, default)
        old_portfolio["stats"] = stats

        return old_portfolio

    def _save_portfolio(self, portfolio: dict):
        with open(self.db_path, "w") as f:
            json.dump(portfolio, f, indent=2)

    def calculate_kelly_sizing(self, backtest_stats: dict) -> dict:
        """
        Calculate optimal position size using Kelly Criterion with real W/L ratio.

        Kelly% = W - ((1 - W) / R)
        Where: W = win rate (as decimal), R = win/loss ratio

        Uses Half-Kelly for institutional risk management (reduces volatility by 50%).
        """
        win_rate = backtest_stats.get("win_rate_percent", 50.0) / 100.0
        total_pnl = backtest_stats.get("total_pnl_proxy", 0.0)
        num_trades = backtest_stats.get("num_trades", 1)

        if num_trades < 5:
            # Not enough trades for reliable Kelly sizing — use conservative default
            return {
                "kelly_pct": 0.05,  # Default 5% if insufficient data
                "half_kelly_pct": 0.025,
                "optimal_allocation_pct": 0.025,
                "win_rate": round(win_rate, 4),
                "avg_win_loss_ratio": 1.0,
                "profit_factor": backtest_stats.get("profit_factor", 1.0),
                "num_trades": num_trades,
                "is_reliable": False,
                "reason": f"Insufficient trades ({num_trades} < 5) for reliable Kelly estimation"
            }

        # Calculate actual average win and average loss from backtest stats
        # Since we don't have granular win/loss data, estimate from profit factor and win rate
        profit_factor = backtest_stats.get("profit_factor", 1.0)

        # If PF = total_wins / total_losses and WR = wins / total_trades
        # Then: avg_win / avg_loss = PF * (1 - WR) / WR
        if win_rate > 0 and win_rate < 1:
            avg_win_loss_ratio = profit_factor * (1 - win_rate) / win_rate
        else:
            avg_win_loss_ratio = 1.0

        # Prevent division by zero or negative R
        avg_win_loss_ratio = max(0.1, min(avg_win_loss_ratio, 10.0))

        # Full Kelly calculation
        kelly_pct = win_rate - ((1.0 - win_rate) / avg_win_loss_ratio)

        # Half-Kelly (institutional standard — reduces variance while maintaining edge)
        half_kelly = kelly_pct / 2.0

        # Cap at configured limits
        optimal_pct = max(self.config["min_allocation_pct"],
                          min(half_kelly, self.config["max_allocation_pct"]))

        return {
            "kelly_pct": round(kelly_pct, 4),
            "half_kelly_pct": round(half_kelly, 4),
            "optimal_allocation_pct": round(optimal_pct, 4),
            "win_rate": round(win_rate, 4),
            "avg_win_loss_ratio": round(avg_win_loss_ratio, 4),
            "profit_factor": profit_factor,
            "num_trades": num_trades,
            "is_reliable": num_trades >= 30,
            "reason": "Half-Kelly capped between 1%-20%"
        }

    def execute_trade(self, ticker: str, spot_price: float, strategy: str,
                      critic_approved: bool, backtest_stats: dict,
                      stop_loss_pct: float = None, take_profit_pct: float = None,
                      max_hold_days: int = 5) -> dict:
        """
        Execute a new trade with Kelly Criterion sizing and Triple Barrier parameters.
        """
        if not critic_approved:
            return {"status": "rejected", "reason": "Critic rejected this strategy"}

        portfolio = self._load_portfolio()

        # Check position limits
        open_positions = [p for p in portfolio["positions"] if p.get("status") == "OPEN"]
        if len(open_positions) >= self.config["max_positions"]:
            return {"status": "rejected", "reason": f"Max positions ({self.config['max_positions']}) reached"}

        # Check daily loss limit
        today = datetime.now().strftime("%Y-%m-%d")
        today_pnl = sum(p.get("daily_pnl", 0) for p in portfolio.get("daily_pnl", []) if p.get("date") == today)
        if today_pnl < -self.config["initial_balance"] * self.config["daily_loss_limit"]:
            return {"status": "rejected", "reason": "Daily loss limit breached — trading halted"}

        # Calculate Kelly sizing
        kelly = self.calculate_kelly_sizing(backtest_stats)
        allocation_pct = kelly.get("optimal_allocation_pct", self.config["min_allocation_pct"])

        # Calculate position size
        allocation = portfolio["cash_balance"] * allocation_pct
        shares_or_contracts = allocation / spot_price if spot_price > 0 else 0

        # Apply slippage to entry price
        slippage_factor = 1.0 + (self.config["slippage_bps"] / 10000)
        entry_price = spot_price * slippage_factor

        # Triple Barrier parameters
        if stop_loss_pct is None:
            stop_loss_pct = 0.02  # Default 2% stop for underlying
        if take_profit_pct is None:
            take_profit_pct = 0.01  # Default 1% profit target

        trade = {
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker.upper(),
            "strategy": strategy,
            "entry_price": round(entry_price, 2),
            "stop_loss_price": round(entry_price * (1 - stop_loss_pct), 2),
            "take_profit_price": round(entry_price * (1 + take_profit_pct), 2),
            "shares_or_contracts": round(shares_or_contracts, 4),
            "capital_allocated": round(allocation, 2),
            "kelly_pct": kelly["optimal_allocation_pct"],
            "kelly_is_reliable": kelly["is_reliable"],
            "status": "OPEN",
            "max_hold_days": max_hold_days,
            "barrier_hit": None,
            "pnl_realized": 0.0,
            "pnl_unrealized": 0.0,
            "entry_date": datetime.now().date().isoformat(),
        }

        portfolio["cash_balance"] -= allocation
        portfolio["positions"].append(trade)
        portfolio["stats"]["total_trades"] += 1

        self._save_portfolio(portfolio)

        return {
            "status": "executed",
            "trade": trade,
            "kelly_info": kelly,
            "portfolio": {
                "cash_balance": round(portfolio["cash_balance"], 2),
                "open_positions": len(open_positions) + 1
            }
        }

    def check_barriers(self, ticker: str, current_price: float) -> dict:
        """
        Check Triple Barrier exit conditions for all open positions of a ticker.
        Returns list of positions that should be closed.
        """
        portfolio = self._load_portfolio()
        to_close = []
        updated_positions = []

        for pos in portfolio["positions"]:
            if pos.get("ticker") != ticker.upper() or pos.get("status") != "OPEN":
                updated_positions.append(pos)
                continue

            # Check time barrier
            entry_date = datetime.fromisoformat(pos["timestamp"]).date()
            days_held = (datetime.now().date() - entry_date).days
            if days_held >= pos.get("max_hold_days", 5):
                pos["barrier_hit"] = "time"
                pos["pnl_realized"] = self._calculate_pnl(pos, current_price)
                pos["status"] = "CLOSED"
                pos["close_timestamp"] = datetime.now().isoformat()
                pos["close_price"] = current_price
                to_close.append(pos)
                continue

            # Check stop loss barrier
            sl_price = pos.get("stop_loss_price", 0)
            if sl_price > 0 and current_price <= sl_price:
                pos["barrier_hit"] = "stop_loss"
                pos["pnl_realized"] = self._calculate_pnl(pos, current_price)
                pos["status"] = "CLOSED"
                pos["close_timestamp"] = datetime.now().isoformat()
                pos["close_price"] = current_price
                to_close.append(pos)
                continue

            # Check take profit barrier
            tp_price = pos.get("take_profit_price", 0)
            if tp_price > 0 and current_price >= tp_price:
                pos["barrier_hit"] = "take_profit"
                pos["pnl_realized"] = self._calculate_pnl(pos, current_price)
                pos["status"] = "CLOSED"
                pos["close_timestamp"] = datetime.now().isoformat()
                pos["close_price"] = current_price
                to_close.append(pos)
                continue

            # Update unrealized PnL
            pos["pnl_unrealized"] = self._calculate_pnl(pos, current_price)
            updated_positions.append(pos)

        # Process closed positions
        for closed_pos in to_close:
            self._update_portfolio_stats(portfolio, closed_pos)
            portfolio["closed_trades"].append(closed_pos)

        portfolio["positions"] = updated_positions
        self._save_portfolio(portfolio)

        return {
            "ticker": ticker,
            "positions_checked": len([p for p in portfolio["positions"] if p.get("ticker") == ticker.upper()]),
            "positions_closed": len(to_close),
            "closed_positions": to_close
        }

    def _calculate_pnl(self, position: dict, current_price: float) -> float:
        """Calculate PnL for a position at current price."""
        entry_price = position["entry_price"]
        shares = position["shares_or_contracts"]
        direction = 1 if position["strategy"] in ["covered_call", "long_gamma"] else -1

        # Apply slippage to exit price
        exit_price = current_price * (1 - (self.config["slippage_bps"] / 10000) * direction)

        pnl = (exit_price - entry_price) * shares * direction
        return round(pnl, 2)

    def _update_portfolio_stats(self, portfolio: dict, closed_position: dict):
        """Update running statistics with a closed position."""
        pnl = closed_position.get("pnl_realized", 0)
        portfolio["stats"]["total_trades"] += 1
        if pnl > 0:
            portfolio["stats"]["winning_trades"] += 1
            portfolio["stats"]["total_wins"] += pnl
        elif pnl < 0:
            portfolio["stats"]["losing_trades"] += 1
            portfolio["stats"]["total_losses"] += abs(pnl)

        # Update cash balance
        portfolio["cash_balance"] += closed_position["capital_allocated"] + pnl

    def get_portfolio(self) -> dict:
        """Return full portfolio state with calculated metrics."""
        portfolio = self._load_portfolio()

        sb = float(portfolio.get("starting_balance") or portfolio.get("cash_balance") or self.config["initial_balance"])
        if sb <= 0:
            sb = float(self.config["initial_balance"])

        # Calculate current metrics
        total_equity = float(portfolio["cash_balance"]) + sum(
            float(p.get("capital_allocated", 0)) + float(p.get("pnl_unrealized", 0))
            for p in portfolio["positions"] if p.get("status") == "OPEN"
        )

        # Win rate from closed trades (fraction 0–1 for UI that multiplies by 100)
        closed = portfolio.get("closed_trades", [])
        if closed:
            wins = sum(1 for p in closed if p.get("pnl_realized", 0) > 0)
            win_rate_fraction = wins / len(closed)
            avg_win = portfolio["stats"]["total_wins"] / max(1, portfolio["stats"]["winning_trades"])
            avg_loss = portfolio["stats"]["total_losses"] / max(1, portfolio["stats"]["losing_trades"])
        else:
            win_rate_fraction = 0.0
            avg_win = 0.0
            avg_loss = 0.0

        total_return_fraction = (total_equity - sb) / sb

        open_rows = [p for p in portfolio["positions"] if p.get("status") == "OPEN"]
        kelly_vals = [
            float(p.get("kelly_percentage", p.get("kelly_pct", 0.1))) for p in open_rows
        ]
        # Stored Kelly may be allocation fraction (0–0.2) or legacy 0–1 scale; cap for display
        avg_kelly = sum(kelly_vals) / len(kelly_vals) if kelly_vals else 0.1
        avg_kelly = max(0.0, min(float(avg_kelly), 1.0))

        return {
            "cash_balance": round(float(portfolio["cash_balance"]), 2),
            "total_equity": round(total_equity, 2),
            "starting_balance": sb,
            "total_return_pct": round(total_return_fraction * 100, 2),
            "total_return": round(total_return_fraction, 6),
            "open_positions": len(open_rows),
            "closed_trades_count": len(closed),
            "win_rate": round(win_rate_fraction, 6),
            "average_kelly_sizing": round(avg_kelly, 6),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "stats": portfolio["stats"],
            "positions": portfolio["positions"],
            "recent_trades": closed[-10:] if closed else [],
        }

    def force_close_position(self, ticker: str, reason: str = "manual") -> dict:
        """Manually close all open positions for a ticker."""
        portfolio = self._load_portfolio()
        closed = []

        for pos in portfolio["positions"]:
            if pos.get("ticker") == ticker.upper() and pos.get("status") == "OPEN":
                pos["status"] = "CLOSED"
                pos["barrier_hit"] = reason
                pos["close_timestamp"] = datetime.now().isoformat()
                pos["pnl_realized"] = 0.0  # No mark-to-market on force close
                self._update_portfolio_stats(portfolio, pos)
                portfolio["closed_trades"].append(pos)
                closed.append(pos)

        portfolio["positions"] = [p for p in portfolio["positions"]
                                  if not (p.get("ticker") == ticker.upper() and p.get("status") == "CLOSED")]
        self._save_portfolio(portfolio)

        return {"closed": len(closed), "ticker": ticker, "reason": reason}


# Global singleton instance
paper_broker = PaperTrader()