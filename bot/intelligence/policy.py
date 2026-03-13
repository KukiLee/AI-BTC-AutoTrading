"""Policy resolution for safely applying AI output to baseline signal."""

from __future__ import annotations


def resolve_trade_policy(signal: dict, ai_eval, settings) -> dict:
    baseline_ready = signal.get("status") == "READY"
    mode = settings.ai_evaluation_mode

    result = {
        "mode": mode,
        "baseline_ready": baseline_ready,
        "final_execute": baseline_ready,
        "ai_considered": bool(ai_eval and getattr(ai_eval, "enabled", False)),
        "ai_blocked": False,
        "policy_reason": "baseline_authoritative",
    }

    if mode in {"off", "shadow", "advisory"}:
        return result

    if mode == "filter_testnet":
        if settings.execution_mode.value != "testnet_auto":
            result["policy_reason"] = "filter_testnet_not_allowed_outside_testnet"
            return result

        if not baseline_ready:
            result["policy_reason"] = "cannot_promote_no_trade"
            return result

        score = getattr(ai_eval, "score", None)
        if score is not None and score < settings.ai_min_score_to_allow:
            result["final_execute"] = False
            result["ai_blocked"] = True
            result["policy_reason"] = "ai_filtered_low_score"
        else:
            result["policy_reason"] = "ai_filter_pass"
        return result

    result["policy_reason"] = "unknown_mode_fallback_baseline"
    return result
