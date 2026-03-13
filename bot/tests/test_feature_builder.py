import pandas as pd

from config import Settings
from intelligence.feature_builder import build_setup_feature_row


def _settings():
    return Settings(BINANCE_TESTNET=True, EXECUTION_MODE="alert_only")


def _dfs():
    df_15m = pd.DataFrame([{"close": 100, "ma20": 99, "ma50": 98, "ma200": 95, "rsi14": 55}])
    df_1h = pd.DataFrame([{"close": 101, "ma20": 100, "ma50": 99, "ma200": 96, "rsi14": 57}])
    df_4h = pd.DataFrame([{"close": 102, "ma20": 100, "ma50": 99, "ma200": 97, "rsi14": 59}])
    return df_15m, df_1h, df_4h


def test_feature_row_builds_for_ready_signal():
    signal = {
        "setup_id": "abc",
        "timestamp": "2025-01-01T00:00:00Z",
        "symbol": "BTCUSDT",
        "status": "READY",
        "baseline_decision": "READY",
        "baseline_reason": "All checks passed",
        "side": "LONG",
        "bias": "LONG",
        "entry": 100.0,
        "sl": 99.0,
        "tp": 102.0,
        "entry_type": "retest",
        "retest_confirmed": True,
        "structure_summary": {"box_high": 100.5, "box_low": 98.5, "room_check_passed": True},
        "blockers": [],
        "chase_info": {"triggered": False, "move_pct": 0.2},
        "news_score": 0,
        "news_reason": "ok",
        "news_matches": [],
    }
    row = build_setup_feature_row(signal, *_dfs(), _settings())
    assert row.status == "READY"
    assert row.rr == 2.0
    assert row.room_check_passed is True


def test_feature_row_builds_for_no_trade_signal():
    signal = {
        "setup_id": "abc2",
        "timestamp": "2025-01-01T00:00:00Z",
        "symbol": "BTCUSDT",
        "status": "NO_TRADE",
        "baseline_decision": "NO_TRADE",
        "baseline_reason": "Blocked by news",
        "entry_type": "breakout_fallback",
        "retest_confirmed": False,
        "structure_summary": {"box_high": 100.5, "box_low": 98.5, "room_check_passed": False},
        "blockers": ["Blocked by news"],
        "chase_info": {"triggered": True, "move_pct": 2.1},
        "news_score": -2,
        "news_reason": "high-risk",
        "news_matches": [{"keyword": "hack"}],
    }
    row = build_setup_feature_row(signal, *_dfs(), _settings())
    assert row.status == "NO_TRADE"
    assert row.blocker_count == 1
    assert row.entry is None


def test_feature_builder_handles_missing_optional_fields():
    signal = {
        "setup_id": "abc3",
        "timestamp": "2025-01-01T00:00:00Z",
        "symbol": "BTCUSDT",
        "status": "NO_TRADE",
        "baseline_decision": "NO_TRADE",
        "baseline_reason": "neutral",
    }
    df_15m = pd.DataFrame([{"close": 100}])
    df_1h = pd.DataFrame([{"close": 100}])
    df_4h = pd.DataFrame([{"close": 100}])
    row = build_setup_feature_row(signal, df_15m, df_1h, df_4h, _settings())
    assert row.ma20_15m is None
    assert row.news_score is None
