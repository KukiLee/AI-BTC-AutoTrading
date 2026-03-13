"""AI evaluation scaffold (heuristic now, ML swappable later)."""

from __future__ import annotations

from storage.schemas import AIEvaluationResult, SetupFeatureRow


def _confidence_bucket(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


def evaluate_setup(feature_row: SetupFeatureRow, settings) -> AIEvaluationResult:
    mode = settings.ai_evaluation_mode
    if not settings.ai_evaluation_enabled or mode == "off":
        return AIEvaluationResult(enabled=False, mode=mode, score=None, recommendation="allow", reasons=["ai_disabled"])

    score = 0.5
    reasons: list[str] = []

    if feature_row.chase_triggered:
        score -= 0.25
        reasons.append("chase_triggered")
    if feature_row.blocker_count >= 2:
        score -= 0.20
        reasons.append("multiple_blockers")
    if (feature_row.news_score or 0) <= -2:
        score -= 0.15
        reasons.append("negative_news")
    if feature_row.retest_confirmed and feature_row.entry_type == "retest":
        score += 0.20
        reasons.append("clean_retest")
    if feature_row.room_check_passed:
        score += 0.15
        reasons.append("room_check_passed")
    if feature_row.bias in {"LONG", "SHORT"} and feature_row.status == "READY":
        score += 0.10
        reasons.append("aligned_bias")

    score = max(0.0, min(1.0, score))
    recommendation = "allow" if score >= settings.ai_min_score_to_allow else "block"
    regime_tag = "trend_following" if feature_row.status == "READY" and (feature_row.news_score or 0) >= 0 else "high_news_risk"
    agree = None
    if feature_row.baseline_decision in {"READY", "NO_TRADE"}:
        agree = (feature_row.baseline_decision == "READY" and recommendation == "allow") or (
            feature_row.baseline_decision == "NO_TRADE" and recommendation == "block"
        )

    return AIEvaluationResult(
        enabled=True,
        mode=mode,
        score=score,
        recommendation=recommendation,
        confidence_bucket=_confidence_bucket(score),
        regime_tag=regime_tag,
        agree_with_baseline=agree,
        reasons=reasons or ["neutral_profile"],
    )
