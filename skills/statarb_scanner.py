import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class StatArbScanner:
    """
    Statistical Arbitrage & Pairs Trading Engine
    Calculates the Z-Score of the pricing spread between highly cointegrated assets.
    """
    
    DEFAULT_PAIRS = [
        ("SPY", "QQQ"),   # Broad vs Tech
        ("XLK", "XLV"),   # Tech vs Healthcare
        ("IWM", "SPY"),   # Small Cap vs Large Cap
        ("XLF", "XLE"),   # Financials vs Energy
        ("GLD", "SLV")    # Gold vs Silver
    ]
    
    @classmethod
    def scan_pairs(cls, pairs: list = None, days: int = 90) -> list:
        if pairs is None:
            pairs = cls.DEFAULT_PAIRS
            
        results = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Batch download all tickers for efficiency
        all_tickers = list(set([ticker for pair in pairs for ticker in pair]))
        try:
            # Download adjusted close for accurate ratio math
            data = yf.download(all_tickers, start=start_str, end=end_str, progress=False)['Close']
        except Exception as e:
            return [{"error": str(e)}]
        
        # Handle single ticker return structure dynamically
        if isinstance(data, pd.Series):
             return [{"error": "YFinance failed to batch return matrix."}]
             
        for pair in pairs:
            leg_1, leg_2 = pair
            try:
                # Ensure data exists for both
                if leg_1 not in data.columns or leg_2 not in data.columns:
                    continue
                    
                series_1 = data[leg_1].dropna()
                series_2 = data[leg_2].dropna()
                
                # Align dates
                aligned = pd.concat([series_1, series_2], axis=1, join='inner').dropna()
                aligned.columns = [leg_1, leg_2]
                
                if len(aligned) < 20: 
                    continue # Not enough data to calculate a valid spread
                
                # Calculate Spread Math (Ratio)
                # Spread = Leg_1 / Leg_2
                spread = aligned[leg_1] / aligned[leg_2]
                
                mean_spread = spread.mean()
                std_spread = spread.std()
                current_spread = spread.iloc[-1]
                
                # Z-Score = (Current - Mean) / StdDev
                if pd.isna(std_spread) or std_spread == 0:
                    z_score = 0.0
                else:
                    z_score = (current_spread - mean_spread) / std_spread
                
                # Calculate Sentiment Action based on AFML rules
                action = "HOLD"
                if z_score > 2.0:
                    action = f"SHORT {leg_1} / BUY {leg_2}"
                elif z_score < -2.0:
                    action = f"BUY {leg_1} / SHORT {leg_2}"
                    
                results.append({
                    "pair": f"{leg_1}/{leg_2}",
                    "leg_1": leg_1,
                    "leg_2": leg_2,
                    "z_score": round(float(z_score), 2),
                    "mean_spread": round(float(mean_spread), 4),
                    "current_spread": round(float(current_spread), 4),
                    "action": action
                })
                
            except Exception as e:
                # Silently skip failed pairs (e.g. delists)
                continue
                
        # Sort by absolute Z-Score descending (most extreme divergence first)
        results = sorted(results, key=lambda x: abs(x['z_score']), reverse=True)
        return results
