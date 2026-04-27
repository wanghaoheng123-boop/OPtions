# GraphRAG Extraction Map

## Purpose
Defines how to keep `nodes.jsonl` and `edges.jsonl` synchronized with code and architecture changes.

## Source Files
- `backend/main.py`
- `core_agents/orchestrator.py`
- `skills/gamma_exposure.py`
- `skills/greeks_calculator.py`
- `skills/parameter_optimizer.py`
- `skills/backtester.py`
- `skills/paper_trader.py`
- `skills/brokers.py`
- `skills/regime_hmm.py`
- `skills/volatility_skew.py`
- `skills/market_data_api.py`
- `skills/macro_fetcher.py`
- `skills/kalman_filter.py`
- `skills/meta_model.py`
- `skills/methodology_catalog.py`

## Mapping Rules
1. Add a `DataStream` node when a distinct market/context feed is introduced.
2. Add a `Computation` node when a module transforms upstream data into strategy/risk/execution signals.
3. Add a `RiskModule` node for gate, sizing, and account-eligibility controls.
4. Add a `Strategy` node for any strategy target that can be selected or evaluated.
5. Add an `ExecutionModule` node for paper/live routing endpoints.
6. Add edges:
   - `feeds` for signal/data handoff
   - `depends_on` for non-trivial module prerequisites
   - `constrains` for explicit veto/limit logic
   - `routes_to` for execution dispatch paths
   - `sizes` for quantity/risk sizing influence
   - `produces_metric` for metric/result flow into downstream gates
7. `depends_on` can target `Instrument` when stream/module relationships are ticker-bound.

## Required Dependency Slices
- Volatility/GEX data path to strategy and risk gates.
- Risk/margin/sizing controls to execution pathways.
- Strategy outputs to execution and portfolio-state impact.
- Macro data path from fetcher/API adapters into orchestration context.
- Meta-label and Kalman computations to validation and strategy constraint layers.
