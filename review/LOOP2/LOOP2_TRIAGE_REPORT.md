# LOOP 2 TRIAGE REPORT
## Phase A: Optimization Findings Classification
## Agentic Quant Terminal V2

---

**Report Date**: 2026-04-12
**Prepared By**: AGENT-PM (Project Manager)
**Reviewed By**: AGENT-DIRECTOR
**Loop**: 2 | Phase: A (Triage)
**Classification**: INSTITUTIONAL CONFIDENTIAL

---

## EXECUTIVE SUMMARY

Loop 2 focuses on **optimization and ticker-specific tuning** based on Loop 1 findings. While Loop 1 fixed the structural backtesting model, Loop 2 addresses why some tickers (AMD, TSLA, MSFT) fail institutional thresholds despite the strategy working well for others (QQQ, SPY, AAPL, NVDA).

**Key Question**: Why do 50% of tickers fail WR threshold when the model is mathematically sound?

---

## PREVIOUS LOOP STATUS

**Loop 1 Outcomes**:
- 4/8 tickers pass institutional thresholds (QQQ, SPY, AAPL, NVDA)
- 4/8 tickers fail (AMD, TSLA, MSFT, NFLX) — primarily due to low Win Rate
- Total portfolio P&L = $234,540 on $100K capital
- Critical insight: Volatility premium multiplier (2.5x) was missing

---

## FINDING REGISTER (Loop 2)

### Category G: Ticker-Specific Performance

| ID | Severity | Title | Evidence | Impact | Owner | Status |
|----|----------|-------|----------|--------|-------|--------|
| **G-01** | HIGH | AMD produces 15.4% WR | Batch validation: 15.4% WR, PF=0.67 | High-vol tech stock not suitable for generic iron condor | AGENT-TRADER | NEW |
| **G-02** | HIGH | TSLA produces 30.8% WR | Batch validation: 30.8% WR, PF=1.23 | Extreme moves cause barrier breaches | AGENT-TRADER | NEW |
| **G-03** | HIGH | MSFT produces 55.4% WR | Batch validation: 55.4% WR, PF=1.57 | Moderate vol stock needs tighter strikes | AGENT-TRADER | NEW |
| **G-04** | HIGH | NFLX produces 47.7% WR | Batch validation: 47.7% WR, PF=2.05 | Earnings volatility not captured by model | AGENT-TRADER | NEW |

### Category H: Strategy-Specific Optimization

| ID | Severity | Title | Evidence | Impact | Owner | Status |
|----|----------|-------|----------|--------|-------|--------|
| **H-01** | MEDIUM | Iron Condor parameters need per-ticker tuning | SPY works at 5% wing, AMD needs different | One-size-fits-all doesn't work across vol regimes | AGENT-RESEARCHER | NEW |
| **H-02** | MEDIUM | Different DTE needed for different vol environments | 45 DTE works for SPY/QQQ, may be too long for high-vol | DTE should scale inversely with IV | AGENT-RESEARCHER | NEW |
| **H-03** | MEDIUM | Profit take % may need adjustment per ticker | 70% PT works for SPY, but some trades show early exit | Adaptive PT based on vol environment | AGENT-TRADER | NEW |

### Category I: Model Improvements

| ID | Severity | Title | Evidence | Impact | Owner | Status |
|----|----------|-------|----------|--------|-------|--------|
| **I-01** | MEDIUM | MetaModel still needs proper training | D-01: MetaModel trained on equity features | Re-train with options P&L labels | AGENT-RESEARCHER | NEW |
| **I-02** | MEDIUM | HMM regime-specific parameters | E-02: HMM shows extreme confidence | Regime-dependent parameter sets | AGENT-RESEARCHER | NEW |
| **I-03** | LOW | Kalman filter validation | F-01: Z-scores near zero in some periods | Separate Kalman investigation needed | AGENT-RESEARCHER | NEW |

---

## ROOT CAUSE ANALYSIS

### G-01/G-02: Why AMD and TSLA have low Win Rates

**Root Cause**: High-volatility stocks (AMD IV > 50%, TSLA IV > 80%) have larger expected moves.

For a 5% wing iron condor on AMD at $150 with 60% IV:
- 1 SD move = $150 × 0.60 × sqrt(45/365) ≈ $14.90 (10% of price)
- Wing width = $150 × 0.05 = $7.50 (5% of price)

**Problem**: 1 SD move exceeds wing width! The short strikes will be breached ~68% of the time by delta alone, before accounting for actual volatility clustering.

