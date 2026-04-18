"""FastAPI smoke tests (in-process)."""

from __future__ import annotations

import pytest


def test_methodology_index(api_client):
    r = api_client.get("/api/methodology")
    assert r.status_code == 200
    panels = r.json().get("panels")
    assert isinstance(panels, list) and "chart" in panels


def test_methodology_chart_panel(api_client):
    r = api_client.get("/api/methodology/chart")
    assert r.status_code == 200
    j = r.json()
    assert j.get("title")
    for key in ("inputs", "method", "limits", "code_paths"):
        assert key in j


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
def test_analyze_spy_contract(api_client):
    """POST /api/analyze returns mosaic payload shape (requires options chain + yfinance)."""
    r = api_client.post("/api/analyze", json={"ticker": "SPY", "days": 126})
    if r.status_code != 200:
        pytest.skip(f"analyze unavailable: {r.status_code} {r.text[:200]}")
    j = r.json()
    assert j.get("ticker") == "SPY"
    assert "current_price" in j and isinstance(j["current_price"], (int, float))
    assert "market_structure" in j and isinstance(j["market_structure"], dict)
    assert "paper_trade_status" in j


@pytest.mark.network
def test_chart_spy_contract(api_client):
    """GET /api/chart must return a non-empty OHLC list usable by lightweight-charts."""
    r = api_client.get("/api/chart/SPY")
    assert r.status_code == 200, r.text
    j = r.json()
    assert "data" in j and isinstance(j["data"], list) and len(j["data"]) > 0
    bar = j["data"][0]
    for key in ("time", "open", "high", "low", "close"):
        assert key in bar, f"missing {key} in bar: {bar!r}"


@pytest.mark.network
def test_gex_live_spy(api_client):
    r = api_client.get("/api/gex/live/SPY")
    assert r.status_code == 200
    j = r.json()
    if j.get("error"):
        pytest.skip(f"chain unavailable: {j.get('error')}")
    assert j.get("source") == "chain"
    assert "spot_price" in j and "strikes" in j
