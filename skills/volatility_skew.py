import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional


class VolatilitySkewAnalyzer:
    """
    Calculates the Options Volatility Skew to ascertain hidden institutional market sentiment.
    Formula: IV of 5% OTM Put - IV of 5% OTM Call.
    Positive Skew indicates market makers are charging high premiums for crash protection (Fear).

    Also implements IV Rank and IV Percentile — critical for QUANT_KB Rule 1:
    "Never buy premium when IV Rank > 50. Always sell premium."
    """

    def calculate_skew(calls: pd.DataFrame, puts: pd.DataFrame, spot_price: float,
                       lookback_days: int = 20) -> dict:
        """
        Calculate IV skew with sentiment classification.
        Also computes IV Rank and IV Percentile over lookback period.
        """
        try:
            # Drop invalid IVs
            valid_calls = calls[(calls['impliedVolatility'] > 0) & (calls['impliedVolatility'] < 3.0)]
            valid_puts = puts[(puts['impliedVolatility'] > 0) & (puts['impliedVolatility'] < 3.0)]

            if valid_calls.empty or valid_puts.empty:
                return {
                    "volatility_skew_index": 0.0,
                    "sentiment": "Neutral (Insufficient Data)",
                    "iv_rank": None,
                    "iv_percentile": None,
                    "iv_current": None
                }

            # Locate 5% OTM Strikes
            target_otm_call_strike = spot_price * 1.05
            target_otm_put_strike = spot_price * 0.95

            # Find the closest strike to the targets
            otm_call = valid_calls.iloc[(valid_calls['strike'] - target_otm_call_strike).abs().argsort()[:1]]
            otm_put = valid_puts.iloc[(valid_puts['strike'] - target_otm_put_strike).abs().argsort()[:1]]

            call_iv = otm_call['impliedVolatility'].values[0] if not otm_call.empty else 0
            put_iv = otm_put['impliedVolatility'].values[0] if not otm_put.empty else 0

            # Skew Index: How much more expensive is downside protection vs upside speculation?
            skew = put_iv - call_iv
            skew_rounded = round(float(skew) * 100, 2)  # convert to IV percentage points

            # Analytical translation
            if skew_rounded > 5.0:
                sentiment = "Extreme Fear (High Skew)"
            elif skew_rounded > 1.0:
                sentiment = "Bearish Protection (Moderate Skew)"
            elif skew_rounded < -1.0:
                sentiment = "Bullish Greed (Call Skew)"
            else:
                sentiment = "Neutral Skew"

            return {
                "volatility_skew_index": skew_rounded,
                "sentiment": sentiment,
                "otm_put_iv": round(float(put_iv) * 100, 2),
                "otm_call_iv": round(float(call_iv) * 100, 2),
                "spot_price": spot_price,
                "iv_current": round(float(call_iv + put_iv) / 2 * 100, 2),
                "iv_rank": None,  # Computed separately via get_iv_rank
                "iv_percentile": None
            }
        except Exception as e:
            print(f"Error calculating IV Skew: {e}")
            return {
                "volatility_skew_index": 0.0,
                "sentiment": "Error calculating skew",
                "iv_rank": None,
                "iv_percentile": None,
                "iv_current": None
            }

    @staticmethod
    def get_iv_rank(ticker: str, lookback_days: int = 252) -> Optional[dict]:
        """
        Calculate IV Rank:
        IV Rank = (Current IV - Lowest IV over lookback) / (Highest IV - Lowest IV over lookback) * 100

        IV Rank measures where the current IV sits relative to its range over the lookback period.
        IV Rank > 50 means IV is historically elevated → sell premium (QUANT_KB Rule 1)
        IV Rank < 30 means IV is historically depressed → buy premium (rare opportunities)

        Uses ATM options IV as the reference point.
        """
        try:
            tk = yf.Ticker(ticker)
            current_price = tk.history(period="1d")["Close"].iloc[-1]
        except Exception:
            return None

        # Fetch 1 year of option chain expirations to find ATM IV
        try:
            expirations = tk.options
            if not expirations:
                return None

            # Collect ATM IV from nearest 4 expirations for stability
            atm_ivs = []
            for expiry in expirations[:4]:
                try:
                    chain = tk.option_chain(expiry)
                    calls = chain.calls
                    puts = chain.puts

                    # Find ATM strike (closest to current price)
                    all_strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
                    atm_strike = min(all_strikes, key=lambda s: abs(s - current_price))

                    # Get IV at ATM strike
                    atm_call_iv = calls[calls['strike'] == atm_strike]['impliedVolatility'].values
                    atm_put_iv = puts[puts['strike'] == atm_strike]['impliedVolatility'].values

                    if len(atm_call_iv) > 0 and atm_call_iv[0] > 0:
                        atm_ivs.append(atm_call_iv[0])
                    if len(atm_put_iv) > 0 and atm_put_iv[0] > 0:
                        atm_ivs.append(atm_put_iv[0])
                except Exception:
                    continue

            if len(atm_ivs) < 2:
                return None

            current_iv = np.mean(atm_ivs)

            # For historical IV, we approximate from past ATM IVs
            # In production, would use OptionsAPI historical data
            # Here we simulate via a 20-day rolling IV approximation from past 2 years
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)

            try:
                hist = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'),
                                   end=end_date.strftime('%Y-%m-%d'), progress=False)
                if len(hist) < 20:
                    return None

                # Approximate IV from historical price volatility
                # Use rolling 20-day returns to estimate realized vol, then annualize
                close_prices = hist['Close']
                if isinstance(close_prices, pd.DataFrame):
                    close_prices = close_prices.iloc[:, 0]

                returns = close_prices.pct_change().dropna()
                rolling_vol = returns.rolling(20).std() * np.sqrt(252)  # Annualized

                # Current realized vol vs range over lookback
                current_realized_vol = float(rolling_vol.iloc[-1])
                historical_low = float(rolling_vol.min())
                historical_high = float(rolling_vol.max())

                # Map realized vol to a range — for approximation
                # Realized vol is typically lower than IV, so scale by 1.2x as IV proxy
                iv_low = historical_low * 1.2
                iv_high = historical_high * 1.2
                iv_range = iv_high - iv_low

                if iv_range <= 0:
                    return None

                iv_rank = ((current_iv - iv_low) / iv_range) * 100

                return {
                    "ticker": ticker,
                    "iv_current": round(current_iv * 100, 2),
                    "iv_rank": round(iv_rank, 1),
                    "iv_low": round(iv_low * 100, 2),
                    "iv_high": round(iv_high * 100, 2),
                    "lookback_days": lookback_days,
                    "verdict": "SELL_PREMIUM" if iv_rank > 50 else ("BUY_PREMIUM" if iv_rank < 30 else "NEUTRAL"),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception:
                return None

        except Exception:
            return None

    @staticmethod
    def get_iv_percentile(ticker: str, lookback_days: int = 252) -> Optional[dict]:
        """
        Calculate IV Percentile:
        IV Percentile = % of days in lookback where IV was below current IV.

        This is more robust than IV Rank because it isn't affected by extreme outliers.
        IV Percentile > 50 means IV is elevated relative to most days → sell premium
        IV Percentile < 30 means IV is depressed relative to most days → buy premium
        """
        try:
            tk = yf.Ticker(ticker)
            current_price = tk.history(period="1d")["Close"].iloc[-1]
            expirations = tk.options

            if not expirations:
                return None

            # Get current ATM IV
            atm_ivs = []
            for expiry in expirations[:4]:
                try:
                    chain = tk.option_chain(expiry)
                    calls = chain.calls
                    puts = chain.puts

                    all_strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
                    atm_strike = min(all_strikes, key=lambda s: abs(s - current_price))

                    atm_call_iv = calls[calls['strike'] == atm_strike]['impliedVolatility'].values
                    atm_put_iv = puts[puts['strike'] == atm_strike]['impliedVolatility'].values

                    if len(atm_call_iv) > 0 and atm_call_iv[0] > 0:
                        atm_ivs.append(atm_call_iv[0])
                    if len(atm_put_iv) > 0 and atm_put_iv[0] > 0:
                        atm_ivs.append(atm_put_iv[0])
                except Exception:
                    continue

            if len(atm_ivs) < 2:
                return None

            current_iv = np.mean(atm_ivs)

            # Calculate IV percentile from historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)

            try:
                hist = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'),
                                   end=end_date.strftime('%Y-%m-%d'), progress=False)
                if len(hist) < 20:
                    return None

                close_prices = hist['Close']
                if isinstance(close_prices, pd.DataFrame):
                    close_prices = close_prices.iloc[:, 0]

                returns = close_prices.pct_change().dropna()
                rolling_vol = returns.rolling(20).std() * np.sqrt(252) * 1.2  # Scale to IV proxy

                # Calculate percentile: % of observations below current IV
                iv_series = rolling_vol.dropna()
                if len(iv_series) < 10:
                    return None

                iv_below_current = (iv_series < current_iv).sum()
                iv_percentile = (iv_below_current / len(iv_series)) * 100

                return {
                    "ticker": ticker,
                    "iv_current": round(current_iv * 100, 2),
                    "iv_percentile": round(iv_percentile, 1),
                    "days_above_current": int(len(iv_series) - iv_below_current),
                    "total_days": int(len(iv_series)),
                    "lookback_days": lookback_days,
                    "verdict": "SELL_PREMIUM" if iv_percentile > 50 else ("BUY_PREMIUM" if iv_percentile < 30 else "NEUTRAL"),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception:
                return None

        except Exception:
            return None

    @classmethod
    def full_volatility_analysis(cls, calls: pd.DataFrame, puts: pd.DataFrame,
                                  spot_price: float, ticker: str,
                                  lookback_days: int = 252) -> dict:
        """
        Combined analysis: IV Skew + IV Rank + IV Percentile.
        This is the primary entry point for institutional volatility analysis.
        """
        skew_data = cls.calculate_skew(calls, puts, spot_price)
        iv_rank_data = cls.get_iv_rank(ticker, lookback_days)
        iv_percentile_data = cls.get_iv_percentile(ticker, lookback_days)

        # Aggregate verdict
        verdicts = []
        if iv_rank_data:
            verdicts.append(iv_rank_data["verdict"])
        if iv_percentile_data:
            verdicts.append(iv_percentile_data["verdict"])

        # If any metric says sell premium, that's the dominant signal
        if "SELL_PREMIUM" in verdicts:
            aggregate_verdict = "SELL_PREMIUM"
        elif "BUY_PREMIUM" in verdicts:
            aggregate_verdict = "BUY_PREMIUM"
        else:
            aggregate_verdict = "NEUTRAL"

        return {
            "ticker": ticker,
            "spot_price": spot_price,
            "volatility_skew": skew_data,
            "iv_rank": iv_rank_data,
            "iv_percentile": iv_percentile_data,
            "aggregate_verdict": aggregate_verdict,
            "recommendation": cls._generate_recommendation(skew_data, iv_rank_data, iv_percentile_data)
        }

    @staticmethod
    def _generate_recommendation(skew_data: dict, iv_rank_data: Optional[dict],
                                 iv_percentile_data: Optional[dict]) -> str:
        """Generate a human-readable recommendation string."""
        sentiment = skew_data.get("sentiment", "Neutral")

        rank_verdict = iv_rank_data.get("verdict", "NEUTRAL") if iv_rank_data else "NEUTRAL"
        percentile_verdict = iv_percentile_data.get("verdict", "NEUTRAL") if iv_percentile_data else "NEUTRAL"

        parts = []
        if rank_verdict == "SELL_PREMIUM" or percentile_verdict == "SELL_PREMIUM":
            parts.append("SELL premium (elevated IV)")
        elif rank_verdict == "BUY_PREMIUM" or percentile_verdict == "BUY_PREMIUM":
            parts.append("BUY premium (depressed IV)")
        else:
            parts.append("Neutral volatility regime")

        if "Fear" in sentiment:
            parts.append("Extreme Fear sentiment — wheel/covered call preferred")
        elif "Greed" in sentiment:
            parts.append("Bullish Greed — consider iron condor")
        elif "Bearish" in sentiment:
            parts.append("Bearish protection skew — cash-secured puts")

        return ". ".join(parts)