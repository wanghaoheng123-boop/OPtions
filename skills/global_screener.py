import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class GlobalScreener:
    """
    Acts as the top-level Discovery engine. Instead of searching, this module proactively 
    scans a predefined universe of diverse, hyper-liquid institutional assets and ranks them.
    """
    
    # Predefined universe of liquidity and volatility
    UNIVERSE = {
        "Equities": ["AAPL", "NVDA", "TSLA", "META", "AMZN"],
        "Commodities": ["GLD", "SLV", "USO", "UNG", "DBA"],
        "Macro / Rates": ["SPY", "QQQ", "IWM", "TLT", "HYG"]
    }

    @classmethod
    def run_daily_sweep(cls):
        """
        Calculates simple momentum, standard deviation, and identifies actionable anomalies.
        """
        opportunities = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        flat_tickers = [tkr for cat in cls.UNIVERSE.values() for tkr in cat]
        
        try:
            # Batch fetch to bypass massive rate delays
            data = yf.download(flat_tickers, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)['Close']
        except Exception as e:
            return {"error": "Failed to pull base universe data"}
            
        for category, tickers in cls.UNIVERSE.items():
            for tkr in tickers:
                if tkr not in data.columns:
                    continue
                    
                series = data[tkr].dropna()
                if len(series) < 20: continue
                
                current = float(series.iloc[-1])
                rolling_mean_20 = series.rolling(20).mean()
                std_20 = series.rolling(20).std()
                
                current_mean = float(rolling_mean_20.iloc[-1])
                current_std = float(std_20.iloc[-1])
                
                if current_std == 0: continue
                
                # Deviation from 20-Day baseline
                z_score = (current - current_mean) / current_std
                
                # Classify Opportunity based on structural edges
                thesis = ""
                action = ""
                urgency = "LOW"
                
                if z_score > 2.5:
                    thesis = f"Extremely Overextended (Z: +{z_score:.2f}). Mean-reversion probability high. IV likely inflated."
                    action = "SELL PREMIUM / PUT SPREAD"
                    urgency = "HIGH"
                elif z_score < -2.5:
                    thesis = f"Panic Sold (Z: {z_score:.2f}). Dealer short gamma trap likely. Premium rich."
                    action = "SELL PUTS / WHEEL"
                    urgency = "CRITICAL"
                elif abs(z_score) < 0.5:
                    thesis = f"Consolidating at mean. Options historically underpriced here."
                    action = "LONG STRADDLE / CONDOR"
                    urgency = "MEDIUM"
                else:
                    # Skip boring middle zones entirely in the screener
                    continue 
                    
                opportunities.append({
                    "ticker": tkr,
                    "category": category,
                    "current_price": round(current, 2),
                    "z_score": round(z_score, 2),
                    "thesis": thesis,
                    "action": action,
                    "urgency": urgency,
                    "score": abs(z_score) # Rank by extremity
                })
                
        # Sort by most mathematically extreme edges
        opportunities = sorted(opportunities, key=lambda x: x["score"], reverse=True)
        return {"top_opportunities": opportunities[:8]} # Return top 8 best edges
