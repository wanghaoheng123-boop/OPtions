import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

class StrategyBacktester:
    """
    AP Specialist Programmatic Backtesting Module.
    Ensures that any strategy proposed by the Trader Agent is historically vetted before approval.
    """
    
    @staticmethod
    def run_historical_backtest(ticker: str, strategy_type: str, days: int = 90) -> dict:
        """
        Runs a vectorized historical backtest for a given strategy.
        Supported strategies: 'short_put', 'covered_call', 'long_gamma'.
        This uses basic daily OHLCV data as a proxy for options success since historical
        intraday options chains are extremely heavy/expensive to fetch without API keys.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            hist = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
            if hist.empty:
                return {"error": "Failed to pull historical data for backtesting."}
                
            # Flatten multi-index columns if downloaded from newer yfinance versions
            univariate = False
            if isinstance(hist.columns, pd.MultiIndex):
                try:
                    hist = hist.xs(ticker, axis=1, level=1)
                except Exception:
                    univariate = True
            
            # Use 'Close' column
            close_prices = hist['Close']
            returns = close_prices.pct_change().dropna()
            
            # 1. Implement Out-of-Sample Split (70% In-Sampe, 30% Out-Of-Sample)
            split_idx = int(len(returns) * 0.70)
            in_sample_ret = returns[:split_idx]
            out_sample_ret = returns[split_idx:]
            in_sample_prices = close_prices[:split_idx]
            out_sample_prices = close_prices[split_idx:]
            
            # --- TRIPLE BARRIER METHOD (AFML) ---
            # Dynamically calc rolling volatility (EWMA) for barrier widths
            volatility = out_sample_ret.ewm(span=20).std().fillna(out_sample_ret.std())
            
            daily_pnl = []
            gross_profit = 0.0
            gross_loss = 0.0
            win_count = 0
            
            std_dev = in_sample_ret.std() * np.sqrt(252) # Annualized volatility

            # TBM Horizon (Time Barrier)
            t_horizon = 5 
            
            for i in range(len(out_sample_ret) - t_horizon):
                current_price = out_sample_prices.iloc[i]
                current_vol = volatility.iloc[i]
                
                # Dynamic Barriers based on current volatility
                if strategy_type in ['short_put', 'wheel']:
                    pt_barrier = current_price * (1 + (current_vol * 0.5)) # Take Profit
                    sl_barrier = current_price * (1 - (current_vol * 1.5)) # Stop Loss (wider for selling)
                elif strategy_type in ['iron_condor', 'short_strangle']:
                    pt_barrier = current_price * (1 + (current_vol * 0.8))
                    sl_barrier = current_price * (1 - (current_vol * 1.2)) # Two-sided boundaries
                else:
                    pt_barrier = current_price * (1 + (current_vol * 1.0))
                    sl_barrier = current_price * (1 - (current_vol * 1.0))

                # Walk forward to find first barrier touched
                hit_barrier = "time"
                pnl = 0.0
                
                for j in range(1, t_horizon + 1):
                    future_price = out_sample_prices.iloc[i + j]
                    
                    if strategy_type in ['short_put', 'wheel', 'covered_call']:
                        # Selling put -> want price to stay flat or go up.
                        # Breaches SL if price crashes.
                        if future_price < sl_barrier:
                            hit_barrier = "sl"
                            pnl = -1.5 # 1.5R Loss
                            break
                        # Hits PT if price rises
                        elif future_price > pt_barrier:
                            hit_barrier = "pt"
                            pnl = 0.5 # 0.5R Gain
                            break
                            
                    elif strategy_type in ['iron_condor', 'short_strangle']:
                        # Both directions represent danger
                        if future_price > pt_barrier or future_price < sl_barrier:
                            hit_barrier = "sl" # Wing breached
                            pnl = -1.2
                            break

                # Resolve Time Barrier if bounds not breached
                if hit_barrier == "time":
                    if strategy_type in ['short_put', 'wheel', 'iron_condor', 'short_strangle']:
                        # Net seller: time decay captured
                        pnl = 0.5 
                    else:
                        future_price = out_sample_prices.iloc[i + t_horizon]
                        pnl = (future_price - current_price) / current_price * 100
                        
                daily_pnl.append(pnl)
                if pnl > 0:
                    win_count += 1
                    gross_profit += pnl
                else:
                    gross_loss += abs(pnl)
            total_pnl = sum(daily_pnl)
            win_rate = (win_count / len(daily_pnl)) * 100 if daily_pnl else 0
            
            # Calculate Max Drawdown
            cumulative = np.cumsum(daily_pnl)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = running_max - cumulative
            max_drawdown = float(drawdowns.max()) if len(drawdowns) > 0 else 0.0
            
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999.0
            
            # Strict Critic Hardware Constraint
            verdict = "PASS" if (win_rate >= 75.0 and profit_factor >= 1.2 and max_drawdown < 20.0) else "FAIL"
            
            return {
                "strategy_tested": strategy_type,
                "days_tested": days,
                "win_rate_percent": round(win_rate, 2),
                "profit_factor": round(profit_factor, 2),
                "total_pnl_proxy": round(total_pnl, 2),
                "max_drawdown": round(max_drawdown, 2),
                "out_of_sample_verified": True,
                "verdict": verdict
            }
            
        except Exception as e:
            return {"error": str(e)}

