from bot.config import Settings
from bot.strategy.candidate_builder import build_trade_candidates


def _settings():
    return Settings(BINANCE_TESTNET=True, POLICY_MODE="ai_testnet_auto", AI_CAN_EXECUTE_TESTNET=True)


def test_baseline_ready_produces_candidate():
    signal = {
        "setup_id": "s1",
        "symbol": "BTCUSDT",
        "status": "READY",
        "side": "LONG",
        "entry": 100.0,
        "sl": 99.0,
        "tp": 102.0,
        "entry_type": "retest",
        "blockers": [],
    }
    cands = build_trade_candidates(signal, None, None, None, _settings())
    assert len(cands) == 1
    assert cands[0]["candidate_type"] == "retest_long"


def test_hard_blocked_propagates():
    signal = {
        "setup_id": "s2",
        "symbol": "BTCUSDT",
        "status": "READY",
        "side": "SHORT",
        "entry": 100.0,
        "sl": 101.0,
        "tp": 98.0,
        "entry_type": "retest",
        "blockers": ["Blocked by news filter"],
    }
    cands = build_trade_candidates(signal, None, None, None, _settings())
    assert cands[0]["hard_blocked"] is True


def test_candidate_type_within_allowed_universe():
    signal = {
        "setup_id": "s3",
        "symbol": "BTCUSDT",
        "status": "READY",
        "side": "SHORT",
        "entry": 100.0,
        "sl": 101.0,
        "tp": 98.0,
        "entry_type": "breakout_fallback",
        "blockers": [],
    }
    cands = build_trade_candidates(signal, None, None, None, _settings())
    assert cands[0]["candidate_type"] in {
        "retest_long",
        "retest_short",
        "breakout_fallback_long",
        "breakout_fallback_short",
    }
