import pandas as pd

from bot.indicators.ta import add_indicators


def test_indicator_columns_exist_and_length_unchanged():
    df = pd.DataFrame({"close": [float(i) for i in range(1, 260)]})
    out = add_indicators(df)
    assert len(out) == len(df)
    assert "ma20" in out.columns
    assert "ma50" in out.columns
    assert "ma200" in out.columns
    assert "rsi14" in out.columns


def test_indicator_early_nan_regions_are_expected():
    df = pd.DataFrame({"close": [float(i) for i in range(1, 260)]})
    out = add_indicators(df)
    assert out["ma20"].isna().sum() > 0
    assert out["ma50"].isna().sum() > 0
    assert out["ma200"].isna().sum() > 0
