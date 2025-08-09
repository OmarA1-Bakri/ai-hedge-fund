import pandas as pd
import numpy as np

from src.labels.targets import (
    make_forward_returns,
    make_binary_labels,
    make_meta_labels,
    validate_alignment,
)


def test_forward_returns_and_embargo_and_tolerance():
    idx = pd.bdate_range("2024-01-01", periods=30)
    prices = pd.Series(np.linspace(100, 130, len(idx)), index=idx)

    y = make_forward_returns(prices, horizons=[1, 5], embargo_days=3)
    assert set(y.columns) == {"fret_1", "fret_5"}

    # Last 3 rows must be NaN due to embargo
    assert y.tail(3).isna().all().all()

    # 1-day forward return equals pct change shifted to align at t
    expected = prices.shift(-1) / prices - 1
    pd.testing.assert_series_equal(
        y["fret_1"].dropna(),
        expected.dropna(),
        rtol=1e-5,
        atol=1e-8,
    )


def test_binary_and_meta_labels():
    idx = pd.bdate_range("2024-01-01", periods=10)
    prices = pd.Series(np.linspace(100, 109, len(idx)), index=idx)
    fwd = make_forward_returns(prices, horizons=[1], embargo_days=0)

    yb = make_binary_labels(fwd, threshold=0.0, column="fret_1")
    assert set(yb.dropna().unique()).issubset({0.0, 1.0})

    # Primary signal (e.g., entry signal exists where value == 1)
    primary = pd.Series(0.0, index=idx)
    primary.iloc[2:7] = 1.0  # signal is "on" in this window
    meta = make_meta_labels(primary, fwd["fret_1"], threshold=0.0)

    # Meta is NaN outside primary "on" window (or where fwd NaN), else {0,1}
    assert meta[primary == 0].isna().all()
    assert set(meta[primary == 1].dropna().unique()).issubset({0.0, 1.0})


def test_alignment_validator_ok():
    # Simple synthetic: features are lagged (safe), labels are forward returns
    idx = pd.bdate_range("2024-01-01", periods=60)
    rng = np.random.default_rng(42)
    x = pd.Series(100.0, index=idx) * (1 + pd.Series(rng.normal(0, 0.01, len(idx)), index=idx)).cumprod()

    # Features: past-only transform
    feats = pd.DataFrame({
        "ret_1": x.pct_change().shift(1),
        "mom_5": x.pct_change(5).shift(1),
    }, index=idx)

    labels = make_forward_returns(x, horizons=[1], embargo_days=2)

    ok, msg = validate_alignment(feats, labels["fret_1"])
    assert ok, f"Expected alignment OK, got: {msg}"
