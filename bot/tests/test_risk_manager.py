import pytest

from strategy.risk_manager import calc_position_size, calc_rr_targets
from utils.exceptions import RiskValidationError


def test_rr_targets_long_short():
    assert calc_rr_targets("LONG", 100.0, 95.0, rr=2.0) == 110.0
    assert calc_rr_targets("SHORT", 100.0, 105.0, rr=2.0) == 90.0


def test_invalid_stop_distance():
    with pytest.raises(RiskValidationError):
        calc_rr_targets("LONG", 100.0, 100.0)
    with pytest.raises(RiskValidationError):
        calc_position_size(1000, 0.01, 100.0, 100.0)
