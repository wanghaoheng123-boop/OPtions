import yfinance as yf
import pandas as pd

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
            df = tk.history(period=period, interval=interval)
            if df.empty:
                return []
            
            # TradingView format: { time: 'yyyy-mm-dd', open, high, low, close }
            df = df.reset_index()
            # Normalize column names in case yfinance changes index names
            date_col = 'Date' if 'Date' in df.columns else 'Datetime'
            
            formatted_data = []
            for _, row in df.iterrows():
                formatted_data.append({
                    "time": row[date_col].strftime('%Y-%m-%d'),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "value": row["Volume"] # For volume overlay
                })
            return formatted_data
        except Exception as e:
            print(f"Error fetching OHLCV for {ticker}: {e}")
            return []

    @classmethod
    def get_sector_heatmap(cls) -> list:
        """
        Fetches 1D performance of major Sector ETFs to construct a fast Heatmap proxy.
        """
        tickers = list(cls.SECTOR_ETFS.values())
        try:
            data = yf.download(tickers, period="5d", progress=False)['Close']
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
            print(f"Error fetching Heatmap: {e}")
            return []
