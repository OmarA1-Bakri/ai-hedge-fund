import pandas as pd
import numpy as np
from typing import Dict, Any

def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    out = a / b.replace(0, np.nan)
    return out.replace([np.inf, -np.inf], np.nan)

def build_microstructure_features(ohlcv: pd.DataFrame, windows: Dict[str, int]) -> pd.DataFrame:
    """
    Compute leakage-safe microstructure features from OHLCV.
    Assumes columns: ['open','high','low','close','volume'] and a DateTimeIndex.
    All features use ONLY past data (shifted where needed) so no look-ahead.
    """
    required = {"open", "high", "low", "close"}
    missing = required - set(map(str.lower, ohlcv.columns))
    if missing:
        raise ValueError(f"Missing OHLCV columns: {missing}")

    df = ohlcv.copy()
    # Ensure canonical lower-case
    df.columns = [c.lower() for c in df.columns]

    # Basic returns (close-to-close), past-only
    df["ret_1"] = df["close"].pct_change()

    # Open-open and high-low gaps (shifted to be known at time t)
    df["oo_gap"] = df["open"].pct_change()  # open_t / open_{t-1} - 1
    df["hl_range"] = _safe_div(df["high"] - df["low"], df["close"].shift(1))

    # Realized volatility (rolling std of returns), no look-ahead
    vol_lb = int(windows.get("vol_lookback", 20))
    df[f"rv_{vol_lb}"] = df["ret_1"].rolling(vol_lb).std()

    # Momentum signals (past window close/close - 1)
    mom_s = int(windows.get("mom_short", 5))
    mom_l = int(windows.get("mom_long", 20))
    df[f"mom_{mom_s}"] = df["close"].pct_change(mom_s)
    df[f"mom_{mom_l}"] = df["close"].pct_change(mom_l)

    # Volume imbalance proxy vs its own rolling mean (if volume present)
    if "volume" in df.columns:
        vol_mean_win = max(5, min(60, vol_lb))
        df["vol_rel"] = _safe_div(df["volume"], df["volume"].rolling(vol_mean_win).mean()).shift(1)

    # Bid-ask spread proxy (HL over close_prev) — microstructure roughness
    df["spread_proxy"] = _safe_div(df["high"] - df["low"], df["close"].shift(1))

    # Ensure no future data leaks into time t row: shift any feature that
    # references the close/high/low of t in a way that wouldn’t be known intraday.
    # For a daily close decision, most rolling stats are safe; gaps that use t's prices
    # are considered "after the bar closes". Keep it simple: shift all derived cols by 1.
    derived_cols = [c for c in df.columns if c not in ["open", "high", "low", "close", "volume"]]
    df[derived_cols] = df[derived_cols].shift(1)

    return df
