import os
from fredapi import Fred
from dotenv import load_dotenv
import pandas as pd

# Automatically read from a local .env file
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))

class MacroFetcher:
    """
    Ingests Federal Reserve Economic Data (FRED) mirroring institutional macro feeds.
    Provides complete historical capabilities via the official `fredapi` repository.
    """
    def __init__(self):
        self.api_key = os.getenv("FRED_API_KEY", None)
        self.fred = Fred(api_key=self.api_key) if self.api_key else None

    def search_macro_database(self, query: str):
        """
        Searches the Federal Reserve registry for matching economic data.
        Example: "GDP", "Inflation", "Mortgage Returns"
        """
        if not self.fred:
            return {"error": "FRED_API_KEY_MISSING", "message": "Please configure your FRED API Key in the .env file."}
        
        try:
            # Returns a pandas DataFrame of search results
            df = self.fred.search(query)
            if df.empty:
                return []
            
            df = df.head(50) # Limit to top 50 results
            results = []
            for id, row in df.iterrows():
                results.append({
                    "id": id,
                    "title": row.get('title', 'Unknown'),
                    "frequency": row.get('frequency', 'Unknown'),
                    "observation_start": str(row.get('observation_start', '')),
                    "observation_end": str(row.get('observation_end', '')),
                    "popularity": row.get('popularity', 0)
                })
            
            # Sort by popularity descending
            results = sorted(results, key=lambda x: x["popularity"], reverse=True)
            return results
        except Exception as e:
            return {"error": "FRED_API_ERROR", "message": str(e)}

    def get_historical_series(self, series_id: str):
        """
        Returns full historical data for a specific Federal Reserve code formatted for TradingView charts.
        """
        if not self.fred:
            return {"error": "FRED_API_KEY_MISSING", "message": "Please configure your FRED API Key in the .env file."}
        
        try:
            series = self.fred.get_series(series_id)
            if series.empty:
                return []
                
            # series index is datetime, values are floats. Drop NaNs
            series = series.dropna()
            
            formatted_data = []
            for date, val in series.items():
                formatted_data.append({
                    "time": date.strftime('%Y-%m-%d'),
                    "value": float(val)
                })
            return formatted_data
        except Exception as e:
            return {"error": "FRED_API_ERROR", "message": str(e)}
            
    def get_latest_macro_indicators(self):
        """
        Fallback simple panel view. Mocked if key is missing.
        """
        if not self.fred:
            return {"error": "FRED_API_KEY_MISSING", "DGS10": 4.25, "SOFR": 5.30, "CPIAUCSL_YoY": 3.1}
            
        try:
            dgs10 = self.fred.get_series('DGS10').dropna().iloc[-1]
            sofr = self.fred.get_series('SOFR').dropna().iloc[-1]
            cpi = self.fred.get_series('CPIAUCSL').dropna()
            cpi_yoy = ((cpi.iloc[-1] - cpi.iloc[-13]) / cpi.iloc[-13]) * 100
            
            return {
                "DGS10": round(dgs10, 2),
                "SOFR": round(sofr, 2),
                "CPIAUCSL_YoY": round(cpi_yoy, 2)
            }
        except:
             return {"error": "FRED_API_KEY_MISSING", "DGS10": 4.25, "SOFR": 5.30, "CPIAUCSL_YoY": 3.1}

macro_client = MacroFetcher()
