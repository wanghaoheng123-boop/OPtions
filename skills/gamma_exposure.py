import pandas as pd
from typing import Dict, Any

class MarketStructureAnalyzer:
    """
    Calculates macro options levels such as Call Walls, Put Walls, and Net Gamma Exposure.
    Crucial element of the Market Maker / Quant Agent's reasoning loop.
    """
    
    @staticmethod
    def calculate_gamma_exposure(calls_df: pd.DataFrame, puts_df: pd.DataFrame, spot_price: float) -> Dict[str, Any]:
        """
        Assumes calls_df and puts_df possess 'openInterest', 'strike', and 'calc_gamma'
        GEX logic: Calls are positive gamma for MMs, Puts are negative gamma.
        (Actually, standard convention: Market makers are short calls (so they sell calls, retail buys), 
        which means as market goes up, MM gets shorter delta, so MM Gamma is negative. But here we stick to
        absolute exposure Open Interest * Gamma * 100 * Spot to find macro levels).
        """
        
        if calls_df.empty or puts_df.empty:
            return {"error": "Missing options data"}
            
        calls = calls_df.copy()
        puts = puts_df.copy()
        
        # Spot * Gamma * Open Interest * 100 (contract factor)
        # Using Spot * Gamma or just Gamma * OI is a common approximation for GEX.
        calls['CallGEX'] = calls['calc_gamma'] * calls['openInterest'] * 100 * spot_price
        puts['PutGEX'] = puts['calc_gamma'] * puts['openInterest'] * 100 * spot_price * -1 # Puts given negative sign for visualization
        
        call_wall_idx = calls['CallGEX'].idxmax()
        put_wall_idx = puts['PutGEX'].idxmin() # Minimum because put GEX is negative
        
        call_wall_strike = float(calls.loc[call_wall_idx, 'strike'])
        put_wall_strike = float(puts.loc[put_wall_idx, 'strike'])
        
        total_market_gex = float(calls['CallGEX'].sum() + puts['PutGEX'].sum())
        
        return {
            "spot_price": spot_price,
            "call_wall_strike": call_wall_strike,
            "call_wall_gex": float(calls.loc[call_wall_idx, 'CallGEX']),
            "put_wall_strike": put_wall_strike,
            "put_wall_gex": float(puts.loc[put_wall_idx, 'PutGEX']),
            "total_net_gex": total_market_gex,
            "dealer_position_tilt": "Long Gamma" if total_market_gex > 0 else "Short Gamma"
        }
