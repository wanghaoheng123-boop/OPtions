from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
import logging
from skills.data_resilience import retry_operation

logger = logging.getLogger(__name__)


class OptionsFetcher:
    """
    Data Specialist component for fetching real-time options chain data.
    """
    
    @staticmethod
    def get_options_expiration_dates(ticker: str) -> List[str]:
        try:
            tk = yf.Ticker(ticker)
            return retry_operation("get_options_expiration_dates", lambda: tk.options)
        except Exception as e:
            logger.warning("Options expirations unavailable for %s: %s", ticker, e)
            return []

    @staticmethod
    def get_options_chain(ticker: str, expiration_date: str) -> Dict[str, pd.DataFrame]:
        """
        Returns calls and puts DataFrames for a specific expiration.
        """
        try:
            tk = yf.Ticker(ticker)
            opt = retry_operation("get_options_chain", lambda: tk.option_chain(expiration_date))
            if opt.calls is None or opt.puts is None:
                logger.warning("Options chain missing calls/puts for %s %s", ticker, expiration_date)
                return {}
            return {
                "calls": opt.calls,
                "puts": opt.puts
            }
        except Exception as e:
            logger.warning("Error fetching options chain for %s on %s: %s", ticker, expiration_date, e)
            return {}

    @staticmethod
    def get_current_price(ticker: str) -> float:
        try:
            tk = yf.Ticker(ticker)
            history = retry_operation("get_current_price_history", lambda: tk.history(period="1d"))
            if history.empty or "Close" not in history.columns:
                logger.warning("Current price history empty/missing close for %s", ticker)
                return 0.0
            return float(history["Close"].iloc[-1])
        except Exception as e:
            logger.warning("Error fetching current price for %s: %s", ticker, e)
            return 0.0
