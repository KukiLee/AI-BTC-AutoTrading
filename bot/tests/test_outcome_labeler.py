from intelligence.outcome_labeler import label_trade_outcome_from_path


def test_tp_first_labeling_long():
    out = label_trade_outcome_from_path(
        setup_id="s1",
        side="LONG",
        entry=100.0,
        tp=102.0,
        sl=99.0,
        candles=[{"high": 101.0, "low": 99.5}, {"high": 102.1, "low": 100.2}],
    )
    assert out.outcome_status == "tp_first"
    assert out.hit_tp_first is True


def test_sl_first_labeling_long():
    out = label_trade_outcome_from_path(
        setup_id="s2",
        side="LONG",
        entry=100.0,
        tp=102.0,
        sl=99.0,
        candles=[{"high": 100.2, "low": 98.8}],
    )
    assert out.outcome_status == "sl_first"
    assert out.hit_sl_first is True


def test_unresolved_labeling_when_no_barrier_hit():
    out = label_trade_outcome_from_path(
        setup_id="s3",
        side="SHORT",
        entry=100.0,
        tp=98.0,
        sl=101.0,
        candles=[{"high": 100.5, "low": 99.5}, {"high": 100.6, "low": 99.6}],
    )
    assert out.outcome_status == "unresolved"
    assert out.bars_to_outcome is None


def test_mfe_mae_sanity():
    out = label_trade_outcome_from_path(
        setup_id="s4",
        side="LONG",
        entry=100.0,
        tp=105.0,
        sl=95.0,
        candles=[{"high": 103.0, "low": 99.0}, {"high": 104.0, "low": 98.0}],
    )
    assert out.mfe is not None and out.mfe > 0
    assert out.mae is not None and out.mae > 0
