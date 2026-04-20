from __future__ import annotations


def test_backtest_optimize_contract(api_client, monkeypatch):
    def fake_quick_scan(ticker, strategy_type, days=90):
        return {
            "optimal_tp_multiplier": 0.5,
            "optimal_sl_multiplier": 1.5,
            "optimal_time_days": 5,
            "optimal_ewma_span": 20,
            "trained_volatility": 0.2,
            "win_rate": 80.0,
            "profit_factor": 1.6,
            "sharpe_ratio": 1.8,
            "max_drawdown": 8.0,
            "num_trades": 50,
            "method": "single_split_70_30",
            "verdict": "PASS",
        }

    monkeypatch.setattr("skills.parameter_optimizer.ParameterOptimizer.quick_scan", fake_quick_scan)
    r = api_client.post("/api/backtest/optimize", json={"ticker": "SPY", "strategy": "iron_condor", "days": 180})
    assert r.status_code == 200
    j = r.json()
    assert j.get("verdict") == "PASS"
    for key in ("optimal_tp_multiplier", "optimal_sl_multiplier", "optimal_time_days", "num_trades"):
        assert key in j


def test_backtest_batch_contract(api_client, monkeypatch):
    def fake_backtest(ticker, strategy, days=252):
        return {
            "ticker": ticker,
            "strategy": strategy,
            "win_rate_percent": 80.0,
            "profit_factor": 1.5,
            "max_drawdown": 10.0,
            "sharpe_ratio": 1.7,
            "n_trades": 40,
            "verdict": "PASS",
        }

    monkeypatch.setattr("skills.backtester.StrategyBacktester.run_historical_backtest", fake_backtest)
    r = api_client.post("/api/backtest/batch", json={"tickers": ["SPY", "QQQ"], "strategy": "iron_condor", "days": 200})
    assert r.status_code == 200
    j = r.json()
    assert "results" in j and len(j["results"]) == 2
    assert "summary" in j and j["summary"].get("n_tickers") == 2
