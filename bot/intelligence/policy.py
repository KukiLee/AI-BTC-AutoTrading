"""Policy resolution for safely applying AI output to baseline and candidate streams."""

from __future__ import annotations

from .ab_test import compare_baseline_vs_ai
from .candidate_selector import select_ai_candidate


def resolve_trade_policy(signal: dict, candidates: list[dict], ai_setup_eval, ai_candidate_evals: dict[str, dict], settings) -> dict:
    mode = settings.policy_mode.value
    baseline_ready = signal.get("baseline_decision", signal.get("status")) == "READY"
    result = {
        "policy_mode": mode,
        "baseline_decision": signal.get("baseline_decision", "NO_TRADE"),
        "final_decision": "READY" if baseline_ready else "NO_TRADE",
        "execute": False,
        "reason": "baseline",
        "selected_candidate": None,
        "ab_comparison": None,
    }

    if mode == "baseline_alert_only":
        result["execute"] = False
        result["reason"] = "alerts_only"
    elif mode == "baseline_testnet_auto":
        result["execute"] = baseline_ready and settings.binance_testnet
        result["reason"] = "baseline_testnet_execution"
    elif mode == "ai_shadow":
        result["execute"] = False
        result["reason"] = "ai_shadow_non_executing"
    elif mode == "ai_filter_testnet":
        if not baseline_ready:
            result["execute"] = False
            result["final_decision"] = "NO_TRADE"
            result["reason"] = "cannot_promote_no_trade"
        elif ai_setup_eval and not ai_setup_eval.allow:
            result["execute"] = False
            result["final_decision"] = "NO_TRADE"
            result["reason"] = "ai_filtered_baseline"
        else:
            result["execute"] = True
            result["reason"] = "ai_filter_pass"
    elif mode == "ai_testnet_auto":
        selected = select_ai_candidate(candidates, ai_candidate_evals, settings)
        result["selected_candidate"] = selected
        if selected is None:
            result["execute"] = False
            result["final_decision"] = "NO_TRADE"
            result["reason"] = "no_candidate_passed_threshold"
        else:
            result["execute"] = True
            result["final_decision"] = "READY"
            result["reason"] = "ai_selected_candidate"
    elif mode == "baseline_vs_ai_ab_test":
        selected = select_ai_candidate(candidates, ai_candidate_evals, settings)
        ai_decision = {"final_decision": "READY" if selected else "NO_TRADE", "selected_candidate": selected}
        result["selected_candidate"] = selected
        result["ab_comparison"] = compare_baseline_vs_ai(signal, ai_decision)
        result["execute"] = baseline_ready and settings.binance_testnet and settings.execution_mode.value == "testnet_auto"
        result["reason"] = "ab_test_baseline_exec" if result["execute"] else "ab_test_no_exec"

    if result["execute"] and settings.execution_mode.value == "alert_only":
        result["execute"] = False
        result["reason"] = "execution_mode_alert_only"

    return result
