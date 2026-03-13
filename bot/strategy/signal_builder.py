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
    timestamp: str = field(default_factory=to_iso)


def build_trade_setup(
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
    df_4h: pd.DataFrame,
    headlines: list[dict],
    settings,
) -> dict:
    blockers: list[str] = []
    bias = get_bias(df_1h, df_4h)

    news_eval = score_news(headlines)
    gate = news_gate(news_eval["score"], bias)

    if bias == "NEUTRAL":
        return asdict(
            SignalResult(
                status="NO_TRADE",
                reason="Higher timeframe bias is neutral",
                bias=bias,
                news_score=news_eval["score"],
                news_reason=gate["reason"],
                blockers=["Bias neutral"],
            )
        )

    box = get_recent_box(df_15m, lookback=settings.box_lookback)
    swings = find_swings(df_15m, left=2, right=2)

    chase = is_chasing_move(df_15m, threshold_pct=settings.chase_threshold_pct, bars=3)
    if chase:
        blockers.append("Momentum chase filter triggered")

    if bias == "LONG":
        entry = box["box_high"]
        sl = box["box_low"] * (1 - settings.stop_buffer_pct)
    else:
        entry = box["box_low"]
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
                blockers=blockers + ["Invalid stop distance"],
                chase_info={"triggered": chase},
            )
        )

    tp = calc_rr_targets(bias, entry, sl, rr=2.0)
    room_ok, room_reason = room_check(
        bias, entry, tp, swings["swing_highs"], swings["swing_lows"]
    )
    if not room_ok:
        blockers.append(room_reason)

    if not gate["allowed"]:
        blockers.append(gate["reason"])

    if blockers:
        return asdict(
            SignalResult(
                status="NO_TRADE",
                reason="Setup blocked by filters",
                side=bias,
                bias=bias,
                entry=entry,
                sl=sl,
                tp=tp,
                risk_per_unit=risk_per_unit,
                news_score=news_eval["score"],
                news_reason=gate["reason"],
                blockers=blockers,
                chase_info={"triggered": chase},
            )
        )

    return asdict(
        SignalResult(
            status="READY",
            reason="All checks passed",
            side=bias,
            bias=bias,
            entry=entry,
            sl=sl,
            tp=tp,
            risk_per_unit=risk_per_unit,
            news_score=news_eval["score"],
            news_reason=gate["reason"],
            blockers=[],
            chase_info={"triggered": chase},
        )
    )
