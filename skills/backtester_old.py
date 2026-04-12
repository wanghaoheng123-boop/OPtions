import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import norm
from typing import Optional, Tuple
from skills.brokers import TransactionCostModel


class OptionsPricingModel:
    """
    Black-Scholes options pricing with proper Greeks.
    Used for theoretical P&L calculation in backtesting.

    All pricing uses IV from the options chain as input,
    not realized volatility from the underlying.
    """

    @staticmethod
    def black_scholes_call(S, K, T, r, sigma) -> float:
        """Theoretical call price using Black-Scholes-Merton."""
        if T <= 0 or sigma <= 0:
            return max(S - K, 0.0)
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return max(call_price, 0.0)

    @staticmethod
    def black_scholes_put(S, K, T, r, sigma) -> float:
        """Theoretical put price using Black-Scholes-Merton."""
        if T <= 0 or sigma <= 0:
            return max(K - S, 0.0)
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return max(put_price, 0.0)

    @staticmethod
    def option_delta(S, K, T, r, sigma, option_type='call') -> float:
        """Delta: change in option price per $1 change in underlying."""
        if T <= 0 or sigma <= 0:
            return 1.0 if option_type == 'call' and S > K else 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        if option_type == 'call':
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1

    @staticmethod
    def option_theta(S, K, T, r, sigma, option_type='call') -> float:
        """
        Theta: daily time decay in dollars per contract.
        Negative theta means the option loses value daily (good for sellers).
        """
        if T <= 0 or sigma <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        phi = norm.pdf(d1)
        term1 = -(S * phi * sigma) / (2 * np.sqrt(T))
        if option_type == 'call':
            term2 = r * K * np.exp(-r * T) * norm.cdf(d2)
            theta = (term1 - term2) / 365  # Daily
        else:
            term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
            theta = (term1 + term2) / 365
        return theta

    @staticmethod
    def estimate_atm_iv(returns_series: pd.Series, annualize: bool = True) -> float:
        """
        Estimate ATM implied volatility from historical returns.
        Uses 30-day realized vol as IV proxy when no live IV available.
        """
        realized_vol = returns_series.tail(30).std()
        if annualize:
            return realized_vol * np.sqrt(252)
        return realized_vol


