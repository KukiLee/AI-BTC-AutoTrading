from dataclasses import dataclass

from bot.config import Settings
from bot.intelligence.policy import resolve_trade_policy


@dataclass
class DummyEval:
    allow: bool
    score: float


def _settings(mode: str):
    kwargs = {"POLICY_MODE": mode, "BINANCE_TESTNET": True}
    if mode == "ai_testnet_auto":
        kwargs["AI_CAN_EXECUTE_TESTNET"] = True
    return Settings(**kwargs)


def test_baseline_alert_only_never_executes():
    out = resolve_trade_policy({"baseline_decision": "READY"}, [], DummyEval(True, 0.8), {}, _settings("baseline_alert_only"))
    assert out["execute"] is False


def test_ai_shadow_never_changes_execution():
    out = resolve_trade_policy({"baseline_decision": "READY"}, [], DummyEval(False, 0.2), {}, _settings("ai_shadow"))
    assert out["final_decision"] == "READY"


def test_ai_filter_can_block_ready_but_not_promote_no_trade():
    st = _settings("ai_filter_testnet")
    blocked = resolve_trade_policy({"baseline_decision": "READY"}, [], DummyEval(False, 0.1), {}, st)
    assert blocked["execute"] is False
    no_promote = resolve_trade_policy({"baseline_decision": "NO_TRADE"}, [], DummyEval(True, 0.9), {}, st)
    assert no_promote["final_decision"] == "NO_TRADE"


def test_ai_testnet_auto_choose_only_valid_candidates():
    st = _settings("ai_testnet_auto")
    cands = [{"candidate_id": "x", "hard_blocked": False, "candidate_type": "retest_long"}]
    evals = {"x": {"score": 0.9}}
    out = resolve_trade_policy({"baseline_decision": "NO_TRADE"}, cands, DummyEval(True, 0.8), evals, st)
    assert out["selected_candidate"]["candidate_id"] == "x"


def test_ab_test_returns_both_streams():
    out = resolve_trade_policy(
        {"baseline_decision": "READY", "side": "LONG", "entry_type": "retest"},
        [],
        DummyEval(True, 0.8),
        {},
        _settings("baseline_vs_ai_ab_test"),
    )
    assert out["ab_comparison"] is not None
