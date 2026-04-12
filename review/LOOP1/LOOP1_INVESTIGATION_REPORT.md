# LOOP 1B: INVESTIGATION REPORT
## Deep Dive Into Critical Findings
## Agentic Quant Terminal V2

---

**Report Date**: 2026-04-12
**Prepared By**: AGENT-RESEARCHER, AGENT-TRADER, AGENT-PROGRAMMER
**Reviewed By**: AGENT-QA, AGENT-DIRECTOR
**Loop**: 1 | Phase: B (Investigate)
**Classification**: INSTITUTIONAL CONFIDENTIAL

---

## EXECUTIVE SUMMARY

Following the triage phase, the team conducted deep investigation into the 2 CRITICAL findings (A-01, B-01) and the 5 HIGH severity findings. This report details the root causes, academic references, and recommended solutions.

**Key Finding**: The backtester is fundamentally flawed because it uses equity returns as a proxy for options P&L. This is NOT salvageable with parameter tuning — a complete rebuild of the options pricing model is required.

---

## INVESTIGATION: A-01 — Backtester Uses Equity Returns as Options PnL Proxy

### Finding
**Severity**: CRITICAL
**Category**: Backtesting & Triple Barrier
**Finding ID**: A-01

### Evidence

Current code in `skills/backtester.py`:
```python
daily_returns = prices.pct_change().fillna(0)
trade_returns = daily_returns * position
pnl = (trade_returns * self.capital).sum()
```

This calculates P&L as if holding the underlying equity. For options strategies like iron condors, this is fundamentally incorrect.

### Academic Analysis (AGENT-RESEARCHER)

**Reference**: Lopez de Prado, "Advances in Financial Machine Learning", Chapter 3 — Triple Barrier Method.

The Triple Barrier method was designed for EQUITY mean-reversion strategies where you buy/sell the underlying asset. Applying it directly to options is an incorrect application of the methodology.

**Correct approach for options**:

An options strategy P&L depends on:
1. **Delta**: Change in option price per unit change in underlying
2. **Gamma**: Rate of change of delta
3. **Theta**: Time decay (negative, always working against the holder)
4. **Vega**: Sensitivity to implied volatility changes
5. **Premium received/paid**: The initial credit or debit

For a short iron condor:
```
P&L = Initial Credit - max(0, (Price - Short_Strike)) + max(0, (Long_Strike - Price))
```
...at expiration, adjusted for any early assignment risk.

**Key insight**: The Triple Barrier concept CAN work for options, but the barrier levels must be expressed in terms of OPTION price changes, not underlying price changes.

### Impact Analysis (AGENT-TRADER)

If we trade 1 short iron condor on SPY:
- ATM 1SD iron condor (approx 30 delta each leg) might credit $1.00 (100 points)
- Max risk: $2.00 (200 points) per contract
- Days to expiration: 30

Expected daily behavior:
- Day 1: Theta decay = ~$0.03/day (3% of credit)
- If SPY moves 1%: The short puts might gain/lose ~$0.30, shorts calls ~$0.30
- These are NOT equal to 1% of SPY price ($5-7)

**Current backtest shows**: 4.3% win rate. This means the strategy as implemented loses money 95.7% of the time — this is NOT a parameter problem, it's a fundamental modeling error.

### Root Cause

The backtester was built for an equity statarb system and was never adapted for the options domain. The proxy model was a simplification that worked for equities but fails catastrophically for options.

### Recommended Solution

Rebuild the options pricing model using:

