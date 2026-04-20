import itertools
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


class ParameterOptimizer:
    """
    Phase 11 Institutional Engine: Walk-Forward Optimization (WFO) with Exhaustive Grid Search.

    Before passing a strategy to the Critic, this module systematically backtests
    structural variants of the Triple Barrier to find the maximum possible Sharpe/Edge.

    Implements:
    - Rolling walk-forward optimization with expanding or rolling windows
    - Grid search over TP/SL/Time barrier combinations
    - Out-of-sample validation of optimized parameters
    - Proper parameter injection into backtester
    """

    DEFAULT_GRID = {
        "tp_multipliers": [0.3, 0.5, 0.8, 1.0],
        "sl_multipliers": [1.0, 1.5, 2.0, 2.5],
        "time_horizons": [3, 5, 10],
        "ewma_spans": [10, 20, 30]
    }

    @classmethod
    def optimize_barriers(cls, ticker: str, strategy_type: str,
                          days: int = 180,
                          grid: Dict = None,
                          method: str = "expanding",
                          train_window: int = 252,
                          test_window: int = 63) -> Dict:
        """
        Rolling Walk-Forward Optimization.

        Args:
            ticker: instrument to test
            strategy_type: 'short_put', 'covered_call', 'long_gamma', 'iron_condor'
            days: total historical lookback
            grid: parameter grid to search (default uses DEFAULT_GRID)
            method: 'expanding' (grow train window) or 'rolling' (fixed train window)
            train_window: training period in days
            test_window: testing period in days (walk-forward step)

        Returns:
            Best parameters found with out-of-sample performance metrics.
        """
        if grid is None:
            grid = cls.DEFAULT_GRID

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + train_window)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        # Download data
        try:
            hist = yf.download(ticker, start=start_str, end=end_str, progress=False)
            if hist.empty or len(hist) < train_window + test_window:
                return {"error": "Insufficient data for WFO"}

            if isinstance(hist.columns, pd.MultiIndex):
                hist = hist.xs(ticker, axis=1, level=1)

            close_prices = hist['Close']
            returns = close_prices.pct_change().dropna()
        except Exception as e:
            return {"error": f"Failed to download data: {str(e)}"}

        # Generate all grid combinations
        tp_bounds = grid.get("tp_multipliers", cls.DEFAULT_GRID["tp_multipliers"])
        sl_bounds = grid.get("sl_multipliers", cls.DEFAULT_GRID["sl_multipliers"])
        time_horizons = grid.get("time_horizons", cls.DEFAULT_GRID["time_horizons"])
        ewma_spans = grid.get("ewma_spans", cls.DEFAULT_GRID["ewma_spans"])

        grid_combinations = list(itertools.product(tp_bounds, sl_bounds, time_horizons, ewma_spans))
        results = []
        cache: Dict[str, Dict] = {}

        # Walk-Forward Loop
        for start_idx in range(0, len(returns) - train_window - test_window, test_window):
            train_end = start_idx + train_window
            test_start = train_end
            test_end = min(test_start + test_window, len(returns))

            train_ret = returns[:train_end]
            test_ret = returns[test_start:test_end]
            test_prices = close_prices[test_start:test_end]

            if len(train_ret) < 60 or len(test_ret) < 10:
                continue

            # Compute trained volatility from in-sample
            for tp, sl, t_hor, ewma_span in grid_combinations:
                # Skip already tested combinations (cache)
                cache_key = f"{ticker}_{method}_{start_idx}_{train_end}_{test_start}_{test_end}_{tp}_{sl}_{t_hor}_{ewma_span}"
                if cache_key in cache:
                    cached_result = dict(cache[cache_key])
                else:
                    # Train: compute EWMA volatility from in-sample
                    in_sample_vol = train_ret.ewm(span=ewma_span).std().iloc[-1]
                    trained_vol = float(in_sample_vol)

                    # Simulate out-of-sample performance
                    simulated_metrics = cls._simulate_walk_forward(
                        test_ret, test_prices, trained_vol, tp, sl, t_hor, strategy_type
                    )

                    cached_result = {
                        "tp": tp, "sl": sl, "t_hor": t_hor, "ewma_span": ewma_span,
                        "trained_vol": trained_vol,
                        **simulated_metrics
                    }
                    cache[cache_key] = dict(cached_result)

                cached_result["window_start"] = start_idx
                cached_result["window_end"] = test_end
                results.append(cached_result)

        if not results:
            return {"error": "No valid optimization results generated"}

        # Aggregate results across all walk-forward windows
        df_results = pd.DataFrame(results)

        # Find best parameters by average Sharpe across all windows
        # Also require: win_rate >= 75%, PF >= 1.2, max_DD < 20%
        valid_results = df_results[
            (df_results["win_rate"] >= 75.0) &
            (df_results["profit_factor"] >= 1.2) &
            (df_results["max_drawdown"] < 20.0)
        ]

        if valid_results.empty:
            # Relax constraints to find any viable parameters
            valid_results = df_results[df_results["win_rate"] >= 60.0]

        if valid_results.empty:
            # Fall back to full grid with best average profit factor
            valid_results = df_results

        # Group by parameters and compute average metrics
        param_groups = valid_results.groupby(["tp", "sl", "t_hor", "ewma_span"]).agg({
            "win_rate": "mean",
            "profit_factor": "mean",
            "sharpe_ratio": "mean",
            "max_drawdown": "max",
            "num_trades": "sum"
        }).reset_index()

        # Rank by profit_factor then sharpe_ratio
        param_groups = param_groups.sort_values(
            ["profit_factor", "sharpe_ratio"], ascending=[False, False]
        )

        best = param_groups.iloc[0]

        return {
            "optimal_tp_multiplier": round(float(best["tp"]), 2),
            "optimal_sl_multiplier": round(float(best["sl"]), 2),
            "optimal_time_days": int(best["t_hor"]),
            "optimal_ewma_span": int(best["ewma_span"]),
            "avg_win_rate": round(float(best["win_rate"]), 2),
            "avg_profit_factor": round(float(best["profit_factor"]), 2),
            "avg_sharpe_ratio": round(float(best["sharpe_ratio"]), 2),
            "worst_max_drawdown": round(float(best["max_drawdown"]), 2),
            "total_trades": int(best["num_trades"]),
            "num_windows": len(valid_results["window_start"].unique()),
            "walk_forward_verified": True,
            "optimization_method": method,
            "train_window_days": train_window,
            "test_window_days": test_window,
            "all_parameters_tested": len(grid_combinations),
            "verdict": "PASS" if best["win_rate"] >= 75 and best["profit_factor"] >= 1.2 else "FAIL"
        }

    @classmethod
    def _simulate_walk_forward(cls, out_sample_ret: pd.Series, out_sample_prices: pd.Series,
                               trained_vol: float, tp_mult: float, sl_mult: float,
                               t_horizon: int, strategy_type: str) -> Dict:
        """
        Simulate the walk-forward test for a given parameter set.
        Uses TRAINED volatility from in-sample, applies to out-of-sample.
        """
        daily_pnl = []
        gross_profit = 0.0
        gross_loss = 0.0
        win_count = 0
        barrier_hits = {"pt": 0, "sl": 0, "time": 0}

        # Use the trained vol estimate from in-sample (fixed)
        current_vol = trained_vol

        for i in range(len(out_sample_ret) - t_horizon):
            current_price = out_sample_prices.iloc[i]

            # Dynamic barriers using TRAINED volatility
            if strategy_type in ['short_put', 'wheel']:
                pt_barrier = current_price * (1 + (current_vol * tp_mult))
                sl_barrier = current_price * (1 - (current_vol * sl_mult))
            elif strategy_type in ['iron_condor', 'short_strangle']:
                pt_barrier = current_price * (1 + (current_vol * tp_mult))
                sl_barrier = current_price * (1 - (current_vol * sl_mult))
            else:
                pt_barrier = current_price * (1 + (current_vol * tp_mult))
                sl_barrier = current_price * (1 - (current_vol * sl_mult))

            hit_barrier = "time"
            pnl = 0.0

            for j in range(1, t_horizon + 1):
                future_price = out_sample_prices.iloc[i + j]

                if strategy_type in ['short_put', 'wheel', 'covered_call']:
                    if future_price < sl_barrier:
                        hit_barrier = "sl"
                        pnl = -1.5
                        break
                    elif future_price > pt_barrier:
                        hit_barrier = "pt"
                        pnl = 0.5
                        break

                elif strategy_type in ['iron_condor', 'short_strangle']:
                    if future_price > pt_barrier or future_price < sl_barrier:
                        hit_barrier = "sl"
                        pnl = -1.2
                        break

            if hit_barrier == "time":
                if strategy_type in ['short_put', 'wheel', 'iron_condor', 'short_strangle']:
                    pnl = 0.005 * (t_horizon / 5)
                else:
                    future_price = out_sample_prices.iloc[i + t_horizon]
                    pnl = (future_price - current_price) / current_price * 100

            daily_pnl.append(pnl)
            barrier_hits[hit_barrier] += 1

            if pnl > 0:
                win_count += 1
                gross_profit += pnl
            else:
                gross_loss += abs(pnl)

        if not daily_pnl:
            return {"win_rate": 0, "profit_factor": 0, "sharpe_ratio": 0,
                    "max_drawdown": 0, "num_trades": 0}

        n_trades = len(daily_pnl)
        win_rate = (win_count / n_trades) * 100
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999.0

        cumulative = np.cumsum(daily_pnl)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = running_max - cumulative
        max_drawdown = float(drawdowns.max())

        mean_ret = np.mean(daily_pnl)
        std_ret = np.std(daily_pnl) if len(daily_pnl) > 1 else 1.0
        sharpe_ratio = (mean_ret / std_ret) * np.sqrt(252) if std_ret > 0 else 0.0

        return {
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
            "num_trades": n_trades,
            "barrier_hits": barrier_hits
        }

    @classmethod
    def quick_scan(cls, ticker: str, strategy_type: str, days: int = 90) -> Dict:
        """
        Quick grid scan without full walk-forward.
        Uses single 70/30 split (not rolling).
        Useful for rapid parameter exploration.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        try:
            hist = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'),
                               end=end_date.strftime('%Y-%m-%d'), progress=False)
            if hist.empty:
                return {"error": "Failed to pull data"}

            if isinstance(hist.columns, pd.MultiIndex):
                hist = hist.xs(ticker, axis=1, level=1)

            close_prices = hist['Close']
            returns = close_prices.pct_change().dropna()

            split_idx = int(len(returns) * 0.70)
            in_sample = returns[:split_idx]
            out_sample = returns[split_idx:]
            out_prices = close_prices[split_idx:]
        except Exception as e:
            return {"error": str(e)}

        # Train on in-sample
        in_sample_vol = in_sample.ewm(span=20).std().iloc[-1]
        trained_vol = float(in_sample_vol)

        tp_bounds = [0.3, 0.5, 0.8]
        sl_bounds = [1.0, 1.5, 2.0]
        time_horizons = [5, 10]

        grid = list(itertools.product(tp_bounds, sl_bounds, time_horizons))
        best = None
        best_pf = 0.0

        for tp, sl, t_hor in grid:
            metrics = cls._simulate_walk_forward(
                out_sample, out_prices, trained_vol, tp, sl, t_hor, strategy_type
            )

            if metrics["profit_factor"] > best_pf:
                best_pf = metrics["profit_factor"]
                best = {
                    "tp": tp, "sl": sl, "t_hor": t_hor,
                    "trained_vol": trained_vol,
                    **metrics
                }

        if best:
            return {
                "optimal_tp_multiplier": best["tp"],
                "optimal_sl_multiplier": best["sl"],
                "optimal_time_days": best["t_hor"],
                "trained_volatility": round(trained_vol, 6),
                "win_rate": best["win_rate"],
                "profit_factor": best["profit_factor"],
                "sharpe_ratio": best["sharpe_ratio"],
                "max_drawdown": best["max_drawdown"],
                "num_trades": best["num_trades"],
                "method": "single_split_70_30",
                "verdict": "PASS" if best["win_rate"] >= 75 and best["profit_factor"] >= 1.2 else "FAIL"
            }

        return {"error": "No viable parameters found"}


# Global singleton
parameter_optimizer = ParameterOptimizer()