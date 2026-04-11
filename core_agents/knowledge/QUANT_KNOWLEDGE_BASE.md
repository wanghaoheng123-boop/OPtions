# Algorithmic Trading Knowledge Base: The 80% Expectancy Protocol

> **CRITICAL DIRECTIVE FOR ALL AGENTS:** 
> You MUST conform your logic to the following quantitative mechanics. Naive "directional" trading or delta-1 tracking (buying calls/puts) results in a structural ~45-50% win rate and negative expectancy over time due to premium decay. To achieve an 80%+ win rate, all proposed strategies MUST be mathematically structured as **Net Volatility Sellers**.

## I. Structural Edge: Volatility Risk Premium (VRP)
The single greatest, mathematically persistent edge in quantitative options trading is the Volatility Risk Premium. Historically, **Implied Volatility (IV) overstates Realized Volatility (RV) roughly 85% of the time.** 
- Options are priced as insurance. You must act as the insurance company.
- **Rule:** Never buy premium when IV Rank > 50. Always sell premium.

## II. High-Probability Topologies (80%+ Target)

### 1. Iron Condors & Strangles (The Core Engine)
- **Mechanics:** Sell a 16-delta (1 Standard Deviation) OTM Put, and sell a 16-delta OTM Call. 
- **Win Rate:** Statistically provides a ~68.2% baseline win rate via normal distribution, scaling to 80%+ when combined with IV Mean Reversion.
- **Agent Instruction:** Default to non-directional Iron Condors when the Volatility Skew is neutral and IV Rank is high.

### 2. The 'Wheel' / Cash-Secured Puts
- **Mechanics:** Selling 30-delta puts on fundamentally sound indices (SPY, QQQ) during market drawdowns. If assigned, selling Covered Calls.
- **Agent Instruction:** Only deploy during high "Fear" volatility skews, acting as the liquidity provider to panic sellers.

## III. Mandatory Backtesting & Verification Methodology
To ensure no hallucinations or overfitting, the Backtester Agent MUST enforce the following constraints:
1. **Out-of-Sample Verification:** The backtest must run 70% of historical data as "In-Sample", and 30% as "Out-Of-Sample" to prevent curve-fitting.
2. **Profit Factor over Win Rate:** An 80% win rate is useless if the Profit Factor (Gross Profit / Gross Loss) is < 1.0. The Critic Agent must reject any strategy with a Profit Factor below `1.2`.
3. **Strict Exit Rules:** High probability strategies have terrible risk/reward profiles (risking $10 to make $1).
   - **Take Profit:** Automatically close short options at 50% of maximum profit to eliminate tail risk.
   - **Stop Loss:** Automatically close short options at 200% loss of initial credit received.

## IV. Statistical Arbitrage & Mean Reversion (StatArb)
While Volatility Selling generates foundational yield, **Statistical Arbitrage** exploits structural inefficiencies between cointegrated assets (e.g., XLK vs QQQ) to generate uncorrelated edge.
1. **Cointegration over Correlation:** Do not trade highly correlated assets if they frequently diverge permanently. Only trade pairs that demonstrably snap back to a zero-mean spread.
2. **The Z-Score Trigger:** 
   - Wait for the price ratio (Spread) between two cointegrated indices to hit a `Z-Score > +2.0` or `< -2.0`.
   - **Math:** `Z = (Current Spread - Mean Spread) / Standard Deviation of Spread`
3. **Execution Mechanics:** When `Z > 2.0`, the system must short the overperforming leg and buy the underperforming leg. The Critic must reject any pairs trade that lacks a historical Z-score reversion rate above 80%.

## V. Institutional Machine Learning (Advances in Financial Machine Learning)
Based on research from Marcos Lopez de Prado and leading GitHub quant repositories (e.g., `mlfinlab`), traditional quantitative models often fail due to structural flaws in data processing and labeling. Agents must adhere to the following when structuring predictive models:

1. **Information-Driven Bars (Data Retrieval Path):**
   - **Flaw:** Standard Time-bars (e.g., Daily OHLC) oversample low-activity periods and undersample high-activity periods, destroying statistical normality.
   - **Solution:** Agents must eventually request data transitioned into **Dollar Bars** or **Volume Bars**, where a new "candle" is only formed after a certain amount of capital or volume has traded.
2. **The Triple Barrier Method (TBM):**
   - **Flaw:** Labeling a return based purely on a fixed time horizon (e.g., "return in 5 days") ignores the path the price took (it could have crashed before recovering).
   - **Solution:** Set 3 dynamic barriers based on current Implied Volatility:
     - Upper Barrier (Take Profit)
     - Lower Barrier (Stop Loss)
     - Vertical Barrier (Maximum Time Holding)
     The first barrier touched becomes the label.
3. **Meta-Labeling (Sizing Engine):**
   - **Flaw:** Primary quantitative models (like Mean Reversion) are prone to false positives in shifting regimes.
   - **Solution:** Run a secondary Machine Learning classifier (like Random Forest) that only decides **HOW MUCH** to bet (0 to 1). If the secondary model predicts the primary model will be wrong, the bet size is 0.
4. **Fractional Differencing:**
   - Instead of using raw percentages (which destroys 100% of price memory), use fractional derivatives to make price data stationary for ML while retaining the structural memory of the asset.

## VI. Core Directives for System Refactoring
- **Trader Agent:** Must ONLY propose strategies outlined in Section II and Section IV.
- **Critic Agent:** Must reject any backtest that does not explicitly cap risk or violates the `1.2` Profit Factor rule.
- **Risk System:** Position sizing must not exceed `Kelly / 2`, mathematically capping ruin probabilities.
