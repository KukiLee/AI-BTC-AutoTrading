"""A/B helpers for baseline vs constrained AI decision comparison."""

from __future__ import annotations


def compare_baseline_vs_ai(baseline_signal: dict, ai_policy_result: dict) -> dict:
    baseline_ready = baseline_signal.get("baseline_decision", baseline_signal.get("status")) == "READY"
    ai_ready = ai_policy_result.get("final_decision") == "READY"
    selected = ai_policy_result.get("selected_candidate") or {}
    same_side = baseline_signal.get("side") == selected.get("side") if ai_ready and baseline_ready else None
    same_entry_type = baseline_signal.get("entry_type") in (selected.get("candidate_type") or "") if ai_ready and baseline_ready else None

    disagreement_reason = "none"
    if baseline_ready and not ai_ready:
        disagreement_reason = "ai_blocked_baseline"
    elif not baseline_ready and ai_ready:
        disagreement_reason = "ai_selected_candidate"

    return {
        "baseline_ready": baseline_ready,
        "ai_ready": ai_ready,
        "same_side": same_side,
        "same_entry_type": same_entry_type,
        "ai_blocked_baseline": baseline_ready and not ai_ready,
        "ai_selected_candidate_type": selected.get("candidate_type"),
        "disagreement_reason": disagreement_reason,
    }
