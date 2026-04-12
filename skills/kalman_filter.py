import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict
from statsmodels.tsa.stattools import adfuller


class KalmanFilterPairs:
    """
    Kalman Filter for Dynamic Hedge Ratio in Statistical Arbitrage.

    Instead of a static OLS hedge ratio, the Kalman Filter estimates
    a time-varying hedge ratio that adapts to changing market relationships.

    State equation: beta_t = beta_{t-1} + noise (random walk)
    Observation: y_t = alpha + beta_t * x_t + observation_noise

    Where y = leg1 (underperforming), x = leg2 (overperforming)
    Spread = y - beta * x (dynamic)
    Z-Score = (spread - mean) / std

    Trade when |Z-Score| > threshold.
    """

    def __init__(self, state_variance: float = 0.001, observation_variance: float = 0.1):
        """
        Args:
            state_variance: Process noise for hedge ratio evolution
            observation_variance: Measurement noise for spread observation
        """
        self.state_variance = state_variance
        self.observation_variance = observation_variance

        # State variables (initialized on first observation)
        self.beta = 0.0       # Current hedge ratio estimate
        self.P = 1.0          # Error covariance (uncertainty in beta)
        self.alpha = 0.0      # Intercept (spread mean)

        self._initialized = False
        self.beta_history = []
        self.spread_history = []
        self.z_score_history = []

    def initialize(self, y0: float, x0: float):
        """Initialize state from first observation."""
        if x0 == 0:
            x0 = 0.001
        self.beta = y0 / x0  # Simple ratio as initial estimate
        self.alpha = 0.0
        self.P = 1.0
        self._initialized = True
        self.beta_history = [self.beta]
        self.spread_history = []
        self.z_score_history = []

    def update(self, y: float, x: float) -> Dict:
        """
        Update the Kalman Filter with a new observation.
        Returns current state estimates.
        """
        if not self._initialized or x == 0:
            self.initialize(y, x)
            return self.get_state()

        # Prediction step
        # beta_t|t-1 = beta_{t-1} (random walk)
        beta_pred = self.beta
        P_pred = self.P + self.state_variance

        # Observation: y = alpha + beta * x + v
        x_safe = x if x != 0 else 0.001
        y_pred = self.alpha + beta_pred * x_safe

        # Measurement residual (innovation)
        residual = y - y_pred

        # Kalman gain
        observation_cov = self.observation_variance + P_pred * (x_safe ** 2)
        K = P_pred * x_safe / observation_cov  # Vector for beta update

        # Update step
        self.beta = beta_pred + K * residual
        self.alpha = self.alpha + 0.1 * residual  # Slow drift for alpha

        # Covariance update (Joseph form for numerical stability)
        I_Kx = 1 - K * x_safe
        self.P = P_pred * I_Kx + self.observation_variance * (K ** 2)

        # Clamp P to prevent explosion
        self.P = min(max(self.P, 1e-8), 10.0)
        self.beta = min(max(self.beta, -5.0), 5.0)

        # Store history
        self.beta_history.append(self.beta)
        spread = y - self.beta * x_safe
        self.spread_history.append(spread)

        # Update Z-Score if we have enough history
        if len(self.spread_history) >= 20:
            spread_arr = np.array(self.spread_history[-90:])  # Use last 90
            mean_spread = np.mean(spread_arr)
            std_spread = np.std(spread_arr)
            z_score = (spread - mean_spread) / std_spread if std_spread > 0 else 0.0
        else:
            z_score = 0.0

        self.z_score_history.append(z_score)

        return self.get_state()

    def get_state(self) -> Dict:
        """Get current filter state."""
        spread = self.spread_history[-1] if self.spread_history else 0.0
        z = self.z_score_history[-1] if self.z_score_history else 0.0

        return {
            "hedge_ratio": round(self.beta, 4),
            "spread": round(spread, 4),
            "z_score": round(z, 2),
            "beta_uncertainty": round(self.P, 6),
            "observations": len(self.spread_history)
        }

    def get_signal(self, z_entry: float = 2.0, z_exit: float = 0.0) -> Dict:
        """
        Generate trading signal from current Z-Score.
        Uses dynamic hedge ratio from Kalman filter.
        """
        if len(self.spread_history) < 20:
            return {
                "signal": "NO_SIGNAL",
                "z_score": 0.0,
                "reason": "Insufficient history for Z-Score"
            }

        current_z = self.z_score_history[-1]
        spread = self.spread_history[-1]
        beta = self.beta

        # Determine action based on Z-Score
        if current_z > z_entry:
            # Spread too high (leg1 overperforming relative to leg2)
            # Short leg1, Long leg2
            action = "SHORT_SPREAD"
            direction = -1
        elif current_z < -z_entry:
            # Spread too low (leg1 underperforming)
            # Long leg1, Short leg2
            action = "LONG_SPREAD"
            direction = 1
        elif abs(current_z) < z_exit:
            # Spread reverted to mean — exit
            action = "EXIT"
            direction = 0
        else:
            action = "HOLD"
            direction = 0

        return {
            "signal": action,
            "z_score": round(current_z, 2),
            "hedge_ratio": round(beta, 4),
            "spread": round(spread, 4),
            "direction": direction,
            "confidence": "high" if abs(current_z) > 2.5 else "medium" if abs(current_z) > 1.5 else "low"
        }

    def get_performance_metrics(self) -> Dict:
        """Compute performance metrics from spread history."""
        if len(self.spread_history) < 30:
            return {"error": "Insufficient history"}

        spreads = np.array(self.spread_history)
        returns = np.diff(spreads) / spreads[:-1].replace(0, 0.001)

        cumulative_return = (spreads[-1] - spreads[0]) / abs(spreads[0]) if spreads[0] != 0 else 0
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 5 and np.std(returns) > 0 else 0
        max_dd = 0.0
        running_max = spreads[0]
        for s in spreads:
            if s > running_max:
                running_max = s
            dd = (running_max - s) / running_max if running_max != 0 else 0
            max_dd = max(max_dd, dd)

        return {
            "total_spread_change": round(cumulative_return * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "avg_hedge_ratio": round(np.mean(self.beta_history[-60:]), 4),
            "hedge_ratio_volatility": round(np.std(self.beta_history[-60:]), 4),
            "n_observations": len(self.spread_history)
        }

    def reset(self):
        """Reset filter to initial state."""
        self.beta = 0.0
        self.P = 1.0
        self.alpha = 0.0
        self._initialized = False
        self.beta_history = []
        self.spread_history = []
        self.z_score_history = []


class KalmanFilterPairTrader:
    """
    Higher-level interface for Kalman Filter pairs trading.
    Manages multiple pairs simultaneously with proper state management.
    """

    def __init__(self, z_entry: float = 2.0, z_exit: float = 0.0):
        self.z_entry = z_entry
        self.z_exit = z_exit
        self.filters = {}
        self.positions = {}  # Current positions: {pair: direction}
        self.trade_log = []

    def add_pair(self, pair_name: str):
        """Add a new pair to track."""
        self.filters[pair_name] = KalmanFilterPairs()
        self.positions[pair_name] = 0  # 0 = no position

    def update_pair(self, pair_name: str, leg1_price: float, leg2_price: float) -> Dict:
        """Update a pair with new price data."""
        if pair_name not in self.filters:
            self.add_pair(pair_name)

        kf = self.filters[pair_name]
        state = kf.update(leg1_price, leg2_price)

        # Generate signal
        signal = kf.get_signal(z_entry=self.z_entry, z_exit=self.z_exit)

        # Check if we should open/close position based on signal
        current_pos = self.positions[pair_name]
        new_pos = signal["direction"]

        if new_pos != 0 and current_pos == 0:
            # Opening position
            self.positions[pair_name] = new_pos
            self.trade_log.append({
                "timestamp": pd.Timestamp.now(),
                "pair": pair_name,
                "action": "OPEN",
                "direction": new_pos,
                "z_score": signal["z_score"],
                "hedge_ratio": signal["hedge_ratio"]
            })
            signal["trade_event"] = "POSITION_OPENED"

        elif new_pos == 0 and current_pos != 0:
            # Closing position
            self.positions[pair_name] = 0
            self.trade_log.append({
                "timestamp": pd.Timestamp.now(),
                "pair": pair_name,
                "action": "CLOSE",
                "direction": 0,
                "z_score": signal["z_score"],
                "hedge_ratio": signal["hedge_ratio"]
            })
            signal["trade_event"] = "POSITION_CLOSED"

        signal["current_position"] = self.positions[pair_name]
        signal["hedge_ratio"] = kf.beta

        return signal

    def get_portfolio_state(self) -> Dict:
        """Get current portfolio state for all pairs."""
        total_signal = {}
        for pair_name, kf in self.filters.items():
            metrics = kf.get_performance_metrics()
            signal = kf.get_signal(z_entry=self.z_entry, z_exit=self.z_exit)
            total_signal[pair_name] = {
                "position": self.positions[pair_name],
                "z_score": signal.get("z_score", 0),
                "hedge_ratio": kf.beta,
                "performance": metrics
            }
        return total_signal

    def close_all(self):
        """Emergency close all positions."""
        for pair_name in self.positions:
            if self.positions[pair_name] != 0:
                self.positions[pair_name] = 0
                self.trade_log.append({
                    "timestamp": pd.Timestamp.now(),
                    "pair": pair_name,
                    "action": "FORCE_CLOSE",
                    "direction": 0
                })


def test_cointegration_eg(series_1: pd.Series, series_2: pd.Series,
                         alpha: float = 0.05) -> Dict:
    """
    Engle-Granger two-step cointegration test (standalone function).

    Step 1: OLS regression Y = alpha + beta*X + epsilon
    Step 2: ADF test on residuals

    Returns cointegration result.
    """
    if len(series_1) < 30:
        return {"is_cointegrated": False, "reason": "Insufficient data"}

    aligned = pd.concat([series_1, series_2], axis=1).dropna()
    if len(aligned) < 30:
        return {"is_cointegrated": False, "reason": "Alignment failed"}

    Y = aligned.iloc[:, 0].values
    X = aligned.iloc[:, 1].values
    X_with_const = np.column_stack([np.ones(len(X)), X])

    try:
        beta_hat = np.linalg.lstsq(X_with_const, Y, rcond=None)[0]
        alpha_const = beta_hat[0]
        hedge_ratio = beta_hat[1]
    except Exception:
        return {"is_cointegrated": False, "reason": "OLS failed"}

    residuals = Y - (alpha_const + hedge_ratio * X)

    try:
        adf_result = adfuller(residuals, maxlag=1, regression='c', autolag='AIC')
        p_value = adf_result[1]
    except Exception:
        return {"is_cointegrated": False, "reason": "ADF failed"}

    is_cointegrated = p_value < alpha

    return {
        "is_cointegrated": is_cointegrated,
        "p_value": round(p_value, 4),
        "adf_statistic": round(adf_result[0], 4),
        "hedge_ratio": round(hedge_ratio, 4),
        "alpha": round(alpha_const, 4),
        "critical_value_5pct": round(adf_result[4]['5%'], 4)
    }


def calculate_half_life(spread: pd.Series) -> Optional[float]:
    """
    Calculate half-life of mean reversion.
    Uses Ornstein-Uhlenbeck formula: half_life = -ln(2) / lambda
    where lambda from AR(1): spread_t = a + b*spread_{t-1} + noise
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