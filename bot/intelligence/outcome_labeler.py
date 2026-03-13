"""Outcome labeling scaffold based on post-entry candle paths."""

from __future__ import annotations

from datetime import datetime, timezone

from ..storage.schemas import OutcomeLabel


def label_trade_outcome_from_path(
    *,
    setup_id: str,
    side: str,
    entry: float,
    tp: float,
    sl: float,
    candles: list[dict],
    trade_id: str | None = None,
) -> OutcomeLabel:
    """Label TP/SL-first outcome from candle sequence.

    TODO: extend with exact exchange fill/partial-fill reconciliation.
    """
    hit_tp_idx = None
    hit_sl_idx = None
    mfe = 0.0
    mae = 0.0

    for idx, candle in enumerate(candles):
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

    bars_to_outcome = None
    outcome_status = "unresolved"
    hit_tp_first = False
    hit_sl_first = False

    if hit_tp_idx is not None and (hit_sl_idx is None or hit_tp_idx <= hit_sl_idx):
        outcome_status = "tp_first"
        hit_tp_first = True
        bars_to_outcome = hit_tp_idx + 1
    elif hit_sl_idx is not None:
        outcome_status = "sl_first"
        hit_sl_first = True
        bars_to_outcome = hit_sl_idx + 1

    risk = abs(entry - sl)
    pnl_r = None
    if outcome_status == "tp_first" and risk > 0:
        pnl_r = abs(tp - entry) / risk
    elif outcome_status == "sl_first":
        pnl_r = -1.0

    return OutcomeLabel(
        setup_id=setup_id,
        trade_id=trade_id,
        outcome_status=outcome_status,
        hit_tp_first=hit_tp_first,
        hit_sl_first=hit_sl_first,
        pnl_r=pnl_r,
        mfe=mfe,
        mae=abs(mae),
        bars_to_outcome=bars_to_outcome,
        labeled_at=datetime.now(timezone.utc).isoformat(),
    )