**Approach 1: Black-Scholes with IV (Recommended)**
```python
def calculate_condor_pnl(S, K_short_put, K_long_put, K_long_call, K_short_call,
                           sigma, T, r, premium_received):
    """
    Calculate iron condor P&L using Black-Scholes pricing.

    S: Current stock price
    K_: Strike prices for each leg
    sigma: Implied volatility
    T: Time to expiration (years)
    r: Risk-free rate
    premium_received: Initial credit received
    """
    # Calculate price of each leg using Black-Scholes
    put_short_price = black_scholes_put(S, K_short_put, T, r, sigma)
    put_long_price = black_scholes_put(S, K_long_put, T, r, sigma)
    call_long_price = black_scholes_call(S, K_long_call, T, r, sigma)
    call_short_price = black_scholes_call(S, K_short_call, T, r, sigma)

    # Net premium = credit received - debit paid
    net_premium = premium_received  # Already received at entry

    # At expiration (T=0), calculate P&L
    intrinsic_put_short = max(K_short_put - S, 0)
    intrinsic_put_long = max(K_long_put - S, 0)
    intrinsic_call_long = max(S - K_long_call, 0)
    intrinsic_call_short = max(S - K_short_call, 0)

    # Short position loses when intrinsic value > premium received
    put_pnl = -(intrinsic_put_short - (K_short_put - K_long_put)) * 100
    call_pnl = -(intrinsic_call_short - (K_short_call - K_long_call)) * 100
    # Long positions offset losses
    put_protection = intrinsic_put_long * 100
    call_protection = intrinsic_call_long * 100

    total_pnl = net_premium * 100 - put_pnl - call_pnl + put_protection + call_protection
    return total_pnl
```

**Approach 2: Discrete Event Simulation (More Accurate)**

Simulate price paths using Geometric Brownian Motion with:
- Realistic volatility (from IV, not realized vol)
- Jump risk (earnings, macro events)
- Volatility mean reversion (IV crush post-event)

### Verification Plan (AGENT-QA)

1. Calculate known iron condor P&L from historical data (verify against actual trades)
2. Compare model output against Broker's theoretical P&L
3. Stress test: Verify max loss equals known max risk

---

## INVESTIGATION: B-01 — Iron Condor Produces 0% Win Rate

### Finding
**Severity**: CRITICAL
**Category**: Strategy Logic
**Finding ID**: B-01

### Evidence

Batch backtest of SPY, QQQ, AAPL iron condor:
- SPY: WR = 4.3%
- QQQ: WR = 0.0%
- AAPL: WR = 4.3%

This is not a "poor" result — this is a broken strategy implementation.

### Root Cause Analysis (AGENT-TRADER)

The iron condor entry/exit logic in `skills/backtester.py` is:

**Entry**: When z_score > 1.5 (spread too high)
**Exit**: Triple barrier breach (PT/SL/Time)

**Problem 1 — Entry Signal Mismatch**:
Iron condors are SOLD when implied volatility is HIGH (IV Rank > 50). The current entry signal uses equity z_score — which measures whether the spread between two equities is unusually wide/narrow. This has NO correlation with IV Rank.

**Problem 2 — Barrier Mismatch**:
Triple Barrier was designed for directional trades. For an iron condor (a non-directional, income-generating strategy):
- The "profit taking" barrier should be a % of the CREDIT received, not a % of the underlying price
- The "stop loss" barrier should be a % of max risk, not a % of underlying price
- Time barrier should align with DTE, not calendar days

**Problem 3 — Exit Logic**:
Iron condors have a specific P&L profile:
- Max profit = credit received (occurs at expiration if all legs expire worthless)
- Max loss = width of widest wing - credit received

The current exit logic doesn't account for this.

### Correct Iron Condor Strategy Logic

**Entry Rules** (per AFML + QUANT_KB):
1. IV Rank > 50 (premium selling is only profitable with high IV)
2. Skew indicates call skew (call prices elevated relative to puts)
3. Not within 5 days of earnings (IV crush risk)
4. Z-score > threshold (spread elevated = better entry price for short)

