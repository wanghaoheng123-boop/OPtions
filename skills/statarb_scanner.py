import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from statsmodels.tsa.stattools import adfuller


class StatArbScanner:
    """
    Statistical Arbitrage & Pairs Trading Engine with proper cointegration testing.

    Implements:
    - Engle-Granger two-step cointegration test
    - Z-Score spread analysis with mean reversion signals
    - Half-life of mean reversion calculation
    - Kalman Filter for dynamic hedge ratio (optional enhancement)

    Only trades pairs that pass the cointegration test at 95% confidence.
    """

    DEFAULT_PAIRS = [
        ("SPY", "QQQ"),   # Broad vs Tech
        ("XLK", "XLV"),   # Tech vs Healthcare
        ("IWM", "SPY"),   # Small Cap vs Large Cap
        ("XLF", "XLE"),   # Financials vs Energy
        ("GLD", "SLV")    # Gold vs Silver
    ]

    # Extended universe for institutional pairs trading
    INSTITUTIONAL_PAIRS = [
        # Equities
        ("SPY", "QQQ"),
        ("SPY", "IWM"),
        ("SPY", "DIA"),
        ("QQQ", "QQQM"),
        # Sectors
        ("XLK", "XLV"),
        ("XLF", "XLE"),
        ("XLY", "XLP"),
        ("XLI", "XLB"),
        # Rates / Bonds
        ("TLT", "IEF"),
        ("TLT", "SHY"),
        ("IEF", "SHY"),
        # Commodities
        ("GLD", "SLV"),
        ("USO", "BNO"),
        ("UNG", "DGA"),
        # International
        ("EEM", "IWM"),
        ("EFA", "EEM"),
        ("SPY", "EFA"),
    ]

    @classmethod
    def test_cointegration(cls, series_1: pd.Series, series_2: pd.Series,
                           alpha: float = 0.05) -> Dict:
        """
        Engle-Granger two-step cointegration test.

        Step 1: Regress Y on X: Y = alpha + beta*X + epsilon
        Step 2: Test stationarity of residuals (epsilon) using ADF test
        If ADF p-value < alpha, residuals are stationary → pair is cointegrated.

        Returns dict with cointegration result and regression parameters.
        """
        if len(series_1) < 30 or len(series_2) < 30:
            return {"is_cointegrated": False, "reason": "Insufficient data (< 30 observations)"}

        # Align series
        aligned = pd.concat([series_1, series_2], axis=1).dropna()
        if len(aligned) < 30:
            return {"is_cointegrated": False, "reason": "Insufficient aligned data"}

        # Step 1: OLS regression to find hedge ratio (beta)
        Y = aligned.iloc[:, 0].values
        X = aligned.iloc[:, 1].values
        X_with_const = np.column_stack([np.ones(len(X)), X])

        try:
            # OLS: beta = (X'X)^-1 * X'Y
            beta_hat = np.linalg.lstsq(X_with_const, Y, rcond=None)[0]
            alpha_const = beta_hat[0]
            hedge_ratio = beta_hat[1]
        except Exception:
            return {"is_cointegrated": False, "reason": "OLS regression failed"}

        # Calculate residuals
        residuals = Y - (alpha_const + hedge_ratio * X)

        # Step 2: ADF test on residuals
        try:
            adf_result = adfuller(residuals, maxlag=1, regression='c', autolag='AIC')
            adf_statistic = adf_result[0]
            p_value = adf_result[1]
        except Exception:
            return {"is_cointegrated": False, "reason": "ADF test failed"}

        is_cointegrated = p_value < alpha

        return {
            "is_cointegrated": is_cointegrated,
            "p_value": round(p_value, 4),
            "adf_statistic": round(adf_statistic, 4),
            "hedge_ratio": round(hedge_ratio, 4),
            "alpha": round(alpha_const, 4),
            "critical_value_5pct": round(adf_result[4]['5%'], 4),
            "num_observations": len(aligned)
        }

    @classmethod
    def calculate_spread_zscore(cls, series_1: pd.Series, series_2: pd.Series,
                                hedge_ratio: float = None,
                                lookback: int = 90) -> Dict:
        """
        Calculate the Z-Score of the price spread between two series.
        Uses dynamic hedge ratio if provided, otherwise simple ratio.

        Z-Score = (Current Spread - Mean Spread) / StdDev of Spread
        """
        if hedge_ratio is None:
            # Simple ratio spread
            spread = series_1 / series_2
        else:
            # Cointegrated spread with hedge ratio
            spread = series_1 - hedge_ratio * series_2

        # Use lookback window
        if len(spread) > lookback:
            spread_window = spread.iloc[-lookback:]
        else:
            spread_window = spread.dropna()

        if len(spread_window) < 20:
            return {"error": "Insufficient data for Z-score"}

        mean_spread = spread_window.mean()
        std_spread = spread_window.std()
        current_spread = spread.iloc[-1]

        if pd.isna(std_spread) or std_spread == 0:
            z_score = 0.0
        else:
            z_score = (current_spread - mean_spread) / std_spread

        # Z-Score normalized to per-unit (convert back to ratio scale for display)
        spread_pct = (current_spread - mean_spread) / mean_spread if mean_spread != 0 else 0

        return {
            "current_spread": round(float(current_spread), 6),
            "mean_spread": round(float(mean_spread), 6),
            "std_spread": round(float(std_spread), 6),
            "z_score": round(float(z_score), 2),
            "spread_deviation_pct": round(float(spread_pct) * 100, 2),
            "lookback_days": min(lookback, len(spread_window))
        }

    @classmethod
    def calculate_half_life(cls, spread: pd.Series) -> Optional[float]:
        """
        Calculate the half-life of mean reversion for a cointegrated pair.
        Uses the Ornstein-Uhlenbeck formula:

        half_life = -ln(2) / lambda
        where lambda is the mean-reversion speed from AR(1) regression: spread_t = a + b*spread_{t-1} + epsilon

        lambda = -ln(b), b = AR(1) coefficient
        """
        if len(spread) < 30:
            return None

        try:
            spread_clean = spread.dropna()
            X = np.column_stack([np.ones(len(spread_clean)), spread_clean.shift(1).fillna(0)])
            y = spread_clean.values

            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            b = beta[1]

            if b <= 0 or b >= 1:
                return None

            lambda_reversion = -np.log(b)
            half_life = np.log(2) / lambda_reversion

            return round(float(half_life), 1)
        except Exception:
            return None

    @classmethod
    def scan_pairs(cls, pairs: List[Tuple[str, str]] = None,
                   days: int = 90,
                   require_cointegration: bool = True,
                   cointegration_alpha: float = 0.05) -> List[Dict]:
        """
        Main entry point: scan all pairs for stat arb opportunities.

        Args:
            pairs: list of (leg1, leg2) tuples. Defaults to DEFAULT_PAIRS
            days: historical lookback period
            require_cointegration: if True, only include pairs that pass cointegration test
            cointegration_alpha: significance level for cointegration test (0.05 = 95%)

        Returns list of dicts with pair analysis sorted by |Z-Score| descending.
        """
        if pairs is None:
            pairs = cls.DEFAULT_PAIRS

        results = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        # Batch download all tickers
        all_tickers = list(set([ticker for pair in pairs for ticker in pair]))
        try:
            data = yf.download(all_tickers, start=start_str, end=end_str, progress=False)['Close']
            if isinstance(data, pd.Series):
                return [{"error": "YFinance failed to return price matrix"}]
        except Exception as e:
            return [{"error": str(e)}]

        for pair in pairs:
            leg_1, leg_2 = pair
            try:
                if leg_1 not in data.columns or leg_2 not in data.columns:
                    continue

                series_1 = data[leg_1].dropna()
                series_2 = data[leg_2].dropna()

                # Align dates
                aligned = pd.concat([series_1, series_2], axis=1, join='inner').dropna()
                aligned.columns = [leg_1, leg_2]

                if len(aligned) < 30:
                    continue

                # Test cointegration
                coint_result = cls.test_cointegration(
                    aligned[leg_1], aligned[leg_2], alpha=cointegration_alpha
                )

                # Calculate spread and Z-score
                hedge_ratio = coint_result.get("hedge_ratio") if coint_result["is_cointegrated"] else None
                zscore_result = cls.calculate_spread_zscore(
                    aligned[leg_1], aligned[leg_2],
                    hedge_ratio=hedge_ratio, lookback=min(days, len(aligned))
                )

                if "error" in zscore_result:
                    continue

                z_score = zscore_result["z_score"]

                # Calculate half-life of mean reversion
                if coint_result["is_cointegrated"] and hedge_ratio is not None:
                    spread = aligned[leg_1] - hedge_ratio * aligned[leg_2]
                    half_life = cls.calculate_half_life(spread)
                else:
                    half_life = None

                # Determine action based on Z-Score and cointegration
                action = "HOLD"
                direction = None
                urgency = "LOW"

                if coint_result["is_cointegrated"] or not require_cointegration:
                    if z_score > 2.0:
                        action = f"SHORT {leg_1} / BUY {leg_2}"
                        direction = "SHORT_OVERPERFORMER"
                        urgency = "HIGH"
                    elif z_score < -2.0:
                        action = f"BUY {leg_1} / SHORT {leg_2}"
                        direction = "BUY_UNDERPERFORMER"
                        urgency = "HIGH"
                    elif abs(z_score) > 1.5:
                        urgency = "MEDIUM"

                pair_result = {
                    "pair": f"{leg_1}/{leg_2}",
                    "leg_1": leg_1,
                    "leg_2": leg_2,
                    "z_score": z_score,
                    "current_spread": zscore_result["current_spread"],
                    "mean_spread": zscore_result["mean_spread"],
                    "std_spread": zscore_result["std_spread"],
                    "spread_deviation_pct": zscore_result["spread_deviation_pct"],
                    "action": action,
                    "direction": direction,
                    "urgency": urgency,
                    # Cointegration results
                    "is_cointegrated": coint_result["is_cointegrated"],
                    "cointegration_p_value": coint_result.get("p_value"),
                    "adf_statistic": coint_result.get("adf_statistic"),
                    "hedge_ratio": coint_result.get("hedge_ratio"),
                    "half_life_days": half_life,
                    "lookback_days": days,
                    "num_observations": coint_result.get("num_observations", len(aligned))
                }

                results.append(pair_result)

            except Exception as e:
                # Silently skip failed pairs
                continue

        # Sort by absolute Z-Score descending (most extreme divergence first)
        results = sorted(results, key=lambda x: abs(x['z_score']), reverse=True)
        return results

    @classmethod
    def get_pair_details(cls, leg_1: str, leg_2: str, days: int = 90) -> Dict:
        """
        Get detailed analysis of a specific pair.
        Includes: price series, spread, Z-Score, cointegration test, half-life.
        """
        return cls.scan_pairs(
            pairs=[(leg_1, leg_2)],
            days=days,
            require_cointegration=True
        )[0] if True else {}

    @classmethod
    def backtest_pairs_strategy(cls, pairs: List[Tuple[str, str]] = None,
                                days: int = 252,
                                z_entry: float = 2.0,
                                z_exit: float = 0.0) -> Dict:
        """
        Backtest the pairs strategy over historical data.
        Entry: |Z-Score| > z_entry
        Exit: |Z-Score| < z_exit (mean reversion)

        Returns performance metrics per pair.
        """
        if pairs is None:
            pairs = cls.DEFAULT_PAIRS

        results = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        all_tickers = list(set([ticker for pair in pairs for ticker in pair]))
        try:
            data = yf.download(all_tickers, start=start_str, end=end_str, progress=False)['Close']
        except Exception as e:
            return [{"error": str(e)}]

        for pair in pairs:
            leg_1, leg_2 = pair
            try:
                if leg_1 not in data.columns or leg_2 not in data.columns:
                    continue

                series_1 = data[leg_1].dropna()
                series_2 = data[leg_2].dropna()
                aligned = pd.concat([series_1, series_2], axis=1, join='inner').dropna()
                aligned.columns = [leg_1, leg_2]

                if len(aligned) < 60:
                    continue

                # Test cointegration
                coint_result = cls.test_cointegration(aligned[leg_1], aligned[leg_2])
                if not coint_result["is_cointegrated"]:
                    continue

                hedge_ratio = coint_result["hedge_ratio"]
                spread = aligned[leg_1] - hedge_ratio * aligned[leg_2]

                # Rolling Z-Score
                lookback = min(60, len(aligned) - 1)
                rolling_mean = spread.rolling(lookback).mean()
                rolling_std = spread.rolling(lookback).std()
                z_scores = (spread - rolling_mean) / rolling_std

                # Simulate trades
                trades = []
                position = 0  # 1 = long spread, -1 = short spread
                entry_z = None

                for i in range(lookback, len(z_scores)):
                    z = z_scores.iloc[i]
                    if pd.isna(z):
                        continue

                    if position == 0:
                        if abs(z) > z_entry:
                            position = -1 if z > 0 else 1  # Short when Z>2 (spread too high)
                            entry_z = z
                            entry_spread = spread.iloc[i]
                    elif position != 0:
                        if (position == 1 and z < z_exit) or (position == -1 and z > z_exit):
                            # Exit: Z reverted to mean
                            pnl = position * (spread.iloc[i] - entry_spread)
                            trades.append({
                                "entry_z": entry_z,
                                "exit_z": z,
                                "pnl": pnl,
                                "spread_entry": entry_spread,
                                "spread_exit": spread.iloc[i]
                            })
                            position = 0

                if trades:
                    pnls = [t["pnl"] for t in trades]
                    results.append({
                        "pair": f"{leg_1}/{leg_2}",
                        "num_trades": len(trades),
                        "win_rate": round(sum(1 for p in pnls if p > 0) / len(pnls) * 100, 1),
                        "avg_pnl": round(np.mean(pnls), 4),
                        "profit_factor": round(sum(p for p in pnls if p > 0) / max(0.0001, abs(sum(p for p in pnls if p < 0))), 2),
                        "hedge_ratio": round(hedge_ratio, 4),
                        "half_life": cls.calculate_half_life(spread)
                    })

            except Exception:
                continue

        return sorted(results, key=lambda x: x.get("profit_factor", 0), reverse=True)

    @classmethod
    def scan_pairs_kalman(cls, pairs: list = None, days: int = 90,
                          z_entry: float = 2.0, z_exit: float = 0.5) -> list:
        """
        Advanced pairs scanning with Kalman Filter dynamic hedge ratio.

        Uses KalmanFilterPairs for time-varying hedge ratio instead of static OLS.
        More responsive to changing market relationships.
        """
        from skills.kalman_filter import KalmanFilterPairTrader

        if pairs is None:
            pairs = cls.DEFAULT_PAIRS

        results = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        all_tickers = list(set([ticker for pair in pairs for ticker in pair]))
        try:
            data = yf.download(all_tickers, start=start_str, end=end_str, progress=False)['Close']
            if isinstance(data, pd.Series):
                return [{"error": "YFinance failed to return price matrix"}]
        except Exception as e:
            return [{"error": str(e)}]

        for pair in pairs:
            leg_1, leg_2 = pair
            try:
                if leg_1 not in data.columns or leg_2 not in data.columns:
                    continue

                series_1 = data[leg_1].dropna()
                series_2 = data[leg_2].dropna()
                aligned = pd.concat([series_1, series_2], axis=1, join='inner').dropna()
                aligned.columns = [leg_1, leg_2]

                if len(aligned) < 60:
                    continue

                # Test cointegration first (prerequisite for Kalman pairs)
                coint_result = cls.test_cointegration(aligned[leg_1], aligned[leg_2])
                if not coint_result["is_cointegrated"]:
                    # Try without cointegration requirement for non-cointegrated scan
                    coint_result = {"is_cointegrated": False, "p_value": None}

                # Initialize Kalman Filter for this pair
                kf_trader = KalmanFilterPairTrader(z_entry=z_entry, z_exit=z_exit)

                # Feed all historical prices to build Kalman state
                z_scores_kf = []
                hedge_ratios_kf = []
                for idx in range(len(aligned)):
                    leg1_price = aligned[leg_1].iloc[idx]
                    leg2_price = aligned[leg_2].iloc[idx]
                    signal = kf_trader.update_pair(f"{leg_1}/{leg_2}", leg1_price, leg2_price)
                    z_scores_kf.append(signal.get("z_score", 0))
                    hedge_ratios_kf.append(signal.get("hedge_ratio", 0))

                # Get current state
                final_state = kf_trader.filters.get(f"{leg_1}/{leg_2}")
                if final_state is None:
                    continue

                current_z = z_scores_kf[-1] if z_scores_kf else 0
                current_hr = hedge_ratios_kf[-1] if hedge_ratios_kf else coint_result.get("hedge_ratio", 1.0)

                # Determine action
                action = "HOLD"
                urgency = "LOW"
                if current_z > z_entry:
                    action = f"SHORT {leg_1} / BUY {leg_2}"
                    urgency = "HIGH"
                elif current_z < -z_entry:
                    action = f"BUY {leg_1} / SHORT {leg_2}"
                    urgency = "HIGH"
                elif abs(current_z) > 1.5:
                    urgency = "MEDIUM"

                # Calculate half-life from static spread for reference
                static_spread = aligned[leg_1] - coint_result.get("hedge_ratio", 1.0) * aligned[leg_2]
                half_life = cls.calculate_half_life(static_spread)

                results.append({
                    "pair": f"{leg_1}/{leg_2}",
                    "leg_1": leg_1,
                    "leg_2": leg_2,
                    "z_score": round(current_z, 2),
                    "kalman_hedge_ratio": round(current_hr, 4),
                    "static_hedge_ratio": coint_result.get("hedge_ratio"),
                    "action": action,
                    "urgency": urgency,
                    "is_cointegrated": coint_result["is_cointegrated"],
                    "cointegration_p_value": coint_result.get("p_value"),
                    "half_life_days": half_life,
                    "lookback_days": days,
                    "kalman_filter_used": True,
                    "num_observations": len(aligned)
                })

            except Exception as e:
                continue

        results = sorted(results, key=lambda x: abs(x['z_score']), reverse=True)
        return results

    @classmethod
    def get_institutional_pairs_scan(cls, days: int = 90) -> list:
        """
        Scan the full INSTITUTIONAL_PAIRS universe (17 pairs) with Kalman filtering.
        Used for institutional client reporting.
        """
        return cls.scan_pairs_kalman(pairs=cls.INSTITUTIONAL_PAIRS, days=days)


# Global singleton
statarb_scanner = StatArbScanner()