import yfinance as yf
import pandas as pd
import logging
from skills.data_resilience import retry_operation

logger = logging.getLogger(__name__)


class MarketDataAPI:
    """
    Expansion module handling Global Search, OHLCV for TradingView, and Sector Heatmap Proxy.
    """
    
    SECTOR_ETFS = {
        "Technology": "XLK",
        "Financials": "XLF",
        "Consumer Discr": "XLY",
        "Healthcare": "XLV",
        "Energy": "XLE",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Real Estate": "XLRE"
    }

    @staticmethod
    def get_ohlcv(ticker: str, period="3mo", interval="1d") -> list:
        """
        Returns JSON formatted OHLCV data for TradingView's lightweight-charts.
        """
        try:
            tk = yf.Ticker(ticker)
            df = retry_operation(
                "get_ohlcv_history",
                lambda: tk.history(period=period, interval=interval, timeout=8),
            )
            if df.empty:
                return []
            
            # TradingView format: { time: 'yyyy-mm-dd', open, high, low, close }
            df = df.reset_index()
            # Normalize column names in case yfinance changes index names
            date_col = 'Date' if 'Date' in df.columns else 'Datetime'
            required_cols = {"Open", "High", "Low", "Close", "Volume", date_col}
            if not required_cols.issubset(df.columns):
                logger.warning("OHLCV missing required columns for %s: %s", ticker, sorted(df.columns))
                return []
            
            def _f(x):
                try:
                    v = float(x)
                    return v if v == v else 0.0  # NaN -> 0
                except (TypeError, ValueError):
                    return 0.0

            formatted_data = []
            for _, row in df.iterrows():
                formatted_data.append({
                    "time": row[date_col].strftime('%Y-%m-%d'),
                    "open": _f(row["Open"]),
                    "high": _f(row["High"]),
                    "low": _f(row["Low"]),
                    "close": _f(row["Close"]),
                    "value": _f(row["Volume"]),
                })
            return formatted_data
        except Exception as e:
            logger.warning("Error fetching OHLCV for %s: %s", ticker, e)
            return []

    @classmethod
    def get_sector_heatmap(cls) -> list:
        """
        Fetches 1D performance of major Sector ETFs to construct a fast Heatmap proxy.
        """
        tickers = list(cls.SECTOR_ETFS.values())
        try:
            downloaded = retry_operation(
                "get_sector_heatmap_download",
                lambda: yf.download(tickers, period="5d", progress=False, timeout=8),
            )
            if "Close" not in downloaded:
                logger.warning("Heatmap close column missing")
                return []
            data = downloaded["Close"]
            returns = data.pct_change().iloc[-1] * 100 # percentage
            
            heatmap_data = []
            for sector_name, ticker in cls.SECTOR_ETFS.items():
                val = returns.get(ticker, 0.0)
                heatmap_data.append({
                    "id": sector_name,
                    "ticker": ticker,
                    "performance": round(float(val), 2)
                })
            return heatmap_data
        except Exception as e:
            logger.warning("Error fetching Heatmap: %s", e)
            return []
