# Active context (volatile — last session handoff)

## Current focus

Orchestration overhaul implementation: Memory Bank genesis, chart/API reliability (lightweight-charts v5), user-visible errors, methodology endpoint, UI polish, adversarial checklist.

## Last actions

- Created Memory Bank core docs and `AGENTS.md` routing.
- Next agent should run `python -m pytest tests/ -m "not network"` then `-m network` before merge.

## Immediate next steps

1. Verify chart on SPY after deploy (OHLC + walls).
2. Expand `GET /api/methodology` content as new panels ship.
3. Append outcomes to `progress.md` after each validation run.