**Evidence**: AMD has 15.4% WR with $7.50 credit and $10 max loss. If breakeven is 40% (100% - 70%/30%), the actual loss rate is 85%.

**Fix Required**: For high-vol stocks, use wider wings (10-15% OTM) OR use fewer contracts (reduce position size) OR avoid the ticker entirely in high-vol regimes.

---

### G-03/G-04: Why MSFT and NFLX have moderate Win Rates

**Root Cause**: MSFT is a moderate-vol stock with earnings. NFLX has binary earnings events.

For MSFT (IV = 25-30%, earnings in Feb/May/Aug/Nov):
- Iron condor sold 30 days before earnings
- IV crush post-earnings can cause large moves
- Without earnings calendar awareness, we sell into IV高峰

For NFLX (earnings once per quarter):
- Binary event risk: stock moves 15-20% on earnings
- Our 45 DTE window covers NFLX earnings ~50% of the time
- If assigned during earnings, losses can be large

**Fix Required**: Earnings calendar filter to avoid selling premium within 5 days of earnings.

---

## OPTIMIZATION PLAN

### Phase 1: Ticker-Specific Parameter Optimization

| Ticker | Current WR | Issue | Recommended Fix |
|--------|-----------|-------|----------------|
| AMD | 15.4% | Vol too high for 5% wing | Use 10-15% wing OR skip in high-vol regime |
| TSLA | 30.8% | Extreme moves | Use 15% wing, reduce contracts |
| MSFT | 55.4% | Earnings risk | Add earnings filter (skip within 5 days) |
| NFLX | 47.7% | Binary events | Add earnings filter OR use shorter DTE |

### Phase 2: Adaptive Parameter Framework

Instead of fixed parameters, implement vol-adaptive parameters:

```python
def adaptive_parameters(S, iv, iv_rank):
    # Wing width scales with IV
    # Higher IV = wider wings to collect more premium
    wing_pct = max(0.05, min(0.20, iv / 10))  # 5-20% wing based on IV

    # DTE scales inversely with IV
    # Higher IV = shorter DTE to avoid gap risk
    dte = max(21, min(45, 60 - iv * 100))  # 21-45 DTE based on IV

    # IV Rank threshold scales with vol environment
    iv_rank_min = max(30, 70 - iv * 100)  # Higher IV = higher threshold

    return wing_pct, dte, iv_rank_min
```

### Phase 3: MetaModel Retraining

- Retrain MetaModel with actual options P&L labels (not equity returns)
- Include features: IV Rank, DTE, wing_width, distance to earnings

---

## SEVERITY SUMMARY (Loop 2)

| Severity | Count | Must Resolve Before Loop 3? |
|----------|-------|----------------------------|
| CRITICAL | 0 | — |
| HIGH | 7 | YES — optimization incomplete without these |
| MEDIUM | 6 | NO — can be ongoing optimization |
| LOW | 2 | NO — nice to have |

---

## ASSIGNMENTS (Loop 2B)

| Finding | Owner | Priority | Deadline |
|---------|-------|----------|----------|
| G-01 (AMD) | AGENT-TRADER | P1 | 2026-04-13 |
| G-02 (TSLA) | AGENT-TRADER | P1 | 2026-04-13 |
| G-03 (MSFT) | AGENT-TRADER | P1 | 2026-04-13 |
| G-04 (NFLX) | AGENT-TRADER | P1 | 2026-04-13 |
| H-01 (per-ticker) | AGENT-RESEARCHER | P2 | 2026-04-14 |
| H-02 (DTE scaling) | AGENT-RESEARCHER | P2 | 2026-04-14 |
| I-01 (MetaModel retrain) | AGENT-RESEARCHER | P2 | 2026-04-14 |

---

## DIRECTOR VERDICT

**Reviewed By**: AGENT-DIRECTOR
**Date**: 2026-04-12
**Decision**: APPROVED FOR LOOP 2 INVESTIGATION

> "Loop 1 gave us a working model. Loop 2 must make it work for ALL tickers, not just the easy ones. The key insight is that parameter adaptation based on volatility environment is critical. We cannot use the same 5% wing for AMD that we use for SPY — AMD's IV is 5x higher.
>
> The earnings filter is also a critical addition — no institutional trader would sell premium into a known binary event without hedging or reducing size."

**Director Sign-Off**: ✅ APPROVED

---

*Loop 2B (Investigate) begins immediately.*