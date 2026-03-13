import pytest

from strategy.risk_manager import (
    apply_exchange_precision,
    calc_position_size,
    calc_rr_targets,
    normalize_order_values,
    round_price_to_tick,
    round_to_step,
)
from utils.exceptions import RiskValidationError


SYMBOL_FILTERS = {
    "PRICE_FILTER": {"tickSize": "0.10"},
    "LOT_SIZE": {"minQty": "0.001", "maxQty": "100.000", "stepSize": "0.001"},
    "MARKET_LOT_SIZE": {"minQty": "0.001", "maxQty": "100.000", "stepSize": "0.001"},
    "MIN_NOTIONAL": {"minNotional": "5"},
}


def test_rr_targets_long_short():
    assert calc_rr_targets("LONG", 100.0, 95.0, rr=2.0) == 110.0
    assert calc_rr_targets("SHORT", 100.0, 105.0, rr=2.0) == 90.0


def test_invalid_stop_distance():
    with pytest.raises(RiskValidationError):
        calc_rr_targets("LONG", 100.0, 100.0)
    with pytest.raises(RiskValidationError):
        calc_position_size(1000, 0.01, 100.0, 100.0)


def test_round_to_step():
    assert round_to_step(0.123456, 0.001) == pytest.approx(0.123)


def test_round_price_to_tick():
    assert round_price_to_tick(123.47, 0.1, side="LONG") == pytest.approx(123.4)
    assert round_price_to_tick(123.47, 0.1, side="SHORT") == pytest.approx(123.5)


def test_precision_missing_raises():
    with pytest.raises(RiskValidationError):
        apply_exchange_precision(1.0, 100.0, None)


def test_normalized_values_align():
    normalized = normalize_order_values(0.123456, 25000.123, 26000.987, SYMBOL_FILTERS, "LONG")
    assert normalized["normalized_qty"] == pytest.approx(0.123)
    assert normalized["normalized_sl"] == pytest.approx(25000.1)
    assert normalized["normalized_tp"] == pytest.approx(26000.9)
