import pandas as pd
import numpy as np
from typing import Iterable, Dict

def make_forward_returns(prices: pd.Series, horizons: Iterable[int], embargo_days: int = 0) -> pd.DataFrame:
    """
    Create forward return labels for multiple horizons, with optional tail embargo.

    prices: Series indexed by datetime (close prices).
    horizons: iterable of day horizons (e.g., [1, 5])
    embargo_days: number of final rows to set to NaN to prevent training on near-future info.

    Returns: DataFrame with columns like 'fret_1', 'fret_5' aligned at time t (known future returns removed).
    """
    if not isinstance(prices, pd.Series):
        raise TypeError("prices must be a pandas Series")
    if len(prices) < max(horizons) + 1:
        raise ValueError("Not enough data to compute requested forward horizons")

    labels = {}
    for h in horizons:
        # forward return from t to t+h using future price => shift negative
        labels[f"fret_{h}"] = prices.shift(-h).pct_change(periods=h)

    y = pd.DataFrame(labels, index=prices.index)

    # Embargo: last E days are unknown (cannot be used for training)
    if embargo_days > 0:
        y.iloc[-embargo_days:, :] = np.nan

    return y