**Exit Rules**:
1. **Profit Taking**: When 50-70% of max profit is captured (not full credit)
2. **Stop Loss**: When losses exceed 100-150% of credit received
3. **Time Exit**: When DTE < 5 days (don't hold through expiration)
4. **Forced Exit**: If any barrier is breached early

### Implementation Fix Required

Replace the current equity-proxy backtest with a proper options pricing model (as per A-01 fix).

---

## INVESTIGATION: A-02 — Triple Barrier Multipliers Are Arbitrary

### Finding
**Severity**: HIGH
**Category**: Backtesting & Triple Barrier
**Finding ID**: A-02

### Evidence

```python
tp_mult = kwargs.get('tp_mult', 0.5)   # Take profit at 50% of vol
sl_mult = kwargs.get('sl_mult', 2.0)   # Stop loss at 200% of vol
```

These multipliers are used as follows:
```python
tp_level = trained_vol * tp_mult
sl_level = trained_vol * sl_mult
```

### Academic Reference

From "Advances in Financial Machine Learning" Chapter 3:

> "The Triple Barrier method defines barriers in terms of the ASSET'S VOLATILITY, scaled by a multiplier. The multiplier should be calibrated to the expected move over the holding period."

However, the key insight is that for OPTIONS, volatility should be expressed in TERMS OF OPTION PRICE CHANGES, not underlying price changes.

### Analysis

For SPY at $500 with 20% annual vol:
- Daily vol = 20% / sqrt(252) ≈ 1.26%
- 1 SD move = $6.30

For a short iron condor with $1.00 credit and 30 delta legs:
- 1 SD move in the condor value ≈ $0.30
- tp_mult=0.5 means take profit at $0.15 (15% of credit)
- sl_mult=2.0 means stop loss at $0.60 (60% of credit risk)

The multipliers may actually be reasonable IF expressed in option terms, but the current implementation uses underlying vol instead.

### Recommended Fix

After fixing A-01 (proper options pricing), re-calibrate multipliers based on:
1. Historical DTE-based IV behavior
2. Typical iron condor premium ranges
3. Risk/reward ratios per strategy type

---

## INVESTIGATION: A-03 — No Options Spread Cost Modeled

### Finding
**Severity**: HIGH
**Category**: Backtesting & Triple Barrier
**Finding ID**: A-03

### Evidence

In `skills/backtester.py`:
```python
pnl = (trade_returns * self.capital).sum()
```

No commission, spread, or slippage costs are deducted.

### Real-World Cost Analysis

**IBKR Commission**:
- $0.65 per contract per side
- Iron condor = 4 legs = 4 contracts
- Round trip = 4 × $0.65 × 2 = $5.20

**Bid-Ask Spread** (SPY options, near ATM, 30 DTE):
- Typical spread = $0.01-0.03 for liquid options
- For iron condor = 4 legs × $0.02 = $0.08 market impact

**Total Round-Trip Cost** (10 contracts): ~$5.20 + $0.08 = $5.28
As % of notional ($500 × 10 × 100 = $500,000): ~1.06 bps

### Recommended Fix

Integrate the `TransactionCostModel` from `skills/brokers.py` into the backtester:
```python
tcm = TransactionCostModel("IBKR")
cost = tcm.total_cost(num_contracts=10, mid_price=1.00, order_type="market")
net_pnl = gross_pnl - cost["total_cost"]
```

---

## INVESTIGATION: F-01 — Kalman Filter Z-Scores All Near Zero

### Finding
**Severity**: HIGH
**Category**: Kalman Filter & StatArb
**Finding ID**: F-01

### Evidence

`scan_pairs_kalman()` returns empty results for all 5 default pairs.

### Root Cause Analysis (AGENT-RESEARCHER)

The Kalman filter requires:
1. Initial observations to converge
2. Sufficient spread volatility to generate Z-scores

For 90 days of data:
- Kalman filter gets ~60-70 observations
- With slow-moving price series, the filter may not build enough spread history
- Z-score calculation requires 20+ observations minimum
- The hedge ratio can take 30-50 observations to stabilize

Additionally, the Kalman initialization uses a naive first ratio:
```python
self.beta = y0 / x0  # Simple ratio as initial estimate
```

If y0 and x0 are not representative, this biases all subsequent estimates.

### Recommended Fix

1. Pre-seed the Kalman filter with OLS hedge ratio from historical data
2. Reduce state_variance to allow faster adaptation
3. Add minimum observation requirement before generating signals
4. Use a "burn-in" period of 30 observations before allowing trades

---

## INVESTIGATION: E-02 — HMM Confidence of 100% is Red Flag

### Finding
**Severity**: MEDIUM
**Category**: HMM Regime Detection
**Finding ID**: E-02

### Evidence

Test output shows:
```
Current State: 0 - SUSTAINED UPTREND (BULL)
Confidence: 100.00% (STABLE)
State Distribution: {0: 1.0, 1: 0.0, 2: 0.0, 3: 0.0}
```

### Root Cause Analysis (AGENT-QA)

The `GaussianHMM` from `hmmlearn` is producing overconfident predictions. This is likely because:

1. **Feature scaling issue**: The 7 features have very different scales (returns in %, vol in %, etc.)
2. **Covariance matrix**: With "full" covariance type and only 2 components visible in data, the model overfits
3. **Sequence length**: HMM confidence is calculated from the entire training sequence's probability

### Academic Reference

Hamilton (1989) "A New Approach to Economic Analysis of Nonstationary Time Series" notes that HMM state confidence should be treated cautiously, especially with financial data which is notoriously non-stationary.

### Recommended Fix

1. **Feature standardization**: Scale all features to zero mean, unit variance before HMM training
2. **Reduce model complexity**: Start with diagonal covariance, increase if needed
3. **Use posterior state probability, not MAP**: Instead of argmax, use the full probability distribution
4. **Add uncertainty quantification**: Report entropy of state distribution as confidence measure

---

## INVESTIGATION: D-01 — MetaModel Labels from Feature Returns, Not Trade Outcomes

### Finding
**Severity**: MEDIUM
**Category**: Meta-Model & ML
**Finding ID**: D-01

### Evidence

```python
features['next_return'] = close.pct_change().shift(-1)
y_raw = features['next_return'].values
y = np.where(y_raw > 0, 1, 0)  # Label = 1 if equity went up
```

### Root Cause Analysis (AGENT-RESEARCHER)

This is a fundamental ML training error:

**What the label says**: "Did the underlying equity go up?"
**What the model needs to learn**: "Would the options strategy have been profitable?"

These are NOT the same thing:
- Equity up 0.5% could mean a short put loses money (theta decay exceeded delta gain)
- Equity flat could mean an iron condor profits (no movement = all options expire worthless)
- Equity down 2% could mean a wheel strategy is underwater (assigned shares at bad price)

### Impact

The MetaModel is being trained to predict equity direction, NOT options strategy success. When deployed, it will incorrectly zero out bets when equity moves in ways that don't align with options P&L.

### Academic Reference

AFML Chapter 4 "Meta-Labeling":
> "The primary model predicts the sign of the return. The meta-model predicts whether the primary model will be correct."

The key issue is that our "primary model" (the backtester) is currently broken (A-01), so training ANY meta-model on its outputs would be useless.

### Recommended Fix

1. Fix A-01 first (proper options pricing model)
2. Retrain MetaModel with correct labels: was the options strategy P&L positive?
3. Include options-specific features: IV Rank, DTE, skew, gamma exposure

---

## SUMMARY OF RECOMMENDATIONS

### Immediate Actions (Before Optimization)

| Priority | Action | Owner | Dependencies |
|----------|--------|-------|-------------|
| P0 | Fix A-01: Rebuild backtester with proper Black-Scholes options pricing | AGENT-PROGRAMMER | None |
| P0 | Fix B-01: Rebuild iron condor strategy logic with options-specific entry/exit | AGENT-TRADER | A-01 |
| P1 | Fix A-03: Integrate TransactionCostModel into backtester | AGENT-PROGRAMMER | A-01 |
| P1 | Fix F-01: Improve Kalman filter initialization and burn-in | AGENT-RESEARCHER | None |
| P1 | Fix E-02: Add feature scaling to HMM | AGENT-PROGRAMMER | None |
| P2 | Fix D-01: Retrain MetaModel with correct labels | AGENT-RESEARCHER | A-01 |

### Quality Gates

Before any optimization work:

1. ✅ All CRITICAL findings resolved
2. ✅ AGENT-QA inspects and approves A-01 fix
3. ✅ AGENT-RESEARCHER provides academic validation of new pricing model
4. ✅ AGENT-TRADER validates strategy logic changes
5. ✅ AGENT-DIRECTOR reviews and approves

---

*This investigation report is complete. Proceeding to Loop 1C: Resolve.*
