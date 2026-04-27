from typing import List, Dict, Any
import yfinance as yf
import pandas as pd
import logging
import time

logger = logging.getLogger(__name__)


def _retry(op_name: str, fn, attempts: int = 3, delay_s: float = 0.4):
    last_err = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_err = exc
            if i < attempts - 1:
                time.sleep(delay_s * (i + 1))
    raise RuntimeError(f"{op_name} failed after {attempts} attempts: {last_err}") from last_err

class OptionsFetcher:
    """
    Data Specialist component for fetching real-time options chain data.
    """
    
    @staticmethod
    def get_options_expiration_dates(ticker: str) -> List[str]:
        try:
            tk = yf.Ticker(ticker)
            return _retry("get_options_expiration_dates", lambda: tk.options)
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
            opt = _retry("get_options_chain", lambda: tk.option_chain(expiration_date))
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
            history = _retry("get_current_price_history", lambda: tk.history(period="1d"))
            if history.empty or "Close" not in history.columns:
                logger.warning("Current price history empty/missing close for %s", ticker)
                return 0.0
            return float(history["Close"].iloc[-1])
        except Exception as e:
            logger.warning("Error fetching current price for %s: %s", ticker, e)
            return 0.0
