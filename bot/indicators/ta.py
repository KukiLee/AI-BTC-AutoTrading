"""Technical indicator calculations."""

from __future__ import annotations

import pandas as pd


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ma20"] = out["close"].rolling(window=20, min_periods=20).mean()
    out["ma50"] = out["close"].rolling(window=50, min_periods=50).mean()
    out["ma200"] = out["close"].rolling(window=200, min_periods=200).mean()

    delta = out["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-12)
    out["rsi14"] = 100 - (100 / (1 + rs))
    return out
