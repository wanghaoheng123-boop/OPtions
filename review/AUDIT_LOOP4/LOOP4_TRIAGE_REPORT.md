# LOOP 4 — INDEPENDENT DATA AUDIT & ANTI-MANIPULATION REVIEW
## Phase A: Triage — Critical Issues Identified

---

**Report Date**: 2026-04-12
**Prepared By**: AGENT-DIRECTOR (Independent Audit)
**Reviewed By**: AGENT-QA, AGENT-RESEARCHER
**Loop**: 4 | Phase: A (Triage)
**Classification**: INSTITUTIONAL CONFIDENTIAL — INDEPENDENT AUDIT

---

## EXECUTIVE SUMMARY

Following concerns about data accuracy and potential backtest manipulation, the DIRECTOR ordered an independent audit of the previous Loop 3 results. **Critical issues were found that invalidate the previous results.**

The previous backtest showed:
- 26/26 tickers passing (100% pass rate)
- 91.4% average win rate
- 144.0 average profit factor
- $812,649 total P&L on $100K capital

**These results are likely inflated by 2-3x due to systematic errors in the backtester.**

---

## CRITICAL ISSUES IDENTIFIED

### ISSUE 1: VOLATILITY_PREMIUM = 2.5 Has No Empirical Basis (CRITICAL)

**Finding**: The code multiplies realized volatility by 2.5x to estimate IV:

```python
# Line 58, skills/backtester.py
VOLATILITY_PREMIUM = 2.5

# Line 297
iv = raw_iv * self.VOLATILITY_PREMIUM  # 18% realized → 45% IV!
```

**Problem**:
- For SPY with ~18% realized vol, this produces IV = 45%
- Real SPY ATM 45 DTE IV is typically 15-25%, not 45%
- At 45% IV, iron condor credits are 2-3x larger than real market credits
- This inflates every P&L calculation

**Evidence**:
- Real SPY iron condor (5-wide, 30-45 DTE): credit ≈ $1.50-2.00
- Backtested SPY iron condor at 45% IV: credit ≈ $4.00-6.00
- The entire 91.4% WR and $812K profit may be built on inflated credits

**Fix Required**: Either:
1. Remove the multiplier (use realized vol directly as IV proxy), OR
2. Calibrate against actual market IV data (CBOE VIX, broker API)

---

### ISSUE 2: trade_open Flag Never Gated Re-Entry (CRITICAL)

**Finding**: `trade_open` is set to `False` at initialization (line 285) but is NEVER set to `True` after entering a trade:

```python
# Line 285
trade_open = False

# Line 309-362: Entry logic inside "if not trade_open:" block
# After a trade is entered:
result = self._simulate_trade(price_path, iv, adaptive_dte, strikes, credit)
equity += result['pnl']
trades.append(result)
# trade_open is NEVER set to True here!
```

**Problem**:
- The backtest enters a NEW trade on EVERY day the previous trade closed
- There is no single-position enforcement
- This means MULTIPLE iron condors are open simultaneously
- Capital requirements are NOT properly calculated
- The equity curve is meaningless because it doesn't account for margin

**Example**:
- If max_hold_days = 40, and trades occur every 2-3 days
- There could be 15-20 simultaneous iron condors open
- Required margin: 20 × $2,000 (per condor) = $40,000+
- But the backtest only has $100,000 starting capital and doesn't track margin

**Fix Required**: Implement proper position tracking with single-position or margin-adjusted capital.

---

### ISSUE 3: Constant IV Throughout Trade Simulation (MEDIUM)

**Finding**: IV is captured once at entry and never updated during `_simulate_trade`:

```python
# Line 297: IV set once at entry
iv = raw_iv * self.VOLATILITY_PREMIUM

# Line 349: Passed to simulation
result = self._simulate_trade(price_path, iv, ...)

# Inside _simulate_trade (line 208+): Same iv used for all days
cur_sp = OptionsPricing.bs_put(S, strikes['short_put'], T, r, iv)  # iv is constant
```

**Problem**:
- If IV spikes from 20% to 35% mid-trade, the backtest doesn't capture it
- Long wings are undervalued at fixed IV (they gain value when IV rises)
- The strategy appears to work better than reality because unrealized gains are understated

**Fix**: Either update IV daily (EWMA-based) or document the conservative bias.

---

### ISSUE 4: Time Exit Calculation Bug (MEDIUM)

