from __future__ import annotations

import numpy as np
import pandas as pd

from skills.backtester import IronCondorBacktester


def _synthetic_ohlc(n: int = 420) -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    trend = np.linspace(100.0, 120.0, n)
    noise = np.sin(np.arange(n) / 5.0) * 0.5
    close = trend + noise
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 0.5,
            "Low": close - 0.5,
            "Close": close,
            "Adj Close": close,
            "Volume": np.full(n, 1_000_000),
        },
        index=idx,
    )


def test_backtester_exposes_contract_keys_and_non_overlapping_entries(monkeypatch):
    def fake_download(*args, **kwargs):
        return _synthetic_ohlc()

    monkeypatch.setattr("skills.backtester.yf.download", fake_download)

    bt = IronCondorBacktester(use_adaptive=False, iv_rank_min=0.0, earnings_filter=False)
    monkeypatch.setattr(bt, "_calc_credit", lambda *args, **kwargs: 2.0)
    out = bt.run("SPY", days=360)
    assert "error" not in out, out.get("error")

    # Contract aliases expected by orchestrator and API layers.
    assert "n_trades" in out
    assert "num_trades" in out
    assert "trained_iv" in out
    assert "trained_volatility" in out

    # Single-position loop should avoid overlapping entries; entry dates unique.
    trade_log = out.get("trade_log", [])
    entry_dates = [t.get("entry_date") for t in trade_log if t.get("entry_date")]
    assert len(entry_dates) == len(set(entry_dates))
