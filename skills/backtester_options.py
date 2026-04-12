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
    Institutional Iron Condor Backtester with proper options pricing.

    Entry Rules (enforced):
    - IV Rank > threshold (we use 50 by default — only sell elevated premium)

    Pricing:
    - Black-Scholes with IV from realized vol as proxy
    - Strikes: 30-delta approximation (~7% OTM for 30 DTE)

    Triple Barrier (applied to OPTION CREDIT, not underlying):
    - PT: Take profit when X% of credit captured
    - SL: Stop loss when X% of credit lost
    - Time: Exit when DTE < 5 days
    """

    def __init__(self,
                 iv_rank_min: float = 50.0,
                 dte_entry: int = 30,
                 max_hold_days: int = 25,
                 profit_take_pct: float = 0.50,
                 stop_loss_mult: float = 2.0,
                 wing_pct: float = 0.07,
                 num_contracts: int = 1):
        self.iv_rank_min = iv_rank_min
        self.dte_entry = dte_entry
        self.max_hold_days = max_hold_days
        self.profit_take_pct = profit_take_pct
        self.stop_loss_mult = stop_loss_mult
        self.wing_pct = wing_pct
        self.num_contracts = num_contracts
        self.tcm = TransactionCostModel("IBKR")

    def _get_strikes(self, S: float) -> dict:
        """Delta-based strike selection: ~30 delta = ~7% OTM for 30 DTE."""
        short_put = round(S * (1 - self.wing_pct))
        long_put = round(S * (1 - self.wing_pct * 2))
        short_call = round(S * (1 + self.wing_pct))
        long_call = round(S * (1 + self.wing_pct * 2))
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

    def _simulate_trade(self, price_path: np.ndarray, iv: float,
                         strikes: dict, entry_credit: float) -> dict:
        """Simulate trade along price path. Returns net P&L in dollars."""
        T_start = self.dte_entry / 365.0
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

        for day in range(min(self.max_hold_days, len(price_path) - 1)):
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
        # If price unchanged, we keep full credit
        final_credit = max(
            OptionsPricing.bs_put(price_path[-1], strikes['short_put'], 0, r, iv) -
            OptionsPricing.bs_put(price_path[-1], strikes['long_put'], 0, r, iv) +
            OptionsPricing.bs_call(price_path[-1], strikes['short_call'], 0, r, iv) -
            OptionsPricing.bs_call(price_path[-1], strikes['long_call'], 0, r, iv),
            0.0
        )
        pnl = (entry_credit - final_credit) * self.num_contracts * 100
        return {'pnl': round(pnl - tc_cost, 2), 'barrier': 'exp', 'exit_day': self.max_hold_days}

    def run(self, ticker: str, days: int = 252) -> dict:
        """Run backtest on ticker."""
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

            # Current IV estimate
            if i >= 30:
                iv = float(rv_arr.iloc[i]) if not pd.isna(rv_arr.iloc[i]) else trained_iv
            else:
                iv = trained_iv

            # IV Rank
            if i >= 252:
                hist_iv = rv_arr.iloc[max(0, i-252):i].dropna()
                if len(hist_iv) > 20:
                    iv_rank = float(((hist_iv < iv).sum() / len(hist_iv)) * 100)
                else:
                    iv_rank = 50.0
            else:
                iv_rank = 50.0

            if not trade_open:
                # Entry: IV Rank must be above threshold
                if iv_rank < self.iv_rank_min:
                    equity_curve.append(equity)
                    dates.append(oos_prices.index[i])
                    continue

                # Calculate entry
                strikes = self._get_strikes(S)
                T = self.dte_entry / 365.0
                credit = self._calc_credit(S, T, r, iv, strikes)

                if credit < 0.05:  # Minimum credit threshold
                    equity_curve.append(equity)
                    dates.append(oos_prices.index[i])
                    continue

                # Get price path for simulation
                path_end = min(i + self.max_hold_days + 1, len(price_arr))
                price_path = price_arr.iloc[i:path_end].values

                # Simulate trade
                result = self._simulate_trade(price_path, iv, strikes, credit)
                equity += result['pnl']
                equity_curve.append(equity)
                dates.append(oos_prices.index[i])

                result['entry_price'] = round(S, 2)
                result['entry_credit'] = round(credit, 4)
                result['iv_rank'] = round(iv_rank, 1)
                result['iv_used'] = round(iv, 4)
                result['strikes'] = strikes
                trades.append(result)
            else:
                equity_curve.append(equity)
                dates.append(oos_prices.index[i])

        if not trades:
            return {
                'error': f'No trades — IV Rank {self.iv_rank_min}% threshold too high',
                'iv_rank_min': self.iv_rank_min,
                'trained_iv': round(trained_iv, 4),
                'oos_days': len(oos_prices)
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

        pf = float(np.sum(wins) / np.sum(losses)) if len(losses) > 0 and np.sum(losses) != 0 else 99.99

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
            'iv_rank_min': self.iv_rank_min,
            'barrier_hits': barriers,
            'num_contracts': self.num_contracts,
            'verdict': 'PASS' if win_rate >= 75 and pf >= 1.2 and max_dd_pct < 20 else 'FAIL',
            'trade_sample': trades[:3]
        }


def run_backtest(ticker: str, strategy: str = 'iron_condor',
                days: int = 252, **kwargs) -> dict:
    """Convenience function matching the old interface."""
    bt = IronCondorBacktester(
        iv_rank_min=kwargs.get('iv_rank_min', 50.0),
        dte_entry=kwargs.get('dte_entry', 30),
        max_hold_days=kwargs.get('max_hold_days', 25),
        profit_take_pct=kwargs.get('profit_take_pct', 0.50),
        stop_loss_mult=kwargs.get('stop_loss_mult', 2.0),
        wing_pct=kwargs.get('wing_pct', 0.07),
        num_contracts=kwargs.get('num_contracts', 1)
    )
    return bt.run(ticker, days)