import pandas as pd

from strategy.setup_rules import get_bias, room_check


def test_bias_detection_long():
    df_1h = pd.DataFrame([{"close": 101.0, "ma20": 100.0}])
    df_4h = pd.DataFrame([{"close": 102.0, "ma50": 100.0}])
    assert get_bias(df_1h, df_4h) == "LONG"


def test_room_check_blocks_long():
    ok, reason = room_check("LONG", 100.0, 110.0, swing_highs=[105.0], swing_lows=[])
    assert not ok
    assert "Intermediate resistance" in reason