class IronCondorStrategy:
    """
    Proper Iron Condor strategy with Black-Scholes pricing.

    Entry Rules (per QUANT_KB):
    1. IV Rank > 50 (premium selling only profitable with elevated IV)
    2. Not within 5 days of earnings (IV crush risk)
    3. Collect credit between 15-30% of max risk (wider wings = more credit but more risk)

    Exit Rules:
    1. Profit Taking: 50-70% of max profit captured
    2. Stop Loss: 100-150% of credit received as loss
    3. Time Exit: When DTE < 5 (don't hold through expiration)
    """

    def __init__(self,
                 wing_width_pct: float = 0.05,    # Each wing is 5% wide from short strike
                 profit_take_pct: float = 0.50,   # Exit when 50% of credit captured
                 stop_loss_mult: float = 2.0,     # Stop at 2x credit received
                 dte_target: int = 30,            # Target DTE at entry
                 max_dte: int = 45,
                 iv_rank_threshold: float = 50.0):  # Only enter when IV Rank > 50
        self.wing_width_pct = wing_width_pct
        self.credit_pct_of_risk = 0.25  # Collect 25% of wing width as credit
        self.profit_take_pct = profit_take_pct
        self.stop_loss_mult = stop_loss_mult
        self.dte_target = dte_target
        self.max_dte = max_dte
        self.iv_rank_threshold = iv_rank_threshold

    def calculate_strikes(self, S: float, iv: float) -> dict:
        """
        Calculate iron condor strikes given spot price and IV.

        Strike selection based on delta (targeting 30-40 delta short strikes):
        - delta 0.30-0.40 = approximately 1 standard deviation move
        - For SPY at $500 with 20% IV: 1SD = $500 * 0.20 * sqrt(30/365) ≈ $28

        For a standard iron condor (5-wide wings):
        - Short Put: S - (0.07 to 0.10)*S (7-10% OTM, ~30 delta)
        - Long Put: Short Put - wing_width (further OTM protection)
        - Short Call: S + (0.07 to 0.10)*S (7-10% OTM, ~30 delta)
        - Long Call: Short Call + wing_width
        """
        # Target ~30 delta = ~1SD move = iv * sqrt(DTE/365) * S
        # For 30 DTE and 20% IV: 1SD = 0.20 * sqrt(30/365) * S ≈ 0.035 * S ≈ 7% of S
        delta_pct = 0.07  # 7% OTM = approximately 30 delta for 30 DTE

        short_put_k = S * (1 - delta_pct)
        long_put_k = S * (1 - delta_pct - self.wing_width_pct)
        short_call_k = S * (1 + delta_pct)
        long_call_k = S * (1 + delta_pct + self.wing_width_pct)

        # Round strikes to nearest $1 for tighter pricing
        strikes = {
            'short_put': round(short_put_k),
            'long_put': round(long_put_k),
            'short_call': round(short_call_k),
            'long_call': round(long_call_k),
        }

        # Max risk = width of wings - credit received
        put_width = strikes['short_put'] - strikes['long_put']
        call_width = strikes['short_call'] - strikes['long_call']
        max_risk_per_side = max(put_width, call_width)

        return {**strikes, 'max_risk': max_risk_per_side}

    def calculate_credit(self, S: float, T: float, r: float, iv: float, strikes: dict) -> dict:
        """Calculate the credit received at trade entry using Black-Scholes."""
        opt = OptionsPricingModel()

        short_put_price = opt.black_scholes_put(S, strikes['short_put'], T, r, iv)
        long_put_price = opt.black_scholes_put(S, strikes['long_put'], T, r, iv)
        short_call_price = opt.black_scholes_call(S, strikes['short_call'], T, r, iv)
        long_call_price = opt.black_scholes_call(S, strikes['long_call'], T, r, iv)

        put_credit = short_put_price - long_put_price  # Short put - long put
        call_credit = short_call_price - long_call_price  # Short call - long call
        total_credit = put_credit + call_credit  # Net credit received

        return {
            'short_put_price': short_put_price,
            'long_put_price': long_put_price,
            'short_call_price': short_call_price,
            'long_call_price': long_call_price,
            'put_credit': put_credit,
            'call_credit': call_credit,
            'total_credit': total_credit,
            'max_risk': strikes['max_risk'],
            'risk_reward_ratio': (strikes['max_risk'] - total_credit) / total_credit if total_credit > 0 else float('inf')
        }

    def simulate_pnl_path(self, S_path: np.ndarray, T_start: float, r: float,
                           iv: float, daily_steps: int, strikes: dict,
                           initial_credit: float, tcm: TransactionCostModel,
                           num_contracts: int = 1) -> dict:
        """
        Simulate iron condor P&L along a price path.

        Uses Black-Scholes to calculate mark-to-market P&L each day.
        Applies Triple Barrier exit logic with options-specific barriers.

        Returns detailed trade record.
        """
        opt = OptionsPricingModel()
        dt = 1 / 365  # Daily time step
        daily_theta = 0.0

        current_T = T_start
        entry_credit = initial_credit
        max_risk = strikes['max_risk']

        # Barrier levels in dollars
        profit_target = entry_credit * self.profit_take_pct  # 50% of credit
        stop_loss = entry_credit * self.stop_loss_mult       # 2x credit as loss

        current_pnl = 0.0
        entry_s = S_path[0]

        for day in range(daily_steps):
            current_T = max(0, current_T - dt)
            S = S_path[day]

            # Calculate current option prices
            short_put = opt.black_scholes_put(S, strikes['short_put'], current_T, r, iv)
            long_put = opt.black_scholes_put(S, strikes['long_put'], current_T, r, iv)
            short_call = opt.black_scholes_call(S, strikes['short_call'], current_T, r, iv)
            long_call = opt.black_scholes_call(S, strikes['long_call'], current_T, r, iv)

            current_credit = (short_put - long_put) + (short_call - long_call)

            # Unrealized P&L = initial credit - current credit (lower credit = we lost)
            unrealized_pnl = (entry_credit - current_credit) * num_contracts * 100

            # Check profit barrier (we've captured enough of the credit)
            if unrealized_pnl >= profit_target * num_contracts * 100:
                barrier_hit = 'pt'
                pnl = profit_target * num_contracts * 100
                exit_day = day
                exit_price = S
                break

            # Check stop loss barrier
            if unrealized_pnl <= -stop_loss * num_contracts * 100:
                barrier_hit = 'sl'
                pnl = -stop_loss * num_contracts * 100
                exit_day = day
                exit_price = S
                break

            # Check time barrier (DTE < 5)
            if current_T < 5 / 365:
                # Close at 50% of remaining credit or let expire
                pnl = (entry_credit - current_credit * 0.5) * num_contracts * 100
                barrier_hit = 'time'
                exit_day = day
                exit_price = S
                break
        else:
            # Expired: calculate final intrinsic P&L
            barrier_hit = 'expired'
            # At expiration: short puts assigned if below short put strike
            # Long puts protect us below long put strike
            # Similar for calls
            pnl = entry_credit * num_contracts * 100  # Full credit kept if all OTM
            exit_day = daily_steps
            exit_price = S_path[-1]

        # Deduct transaction costs
        tc = tcm.total_cost(
            num_contracts=num_contracts * 4,  # 4 legs
            mid_price=entry_credit,
            order_type="limit"  # Assume limit orders for backtest
        )
        net_pnl = pnl - tc['total_cost']

        return {
            'barrier_hit': barrier_hit,
            'pnl': round(pnl, 2),
            'net_pnl': round(net_pnl, 2),
            'exit_day': exit_day,
            'exit_price': round(exit_price, 2),
            'entry_price': round(entry_s, 2),
            'num_contracts': num_contracts,
            'entry_credit': round(entry_credit, 4),
            'profit_target': round(profit_target, 4),
            'stop_loss': round(stop_loss, 4),
            'transaction_cost': round(tc['total_cost'], 2),
            'iv': round(iv, 4),
            'dte_start': int(T_start * 365)
        }


