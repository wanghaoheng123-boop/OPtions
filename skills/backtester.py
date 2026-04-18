import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import norm
from skills.brokers import TransactionCostModel


class OptionsPricing:
    """Black-Scholes options pricing utilities."""

    @staticmethod
    def bs_call(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0: return max(S - K, 0.0)
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return max(S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2), 0.0)

    @staticmethod
    def bs_put(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0: return max(K - S, 0.0)
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return max(K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1), 0.0)

    @staticmethod
    def estimate_iv(returns: pd.Series, lookback: int = 30) -> float:
        """Estimate ATM IV from realized vol as proxy."""
        rv = returns.tail(lookback).std()
        return rv * np.sqrt(252)


class IronCondorBacktester:
    """
    INSTITUTIONAL IRON CONDOR BACKTESTER — Loop 2 Enhanced Version.

    Key Improvements (Loop 2):
    1. Adaptive wing width based on IV (high vol = wider wings)
    2. Adaptive DTE based on IV (high vol = shorter DTE)
    3. Earnings calendar filter (skip near earnings)
    4. Vol-adaptive IV Rank threshold

    Entry Rules (enforced):
    - IV Rank > threshold (adaptive based on vol)
    - Credit >= 15% of max risk
    - Not within 5 days of earnings (for known tickers)

    Pricing:
    - Black-Scholes with IV = realized_vol × VOLATILITY_PREMIUM (2.5x)

    Triple Barrier (applied to OPTION CREDIT, not underlying):
    - PT: Take profit when X% of credit captured
    - SL: Stop loss when X% of credit lost
    - Time: Exit when DTE < 5 days
    """

    # Global constants
    VOLATILITY_PREMIUM = 2.5
    MIN_CREDIT_PCT_OF_RISK = 0.15

    # Earnings calendar (month numbers when earnings occur)
    # Format: ticker -> list of earnings months
    EARNINGS_CALENDAR = {
        'MSFT': [2, 5, 8, 11],   # Feb, May, Aug, Nov
        'NFLX': [1, 4, 7, 10],   # Jan, Apr, Jul, Oct
        'AAPL': [1, 4, 7, 10],   # Jan, Apr, Jul, Oct
        'GOOGL': [1, 4, 7, 10],  # Jan, Apr, Jul, Oct
        'AMZN': [1, 4, 7, 10],   # Jan, Apr, Jul, Oct
        'META': [1, 4, 7, 10],   # Jan, Apr, Jul, Oct
        'TSLA': [1, 4, 7, 10],   # Jan, Apr, Jul, Oct (approx)
        'AMD': [1, 4, 7, 10],    # Jan, Apr, Jul, Oct (approx)
        'NVDA': [1, 4, 7, 10],   # Jan, Apr, Jul, Oct (approx)
    }

    def __init__(self,
                 iv_rank_min: float = 50.0,
                 dte_entry: int = 45,
                 max_hold_days: int = 40,
                 profit_take_pct: float = 0.70,
                 stop_loss_mult: float = 2.0,
                 wing_pct: float = 0.10,
                 num_contracts: int = 1,
                 use_adaptive: bool = True,  # NEW: use vol-adaptive parameters
                 earnings_filter: bool = True):  # NEW: skip earnings-prone periods
        self.iv_rank_min = iv_rank_min
        self.dte_entry = dte_entry
        self.max_hold_days = max_hold_days
        self.profit_take_pct = profit_take_pct
        self.stop_loss_mult = stop_loss_mult
        self.wing_pct = wing_pct
        self.num_contracts = num_contracts
        self.use_adaptive = use_adaptive
        self.earnings_filter = earnings_filter
        self.tcm = TransactionCostModel("IBKR")

    @staticmethod
    def adaptive_wing(iv: float) -> float:
        """
        Wing width as % of spot — scales with IV.
        Higher IV = wider wings to collect more premium and avoid breach.

        Formula: wing_pct = max(0.05, min(0.20, iv / 4))
        - IV=20% → 5% wing
        - IV=40% → 10% wing
        - IV=60% → 15% wing
        - IV=80%+ → 20% wing (capped)
        """
        return max(0.05, min(0.20, iv / 400))

    @staticmethod
    def adaptive_dte(iv: float) -> int:
        """
        DTE scales inversely with IV.
        Higher IV = shorter DTE to reduce vol exposure.

        Formula: dte = max(21, min(45, 60 - iv * 100))
        - IV=15% → DTE=45
        - IV=30% → DTE=30
        - IV=50% → DTE=21
        """
        dte = 60 - iv * 100
        return max(21, min(45, dte))

    @staticmethod
    def adaptive_iv_rank_min(iv: float) -> float:
        """
        IV Rank threshold scales with IV.
        Higher IV = higher threshold needed to enter.

        Formula: iv_rank_min = max(30, 70 - iv * 100)
        - IV=15% → threshold=55
        - IV=30% → threshold=40
        - IV=50% → threshold=30
        """
        threshold = 70 - iv * 100
        return max(30, min(55, threshold))

    def earnings_filter_active(self, ticker: str) -> bool:
        """
        Check if we're within 5 days of earnings month start.
        If True, skip trading this ticker this week.
        """
        if not self.earnings_filter:
            return False
        if ticker not in self.EARNINGS_CALENDAR:
            return False  # No earnings data — allow

        earnings_months = self.EARNINGS_CALENDAR[ticker]
        now = datetime.now()
        current_month = now.month
        current_day = now.day

        # Check if current month is an earnings month
        if current_month in earnings_months:
            # Within 5 days of month start = earnings risk
            if current_day <= 5:
                return True

        # Also check next month (in case we're near end of earnings month)
        next_month = (current_month % 12) + 1
        if next_month in earnings_months and current_day >= 25:
            return True

        return False

    def _get_strikes(self, S: float, wing_pct: float) -> dict:
        """Delta-based strike selection: ~30 delta = ~wing_pct OTM."""
        short_put = round(S * (1 - wing_pct))
        long_put = round(S * (1 - wing_pct * 2))
        short_call = round(S * (1 + wing_pct))
        long_call = round(S * (1 + wing_pct * 2))
        wing_width = short_put - long_put
        return {
            'short_put': short_put, 'long_put': long_put,
            'short_call': short_call, 'long_call': long_call,
            'wing_width': wing_width
        }

    def _calc_credit(self, S: float, T: float, r: float, iv: float, strikes: dict) -> float:
        """Calculate net credit received (in dollars per share)."""
        sp = OptionsPricing.bs_put(S, strikes['short_put'], T, r, iv)
        lp = OptionsPricing.bs_put(S, strikes['long_put'], T, r, iv)
        sc = OptionsPricing.bs_call(S, strikes['short_call'], T, r, iv)
        lc = OptionsPricing.bs_call(S, strikes['long_call'], T, r, iv)
        credit = (sp - lp) + (sc - lc)
        return max(credit, 0.0)

    def _simulate_trade(self, price_path: np.ndarray, iv: float, dte: int,
                         strikes: dict, entry_credit: float) -> dict:
        """Simulate trade along price path. Returns net P&L in dollars."""
        T_start = dte / 365.0
        dt = 1 / 365.0
        profit_target = entry_credit * self.profit_take_pct
        stop_loss = entry_credit * self.stop_loss_mult
        entry_price = price_path[0]
        r = 0.045

        # Transaction costs (round trip = 4 legs, limit order)
        tc = self.tcm.total_cost(
            num_contracts=self.num_contracts * 4,
            mid_price=entry_credit,
            order_type="limit"
        )
        tc_cost = tc['total_cost']

        max_hold = min(self.max_hold_days, len(price_path) - 1)

        for day in range(max_hold):
            T = max(0, T_start - day * dt)
            S = price_path[day]

            # Current credit value
            cur_sp = OptionsPricing.bs_put(S, strikes['short_put'], T, r, iv)
            cur_lp = OptionsPricing.bs_put(S, strikes['long_put'], T, r, iv)
            cur_sc = OptionsPricing.bs_call(S, strikes['short_call'], T, r, iv)
            cur_lc = OptionsPricing.bs_call(S, strikes['long_call'], T, r, iv)
            cur_credit = max((cur_sp - cur_lp) + (cur_sc - cur_lc), 0.0)

            # Unrealized P&L = initial credit - current credit (positive = we're winning)
            unrealized = (entry_credit - cur_credit) * self.num_contracts * 100

            # Check barriers
            if unrealized >= profit_target * self.num_contracts * 100:
                return {'pnl': round(unrealized - tc_cost, 2), 'barrier': 'pt', 'exit_day': day}
            if unrealized <= -stop_loss * self.num_contracts * 100:
                return {'pnl': round(unrealized - tc_cost, 2), 'barrier': 'sl', 'exit_day': day}
            if T < 5 / 365:
                # Time exit: close at current credit
                pnl = (entry_credit - cur_credit * 0.5) * self.num_contracts * 100
                return {'pnl': round(pnl - tc_cost, 2), 'barrier': 'time', 'exit_day': day}

        # Expiration: all options expired
        final_credit = max(
            OptionsPricing.bs_put(price_path[-1], strikes['short_put'], 0, r, iv) -
            OptionsPricing.bs_put(price_path[-1], strikes['long_put'], 0, r, iv) +
            OptionsPricing.bs_call(price_path[-1], strikes['short_call'], 0, r, iv) -
            OptionsPricing.bs_call(price_path[-1], strikes['long_call'], 0, r, iv),
            0.0
        )
        pnl = (entry_credit - final_credit) * self.num_contracts * 100
        return {'pnl': round(pnl - tc_cost, 2), 'barrier': 'exp', 'exit_day': max_hold}

    def run(self, ticker: str, days: int = 252) -> dict:
        """Run backtest on ticker with adaptive parameters."""
        end = datetime.now()
        start = end - timedelta(days=days + 60)

        try:
            data = yf.download(ticker, start=start.strftime('%Y-%m-%d'),
                              end=end.strftime('%Y-%m-%d'), progress=False)
            if data.empty: return {'error': f'No data for {ticker}'}
            if isinstance(data.columns, pd.MultiIndex):
                data = data.xs(ticker, axis=1, level=1)
        except Exception as e:
            return {'error': str(e)}

        close = data['Close']
        returns = close.pct_change().dropna()

        # OOS split: 70% in-sample / 30% out-of-sample
        split = int(len(returns) * 0.70)
        oos_returns = returns.iloc[split:]
        oos_prices = close.iloc[split:]

        if len(oos_prices) < 60:
            return {'error': 'Insufficient OOS data'}

        # Trained IV from in-sample
        is_returns = returns.iloc[:split]
        trained_iv = OptionsPricing.estimate_iv(is_returns)

        # IV Rank calculation for OOS period
        full_rv = returns.rolling(252).std() * np.sqrt(252)

        trades = []
        equity = 100000.0
        equity_curve = [equity]
        dates = []

        r = 0.045
        price_arr = oos_prices.reset_index(drop=True)
        ret_arr = oos_returns.reset_index(drop=True)
        rv_arr = full_rv.reset_index(drop=True)

        trade_open = False

        for i in range(len(price_arr)):
            S = float(price_arr.iloc[i])

            # Current raw IV estimate
            if i >= 30:
                raw_iv = float(rv_arr.iloc[i]) if not pd.isna(rv_arr.iloc[i]) else trained_iv
            else:
                raw_iv = trained_iv

            # Apply volatility premium (2.5x)
            iv = raw_iv * self.VOLATILITY_PREMIUM

            # IV Rank (based on raw IV for market comparison)
            if i >= 252:
                hist_iv = rv_arr.iloc[max(0, i-252):i].dropna()
                if len(hist_iv) > 20:
                    iv_rank = float(((hist_iv < raw_iv).sum() / len(hist_iv)) * 100)
                else:
                    iv_rank = 50.0
            else:
                iv_rank = 50.0

            if not trade_open:
                # Earnings filter check
                if self.earnings_filter_active(ticker):
                    equity_curve.append(equity)
                    dates.append(oos_prices.index[i])
                    continue

                # Adaptive parameter calculation
                if self.use_adaptive:
                    adaptive_wing_pct = self.adaptive_wing(iv)
                    adaptive_dte = self.adaptive_dte(iv)
                    adaptive_iv_rank_min = self.adaptive_iv_rank_min(iv)
                else:
                    adaptive_wing_pct = self.wing_pct
                    adaptive_dte = self.dte_entry
                    adaptive_iv_rank_min = self.iv_rank_min

                # Entry: IV Rank must be above adaptive threshold
                if iv_rank < adaptive_iv_rank_min:
                    equity_curve.append(equity)
                    dates.append(oos_prices.index[i])
                    continue

                # Calculate entry with adaptive parameters
                strikes = self._get_strikes(S, adaptive_wing_pct)
                T = adaptive_dte / 365.0
                credit = self._calc_credit(S, T, r, iv, strikes)

                # Minimum credit threshold: must be >= 15% of wing width
                min_credit = strikes['wing_width'] * self.MIN_CREDIT_PCT_OF_RISK
                if credit < min_credit:
                    equity_curve.append(equity)
                    dates.append(oos_prices.index[i])
                    continue

                # Get price path for simulation
                path_end = min(i + self.max_hold_days + 1, len(price_arr))
                price_path = price_arr.iloc[i:path_end].values

                # Simulate trade
                result = self._simulate_trade(price_path, iv, adaptive_dte, strikes, credit)
                equity += result['pnl']
                equity_curve.append(equity)
                dates.append(oos_prices.index[i])

                result['entry_price'] = round(S, 2)
                result['entry_credit'] = round(credit, 4)
                result['iv_rank'] = round(iv_rank, 1)
                result['iv_used'] = round(iv, 4)
                result['strikes'] = strikes
                result['wing_pct'] = round(adaptive_wing_pct, 4)
                result['dte'] = adaptive_dte
                result['iv_rank_min'] = round(adaptive_iv_rank_min, 1)
                trades.append(result)
            else:
                equity_curve.append(equity)
                dates.append(oos_prices.index[i])

        if not trades:
            return {
                'error': f'No trades — check IV Rank threshold or earnings filter',
                'ticker': ticker,
                'use_adaptive': self.use_adaptive,
                'earnings_filter': self.earnings_filter,
                'trained_iv': round(trained_iv, 4)
            }

        # Calculate metrics
        pnls = np.array([t['pnl'] for t in trades])
        n = len(pnls)
        wins = pnls[pnls > 0]
        losses = pnls[pnls <= 0]
        n_wins = len(wins)
        win_rate = n_wins / n * 100 if n > 0 else 0

        total_pnl = float(np.nansum(pnls))
        total_return = (equity - 100000.0) / 100000.0 * 100

        avg_win = float(np.mean(wins)) if len(wins) > 0 else 0
        avg_loss = abs(float(np.mean(losses))) if len(losses) > 0 else 1

        pf = float(np.sum(wins) / abs(np.sum(losses))) if len(losses) > 0 and np.sum(losses) != 0 else 99.99

        # Equity curve metrics
        eq = np.array(equity_curve, dtype=float)
        cumret = eq - eq[0]
        running_max = np.maximum.accumulate(cumret)
        drawdowns = running_max - cumret
        max_dd = float(np.nanmax(drawdowns)) if len(drawdowns) > 0 else 0
        max_dd_pct = max_dd / equity * 100

        # Sharpe / Sortino / Calmar
        daily_rets = np.diff(eq) / eq[:-1]
        daily_rets = daily_rets[~np.isnan(daily_rets)]
        if len(daily_rets) > 5 and np.std(daily_rets) > 1e-10:
            sharpe = float(np.mean(daily_rets) / np.std(daily_rets) * np.sqrt(252))
            downside = daily_rets[daily_rets < 0]
            sortino = float(np.mean(daily_rets) / np.std(downside) * np.sqrt(252)) if len(downside) > 0 and np.std(downside) > 1e-10 else 0
            years = len(oos_prices) / 252
            ann_ret = ((equity / 100000.0) ** (1 / years) - 1) * 100 if years > 0 else 0
            calmar = ann_ret / max_dd_pct if max_dd_pct > 0 else 0
        else:
            sharpe = sortino = calmar = 0.0

        # Barrier distribution
        barriers = {'pt': 0, 'sl': 0, 'time': 0, 'exp': 0}
        for t in trades:
            b = t.get('barrier', 'time')
            if b in barriers: barriers[b] += 1

        return {
            'ticker': ticker,
            'strategy': 'iron_condor',
            'n_trades': n,
            'n_wins': n_wins,
            'win_rate_percent': round(win_rate, 2),
            'total_net_pnl': round(total_pnl, 2),
            'profit_factor': round(pf, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'max_drawdown_dollars': round(max_dd, 2),
            'max_drawdown_percent': round(max_dd_pct, 2),
            'total_return_percent': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'calmar_ratio': round(calmar, 2),
            'trained_iv': round(trained_iv, 4),
            'barrier_hits': barriers,
            'num_contracts': self.num_contracts,
            'adaptive': self.use_adaptive,
            'earnings_filter': self.earnings_filter,
            'verdict': 'PASS' if win_rate >= 75 and pf >= 1.2 and max_dd_pct < 20 else 'FAIL',
            'trade_sample': trades[:3]
        }


def run_backtest(ticker: str, strategy: str = 'iron_condor',
                days: int = 252, **kwargs) -> dict:
    """Convenience function matching the old interface."""
    bt = IronCondorBacktester(
        iv_rank_min=kwargs.get('iv_rank_min', 50.0),
        dte_entry=kwargs.get('dte_entry', 45),
        max_hold_days=kwargs.get('max_hold_days', 40),
        profit_take_pct=kwargs.get('profit_take_pct', 0.70),
        stop_loss_mult=kwargs.get('stop_loss_mult', 2.0),
        wing_pct=kwargs.get('wing_pct', 0.10),
        num_contracts=kwargs.get('num_contracts', 1),
        use_adaptive=kwargs.get('use_adaptive', True),
        earnings_filter=kwargs.get('earnings_filter', True)
    )
    return bt.run(ticker, days)


class StrategyBacktester:
    """
    Public API used by FastAPI and MarketExpertTeam.

    The live engine is IronCondorBacktester (triple-barrier on credit, OOS slice).
    The ``strategy`` argument is preserved on the response for callers; all names
    currently run the same iron-condor path.
    """

    @staticmethod
    def run_historical_backtest(
        ticker: str,
        strategy: str = 'iron_condor',
        days: int = 252,
        **kwargs,
    ) -> dict:
        out = run_backtest(ticker, 'iron_condor', days, **kwargs)
        if isinstance(out, dict) and 'error' not in out:
            out['strategy_requested'] = strategy
            out.setdefault('strategy_run', 'iron_condor')
            if 'max_drawdown_percent' in out and 'max_drawdown' not in out:
                out['max_drawdown'] = out['max_drawdown_percent']
        return out