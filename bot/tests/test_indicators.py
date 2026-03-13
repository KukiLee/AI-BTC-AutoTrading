import pandas as pd

from indicators.ta import add_indicators


def test_indicator_columns_exist():
    df = pd.DataFrame({"close": [float(i) for i in range(1, 260)]})
    out = add_indicators(df)
    assert "ma20" in out.columns
    assert "ma50" in out.columns
    assert "ma200" in out.columns
    assert "rsi14" in out.columns