**Finding**: Line 229 uses inconsistent P&L formula for time exit:

```python
# Line 227-230 (time exit)
if T < 5 / 365:
    pnl = (entry_credit - cur_credit * 0.5) * self.num_contracts * 100

# Line 240 (expiration exit)
pnl = (entry_credit - final_credit) * self.num_contracts * 100
```

**Problem**:
- Time exit discounts `cur_credit` by 50% for no documented reason
- Expiration exit uses `final_credit` without any discount
- The `0.5` multiplier may be a bug — should be `cur_credit` like the expiration case

---

### ISSUE 5: IV Rank and Credit Pricing Use Different IVs (MEDIUM)

**Finding**: IV Rank is calculated from raw (non-multiplied) IV, but credit is priced at multiplied IV:

```python
# Line 303: IV Rank uses raw IV
iv_rank = float(((hist_iv < raw_iv).sum() / len(hist_iv)) * 100)

# Line 297: Credit priced at multiplied IV
iv = raw_iv * self.VOLATILITY_PREMIUM  # 2.5x
```

**Problem**:
- IV Rank tells you whether current vol is high vs history
- But credit is priced at 2.5x the current vol
- This creates an inconsistency: you might have IV Rank=30% (low vol) but price options at IV=45% (very high vol)
- The strategy enters when IV Rank is low but prices options as if IV is high

---

## QUANTIFIED IMPACT OF ISSUES

| Issue | Effect on P&L | Effect on WR | Effect on PF |
|-------|--------------|-------------|-------------|
| VOLATILITY_PREMIUM 2.5x | +200-300% inflation | Inflated | Inflated |
| Overlapping positions | Unknown (margin ignored) | Unreliable | Unreliable |
| Constant IV | Understates hedging value | Mild inflation | Mild inflation |
| Time exit bug | -10-20% per time exit | Slight deflation | Slight deflation |

**Net Effect**: Previous results likely inflated by 2-5x.

---

## PROPOSED FIXES (Phase 1B: Resolve)

### Fix 1: Replace VOLATILITY_PREMIUM with Calibrated IV Estimate

**Option A** (Remove multiplier): Use realized vol directly as IV proxy:
```python
iv = raw_iv  # No multiplier — realized vol IS the proxy
```

**Option B** (Calibrate properly): Use a data-driven multiplier:
```python
# Empirically: VIX typically trades at 1.3-1.8x realized vol
# Use median: 1.5x as conservative default
VOLATILITY_PREMIUM = 1.5
```

### Fix 2: Implement Single-Position Tracking

```python
trade_open = False
position_entry_day = 0
max_hold = self.max_hold_days

for i in range(len(price_arr)):
    if not trade_open:
        # Entry logic...
        result = self._simulate_trade(...)
        equity += result['pnl']
        trades.append(result)
        trade_open = True
        position_entry_day = i
    else:
        # Check if current trade should be closed (time barrier)
        days_held = i - position_entry_day
        if days_held >= max_hold:
            # Close at current price
            trade_open = False
        equity_curve.append(equity)
```

### Fix 3: Fix Time Exit Bug

```python
# Before (buggy):
pnl = (entry_credit - cur_credit * 0.5) * self.num_contracts * 100

# After (consistent with expiration logic):
pnl = (entry_credit - cur_credit) * self.num_contracts * 100
```

---

## DIRECTOR VERDICT

**Reviewed By**: AGENT-DIRECTOR
**Date**: 2026-04-12
**Decision**: FULL INDEPENDENT AUDIT ORDERED

> "The previous results showing 91.4% WR and 144 PF are mathematically impossible for a diversified iron condor strategy with proper risk management. These numbers are inflated by the VOLATILITY_PREMIUM and the lack of position limits.
>
> We will re-run the backtester with:
> 1. Realized vol as IV proxy (no 2.5x multiplier, or calibrated 1.3-1.5x)
> 2. Single-position enforcement (no overlapping trades)
> 3. All bugs fixed (time exit, constant IV documented)
> 4. Stress tests across 2008, COVID, low-vol regimes
>
> The truth will be what the truth is. We will NOT manipulate results to look better."

**Director Sign-Off**: AUDIT ORDERED — ALL PREVIOUS RESULTS SUSPECTED

---

*Loop 4A (Triage) Complete. Proceeding to implementation of fixes.*
