"""Main strategy signal assembly module."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

from strategy.market_structure import find_swings, get_recent_box
from strategy.news_filter import news_gate, score_news
from strategy.risk_manager import calc_rr_targets
from strategy.setup_rules import get_bias, is_chasing_move, room_check
from utils.time_utils import to_iso


@dataclass
class SignalResult:
    status: str
    reason: str
    side: str | None = None
    bias: str | None = None
    entry: float | None = None
    sl: float | None = None
    tp: float | None = None
    risk_per_unit: float | None = None
    news_score: int = 0
    news_reason: str = ""
    blockers: list[str] = field(default_factory=list)
    chase_info: dict = field(default_factory=dict)
    entry_type: str = "none"
    news_matches: list[dict] = field(default_factory=list)
    structure_summary: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=to_iso)


def derive_retest_entry_long(df_15m: pd.DataFrame, box_high: float, tolerance_pct: float, lookback_bars: int) -> float | None:
    tolerance = box_high * tolerance_pct
    recent = df_15m.tail(lookback_bars)
    for _, row in recent.iloc[::-1].iterrows():
        low = float(row["low"])
        close = float(row["close"])
        if (box_high - tolerance) <= low <= (box_high + tolerance) and close >= box_high:
            return box_high
    return None


def derive_retest_entry_short(df_15m: pd.DataFrame, box_low: float, tolerance_pct: float, lookback_bars: int) -> float | None:
    tolerance = box_low * tolerance_pct
    recent = df_15m.tail(lookback_bars)
    for _, row in recent.iloc[::-1].iterrows():
        high = float(row["high"])
        close = float(row["close"])
        if (box_low - tolerance) <= high <= (box_low + tolerance) and close <= box_low:
            return box_low
    return None


def build_trade_setup(
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_4h: pd.DataFrame,
    headlines: list[dict],
    settings,
) -> dict:
    blockers: list[str] = []
    blocker_details: list[str] = []
    bias = get_bias(df_1h, df_4h)

    news_eval = score_news(headlines, lookback_minutes=settings.news_lookback_minutes)
    gate = news_gate(news_eval["score"], bias)

    if bias == "NEUTRAL":
        return asdict(
            SignalResult(
                status="NO_TRADE",
                reason="Higher timeframe neutral",
                bias=bias,
                news_score=news_eval["score"],
                news_reason=gate["reason"],
                blockers=["bias: Higher timeframe neutral"],
                news_matches=news_eval["matched_items"],
            )
        )

    box = get_recent_box(df_15m, lookback=settings.box_lookback)
    swings = find_swings(df_15m, left=2, right=2)

    chase = is_chasing_move(df_15m, threshold_pct=settings.chase_threshold_pct, bars=3)
    if chase["triggered"]:
        blockers.append("Blocked by chase filter")
        blocker_details.append(
            f"chase_filter: direction={chase['direction']}, move_pct={chase['move_pct']:.2f}, threshold={chase['threshold_pct']:.2f}"
        )

    entry_type = "retest"
    used_breakout_fallback = False
    if bias == "LONG":
        entry = derive_retest_entry_long(df_15m, box["box_high"], settings.retest_tolerance_pct, settings.retest_lookback_bars)
        if entry is None:
            entry = box["box_high"]
            entry_type = "breakout_fallback"
            used_breakout_fallback = True
            blockers.append("Retest not confirmed; breakout fallback used")
        sl = box["box_low"] * (1 - settings.stop_buffer_pct)
    else:
        entry = derive_retest_entry_short(df_15m, box["box_low"], settings.retest_tolerance_pct, settings.retest_lookback_bars)
        if entry is None:
            entry = box["box_low"]
            entry_type = "breakout_fallback"
            used_breakout_fallback = True
            blockers.append("Retest not confirmed; breakout fallback used")
        sl = box["box_high"] * (1 + settings.stop_buffer_pct)

    risk_per_unit = abs(entry - sl)
    if risk_per_unit <= 0:
        return asdict(
            SignalResult(
                status="ERROR",
                reason="Invalid structure: stop distance <= 0",
                side=bias,
                bias=bias,
                news_score=news_eval["score"],
                news_reason=gate["reason"],
                blockers=blockers + ["structure: Invalid stop distance"],
                chase_info=chase,
                entry_type=entry_type,
                news_matches=news_eval["matched_items"],
            )
        )

    tp = calc_rr_targets(bias, entry, sl, rr=2.0)
    room_ok, room_reason, room_blockers = room_check(bias, entry, tp, swings["swing_highs"], swings["swing_lows"])
    if not room_ok:
        blockers.append("Blocked by room check")
        blocker_details.extend(
            [f"room_check: {item['type']}@{item['level']} ({item['distance_pct']:.2f}%)" for item in room_blockers]
        )

    if not gate["allowed"]:
        blockers.append("Blocked by news filter")
        blocker_details.append(f"news_filter: {gate['reason']}")

    reason = "All checks passed"
    if blockers:
        reason = blockers[0]

    result = SignalResult(
        status="NO_TRADE" if blockers else "READY",
        reason=reason,
        side=bias,
        bias=bias,
        entry=entry,
        sl=sl,
        tp=tp,
        risk_per_unit=risk_per_unit,
        news_score=news_eval["score"],
        news_reason=gate["reason"],
        blockers=blockers + blocker_details,
        chase_info=chase,
        entry_type=entry_type,
        news_matches=news_eval["matched_items"],
        structure_summary={
            "box_high": box.get("box_high"),
            "box_low": box.get("box_low"),
            "swing_highs_count": len(swings.get("swing_highs", [])),
            "swing_lows_count": len(swings.get("swing_lows", [])),
            "room_reason": room_reason,
            "room_blockers": room_blockers,
            "used_breakout_fallback": used_breakout_fallback,
        },
    )
    return asdict(result)
