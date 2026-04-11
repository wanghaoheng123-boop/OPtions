import numpy as np
import pandas as pd
import yfinance as yf
from hmmlearn.hmm import GaussianHMM
import warnings
warnings.filterwarnings("ignore")

class RegimeDetectorHMM:
    """
    Phase 10 Institutional Engine: Hidden Markov Model (HMM) Regime Detection
    Instead of relying purely on VIX thresholds, this uses unsupervised learning
    to mathematically cluster recent price action into Hidden Regimes.
    """
    def __init__(self, ticker="SPY", n_components=3):
        self.ticker = ticker
        self.n_components = n_components # Default: Bull, Bear, Chop
        self.model = GaussianHMM(n_components=self.n_components, covariance_type="full", n_iter=100)

    def fetch_training_data(self, days=365):
        try:
            df = yf.download(self.ticker, period=f"{days}d", progress=False)
            if df.empty: return None
            
            # We train the HMM on Daily Returns and Volatility Proxy (High-Low spread)
            df['Returns'] = df['Close'].pct_change()
            df['Range'] = (df['High'] - df['Low']) / df['Close']
            df = df.dropna()
            
            return df[['Returns', 'Range']]
        except Exception as e:
            return None

    def fit_predict(self):
        """
        Trains the Gaussian HMM and identifies the Current Regime.
        """
        data = self.fetch_training_data(days=252) # 1 Year of trading days
        if data is None or len(data) < 50:
            return {"error": "Insufficient data"}
            
        X = data.values
        self.model.fit(X)
        
        # Predict the hidden states for the entire sequence
        hidden_states = self.model.predict(X)
        current_state = hidden_states[-1]
        
        # Analyze state characteristics to label them logically
        state_metrics = []
        for i in range(self.n_components):
            state_data = data[hidden_states == i]
            mean_ret = state_data['Returns'].mean() * 252 # Annualized
            mean_vol = state_data['Range'].mean() * np.sqrt(252)
            state_metrics.append({"state": i, "ret": mean_ret, "vol": mean_vol})
            
        # Simplistic labeling based on return/volatility characteristics
        sorted_by_ret = sorted(state_metrics, key=lambda x: x['ret'], reverse=True)
        bull_state = sorted_by_ret[0]['state']
        bear_state = sorted_by_ret[-1]['state']
        
        regime_label = "CHOP / CONSOLIDATION"
        if current_state == bull_state:
            regime_label = "SUSTAINED UPTREND (BULL)"
        elif current_state == bear_state:
            regime_label = "HIGH-VOLATILITY DISTRESS (BEAR)"
            
        return {
            "current_state_id": int(current_state),
            "regime_label": regime_label,
            "transition_matrix": self.model.transmat_.tolist(),
            "confidence_scores": self.model.predict_proba(X)[-1].tolist()
        }

# Example Usage:
# hmm = RegimeDetectorHMM("SPY")
# result = hmm.fit_predict()
