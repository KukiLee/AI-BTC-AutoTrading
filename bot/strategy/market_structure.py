"""Deterministic market structure extraction."""

from __future__ import annotations

import pandas as pd


def get_recent_box(df: pd.DataFrame, lookback: int) -> dict[str, float]:
    window = df.tail(lookback)
    return {
        "box_high": float(window["high"].max()),
        "box_low": float(window["low"].min()),
    }


def find_swings(df: pd.DataFrame, left: int = 2, right: int = 2) -> dict[str, list[float]]:
    swing_highs: list[float] = []
    swing_lows: list[float] = []

    highs = df["high"].tolist()
    lows = df["low"].tolist()
    for i in range(left, len(df) - right):
        high_slice = highs[i - left : i + right + 1]
        low_slice = lows[i - left : i + right + 1]
        if highs[i] == max(high_slice):
            swing_highs.append(highs[i])
        if lows[i] == min(low_slice):
            swing_lows.append(lows[i])

    return {"swing_highs": swing_highs, "swing_lows": swing_lows}
