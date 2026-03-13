from bot.intelligence.ab_test import compare_baseline_vs_ai


def test_disagreement_case_recorded():
    baseline = {"baseline_decision": "READY", "side": "LONG", "entry_type": "retest"}
    ai = {"final_decision": "NO_TRADE", "selected_candidate": None}
    out = compare_baseline_vs_ai(baseline, ai)
    assert out["ai_blocked_baseline"] is True
    assert out["disagreement_reason"] == "ai_blocked_baseline"


def test_same_decision_case_recorded():
    baseline = {"baseline_decision": "READY", "side": "LONG", "entry_type": "retest"}
    ai = {"final_decision": "READY", "selected_candidate": {"side": "LONG", "candidate_type": "retest_long"}}
    out = compare_baseline_vs_ai(baseline, ai)
    assert out["ai_ready"] is True
    assert out["same_side"] is True
