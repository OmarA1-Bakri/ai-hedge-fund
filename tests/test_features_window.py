import pandas as pd
import numpy as np

from src.features.microstructure import build_microstructure_features

def test_microstructure_feature_alignment_no_lookahead():
    rng = np.random.default_rng(123)
    idx = pd.bdate_range("2024-01-01", periods=40)
    close = pd.Series(100.0, index=idx) * (1 + pd.Series(rng.normal(0, 0.01, len(idx)), index=idx)).cumprod()
    ohlcv = pd.DataFrame({
        "open": close.shift(1).fillna(method="bfill"),
        "high": close * (1 + 0.005),
        "low": close * (1 - 0.005),
        "close": close,
        "volume": 1_000_000
    }, index=idx)

    feats = build_microstructure_features(ohlcv, {"mom_short": 5, "mom_long": 20, "vol_lookback": 20})

    # No NaNs except expected leading window gaps after we shift(1)
    # First non-NaN should appear from max window + 1 due to shift
    assert feats["ret_1"].isna().sum() >= 1  # pct_change creates first NaN then shifted again
    assert feats.filter(regex="mom_|rv_|spread_proxy|hl_range|oo_gap|vol_rel").isna().sum().sum() > 0

    # Critically, today's feature row must NOT depend on future prices
    # So correlation between feature_t and return_{t+1} should not be trivially 1
    future_ret = ohlcv["close"].pct_change().shift(-1)
    corr = feats["ret_1"].corr(future_ret)
    assert not np.isclose(corr, 1.0, equal_nan=True)
