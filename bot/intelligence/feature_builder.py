"""Deterministic setup feature extraction for logging and future ML training."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from ..storage.schemas import SetupFeatureRow


def _last(df: pd.DataFrame, column: str):
    if df.empty or column not in df.columns:
        return None
    value = df.iloc[-1][column]
    return None if pd.isna(value) else float(value)


def build_setup_feature_row(signal: dict, df_15m: pd.DataFrame, df_1h: pd.DataFrame, df_4h: pd.DataFrame, settings) -> SetupFeatureRow:
    structure = signal.get("structure_summary") or {}
    blockers = signal.get("blockers") or []

    entry = signal.get("entry")
    sl = signal.get("sl")
    tp = signal.get("tp")
    rr = None
    if entry is not None and sl is not None and tp is not None:
        risk = abs(float(entry) - float(sl))
        reward = abs(float(tp) - float(entry))
        rr = (reward / risk) if risk > 0 else None

    box_high = structure.get("box_high")
    box_low = structure.get("box_low")
    box_range_pct = None
    if box_high is not None and box_low is not None and box_low != 0:
        box_range_pct = ((float(box_high) - float(box_low)) / float(box_low)) * 100.0

    row = SetupFeatureRow(
        setup_id=signal.get("setup_id", ""),
        timestamp=signal.get("timestamp", ""),
        symbol=signal.get("symbol", settings.symbol),
        status=signal.get("status", "UNKNOWN"),
        baseline_decision=signal.get("baseline_decision", signal.get("status", "NO_TRADE")),
        baseline_reason=signal.get("baseline_reason", signal.get("reason", "")),
        side=signal.get("side"),
        bias=signal.get("bias"),
        entry=float(entry) if entry is not None else None,
        sl=float(sl) if sl is not None else None,
        tp=float(tp) if tp is not None else None,
        rr=rr,
        entry_type=signal.get("entry_type"),
        retest_confirmed=signal.get("retest_confirmed"),
        current_price=_last(df_15m, "close"),
        ma20_15m=_last(df_15m, "ma20"),
        ma50_15m=_last(df_15m, "ma50"),
        ma200_15m=_last(df_15m, "ma200"),
        rsi14_15m=_last(df_15m, "rsi14"),
        ma20_1h=_last(df_1h, "ma20"),
        ma50_1h=_last(df_1h, "ma50"),
        ma200_1h=_last(df_1h, "ma200"),
        rsi14_1h=_last(df_1h, "rsi14"),
        ma20_4h=_last(df_4h, "ma20"),
        ma50_4h=_last(df_4h, "ma50"),
        ma200_4h=_last(df_4h, "ma200"),
        rsi14_4h=_last(df_4h, "rsi14"),
        box_high=float(box_high) if box_high is not None else None,
        box_low=float(box_low) if box_low is not None else None,
        box_range_pct=box_range_pct,
        recent_swing_high_count=structure.get("swing_highs_count"),
        recent_swing_low_count=structure.get("swing_lows_count"),
        room_check_passed=structure.get("room_check_passed"),
        blocker_count=len(blockers),
        blocker_levels=[str(item) for item in blockers[:6]],
        chase_triggered=bool((signal.get("chase_info") or {}).get("triggered", False)),
        chase_move_pct=(signal.get("chase_info") or {}).get("move_pct"),
        news_score=signal.get("news_score"),
        news_reason=signal.get("news_reason", ""),
        news_match_count=len(signal.get("news_matches") or []),
        execution_mode=settings.execution_mode.value,
        ai_mode=settings.ai_evaluation_mode,
    )
    return row


def feature_row_to_dict(row: SetupFeatureRow) -> dict:
    return asdict(row)
