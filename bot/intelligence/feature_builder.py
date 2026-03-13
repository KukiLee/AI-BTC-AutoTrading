"""Deterministic setup/candidate feature extraction for logging and future ML training."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from ..storage.schemas import CandidateFeatureRow, SetupFeatureRow


def _last(df: pd.DataFrame, column: str):
    if df.empty or column not in df.columns:
        return None
    value = df.iloc[-1][column]
    return None if pd.isna(value) else float(value)


def build_setup_feature_row(signal: dict, df_15m: pd.DataFrame, df_1h: pd.DataFrame, df_4h: pd.DataFrame, settings) -> SetupFeatureRow:
    structure = signal.get("structure_summary") or {}
    blockers = signal.get("blockers") or []
    row = SetupFeatureRow(
        setup_id=signal.get("setup_id", ""),
        timestamp=signal.get("timestamp", ""),
        symbol=signal.get("symbol", settings.symbol),
        status=signal.get("status", "UNKNOWN"),
        baseline_decision=signal.get("baseline_decision", "NO_TRADE"),
        baseline_reason=signal.get("baseline_reason", signal.get("reason", "")),
        side=signal.get("side"),
        bias=signal.get("bias"),
        entry=signal.get("entry"),
        sl=signal.get("sl"),
        tp=signal.get("tp"),
        rr=signal.get("rr"),
        entry_type=signal.get("entry_type"),
        retest_confirmed=signal.get("retest_confirmed"),
        trigger_timeframe=signal.get("trigger_timeframe", "15m"),
        bias_1h=signal.get("bias_1h"),
        bias_4h=signal.get("bias_4h"),
        ma20_15m=_last(df_15m, "ma20"),
        ma50_15m=_last(df_15m, "ma50"),
        rsi14_15m=_last(df_15m, "rsi14"),
        ma20_1h=_last(df_1h, "ma20"),
        ma50_1h=_last(df_1h, "ma50"),
        rsi14_1h=_last(df_1h, "rsi14"),
        ma20_4h=_last(df_4h, "ma20"),
        ma50_4h=_last(df_4h, "ma50"),
        rsi14_4h=_last(df_4h, "rsi14"),
        box_high=structure.get("box_high"),
        box_low=structure.get("box_low"),
        room_check_passed=structure.get("room_check_passed"),
        blocker_count=len(blockers),
        blocker_levels=[str(item) for item in blockers],
        chase_triggered=bool((signal.get("chase_info") or {}).get("triggered", False)),
        chase_move_pct=(signal.get("chase_info") or {}).get("move_pct"),
        news_score=signal.get("news_score"),
        news_reason=signal.get("news_reason"),
        policy_mode=settings.policy_mode.value,
    )
    return row


def build_candidate_feature_row(candidate: dict, signal: dict, df_15m: pd.DataFrame, df_1h: pd.DataFrame, df_4h: pd.DataFrame, settings) -> CandidateFeatureRow:
    return CandidateFeatureRow(
        setup_id=signal.get("setup_id", ""),
        candidate_id=candidate.get("candidate_id"),
        timestamp=signal.get("timestamp", ""),
        symbol=signal.get("symbol", settings.symbol),
        candidate_type=candidate.get("candidate_type"),
        side=candidate.get("side"),
        entry=candidate.get("entry"),
        sl=candidate.get("sl"),
        tp=candidate.get("tp"),
        rr=candidate.get("rr"),
        hard_blocked=candidate.get("hard_blocked", False),
        hard_block_reasons=candidate.get("hard_block_reasons") or [],
        reason=candidate.get("reason"),
        news_score=signal.get("news_score"),
        ma20_15m=_last(df_15m, "ma20"),
        ma20_1h=_last(df_1h, "ma20"),
        ma20_4h=_last(df_4h, "ma20"),
        baseline_decision=signal.get("baseline_decision", "NO_TRADE"),
        policy_mode=settings.policy_mode.value,
    )


def feature_row_to_dict(row) -> dict:
    return asdict(row)
