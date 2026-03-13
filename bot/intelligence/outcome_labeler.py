"""Outcome labeling scaffold based on post-entry candle paths."""

from __future__ import annotations


def label_trade_outcome_from_candles(entry: float, sl: float, tp: float, side: str, future_candles: list[dict]) -> dict:
    hit_tp_idx = None
    hit_sl_idx = None
    mfe = 0.0
    mae = 0.0

    for idx, candle in enumerate(future_candles):
        high = float(candle.get("high", entry))
        low = float(candle.get("low", entry))
        if side == "LONG":
            mfe = max(mfe, (high - entry) / entry)
            mae = min(mae, (low - entry) / entry)
            if hit_tp_idx is None and high >= tp:
                hit_tp_idx = idx
            if hit_sl_idx is None and low <= sl:
                hit_sl_idx = idx
        else:
            mfe = max(mfe, (entry - low) / entry)
            mae = min(mae, (entry - high) / entry)
            if hit_tp_idx is None and low <= tp:
                hit_tp_idx = idx
            if hit_sl_idx is None and high >= sl:
                hit_sl_idx = idx

    outcome_status = "unresolved"
    hit_tp_first = False
    hit_sl_first = False
    bars_to_outcome = None
    if hit_tp_idx is not None and (hit_sl_idx is None or hit_tp_idx <= hit_sl_idx):
        outcome_status = "tp_first"
        hit_tp_first = True
        bars_to_outcome = hit_tp_idx + 1
    elif hit_sl_idx is not None:
        outcome_status = "sl_first"
        hit_sl_first = True
        bars_to_outcome = hit_sl_idx + 1

    return {
        "outcome_status": outcome_status,
        "hit_tp_first": hit_tp_first,
        "hit_sl_first": hit_sl_first,
        "mfe": mfe,
        "mae": abs(mae),
        "bars_to_outcome": bars_to_outcome,
    }
