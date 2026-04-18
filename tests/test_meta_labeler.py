"""MetaLabeler label alignment (no external data)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from skills.meta_model import MetaLabeler


def test_generate_training_labels_from_trade_log():
    meta = MetaLabeler(config={"min_training_samples": 3})
    idx = pd.date_range("2024-01-01", periods=40, freq="D")
    features = pd.DataFrame(
        {
            "z_score_price": np.random.randn(40),
            "z_score_slow": np.random.randn(40),
            "plus_dm_ratio": np.random.rand(40),
            "minus_dm_ratio": np.random.rand(40),
            "ret_5d": np.random.randn(40) * 0.01,
            "ret_10d": np.random.randn(40) * 0.01,
            "ret_20d": np.random.randn(40) * 0.01,
            "vol_ratio_10d": np.random.rand(40),
            "vol_ratio_30d": np.random.rand(40),
            "price_vs_ma200": np.random.randn(40) * 0.01,
            "volume_ratio": np.random.rand(40),
            "distance_from_ma20_pct": np.random.randn(40) * 0.01,
            "next_return": np.random.randn(40) * 0.01,
            "day_of_week": idx.dayofweek,
            "month": idx.month,
        },
        index=idx,
    )
    meta._feature_names = [c for c in features.columns if c != "next_return"]

    trade_log = [
        {"entry_date": "2024-01-05", "pnl": 100.0},
        {"entry_date": "2024-01-10", "pnl": -50.0},
        {"entry_date": "2024-01-15", "pnl": 25.0},
    ]
    X, y = meta.generate_training_labels(features, trade_log)
    assert X is not None and y is not None
    assert len(X) == len(y) == 3
    assert set(y.tolist()) == {0, 1}
    assert y.tolist()[0] == 1 and y.tolist()[1] == 0 and y.tolist()[2] == 1
