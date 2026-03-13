import pandas as pd

from bot.config import Settings
from bot.intelligence.feature_builder import build_candidate_feature_row, build_setup_feature_row


def _settings():
    return Settings(BINANCE_TESTNET=True)


def _dfs():
    df_15m = pd.DataFrame([{"ma20": 99, "ma50": 98, "rsi14": 55}])
    df_1h = pd.DataFrame([{"ma20": 100, "ma50": 99, "rsi14": 57}])
    df_4h = pd.DataFrame([{"ma20": 101, "ma50": 100, "rsi14": 59}])
    return df_15m, df_1h, df_4h


def test_setup_feature_row_builds():
    signal = {
        "setup_id": "s1",
        "timestamp": "t",
        "symbol": "BTCUSDT",
        "status": "READY",
        "baseline_decision": "READY",
        "baseline_reason": "ok",
        "side": "LONG",
        "bias": "LONG",
        "entry": 1,
        "sl": 0.9,
        "tp": 1.2,
        "entry_type": "retest",
        "retest_confirmed": True,
    }
    row = build_setup_feature_row(signal, *_dfs(), _settings())
    assert row.setup_id == "s1"


def test_candidate_feature_row_builds():
    signal = {"setup_id": "s1", "timestamp": "t", "symbol": "BTCUSDT", "baseline_decision": "READY"}
    candidate = {"candidate_id": "c1", "candidate_type": "retest_long", "side": "LONG", "entry": 1, "sl": 0.9, "tp": 1.2, "rr": 2, "hard_blocked": False}
    row = build_candidate_feature_row(candidate, signal, *_dfs(), _settings())
    assert row.candidate_id == "c1"


def test_missing_optional_values_do_not_crash():
    signal = {"setup_id": "s1", "timestamp": "t", "symbol": "BTCUSDT", "status": "NO_TRADE", "baseline_decision": "NO_TRADE", "baseline_reason": "x"}
    df = pd.DataFrame([{}])
    row = build_setup_feature_row(signal, df, df, df, _settings())
    assert row.ma20_15m is None
