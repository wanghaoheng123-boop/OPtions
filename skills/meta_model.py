import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class MetaLabeler:
    """
    AFML Meta-Labeling Engine.
    
    Instead of predicting the primary trade direction, this model predicts whether the 
    primary quantitative model (like the Triple Barrier backtester) will be correct.
    It returns a continuous probability (0 to 1) representing the optimal bet size.
    """
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
        
    def train_meta_model(self, market_features: pd.DataFrame, primary_model_pnls: list):
        """
        Trains the meta-model on historical features.
        The target label (Y) is 1 if the primary model made money, and 0 if it lost money.
        """
        # Ensure we have aligned lengths
        cutoff = min(len(market_features), len(primary_model_pnls))
        X = market_features.iloc[-cutoff:]
        
        # Meta Labels: 1 if profitable, 0 if loss
        y = np.where(np.array(primary_model_pnls[-cutoff:]) > 0, 1, 0)
        
        # Train model
        if len(np.unique(y)) > 1: # Require both wins and losses to train a split
            self.model.fit(X, y)
            return True
        return False

    def get_bet_size(self, current_features: np.ndarray) -> float:
        """
        Predicts if the current market regime will result in a successful primary trade.
        Returns the probability (0.0 to 1.0).
        If probability < 0.50, we should aggressively zero out the allocation.
        """
        try:
            # Predict Prob returns [prob_0, prob_1]
            probas = self.model.predict_proba(current_features.reshape(1, -1))[0]
            prob_success = probas[1]
            return float(prob_success)
        except Exception:
            # If the model failed to train or lacks variance, fallback to 1.0 (neutral meta-weight)
            return 1.0
