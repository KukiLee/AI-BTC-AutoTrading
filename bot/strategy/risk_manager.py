"""Risk sizing and target helpers."""

from __future__ import annotations

from utils.exceptions import RiskValidationError


def calc_rr_targets(side: str, entry: float, sl: float, rr: float = 2.0) -> float:
    risk_per_unit = abs(entry - sl)
    if risk_per_unit <= 0:
        raise RiskValidationError("Invalid setup: stop distance must be > 0")

    if side == "LONG":
        return entry + (risk_per_unit * rr)
    if side == "SHORT":
        return entry - (risk_per_unit * rr)
    raise RiskValidationError("Unsupported side")


def calc_position_size(balance: float, risk_pct: float, entry: float, sl: float) -> float:
    risk_amount = balance * risk_pct
    stop_distance = abs(entry - sl)
    if stop_distance <= 0:
        raise RiskValidationError("Cannot size with stop distance <= 0")
    qty = risk_amount / stop_distance
    return qty


def validate_position_size(qty: float, min_qty: float = 0.001, max_qty: float = 100.0) -> tuple[bool, str]:
    if qty <= 0:
        return False, "Quantity must be > 0"
    if qty < min_qty:
        return False, f"Quantity below minimum threshold: {qty} < {min_qty}"
    if qty > max_qty:
        return False, f"Quantity above maximum threshold: {qty} > {max_qty}"
    return True, "Quantity valid"


def apply_exchange_precision(qty: float, price: float, symbol_filters: dict | None) -> tuple[float, float]:
    """TODO Stage-2: apply exchange stepSize/tickSize precision from symbol filters.

    We intentionally return unchanged values in Stage-1 and require caller checks in auto modes.
    """
    return qty, price
