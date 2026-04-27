PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS optimization_episode (
  episode_id TEXT PRIMARY KEY,
  created_at_utc TEXT NOT NULL,
  universe TEXT,
  quick_mode INTEGER NOT NULL DEFAULT 0,
  days INTEGER,
  num_contracts INTEGER,
  search_space_json TEXT NOT NULL,
  combos_evaluated INTEGER,
  selection_rule TEXT,
  best_sort_key_json TEXT,
  best_params_json TEXT,
  best_metrics_json TEXT,
  artifact_paths_json TEXT,
  config_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS walk_forward_window_episode (
  row_id INTEGER PRIMARY KEY AUTOINCREMENT,
  episode_id TEXT NOT NULL,
  ticker TEXT NOT NULL,
  strategy_type TEXT NOT NULL,
  method TEXT,
  train_window_days INTEGER,
  test_window_days INTEGER,
  window_start_idx INTEGER,
  window_end_idx INTEGER,
  param_set_json TEXT NOT NULL,
  trained_vol REAL,
  num_trades INTEGER,
  win_rate REAL,
  profit_factor REAL,
  sharpe_ratio REAL,
  max_drawdown REAL,
  barrier_hits_json TEXT,
  constraint_status TEXT,
  cache_key TEXT,
  failed_signature_hash TEXT,
  created_at_utc TEXT NOT NULL,
  FOREIGN KEY (episode_id) REFERENCES optimization_episode(episode_id)
);

CREATE TABLE IF NOT EXISTS ticker_backtest_episode (
  episode_id TEXT PRIMARY KEY,
  created_at_utc TEXT NOT NULL,
  sector TEXT,
  ticker TEXT NOT NULL,
  strategy TEXT,
  config_snapshot_json TEXT NOT NULL,
  metrics_json TEXT NOT NULL,
  risk_context_json TEXT,
  execution_outcomes_json TEXT,
  verdict TEXT,
  classification TEXT,
  expectancy_dollars REAL,
  error_text TEXT,
  config_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_gate_episode (
  episode_id TEXT PRIMARY KEY,
  created_at_utc TEXT NOT NULL,
  run_type TEXT NOT NULL,
  requested_tickers_json TEXT,
  strategy TEXT,
  days INTEGER,
  gates_json TEXT NOT NULL,
  strict_mode INTEGER NOT NULL DEFAULT 1,
  min_pass INTEGER,
  results_count INTEGER,
  pass_count INTEGER,
  failed_tickers_json TEXT,
  missing_tickers_json TEXT,
  exit_code INTEGER,
  status TEXT,
  source TEXT,
  config_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS failure_constraint_registry (
  failed_signature_hash TEXT PRIMARY KEY,
  first_seen_utc TEXT NOT NULL,
  last_seen_utc TEXT NOT NULL,
  strategy_type TEXT,
  ticker TEXT,
  constraint_class TEXT NOT NULL,
  constraint_detail TEXT,
  failure_context_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_opt_config_hash
  ON optimization_episode(config_hash);

CREATE INDEX IF NOT EXISTS idx_ticker_config_hash
  ON ticker_backtest_episode(config_hash);

CREATE INDEX IF NOT EXISTS idx_walk_failed_sig
  ON walk_forward_window_episode(failed_signature_hash);

CREATE INDEX IF NOT EXISTS idx_walk_ticker_strategy
  ON walk_forward_window_episode(ticker, strategy_type);
