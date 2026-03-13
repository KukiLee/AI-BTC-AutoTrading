from dataclasses import dataclass

from bot.config import Settings
from bot.intelligence.policy import resolve_trade_policy


@dataclass
class DummyEval:
    enabled: bool
    score: float


def _settings(mode: str, execution_mode: str = "alert_only"):
    return Settings(
        BINANCE_TESTNET=True,
        EXECUTION_MODE=execution_mode,
        AI_EVALUATION_MODE=mode,
        AI_MIN_SCORE_TO_ALLOW=0.70,
    )


def test_off_mode_baseline_only():
    result = resolve_trade_policy({"status": "READY"}, DummyEval(enabled=True, score=0.1), _settings("off"))
    assert result["final_execute"] is True


def test_shadow_mode_baseline_only():
    result = resolve_trade_policy({"status": "READY"}, DummyEval(enabled=True, score=0.1), _settings("shadow"))
    assert result["final_execute"] is True


def test_filter_testnet_cannot_promote_no_trade():
    result = resolve_trade_policy(
        {"status": "NO_TRADE"},
        DummyEval(enabled=True, score=0.95),
        _settings("filter_testnet", execution_mode="testnet_auto"),
    )
    assert result["final_execute"] is False


def test_filter_testnet_blocks_ready_below_threshold():
    result = resolve_trade_policy(
        {"status": "READY"},
        DummyEval(enabled=True, score=0.2),
        _settings("filter_testnet", execution_mode="testnet_auto"),
    )
    assert result["final_execute"] is False
    assert result["ai_blocked"] is True


def test_live_mode_baseline_authoritative_by_default():
    settings = Settings(
        BINANCE_TESTNET=False,
        EXECUTION_MODE="live_auto",
        ENABLE_LIVE_TRADING=True,
        AI_EVALUATION_MODE="off",
    )
    result = resolve_trade_policy({"status": "READY"}, DummyEval(enabled=True, score=0.1), settings)
    assert result["final_execute"] is True
