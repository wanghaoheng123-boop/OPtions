import numpy as np
import pandas as pd
import scipy.stats as si

class GreeksCalculator:
    """
    Quantitative Analysis Agent calculation module.
    Responsible for deterministic, rigorous calculation of Black-Scholes variables.
    No LLM Hallucinations allowed here.
    """
    
    @staticmethod
    def _d1(S, K, T, r, sigma):
        return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    @staticmethod
    def _d2(S, K, T, r, sigma):
        return (np.log(S / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    @classmethod
    def call_delta(cls, S, K, T, r, sigma):
        T = max(T, 0.0001) # Avoid div by zero
        return si.norm.cdf(cls._d1(S, K, T, r, sigma))
    
    @classmethod
    def put_delta(cls, S, K, T, r, sigma):
        T = max(T, 0.0001)
        return cls.call_delta(S, K, T, r, sigma) - 1.0
    
    @classmethod
    def gamma(cls, S, K, T, r, sigma):
        T = max(T, 0.0001)
        return si.norm.pdf(cls._d1(S, K, T, r, sigma)) / (S * sigma * np.sqrt(T))
    
    @classmethod
    def vega(cls, S, K, T, r, sigma):
        T = max(T, 0.0001)
        return S * si.norm.pdf(cls._d1(S, K, T, r, sigma)) * np.sqrt(T)

    @classmethod
    def attach_greeks_to_chain(cls, df: pd.DataFrame, current_price: float, risk_free_rate: float, time_to_expiry_years: float, option_type: str = 'call') -> pd.DataFrame:
        """
        Attaches calculated rigorous greeks rather than relying merely on data source estimations.
        Requires columns 'strike' and 'impliedVolatility'
        """
        if df.empty or 'strike' not in df.columns or 'impliedVolatility' not in df.columns:
            return df
        
        df = df.copy()
        
        S = current_price
        r = risk_free_rate
        T = time_to_expiry_years
        
        def safe_calc_greeks(row):
            K = row['strike']
            sigma = row['impliedVolatility']
            
            # Avoid division errors if IV is extremely near 0 or K is anomalous
            if sigma <= 0.01: sigma = 0.01
            
            try:
                gamma = cls.gamma(S, K, T, r, sigma)
                vega = cls.vega(S, K, T, r, sigma)
                if option_type == 'call':
                    delta = cls.call_delta(S, K, T, r, sigma)
                else:
                    delta = cls.put_delta(S, K, T, r, sigma)
                return pd.Series({'calc_delta': delta, 'calc_gamma': gamma, 'calc_vega': vega})
            except Exception:
                return pd.Series({'calc_delta': 0, 'calc_gamma': 0, 'calc_vega': 0})
        
        greeks_series = df.apply(safe_calc_greeks, axis=1)
        return pd.concat([df, greeks_series], axis=1)
