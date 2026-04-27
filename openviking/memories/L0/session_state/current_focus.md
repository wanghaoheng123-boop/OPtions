# L0 Current Focus (Hot Context)
# Current Focus (L0 Hot State)

## Program state

The 15-phase institutional delivery loop is complete and the codebase is release-hardened. Current priority is memory-system migration and synchronization so prolonged coding sessions preserve continuity across agents and devices.

## Last confirmed actions

- Completed program closure artifacts under `review/PROGRAM15/`.
- Core quant fixes and reliability updates already landed in:
  - `skills/backtester.py`
  - `skills/parameter_optimizer.py`
  - `core_agents/orchestrator.py`
  - `frontend/src/components/MacroSearchTerminal.tsx`
  - `.github/workflows/ci.yml`
- Validation gates previously passed for pytest (network + non-network), regression, strict batch backtests, and frontend e2e.

## Immediate next steps

1. Finalize Multi-Agent Hybrid Memory migration layers (OpenViking, GraphRAG, episodic, vector).
2. Preserve cross-agent handoff via `workspace/SESSION_STATE.json` and this L0 record.
3. Keep optimization-loop anti-repeat guard active through `failure_constraint_registry`.

## Session handoff notes

- Treat this file as the first read for any new coding session.
- If context is missing, read `workspace/SESSION_STATE.json` then `openviking/memories/L1/`.
## Purpose
Immediate session handoff for active implementation work.

## Sources
- `activeContext.md`
- `task_plan.md`
- latest status from `progress.md`

## Current Program State
- Program execution baseline is release-hardened and validated.
- Current operational posture emphasizes reliability, regression safety, and controlled iteration.
- Outstanding work is optimization quality expansion and optional websocket contract coverage.

## Immediate Operating Priorities
1. Keep hard risk/quality gates active for any quant or contract changes.
2. Preserve API contract compatibility for frontend panels and orchestration payloads.
3. Record every non-trivial optimization loop result in episodic memory before re-running variants.

## Active Invariants
- Do not claim hidden market intent; only observables + hypothesis + uncertainty.
- Treat external providers and credentials as explicit dependency gates.
- Keep methodology and output contracts synchronized whenever logic changes.
