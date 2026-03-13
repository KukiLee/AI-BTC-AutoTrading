import pandas as pd

from strategy.signal_builder import derive_retest_entry_long
from strategy.setup_rules import get_bias, is_chasing_move, room_check


def test_bias_detection_long():
    df_1h = pd.DataFrame([{"close": 101.0, "ma20": 100.0}])
    df_4h = pd.DataFrame([{"close": 102.0, "ma50": 100.0}])
    assert get_bias(df_1h, df_4h) == "LONG"


def test_room_check_blocks_long_with_blockers():
    ok, reason, blockers = room_check("LONG", 100.0, 110.0, swing_highs=[101.0, 105.0], swing_lows=[])
    assert not ok
    assert "Intermediate resistance" in reason
    assert blockers


def test_chase_filter_returns_direction():
    df = pd.DataFrame([{"close": 100.0}, {"close": 101.0}, {"close": 103.0}])
    chase = is_chasing_move(df, threshold_pct=1.0, bars=3)
    assert chase["triggered"] is True
    assert chase["direction"] == "UP"


def test_retest_helper_long():
    df = pd.DataFrame(
        [
            {"low": 98.0, "close": 99.0},
            {"low": 99.8, "close": 100.2},
            {"low": 100.0, "close": 100.5},
        ]
    )
    assert derive_retest_entry_long(df, box_high=100.0, tolerance_pct=0.003, lookback_bars=3) == 100.0
