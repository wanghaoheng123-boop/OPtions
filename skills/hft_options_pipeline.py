import time
import random
from typing import Any, Dict

import numpy as np
import pandas as pd


class HFTOptionsPipeline:
    """
    Phase 11 Institutional Engine: High-Frequency Options Microstructure.
    Calculates pure mathematically derived Black-Scholes Greeks to assemble
    the live Gamma Exposure (GEX) surfaces needed to detect Call/Put walls.
    """
    
    @staticmethod
    def calc_gamma(S, K, T, r, sigma):
        """
        True Black-Scholes Gamma Calculation.
        S = Spot, K = Strike, T = Time to Exp (Yrs), r = Risk Free, sigma = Implied Volatility
        """
        # Safety for zero values
        if T <= 0 or sigma <= 0:
            return 0.0
            
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        pdf_d1 = (np.exp(-0.5 * d1 ** 2)) / np.sqrt(2 * np.pi)
        gamma = pdf_d1 / (S * sigma * np.sqrt(T))
        return float(gamma)

    @classmethod
    def generate_live_gex_surface(cls, spot_price=500.0) -> dict:
        """
        Generates a 1-second refresh real-time representation of massive Open Interest imbalances.
        Simulating 20 strikes around ATM with dynamic mathematical Greek updates.
        """
        strikes = np.arange(spot_price - 50, spot_price + 55, 5)
        T = 30 / 365.0  # 30 DTE
        r = 0.04        # 4% Risk Free
        
        gex_profile = []
        call_gex_total = 0
        put_gex_total = 0
        
        for K in strikes:
            # Simulating Volatility Smile (IV increases further away from ATM)
            distance_from_spot = abs(K - spot_price)
            iv = 0.15 + (distance_from_spot * 0.002) + random.uniform(-0.01, 0.01)
            
            # Gamma peaks ATM
            gamma = cls.calc_gamma(spot_price, K, T, r, iv)
            
            # Simulating Market Maker Open Interest (Heaviest at round numbers and OTM)
            call_oi = int(10000 * (1 / (distance_from_spot + 1))) + random.randint(1000, 50000)
            put_oi = int(12000 * (1 / (distance_from_spot + 1))) + random.randint(1000, 60000)
            
            if K % 10 == 0: 
                call_oi *= 2 # Massive strike concentration
                put_oi *= 2
                
            # GEX Formula: Open Interest * Gamma * Contract Multiplier (100) * Spot
            call_gex = call_oi * gamma * 100 * spot_price
            put_gex = -1 * put_oi * gamma * 100 * spot_price # Puts act as negative dealer gamma
            
            net_gex = call_gex + put_gex
            call_gex_total += call_gex
            put_gex_total += put_gex
            
            gex_profile.append({
                "strike": float(K),
                "call_gex": float(call_gex / 1e6), # In millions
                "put_gex": float(put_gex / 1e6),
                "net_gex": float(net_gex / 1e6)
            })
            
        # Determine strict Institutional Walls
        sorted_by_positive = sorted(gex_profile, key=lambda x: x["net_gex"], reverse=True)
        sorted_by_negative = sorted(gex_profile, key=lambda x: x["net_gex"])
        
        call_wall = sorted_by_positive[0]["strike"]
        put_wall = sorted_by_negative[0]["strike"]
        
        dealer_tilt = "Long Gamma" if call_gex_total > abs(put_gex_total) else "Short Gamma"

        return {
            "timestamp": time.time(),
            "spot_price": spot_price,
            "call_wall": call_wall,
            "put_wall": put_wall,
            "dealer_tilt": dealer_tilt,
            "total_call_gex_m": round(call_gex_total / 1e6, 2),
            "total_put_gex_m": round(put_gex_total / 1e6, 2),
            "strikes": gex_profile,
            "source": "simulated",
        }

    @classmethod
    def from_option_chain(
        cls,
        calls_df: pd.DataFrame,
        puts_df: pd.DataFrame,
        spot_price: float,
    ) -> Dict[str, Any]:
        """
        Build the same GEX payload shape as ``generate_live_gex_surface`` using
        live chain OI and Black-Scholes gammas (``calc_gamma``).
        """
        from skills.gamma_exposure import MarketStructureAnalyzer

        if calls_df is None or puts_df is None or calls_df.empty or puts_df.empty:
            return {"error": "Missing options chain", "spot_price": spot_price, "strikes": []}

        calls = calls_df.copy()
        puts = puts_df.copy()
        for col, default in (("openInterest", 0), ("calc_gamma", 0.0)):
            if col not in calls.columns:
                calls[col] = default
            if col not in puts.columns:
                puts[col] = default

        calls["openInterest"] = pd.to_numeric(calls["openInterest"], errors="coerce").fillna(0)
        puts["openInterest"] = pd.to_numeric(puts["openInterest"], errors="coerce").fillna(0)

        ms = MarketStructureAnalyzer.calculate_gamma_exposure(calls, puts, spot_price)
        if ms.get("error"):
            return {"error": ms["error"], "spot_price": spot_price, "strikes": []}

        calls["CallGEX"] = calls["calc_gamma"] * calls["openInterest"] * 100 * spot_price
        puts["PutGEX"] = puts["calc_gamma"] * puts["openInterest"] * 100 * spot_price * -1

        call_gex_total = float(calls["CallGEX"].sum())
        put_gex_total = float(puts["PutGEX"].sum())

        all_strikes = sorted(
            set(calls["strike"].astype(float).tolist()) | set(puts["strike"].astype(float).tolist())
        )
        gex_profile = []
        for K in all_strikes:
            cg = float(calls.loc[calls["strike"] == K, "CallGEX"].sum())
            pg = float(puts.loc[puts["strike"] == K, "PutGEX"].sum())
            net = cg + pg
            gex_profile.append(
                {
                    "strike": float(K),
                    "call_gex": round(cg / 1e6, 4),
                    "put_gex": round(pg / 1e6, 4),
                    "net_gex": round(net / 1e6, 4),
                }
            )

        dealer_tilt = ms.get("dealer_position_tilt", "Long Gamma")

        return {
            "timestamp": time.time(),
            "spot_price": float(spot_price),
            "call_wall": float(ms["call_wall_strike"]),
            "put_wall": float(ms["put_wall_strike"]),
            "dealer_tilt": dealer_tilt,
            "total_call_gex_m": round(call_gex_total / 1e6, 2),
            "total_put_gex_m": round(put_gex_total / 1e6, 2),
            "strikes": gex_profile,
            "source": "chain",
        }
