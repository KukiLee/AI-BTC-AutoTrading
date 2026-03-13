import pandas as pd

from strategy.signal_builder import derive_retest_entry_long
from strategy.setup_rules import get_bias, is_chasing_move, room_check


def test_bias_detection_long_short_neutral():
    df_1h_long = pd.DataFrame([{"close": 101.0, "ma20": 100.0}])
    df_4h_long = pd.DataFrame([{"close": 102.0, "ma50": 100.0}])
    assert get_bias(df_1h_long, df_4h_long) == "LONG"

    df_1h_short = pd.DataFrame([{"close": 99.0, "ma20": 100.0}])
    df_4h_short = pd.DataFrame([{"close": 98.0, "ma50": 100.0}])
    assert get_bias(df_1h_short, df_4h_short) == "SHORT"

    df_1h_neutral = pd.DataFrame([{"close": 101.0, "ma20": 100.0}])
    df_4h_neutral = pd.DataFrame([{"close": 98.0, "ma50": 100.0}])
    assert get_bias(df_1h_neutral, df_4h_neutral) == "NEUTRAL"


def test_room_check_returns_blocker_detail_for_long():
    ok, reason, blockers = room_check("LONG", 100.0, 110.0, swing_highs=[101.0, 105.0], swing_lows=[])
    assert not ok
    assert "Intermediate resistance" in reason
    assert blockers[0]["type"] == "resistance"


def test_room_check_returns_blocker_detail_for_short():
    ok, reason, blockers = room_check("SHORT", 100.0, 90.0, swing_highs=[], swing_lows=[99.0, 95.0])
    assert not ok
    assert "Intermediate support" in reason
    assert blockers[0]["type"] == "support"


def test_chase_filter_returns_direction_and_move_pct():
    df = pd.DataFrame([{"close": 100.0}, {"close": 101.0}, {"close": 103.0}])
    chase = is_chasing_move(df, threshold_pct=1.0, bars=3)
    assert chase["triggered"] is True
    assert chase["direction"] == "UP"
    assert isinstance(chase["move_pct"], float)


def test_retest_helper_long():
    df = pd.DataFrame(
        [
            {"low": 98.0, "close": 99.0},
            {"low": 99.8, "close": 100.2},
            {"low": 100.0, "close": 100.5},
        ]
    )
    assert derive_retest_entry_long(df, box_high=100.0, tolerance_pct=0.003, lookback_bars=3) == 100.0
