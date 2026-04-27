# Episodic State Tracker (SQLite Canonical)

## Purpose
Chronological memory for optimization/backtest iterations, including failed-constraint signatures to prevent repeated failed runs.

## Files
- `episodic_state/schema.sql`: canonical schema
- `episodic_state/episodes.db`: initialized SQLite database
- `episodic_state/init_db.py`: helper to initialize schema

## Core Tables
- `optimization_episode`
- `walk_forward_window_episode`
- `ticker_backtest_episode`
- `validation_gate_episode`
- `failure_constraint_registry`

## Non-Repeat Safeguard
- `config_hash` captures deterministic configuration fingerprints.
- `failed_signature_hash` captures normalized failed constraints.
- Before launching a new optimization candidate, query for existing `failed_signature_hash`.

## Suggested Pre-Run Check
1. Compute `config_hash` and prospective `failed_signature_hash`.
2. Query `failure_constraint_registry` for hash hit.
3. Skip or modify candidate if prior failure exists.
