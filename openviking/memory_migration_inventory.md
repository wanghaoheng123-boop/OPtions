# OpenViking Memory Migration Inventory

## Source-to-Target Mapping

| Source | Tier | Target |
|---|---|---|
| `activeContext.md` | L0 | `openviking/memories/L0/session_state/current_focus.md` |
| `progress.md` (latest/operational slices) | L0 | `openviking/memories/L0/session_state/current_focus.md` |
| `task_plan.md` (active scope) | L0 | `openviking/memories/L0/session_state/current_focus.md` |
| `AGENTS.md` | L1 | `openviking/memories/L1/governance/agent_routing_and_quality_gates.md` |
| `CLAUDE.md` | L1 | `openviking/memories/L1/governance/agent_routing_and_quality_gates.md` |
| `systemPatterns.md` | L1 | `openviking/memories/L1/architecture/system_patterns.md` |
| `projectbrief.md` | L1 | `openviking/memories/L1/domain/trading_methodology.md` |
| `productContext.md` | L1 | `openviking/memories/L1/domain/trading_methodology.md` |
| `techContext.md` | L1 | `openviking/memories/L1/domain/trading_methodology.md` |
| `findings.md` | L1 | `openviking/memories/L1/domain/trading_methodology.md` and governance refs |
| `progress.md` (historical slices) | L2 | `openviking/memories/L2/history/progress_archive.md` |
| `review/` | L2 | `openviking/memories/L2/reviews/` |
| `memory/agent_memory.json` | L2 | `openviking/memories/L2/snapshots/agent_memory_snapshot.json` |

## Tiering Rules
- L0: active loop state and immediate invariants.
- L1: stable architecture, governance, and methodology.
- L2: archival reports, history, and large snapshots.