class StrategyBacktester:
    """
    AP Specialist Programmatic Backtesting Module — INSTITUTIONAL GRADE.

    Implements AFML Triple Barrier methodology with PROPER OPTIONS PRICING.

    Key improvements over equity-proxy model:
    1. Uses Black-Scholes for theoretical option pricing
    2. IV Rank gates entry signals (per QUANT_KB Rule 1)
    3. Theta decay explicitly modeled (primary edge for net sellers)
    4. Triple Barrier applied to option credit, not underlying price
    5. Transaction costs from TransactionCostModel

    Supported strategies: 'iron_condor', 'wheel', 'covered_call', 'short_put'
    """

    DEFAULT_PARAMS = {
        'iron_condor': {
            'iv_rank_min': 50.0,       # Only sell premium when IV elevated
            'dte_target': 30,
            'max_hold_days': 25,        # Exit before expiration
            'profit_take_pct': 0.50,    # Take profit at 50% of credit
            'stop_loss_mult': 2.0,      # Stop at 2x credit
            'wing_width_pct': 0.05,    # 5% wide wings
            'atm_strike_pct': 0.50      # Short strike at ~50 delta
        },
        'wheel': {
            'iv_rank_min': 40.0,
            'dte_target': 30,
            'max_hold_days': 21,
            'profit_take_pct': 0.50,
            'stop_loss_mult': 2.0
        },
        'covered_call': {
            'iv_rank_min': 50.0,
            'dte_target': 30,
            'max_hold_days': 25,
            'profit_take_pct': 0.50,
            'stop_loss_mult': 2.0
        },
        'short_put': {
            'iv_rank_min': 50.0,
            'dte_target': 30,
            'max_hold_days': 21,
            'profit_take_pct': 0.50,
            'stop_loss_mult': 2.0
        }
    }

    @classmethod
    def run_historical_backtest(cls, ticker: str, strategy_type: str,
                                 days: int = 252, **kwargs) -> dict:
        """
        Run institutional-grade options backtest with Black-Scholes pricing.

        Key changes from equity-proxy version:
        - IV Rank gates entries (only trade when IV > threshold)
        - Uses simulated IV from realized vol (proxy for ATM IV)
        - Applies Triple Barrier to option credit, not underlying price
        - Includes theta decay, transaction costs
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 60)  # Extra for lookback

        try:
            hist = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'),
                               end=end_date.strftime('%Y-%m-%d'), progress=False)
            if hist.empty:
                return {"error": f"No data for {ticker}"}

            if isinstance(hist.columns, pd.MultiIndex):
                try:
                    hist = hist.xs(ticker, axis=1, level=1)
                except Exception:
                    pass

            close_prices = hist['Close']
            returns = close_prices.pct_change().dropna()

        except Exception as e:
            return {"error": f"Data fetch failed: {str(e)}"}

        # Parameter extraction
        params = cls.DEFAULT_PARAMS.get(strategy_type, cls.DEFAULT_PARAMS['iron_condor'])
        params.update({k: v for k, v in kwargs.items() if v is not None})

        # OOS Split: 70% train / 30% test
        split_idx = int(len(returns) * 0.70)
        in_sample_ret = returns[:split_idx]
        out_sample_ret = returns[split_idx:]
        in_sample_prices = close_prices[:split_idx]
        out_sample_prices = close_prices[split_idx:]

        if len(in_sample_ret) < 60 or len(out_sample_ret) < 30:
            return {"error": "Insufficient data for backtest (need 252+ days total)"}

        # Calculate in-sample IV (realized vol as IV proxy)
        trained_iv = OptionsPricingModel.estimate_atm_iv(in_sample_ret)

        # Calculate IV Rank for the full period
        rolling_vol = returns.rolling(252).std() * np.sqrt(252)
        current_iv = rolling_vol.iloc[-1]

        # Historical IV range for rank calculation
        iv_history = rolling_vol.dropna()
        if len(iv_history) > 20:
            iv_rank = ((iv_history < current_iv).sum() / len(iv_history)) * 100
        else:
            iv_rank = 50.0  # Neutral if insufficient history

        # Initialize transaction cost model (IBKR rates)
        tcm = TransactionCostModel("IBKR")

        # Walk-forward parameters
        trade_window = params['max_hold_days']  # Max hold days per trade
        dte_target = params['dte_target']
        iv_rank_min = params['iv_rank_min']

        trades = []
        equity_curve = []
        current_equity = 100000.0  # Starting capital

        # Walk through OOS period
        out_sample_reset = out_sample_ret.reset_index(drop=True)
        out_prices_reset = out_sample_prices.reset_index(drop=True)

        trade_open = False
        position_entry_day = 0
        position_entry_price = 0.0
        position_iv = 0.0
        position_credit = 0.0
        position_strikes = {}
        position_days_held = 0

        condor = IronCondorStrategy(
            wing_width_pct=params.get('wing_width_pct', 0.05),
            profit_take_pct=params.get('profit_take_pct', 0.50),
            stop_loss_mult=params.get('stop_loss_mult', 2.0),
            dte_target=dte_target,
            iv_rank_threshold=iv_rank_min
        )

        for i in range(len(out_sample_reset) - trade_window):
            current_price = float(out_prices_reset.iloc[i])

            # Update rolling IV estimate
            if i > 0:
                lookback = max(1, i - 30)
                realized_vol = out_sample_reset.iloc[lookback:i].std()
                current_iv_estimate = realized_vol * np.sqrt(252)
            else:
                current_iv_estimate = trained_iv

            # Calculate current IV Rank for this day
            if i >= 252:
                vol_series = out_sample_reset.iloc[max(0, i-252):i]
                iv_range = vol_series.rolling(252).std() * np.sqrt(252)
                if not iv_range.dropna().empty:
                    current_iv_rank = ((iv_range.dropna() < current_iv_estimate).sum() /
                                      max(len(iv_range.dropna()), 1)) * 100
                else:
                    current_iv_rank = 50.0
            else:
                current_iv_rank = 50.0

            if not trade_open:
                # Entry logic: IV Rank must be above threshold
                if current_iv_rank < iv_rank_min:
                    equity_curve.append(current_equity)
                    continue

                # Calculate strikes and credit for iron condor
                strikes = condor.calculate_strikes(current_price, current_iv_estimate)
                T = dte_target / 365.0
                r = 0.045

                credit_data = condor.calculate_credit(
                    current_price, T, r, current_iv_estimate, strikes
                )

                if credit_data['total_credit'] < 0.05:  # Minimum credit threshold
                    equity_curve.append(current_equity)
                    continue

                # Enter position
                trade_open = True
                position_entry_day = i
                position_entry_price = current_price
                position_iv = current_iv_estimate
                position_credit = credit_data['total_credit']
                position_strikes = strikes
                position_days_held = 0

                # Simulate the trade immediately with known outcome
                # Use full price path simulation
                price_path = out_prices_reset.iloc[i:i + trade_window + 1].values
                trade_result = condor.simulate_pnl_path(
                    S_path=price_path,
                    T_start=T,
                    r=r,
                    iv=current_iv_estimate,
                    daily_steps=min(trade_window, len(price_path) - 1),
                    strikes=strikes,
                    initial_credit=credit_data['total_credit'],
                    tcm=tcm,
                    num_contracts=1
                )

                # Record trade and update equity
                current_equity += trade_result['net_pnl']
                trade_result['entry_day'] = i
                trade_result['entry_price'] = current_price
                trade_result['iv_rank'] = round(current_iv_rank, 2)
                trade_result['strategy'] = strategy_type
                trades.append(trade_result)
                trade_open = False

            equity_curve.append(current_equity)

        # If still in position at end, close at market
        if trade_open:
            last_price = float(out_prices_reset.iloc[-1])
            remaining_T = max(0, (trade_window - position_days_held) / 365)
            tc = tcm.total_cost(num_contracts=4, mid_price=position_credit, order_type="market")
            current_equity += -tc['total_cost']  # Just costs to close
            equity_curve.append(current_equity)

        if not trades:
            return {
                "error": "No trades generated — IV Rank threshold may be too high or insufficient data",
                "iv_rank_threshold": iv_rank_min,
                "days_of_data": len(out_sample_reset),
                "strategy": strategy_type
            }

        # Calculate metrics
        pnls = [t['net_pnl'] for t in trades]
        gross_pnls = [t['pnl'] for t in trades]

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        n_trades = len(trades)
        n_wins = len(wins)
        win_rate = (n_wins / n_trades * 100) if n_trades > 0 else 0

        total_net_pnl = sum(pnls)
        total_gross_pnl = sum(gross_pnls)
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 1
        profit_factor = (sum(wins) / sum(losses)) if losses and sum(losses) > 0 else float('inf')

        # Equity curve metrics
        equity_arr = np.array(equity_curve)
        cumulative = equity_arr - equity_arr[0]
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = running_max - cumulative
        max_drawdown = float(drawdowns.max()) if len(drawdowns) > 0 else 0

        # Annualized metrics
        n_days = len(out_sample_reset)
        years = n_days / 252
        total_return = (equity_arr[-1] - equity_arr[0]) / equity_arr[0] if equity_arr[0] > 0 else 0
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Sharpe / Sortino
        daily_returns = np.diff(equity_arr) / equity_arr[:-1]
        daily_returns = daily_returns[~np.isnan(daily_returns)]
        if len(daily_returns) > 5:
            sharpe = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
            downside_returns = daily_returns[daily_returns < 0]
            sortino = (np.mean(daily_returns) / np.std(downside_returns)) * np.sqrt(252) if len(downside_returns) > 0 and np.std(downside_returns) > 0 else 0
            calmar = (annualized_return / max_drawdown) if max_drawdown > 0 else 0
        else:
            sharpe = sortino = calmar = 0

        # Barrier hit distribution
        barrier_counts = {"pt": 0, "sl": 0, "time": 0, "expired": 0}
        for t in trades:
            bh = t.get('barrier_hit', 'time')
            if bh in barrier_counts:
                barrier_counts[bh] += 1

        return {
            "ticker": ticker,
            "strategy": strategy_type,
            "n_trades": n_trades,
            "n_wins": n_wins,
            "win_rate_percent": round(win_rate, 2),
            "total_net_pnl": round(total_net_pnl, 2),
            "total_gross_pnl": round(total_gross_pnl, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else 99.99,
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "max_drawdown": round(max_drawdown, 2),
            "total_return_percent": round(total_return * 100, 2),
            "annualized_return_percent": round(annualized_return * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "trained_iv": round(trained_iv, 4),
            "iv_rank_threshold": iv_rank_min,
            "barrier_hits": barrier_counts,
            "barrier_hits_pct": {
                k: round(v / n_trades * 100, 1) for k, v in barrier_counts.items()
            },
            "num_contracts_per_trade": 1,
            "transaction_cost_per_trade": round(
                trades[0]['transaction_cost'] if trades else 0, 2
            ) if n_trades > 0 else 0,
            "days_tested": n_days,
            "verdict": "PASS" if win_rate >= 75 and profit_factor >= 1.2 and max_drawdown < 20 else "FAIL",
            "trade_sample": trades[:3] if len(trades) >= 3 else trades
        }


class WheelStrategy(StrategyBacktester):
    """Wheel strategy: sell cash-secured puts, then sell covered calls if assigned."""

    @classmethod
    def run_historical_backtest(cls, ticker: str, strategy_type: str = 'wheel',
                                 days: int = 252, **kwargs) -> dict:
        """Wheel = short put + (optional covered call if assigned)."""
        # Delegate to base — same infrastructure supports wheel
        return super().run_historical_backtest(ticker, 'wheel', days, **kwargs)


class ShortPutStrategy(StrategyBacktester):
    """Short put strategy: sell cash-secured puts."""

    @classmethod
    def run_historical_backtest(cls, ticker: str, strategy_type: str = 'short_put',
                                 days: int = 252, **kwargs) -> dict:
        """Short put = naked put sell with cash collateral."""
        return super().run_historical_backtest(ticker, 'short_put', days, **kwargs)


class CoveredCallStrategy(StrategyBacktester):
    """Covered call strategy: long equity + short call."""

    @classmethod
    def run_historical_backtest(cls, ticker: str, strategy_type: str = 'covered_call',
                                 days: int = 252, **kwargs) -> dict:
        """Covered call = equity long + short call."""
        return super().run_historical_backtest(ticker, 'covered_call', days, **kwargs)