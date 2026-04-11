from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
from datetime import datetime

class OptionsFetcher:
    """
    Data Specialist component for fetching real-time options chain data.
    """
    
    @staticmethod
    def get_options_expiration_dates(ticker: str) -> List[str]:
        tk = yf.Ticker(ticker)
        try:
            return tk.options
        except Exception as e:
            print(f"Error fetching options expirations for {ticker}: {e}")
            return []

    @staticmethod
    def get_options_chain(ticker: str, expiration_date: str) -> Dict[str, pd.DataFrame]:
        """
        Returns calls and puts DataFrames for a specific expiration.
        """
        tk = yf.Ticker(ticker)
        try:
            opt = tk.option_chain(expiration_date)
            return {
                "calls": opt.calls,
                "puts": opt.puts
            }
        except Exception as e:
            print(f"Error fetching options chain for {ticker} on {expiration_date}: {e}")
            return {}

    @staticmethod
    def get_current_price(ticker: str) -> float:
        try:
            tk = yf.Ticker(ticker)
            # Use fast info or history for robustness
            history = tk.history(period="1d")
            return float(history["Close"].iloc[-1])
        except Exception as e:
            print(f"Error fetching current price for {ticker}: {e}")
            return 0.0
