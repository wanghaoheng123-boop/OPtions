"""FastAPI smoke tests (in-process)."""

from __future__ import annotations

import pytest


def test_health(api_client):
    r = api_client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "OPERATIONAL"
    assert "endpoints" in body


@pytest.mark.network
def test_backtest_spy(api_client):
    r = api_client.post(
        "/api/backtest",
        json={"ticker": "SPY", "strategy": "iron_condor", "days": 400},
    )
    assert r.status_code == 200
    j = r.json()
    assert "error" not in j or j.get("error") is None, j
    for key in ("win_rate_percent", "trade_log", "tc_summary", "max_drawdown"):
        assert key in j, f"missing {key}: {list(j.keys())}"


@pytest.mark.network
def test_gex_live_spy(api_client):
    r = api_client.get("/api/gex/live/SPY")
    assert r.status_code == 200
    j = r.json()
    if j.get("error"):
        pytest.skip(f"chain unavailable: {j.get('error')}")
    assert j.get("source") == "chain"
    assert "spot_price" in j and "strikes" in j
