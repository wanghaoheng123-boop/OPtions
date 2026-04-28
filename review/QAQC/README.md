# QAQC Verifier Loop

This directory stores simulated independent QAQC artifacts for stability-first iterations.

## Process

1. Implementation changes are completed.
2. Run verifier script:
   - `python scripts/run_qaqc_loop.py`
3. Review `latest_qaqc_report.json`.
4. Block promotion if overall status is `FAIL` unless explicit waiver is documented.

## Required checks per iteration

- API contract and transport-level error behavior
- Frontend display-state correctness (`loading/error/empty/stale/live`)
- Quant integrity gates (failure dedupe and OOS meta-model validation)
- Residual risk ledger

