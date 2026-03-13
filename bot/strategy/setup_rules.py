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


def is_chasing_move(df_15m: pd.DataFrame, threshold_pct: float, bars: int = 3) -> dict:
    chunk = df_15m.tail(bars)
    first = float(chunk.iloc[0]["close"])
    last = float(chunk.iloc[-1]["close"])
    if first <= 0:
        return {"triggered": True, "direction": "UNKNOWN", "move_pct": 0.0, "threshold_pct": threshold_pct}
    pct = ((last - first) / first) * 100
    direction = "UP" if pct > 0 else "DOWN" if pct < 0 else "FLAT"
    return {
        "triggered": abs(pct) >= threshold_pct,
        "direction": direction,
        "move_pct": pct,
        "threshold_pct": threshold_pct,
    }


def room_check(
    side: str,
    entry: float,
    tp: float,
    swing_highs: list[float],
    swing_lows: list[float],
) -> tuple[bool, str, list[dict]]:
    """Check clear path to target.

    Uses a lightweight 2% distance cutoff for "meaningful" blockers to avoid overreacting
    to distant swing points while still surfacing nearby resistance/support.
    """

    if side == "LONG":
        blockers = [h for h in swing_highs if entry < h < tp]
        meaningful = [x for x in blockers if abs(x - entry) / entry <= 0.02]
        detail = [{"type": "resistance", "level": x, "distance_pct": abs(x - entry) / entry * 100} for x in meaningful[:3]]
        if meaningful:
            return False, f"Intermediate resistance detected at {[x for x in meaningful[:3]]}", detail
        return True, "Room clear", []

    if side == "SHORT":
        blockers = [l for l in swing_lows if tp < l < entry]
        meaningful = [x for x in blockers if abs(entry - x) / entry <= 0.02]
        detail = [{"type": "support", "level": x, "distance_pct": abs(entry - x) / entry * 100} for x in meaningful[:3]]
        if meaningful:
            return False, f"Intermediate support detected at {[x for x in meaningful[:3]]}", detail
        return True, "Room clear", []

    return False, "Unsupported side", []
