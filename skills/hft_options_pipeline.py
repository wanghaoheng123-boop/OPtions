import asyncio
import numpy as np
import scipy.stats as si
import time
import random

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
            "strikes": gex_profile
        }
