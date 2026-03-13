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
    trigger_timeframe: str = "15m"
    bias_1h: str | None = None
    bias_4h: str | None = None
    ma20_15m: float | None = None
    ma50_15m: float | None = None
    rsi14_15m: float | None = None
    ma20_1h: float | None = None
    ma50_1h: float | None = None
    rsi14_1h: float | None = None
    ma20_4h: float | None = None
    ma50_4h: float | None = None
    rsi14_4h: float | None = None
    box_high: float | None = None
    box_low: float | None = None
    room_check_passed: bool | None = None
    blocker_count: int = 0
    blocker_levels: list[str] = field(default_factory=list)
    chase_triggered: bool = False
    chase_move_pct: float | None = None
    news_score: int | None = None
    news_reason: str | None = None
    policy_mode: str = "baseline_alert_only"


@dataclass
class CandidateFeatureRow:
    setup_id: str
    candidate_id: str
    timestamp: str
    symbol: str
    candidate_type: str | None
    side: str | None
    entry: float | None
    sl: float | None
    tp: float | None
    rr: float | None
    hard_blocked: bool
    hard_block_reasons: list[str] = field(default_factory=list)
    reason: str | None = None
    news_score: int | None = None
    ma20_15m: float | None = None
    ma20_1h: float | None = None
    ma20_4h: float | None = None
    baseline_decision: str = "NO_TRADE"
    policy_mode: str = "baseline_alert_only"


@dataclass
class AIEvaluationResult:
    enabled: bool
    mode: str
    score: float | None
    recommendation: str
    confidence_bucket: str | None = None
    regime_tag: str | None = None
    reasons: list[str] = field(default_factory=list)
    agree_with_baseline: bool | None = None
    allow: bool = False


@dataclass
class PolicyDecisionRecord:
    setup_id: str
    candidate_id: str | None
    timestamp: str
    symbol: str
    policy_mode: str
    baseline_decision: str
    final_decision: str
    execute: bool
    reason: str
    ai_setup_score: float | None = None
    ai_candidate_score: float | None = None
    ai_selected_candidate_type: str | None = None
    baseline_vs_ai_agree: bool | None = None


@dataclass
class OutcomeLabel:
    setup_id: str
    trade_id: str | None
    timestamp: str
    symbol: str
    outcome_status: str
    hit_tp_first: bool
    hit_sl_first: bool
    mfe: float | None
    mae: float | None
    bars_to_outcome: int | None
    policy_mode: str
