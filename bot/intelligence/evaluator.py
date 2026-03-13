"""AI evaluation scaffold (heuristic now, ML swappable later)."""

from __future__ import annotations

from ..storage.schemas import AIEvaluationResult


def _confidence_bucket(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


def _finalize(score: float, settings, reasons: list[str], mode: str, agree_with_baseline=None) -> AIEvaluationResult:
    score = max(0.0, min(1.0, score))
    allow = score >= settings.ai_min_score_to_allow
    return AIEvaluationResult(
        enabled=True,
        mode=mode,
        score=score,
        recommendation="allow" if allow else "block",
        confidence_bucket=_confidence_bucket(score),
        regime_tag="constrained_universe",
        reasons=reasons or ["neutral_profile"],
        agree_with_baseline=agree_with_baseline,
        allow=allow,
    )


def evaluate_setup(feature_row, settings) -> AIEvaluationResult:
    mode = settings.policy_mode.value
    if not settings.ai_evaluation_enabled:
        return AIEvaluationResult(False, mode, None, "allow", reasons=["ai_disabled"], allow=True)

    score = 0.5
    reasons: list[str] = []
    if feature_row.chase_triggered:
        score -= 0.20
        reasons.append("chase_penalty")
    if feature_row.blocker_count > 0:
        score -= 0.15
        reasons.append("blocker_penalty")
    if (feature_row.news_score or 0) < 0:
        score -= 0.15
        reasons.append("negative_news_penalty")
    if feature_row.retest_confirmed:
        score += 0.15
        reasons.append("clean_retest_reward")
    if feature_row.room_check_passed:
        score += 0.15
        reasons.append("room_check_reward")
    if feature_row.bias and feature_row.bias == feature_row.bias_1h == feature_row.bias_4h:
        score += 0.15
        reasons.append("htf_alignment_reward")

    agree = None
    if feature_row.baseline_decision in {"READY", "NO_TRADE"}:
        allow = score >= settings.ai_min_score_to_allow
        agree = (feature_row.baseline_decision == "READY" and allow) or (
            feature_row.baseline_decision == "NO_TRADE" and not allow
        )
    return _finalize(score, settings, reasons, mode, agree_with_baseline=agree)


def evaluate_candidate(candidate_feature_row, settings) -> AIEvaluationResult:
    mode = settings.policy_mode.value
    if not settings.ai_evaluation_enabled:
        return AIEvaluationResult(False, mode, None, "allow", reasons=["ai_disabled"], allow=True)

    score = 0.5
    reasons: list[str] = []
    if candidate_feature_row.hard_blocked:
        score = 0.0
        reasons.append("hard_blocked")
    else:
        if candidate_feature_row.candidate_type and "retest" in candidate_feature_row.candidate_type:
            score += 0.15
            reasons.append("retest_bonus")
        if (candidate_feature_row.news_score or 0) < 0:
            score -= 0.15
            reasons.append("negative_news_penalty")
        if candidate_feature_row.rr is not None and candidate_feature_row.rr >= 2.0:
            score += 0.10
            reasons.append("rr_reward")

    return _finalize(score, settings, reasons, mode)
