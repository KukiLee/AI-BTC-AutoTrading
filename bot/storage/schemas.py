"""Typed schemas used by dataset logging and AI scaffolding."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SetupFeatureRow:
    setup_id: str
    timestamp: str
    symbol: str
    status: str
    baseline_decision: str
    baseline_reason: str
    side: str | None = None
    bias: str | None = None
    entry: float | None = None
    sl: float | None = None
    tp: float | None = None
    rr: float | None = None
    entry_type: str | None = None
    retest_confirmed: bool | None = None
    current_price: float | None = None
    ma20_15m: float | None = None
    ma50_15m: float | None = None
    ma200_15m: float | None = None
    rsi14_15m: float | None = None
    ma20_1h: float | None = None
    ma50_1h: float | None = None
    ma200_1h: float | None = None
    rsi14_1h: float | None = None
    ma20_4h: float | None = None
    ma50_4h: float | None = None
    ma200_4h: float | None = None
    rsi14_4h: float | None = None
    box_high: float | None = None
    box_low: float | None = None
    box_range_pct: float | None = None
    recent_swing_high_count: int | None = None
    recent_swing_low_count: int | None = None
    room_check_passed: bool | None = None
    blocker_count: int = 0
    blocker_levels: list[str] = field(default_factory=list)
    chase_triggered: bool = False
    chase_move_pct: float | None = None
    news_score: int | None = None
    news_reason: str = ""
    news_match_count: int = 0
    execution_mode: str = "alert_only"
    ai_mode: str = "shadow"


@dataclass
class AIEvaluationResult:
    enabled: bool
    mode: str
    score: float | None
    recommendation: str
    confidence_bucket: str | None = None
    regime_tag: str | None = None
    agree_with_baseline: bool | None = None
    reasons: list[str] = field(default_factory=list)


@dataclass
class OutcomeLabel:
    setup_id: str
    trade_id: str | None
    outcome_status: str
    hit_tp_first: bool
    hit_sl_first: bool
    pnl_r: float | None
    pnl_usd: float | None = None
    mfe: float | None = None
    mae: float | None = None
    bars_to_outcome: int | None = None
    labeled_at: str = ""
