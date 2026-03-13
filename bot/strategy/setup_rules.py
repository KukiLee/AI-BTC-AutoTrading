"""Core bias and setup validation rules."""

from __future__ import annotations

import pandas as pd


def get_bias(df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> str:
    c1 = float(df_1h.iloc[-1]["close"])
    c4 = float(df_4h.iloc[-1]["close"])
    ma20_1h = float(df_1h.iloc[-1]["ma20"])
    ma50_4h = float(df_4h.iloc[-1]["ma50"])

    if c4 > ma50_4h and c1 > ma20_1h:
        return "LONG"
    if c4 < ma50_4h and c1 < ma20_1h:
        return "SHORT"
    return "NEUTRAL"


def is_chasing_move(df_15m: pd.DataFrame, threshold_pct: float, bars: int = 3) -> bool:
    chunk = df_15m.tail(bars)
    first = float(chunk.iloc[0]["close"])
    last = float(chunk.iloc[-1]["close"])
    if first <= 0:
        return True
    pct = ((last - first) / first) * 100
    return abs(pct) >= threshold_pct


def room_check(side: str, entry: float, tp: float, swing_highs: list[float], swing_lows: list[float]) -> tuple[bool, str]:
    if side == "LONG":
        blockers = [h for h in swing_highs if entry < h < tp]
        if blockers:
            return False, f"Intermediate resistance detected at {blockers[:3]}"
        return True, "Room clear"

    if side == "SHORT":
        blockers = [l for l in swing_lows if tp < l < entry]
        if blockers:
            return False, f"Intermediate support detected at {blockers[:3]}"
        return True, "Room clear"

    return False, "Unsupported side"
