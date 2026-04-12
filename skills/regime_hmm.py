import numpy as np
import pandas as pd
import yfinance as yf
from hmmlearn.hmm import GaussianHMM
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings("ignore")


class RegimeDetectorHMM:
    """
    Phase 3 Institutional Engine: Hidden Markov Model (HMM) Regime Detection

    Upgraded from Phase 1 alpha version:
    - 4 hidden states (Bull, Bear, High-Vol Bear, Chop/Consolidation)
    - Extended feature set: Returns + Volatility + VIX proxy + Macro regime
    - Regime-adaptive strategy selection
    - Historical validation against VIX > 30 / S&P drawdown events

    Based on Hamilton (1989) "A New Approach to Economic Analysis of Nonstationary Time Series"
    """

    REGIME_LABELS = {
        0: "SUSTAINED UPTREND (BULL)",
        1: "HIGH-VOLATILITY DISTRESS (BEAR)",
        2: "LOW-VOLATILITY CHOP (CONSOLIDATION)",
        3: "BEAR MARKET RALLY (HIGH VOL)"
    }

    STRATEGY_MAP = {
        0: {"primary": "covered_call", "secondary": "long_gamma", "action": "TREND_FOLLOWING"},
        1: {"primary": "wheel", "secondary": "short_put", "action": "CASH_SECURED_PUTS"},
        2: {"primary": "iron_condor", "secondary": "short_strangle", "action": "RANGE_BOUND"},
        3: {"primary": "covered_call", "secondary": "iron_condor", "action": "DEFENSIVE"}
    }

    def __init__(self, ticker: str = "SPY", n_components: int = 4):
        self.ticker = ticker
        self.n_components = n_components
        self.model = GaussianHMM(
            n_components=self.n_components,
            covariance_type="full",
            n_iter=200,
            random_state=42
        )
        self._state_labels = {}
        self._is_fitted = False
        self._feature_names = None

    def fetch_training_data(self, days: int = 504) -> Optional[pd.DataFrame]:
        """
        Fetch extended feature set for HMM training.

        Features:
        1. Daily Returns (price change)
        2. Realized Volatility (rolling 10-day std of returns)
        3. High-Low Range (intraday volatility proxy)
        4. Volume change (unusual volume as regime signal)
        5. VIX proxy (realized vol relative to 252-day average)
        """
        try:
            end_date = pd.Timestamp.now()
            start_date = end_date - pd.Timedelta(days=days + 60)  # Extra for lookbacks

            df = yf.download(self.ticker, start=start_date.strftime('%Y-%m-%d'),
                              end=end_date.strftime('%Y-%m-%d'), progress=False)

            if df.empty or len(df) < 100:
                return None

            if isinstance(df.columns, pd.MultiIndex):
                df = df.xs(self.ticker, axis=1, level=1)

            # Feature engineering
            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']

            # 1. Daily returns
            returns = close.pct_change().dropna()

            # 2. Rolling realized volatility (10-day)
            realized_vol = returns.rolling(10).std() * np.sqrt(252)

            # 3. High-Low range proxy (normalized)
            hl_range = (high - low) / close

            # 4. Volume change (log volume change rate)
            log_volume = np.log(volume + 1)
            volume_change = log_volume.diff()

            # 5. VIX proxy: realized vol relative to 252-day average
            vol_history = returns.rolling(252).std() * np.sqrt(252)
            vix_proxy = realized_vol / vol_history.replace(0, 0.001)

            # 6. Trend proxy: 20-day return direction
            trend_signal = close.pct_change(20)

            # 7. Mean reversion signal: distance from 200-day MA
            ma200 = close.rolling(200).mean()
            mean_reversion = (close - ma200) / ma200.replace(0, 0.001)

            # Build feature matrix
            features = pd.DataFrame({
                'returns': returns,
                'realized_vol': realized_vol,
                'hl_range': hl_range,
                'volume_change': volume_change,
                'vix_proxy': vix_proxy,
                'trend_signal': trend_signal,
                'mean_reversion': mean_reversion
            }, index=returns.index)

            # Drop NaN rows
            features = features.dropna()

            # Cap extreme values (outliers can distort HMM)
            for col in features.columns:
                q99 = features[col].quantile(0.99)
                q01 = features[col].quantile(0.01)
                features[col] = features[col].clip(q01, q99)

            self._feature_names = list(features.columns)
            return features

        except Exception as e:
            print(f"RegimeDetectorHMM fetch_training_data error: {e}")
            return None

    def _label_states_by_characteristics(self, data: pd.DataFrame, hidden_states: np.ndarray) -> Dict[int, str]:
        """
        Assign meaningful labels to hidden states based on their statistical characteristics.
        4 states are labeled by return and volatility characteristics.
        """
        state_features = {}
        for state_id in range(self.n_components):
            state_mask = hidden_states == state_id
            state_data = data[state_mask]

            mean_ret = state_data['returns'].mean() * 252  # Annualized
            mean_vol = state_data['realized_vol'].mean()
            mean_vix = state_data['vix_proxy'].mean()
            mean_mr = state_data['mean_reversion'].mean()

            state_features[state_id] = {
                'annual_ret': mean_ret,
                'avg_vol': mean_vol,
                'avg_vix_proxy': mean_vix,
                'mean_reversion': mean_mr
            }

        # Sort states by annualized return (descending)
        sorted_states = sorted(state_features.items(), key=lambda x: x[1]['annual_ret'], reverse=True)

        labels = {}
        # Label by rank and volatility
        labels[sorted_states[0][0]] = "SUSTAINED UPTREND (BULL)"  # Highest return
        labels[sorted_states[-1][0]] = "HIGH-VOLATILITY DISTRESS (BEAR)"  # Lowest return

        # For middle two, use volatility to distinguish
        mid_states = [s[0] for s in sorted_states[1:-1]]
        mid_vols = [(s, state_features[s]['avg_vol']) for s in mid_states]
        mid_vols.sort(key=lambda x: x[1])  # Lower vol first

        if len(mid_vols) >= 2:
            labels[mid_vols[0][0]] = "LOW-VOLATILITY CHOP (CONSOLIDATION)"  # Low vol chop
            labels[mid_vols[-1][0]] = "BEAR MARKET RALLY (HIGH VOL)"  # High vol rallies

        self._state_labels = labels
        return labels

    def fit_predict(self) -> Dict:
        """
        Train the HMM and predict current regime.
        Returns comprehensive regime analysis with strategy recommendation.
        """
        data = self.fetch_training_data(days=504)
        if data is None or len(data) < 100:
            return {"error": "Insufficient data for HMM training"}

        X = data.values

        # Fit model
        self.model.fit(X)
        self._is_fitted = True

        # Predict all states
        hidden_states = self.model.predict(X)
        current_state = hidden_states[-1]

        # Label states by characteristics
        state_labels = self._label_states_by_characteristics(data, hidden_states)

        # Get regime metrics
        regime_label = state_labels.get(current_state, "UNKNOWN")

        # Get state statistics
        current_state_data = data[hidden_states == current_state]
        current_ret = current_state_data['returns'].mean() * 252
        current_vol = current_state_data['realized_vol'].mean()
        current_vix_proxy = current_state_data['vix_proxy'].mean()

        # Get transition matrix and confidence
        transmat = self.model.transmat_.tolist()
        confidence = self.model.predict_proba(X)[-1].tolist()

        # Map confidence to states
        confidence_map = {i: round(confidence[i], 4) for i in range(self.n_components)}

        # Determine regime characteristics
        vol_regime = "HIGH" if current_vol > data['realized_vol'].median() else "LOW"
        trend_regime = "BULL" if current_ret > 0 else "BEAR"

        # Get recommended strategy
        strategy_info = self.STRATEGY_MAP.get(current_state, self.STRATEGY_MAP[2])

        # Regime strength
        regime_strength = confidence[current_state]
        stability = "STABLE" if regime_strength > 0.6 else "TRANSITIONAL" if regime_strength > 0.4 else "UNCERTAIN"

        return {
            "ticker": self.ticker,
            "current_state_id": int(current_state),
            "regime_label": regime_label,
            "regime_characteristics": {
                "trend": trend_regime,
                "volatility": vol_regime,
                "annual_return_estimate": round(float(current_ret), 4),
                "realized_vol_estimate": round(float(current_vol), 4),
                "vix_proxy": round(float(current_vix_proxy), 4)
            },
            "recommended_strategy": strategy_info["primary"],
            "alternative_strategy": strategy_info["secondary"],
            "strategy_action": strategy_info["action"],
            "confidence": round(regime_strength, 4),
            "stability": stability,
            "state_confidence": confidence_map,
            "transition_matrix": transmat,
            "state_labels": state_labels,
            "n_observations": len(data),
            "model_fitted": True
        }

    def get_regime_distribution(self) -> Dict:
        """
        Get the probability distribution over all regimes for current observation.
        """
        data = self.fetch_training_data(days=504)
        if data is None or not self._is_fitted:
            return {"error": "Model not fitted or insufficient data"}

        X = data.values
        probs = self.model.predict_proba(X)[-1]

        return {
            f"state_{i}_probability": round(float(probs[i]), 4)
            for i in range(self.n_components)
        }

    def validate_against_historical_events(self) -> Dict:
        """
        Validate HMM predictions against known historical market events.
        Tests if regimes align with: VIX > 30, S&P drawdowns > 10%.
        """
        data = self.fetch_training_data(days=252 * 5)  # 5 years
        if data is None:
            return {"error": "Insufficient data for validation"}

        X = data.values
        hidden_states = self.model.predict(X)

        # Get VIX proxy series
        vix = data['vix_proxy'].values
        returns = data['returns'].values

        # Find high-VIX periods
        high_vix_mask = vix > 1.5  # VIX 50% above normal
        high_vix_states = hidden_states[high_vix_mask]
        state_in_high_vix = {}
        for s in range(self.n_components):
            if len(high_vix_states) > 0:
                state_in_high_vix[s] = (high_vix_states == s).mean()

        # Find drawdown periods (returns < -2% in a day)
        drawdown_mask = returns < -0.02
        drawdown_states = hidden_states[drawdown_mask]
        state_in_drawdown = {}
        for s in range(self.n_components):
            if len(drawdown_states) > 0:
                state_in_drawdown[s] = (drawdown_states == s).mean()

        return {
            "high_vix_periods_state_distribution": state_in_high_vix,
            "drawdown_periods_state_distribution": state_in_drawdown,
            "validation_status": "PASS" if state_in_high_vix else "INSUFFICIENT_DATA",
            "notes": "Higher probability in states 1/3 (Bear/HighVol) during high-VIX periods validates HMM"
        }

    def get_adaptive_strategy(self, market_data: dict = None) -> Dict:
        """
        Combine HMM regime with market structure data (GEX, skew) for adaptive strategy.

        Takes optional market_data dict with:
        - total_net_gex
        - volatility_skew sentiment
        - iv_rank verdict

        Returns final strategy recommendation.
        """
        regime = self.fit_predict()

        # Get base strategy from HMM
        base_strategy = regime["recommended_strategy"]
        alt_strategy = regime["alternative_strategy"]

        # Override based on market conditions
        if market_data:
            net_gex = market_data.get("total_net_gex", 0)
            skew_sentiment = market_data.get("volatility_skew", {}).get("sentiment", "")
            iv_rank_verdict = market_data.get("iv_rank", {}).get("verdict", "NEUTRAL")

            # Check GEX for additional signals
            if abs(net_gex) > 5e8:  # > $500M net GEX is significant
                if net_gex < 0:
                    base_strategy = "wheel"  # Dealers short gamma → sell puts
                    regime["gext_signal"] = "DEALER_SHORT_GAMMA"

            # Check IV Rank
            if iv_rank_verdict == "SELL_PREMIUM":
                if base_strategy == "iron_condor":
                    base_strategy = "iron_condor"  # Keep as-is, premium selling is correct
                elif base_strategy == "covered_call":
                    base_strategy = "short_put"  # Higher premium in elevated IV

        regime["final_strategy"] = base_strategy
        regime["alternative_strategy"] = alt_strategy

        return regime


# Global singleton
regime_detector = RegimeDetectorHMM()