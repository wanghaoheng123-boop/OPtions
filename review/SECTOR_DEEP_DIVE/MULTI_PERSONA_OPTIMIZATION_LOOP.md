# Multi-Persona Review & Optimization Loop

**Context:** Institutional iron condor audit (`skills/backtester_audit.py`) and sector basket (`run_sector_deep_dive.py`).  
**Goal:** Each loop cycle produces **signed-off changes** (engine, parameters, or universe) backed by five professional lenses before you redeploy capital or code.

---

## Roles (who challenges what)

| Persona | Mandate | Primary questions |
|--------|---------|-------------------|
| **Sell-side / prop trader** | Economic edge and behavior under stress | Is this P&L path-dependent on a few wins? Would I size this live after costs? When do I **not** trade? |
| **Market maker** | Microstructure and short-vol risk | Are wings wide enough vs typical move? Is “IV” believable for quoting (RV proxy vs surface)? Pin / gap risk around earnings? |
| **Portfolio manager** | Book-level risk and allocation | Sector caps, correlation, max loss per name, concentration in Tech winners? Does sector P&L justify sleeve exposure? |
| **Programmer** | Correctness and maintainability | Single-position gate, forced close path, contract multiplier, reproducible runs? Tests for regressions? |
| **Quant analyst** | Statistics and research hygiene | N trades in OOS window, PF stability with tiny loss denominators, walk-forward, no multiple-testing theater? |

Optional **adversarial pass** (from review-auditor habit): one persona explicitly argues **against** shipping this iteration’s change until counter-evidence is recorded.

---

## Loop protocol (one full cycle)

### Phase A — Ingest
1. Latest `TICKER_RESULTS.json`, `SECTOR_SUMMARY.json`, `BEST_CONDITIONS.json`, `SECTOR_DEEP_DIVE_REPORT.md`.
2. Run `python review/SECTOR_DEEP_DIVE/optimization_loop_digest.py` → `OPTIMIZATION_LOOP_DIGEST.json` + console summary.

### Phase B — Parallel review (30–45 min human time)
Each persona fills a short block (bullet list):

- **Trader:** list top 3 **do-not-trade** names or regimes; confirm barrier story (PT/SL/time/exp/fc) matches intuition.
- **MM:** flag names where wing % × spot vs ATR is unrealistic; note IV proxy weakness.
- **PM:** set max sector weight and per-ticker notional cap from WORKING list; mark sectors to **zero** until next audit.
- **Programmer:** scan diff since last tag; run targeted tests / one full sector re-run if engine touched.
- **Quant:** require minimum OOS trades for “promotion”; demand pre-registered hypothesis before parameter sweep.

### Phase C — Synthesize (change ticket)
Exactly **one** primary change class per cycle (pick one):
- **Engine** (e.g. IV source, earnings dates, margin model),
- **Parameters** (e.g. `VOLATILITY_RATIO`, wing floors, IV rank min),
- **Universe** (sector ban, whitelist, beta filter).

Record: hypothesis, expected metric movement, rollback plan.

### Phase D — Implement & re-audit
1. Code/params change (small diff).
2. `python review/SECTOR_DEEP_DIVE/run_sector_deep_dive.py`
3. Diff `TICKER_RESULTS.json` vs prior snapshot (store copies under `review/SECTOR_DEEP_DIVE/history/` if you want a paper trail).

### Phase E — Gate
Ship only if: Programmer + Quant sign off **and** PM accepts risk **and** Trader/MM have no blocking issue on the **changed** scope.

---

## Iteration 1 — Seed priorities (from current sector snapshot)

These are **starting hypotheses**, not conclusions:

1. **Quant + PM:** Energy and Staples show weak average win rate and negative sector P&L in the audit — treat as **research-only** until IV model and min-trade count improve; do not increase sizing there.
2. **Trader + MM:** Consumer Discretionary basket fails institutional gates often — consider a **volatility or ATR gate** before short strangles/condors, not only wider static wings.
3. **Programmer:** Any loop that changes `backtester_audit.py` should add or extend a **regression check** (fixed seed path or golden ticker subset) so Loop-3-style bugs do not return.
4. **PM:** Technology has multiple passers — if you deploy, use **hard per-name caps**; correlation in mega-cap tech is high.

---

## Artifacts

| File | Role |
|------|------|
| `OPTIMIZATION_LOOP_DIGEST.json` | Machine-readable backlog (run `optimization_loop_digest.py`) |
| `MULTI_PERSONA_OPTIMIZATION_LOOP.md` | This playbook |
| `SECTOR_DEEP_DIVE_REPORT.md` | Human narrative + tables |

---

## Command cheat sheet

```text
python review/SECTOR_DEEP_DIVE/auto_optimize.py
python review/SECTOR_DEEP_DIVE/auto_optimize.py --quick
python review/SECTOR_DEEP_DIVE/run_sector_deep_dive.py
python review/SECTOR_DEEP_DIVE/optimization_loop_digest.py
```

**Automated optimization:** `auto_optimize.py` grid-searches `volatility_ratio`, `profit_take_pct`, `stop_loss_mult`, and `min_credit_pct_of_risk`, scores the full 35-ticker basket, writes `AUTO_OPTIMIZE_GRID.json`, `AUTO_OPTIMIZE_BEST.json`, and `recommended_params.json`. `run_sector_deep_dive.py` **automatically merges** `recommended_params.json` when that file exists (delete it to revert to script defaults). Regenerate the persona digest after each full sector run.
