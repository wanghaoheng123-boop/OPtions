import pandas as pd
import numpy as np

class VolatilitySkewAnalyzer:
    """
    Calculates the Options Volatility Skew to ascertain hidden institutional market sentiment.
    Formula: IV of 5% OTM Put - IV of 5% OTM Call.
    Positive Skew indicates market makers are charging high premiums for crash protection (Fear).
    """

    @staticmethod
    def calculate_skew(calls: pd.DataFrame, puts: pd.DataFrame, spot_price: float) -> dict:
        try:
            # Drop invalid IVs
            valid_calls = calls[(calls['impliedVolatility'] > 0) & (calls['impliedVolatility'] < 3.0)]
            valid_puts = puts[(puts['impliedVolatility'] > 0) & (puts['impliedVolatility'] < 3.0)]

            if valid_calls.empty or valid_puts.empty:
                return {"volatility_skew_index": 0.0, "sentiment": "Neutral (Insufficient Data)"}

            # Locate 5% OTM Strikes
            target_otm_call_strike = spot_price * 1.05
            target_otm_put_strike = spot_price * 0.95

            # Find the closest strike to the targets
            otm_call = valid_calls.iloc[(valid_calls['strike'] - target_otm_call_strike).abs().argsort()[:1]]
            otm_put = valid_puts.iloc[(valid_puts['strike'] - target_otm_put_strike).abs().argsort()[:1]]

            call_iv = otm_call['impliedVolatility'].values[0] if not otm_call.empty else 0
            put_iv = otm_put['impliedVolatility'].values[0] if not otm_put.empty else 0

            # Skew Index: How much more expensive is downside protection vs upside speculation?
            # Expressed in absolute volatility points
            skew = put_iv - call_iv
            skew_rounded = round(float(skew) * 100, 2) # convert to IV percentage points

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
                "otm_put_iv": round(float(put_iv)*100, 2),
                "otm_call_iv": round(float(call_iv)*100, 2)
            }
        except Exception as e:
            print(f"Error calculating IV Skew: {e}")
            return {"volatility_skew_index": 0.0, "sentiment": "Error calculating skew"}
