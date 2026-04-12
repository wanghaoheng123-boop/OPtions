# INSTITUTIONAL REVIEW GOVERNANCE FRAMEWORK
## Agentic Quant Terminal V2 — Quality Assurance System

---

## Governance Structure

### Role Definitions

| Role | Agent ID | Responsibilities |
|------|---------|-----------------|
| **DIRECTOR** | `AGENT-DIRECTOR` | Final authority on all decisions. Approves/rejects fixes. Sets institutional standards. Ensures no result manipulation. |
| **PROJECT MANAGER** | `AGENT-PM` | Coordinates all teams. Manages task pipeline. Tracks progress. Escalates blockers. Manages agent communications. |
| **QA/QC MANAGER** | `AGENT-QA` | Inspects every fix. Verifies math. Validates backtests. Enforces institutional standards. Issues stop-work orders. |
| **HEAD TRADER** | `AGENT-TRADER` | Institutional trader perspective. Validates strategy logic. Reviews risk management. Approves strategy changes. |
| **SENIOR PROGRAMMER** | `AGENT-PROGRAMMER` | Implements all code fixes. Optimizes algorithms. Maintains code quality. Ensures no tech debt. |
| **PHD RESEARCHER** | `AGENT-RESEARCHER` | Academic rigor. Verifies all quantitative claims. Cross-references AFML/Hamilton/Thorp. Audits math. |

---

## Three-Review-Loop Protocol

### Loop Structure
```
LOOP N (N = 1, 2, 3)
├── PHASE A: TRIAGE (Director + PM)
│   └── Categorize findings, assign severity, assign owners
├── PHASE B: INVESTIGATE (All agents)
│   └── Deep dive into each issue with academic rigor
├── PHASE C: RESOLVE (Programmer + Researcher)
│   └── Fix, optimize, document each issue
└── PHASE D: VERIFY (QA + Director)
    └── QA inspection, director sign-off, gate to next loop
```

### Quality Standards (Non-Negotiable)

1. **No Result Manipulation**: All backtest results are presented as-is. No cherry-picking.
2. **Academic Standards**: All quantitative claims verified against primary sources (AFML, Hamilton, Thorp).
3. **Institutional Metrics**: Win Rate ≥ 75%, Profit Factor ≥ 1.2, Max Drawdown < 20%, Sharpe ≥ 1.5.
4. **Transparency**: All findings, even unfavorable, are documented.
5. **Reproducibility**: All optimizations must be reproducible with documented parameters.

---

## Review Tracking System

### Finding Severity Matrix

| Severity | Definition | Response Time | Example |
|----------|------------|--------------|---------|
| **CRITICAL** | Direct profit loss or regulatory risk | Immediate | Wrong Kelly formula, incorrect hedge ratio |
| **HIGH** | Strategy failure or significant edge loss | 24 hours | Wrong sign in Greeks, cointegration bug |
| **MEDIUM** | Suboptimal performance | 72 hours | Non-optimal parameter, missing feature |
| **LOW** | Minor issue, cosmetic | 1 week | Code style, documentation gaps |

### Finding Status States

```
NEW → ASSIGNED → UNDER_INVESTIGATION → RESOLVED → VERIFIED → CLOSED
                ↓
            ESCALATED (if blocking)
```

### Evidence Requirements

Every finding must have:
1. **Description**: Clear problem statement
2. **Evidence**: Data, logs, backtest results
3. **Impact**: Quantified profit/risk impact
4. **Root Cause**: Why it happened
5. **Fix**: Exact code/data change
6. **Verification**: How QA confirmed fix
7. **Academic Reference**: Source that validates the fix approach

---

## Communication Protocol

### Daily Standup (PM → All)
```
FORMAT: Status Report
CONTENT:
- What was completed yesterday
- What is being worked on today
- Any blockers or escalations
- Findings discovered
```

### Weekly Review (Director → All)
```
FORMAT: Governance Review
CONTENT:
- Loop progress report
- All open findings with age
- Critical decisions required
- Next week priorities
```

### Escalation Path
```
AGENT → QA (if math/strategy issue)
QA → PM (if cross-team coordination needed)
PM → DIRECTOR (if resource/priority decision needed)
```

---

## Loop 1 Focus Areas

1. **Math Audit**: Greeks, Kelly, GEX, HMM all formulas verified
2. **Backtester Audit**: Triple Barrier, OOS split, WFO all verified
3. **Strategy Logic Audit**: iron_condor, wheel, covered_call all verified
4. **Data Flow Audit**: yfinance → backtester → paper_trader → portfolio
5. **API Completeness**: All endpoints return correct data

---

## Loop 2 Focus Areas

1. **Parameter Optimization**: Grid search across all strategies/tickers
2. **Strategy Diversification**: Test all 5 strategies across 10+ tickers
3. **MetaModel Audit**: Verify RandomForest is training correctly
4. **HMM Regime Audit**: Verify 4-state model is stable
5. **Kalman Filter Audit**: Verify dynamic hedge ratio is working

---

## Loop 3 Focus Areas

1. **Full Backtest Suite**: 20+ tickers, all strategies, 5-year history
2. **Institutional Metrics Report**: Win Rate, PF, DD, Sharpe, Sortino, Calmar
3. **Paper Trading Validation**: Live paper trading for 30 days minimum
4. **Final Optimization**: Best parameter sets locked and documented
5. **Delivery Package**: Complete documentation, audit trail, user manual

---

## Sign-Off Requirements

### QA/QC Sign-Off Requires:
- [ ] All test cases pass
- [ ] No new bugs introduced
- [ ] Math verified by Researcher
- [ ] Strategy logic verified by Trader
- [ ] Code reviewed by Senior Programmer

### Director Sign-Off Requires:
- [ ] QA sign-off received
- [ ] PM project summary reviewed
- [ ] All CRITICAL/HIGH findings resolved
- [ ] No outstanding ethical concerns
- [ ] Results are reproducible

---

*This governance framework is binding on all agents. No agent may skip, shorten, or bypass any phase. The DIRECTOR has final authority to extend loops if institutional standards are not met.*
