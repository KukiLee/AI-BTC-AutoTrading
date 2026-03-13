from bot.intelligence.outcome_labeler import label_trade_outcome_from_candles


def test_tp_first():
    out = label_trade_outcome_from_candles(100, 99, 102, "LONG", [{"high": 102.1, "low": 99.5}])
    assert out["outcome_status"] == "tp_first"


def test_sl_first():
    out = label_trade_outcome_from_candles(100, 99, 102, "LONG", [{"high": 100.2, "low": 98.9}])
    assert out["outcome_status"] == "sl_first"


def test_unresolved():
    out = label_trade_outcome_from_candles(100, 99, 102, "LONG", [{"high": 101.1, "low": 99.2}])
    assert out["outcome_status"] == "unresolved"


def test_mfe_mae_sanity():
    out = label_trade_outcome_from_candles(100, 95, 105, "LONG", [{"high": 103.0, "low": 98.0}])
    assert out["mfe"] > 0
    assert out["mae"] > 0
