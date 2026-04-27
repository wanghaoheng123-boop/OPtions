from __future__ import annotations

from skills.paper_trader import PaperTrader


def test_kelly_low_trade_fallback_has_required_keys(tmp_path):
    db_path = tmp_path / "paper_portfolio.json"
    trader = PaperTrader(db_path=str(db_path))
    stats = {
        "win_rate_percent": 60.0,
        "num_trades": 3,
        "profit_factor": 1.1,
    }

    kelly = trader.calculate_kelly_sizing(stats)
    assert kelly["is_reliable"] is False
    assert "optimal_allocation_pct" in kelly
    assert 0 < kelly["optimal_allocation_pct"] <= 1


def test_execute_trade_does_not_crash_with_low_trade_stats(tmp_path):
    db_path = tmp_path / "paper_portfolio.json"
    trader = PaperTrader(db_path=str(db_path))

    result = trader.execute_trade(
        ticker="SPY",
        spot_price=100.0,
        strategy="covered_call",
        critic_approved=True,
        backtest_stats={"win_rate_percent": 55.0, "num_trades": 2, "profit_factor": 1.0},
    )

    assert result["status"] == "executed"
    assert "trade" in result
    assert result["trade"]["kelly_pct"] > 0
