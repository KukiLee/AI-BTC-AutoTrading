"""Risk sizing and target helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_UP

from ..utils.exceptions import RiskValidationError


@dataclass
class PrecisionRules:
    min_qty: Decimal
    max_qty: Decimal
    step_size: Decimal
    tick_size: Decimal
    min_notional: Decimal | None = None


def _to_decimal(value: float | str | Decimal | None, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


def round_to_step(value: float, step: float) -> float:
    dec_value = _to_decimal(value)
    dec_step = _to_decimal(step)
    if dec_step <= 0:
        raise RiskValidationError(f"Invalid step size: {step}")
    rounded = (dec_value / dec_step).to_integral_value(rounding=ROUND_DOWN) * dec_step
    return float(rounded)


def round_price_to_tick(price: float, tick_size: float, side: str | None = None) -> float:
    dec_price = _to_decimal(price)
    dec_tick = _to_decimal(tick_size)
    if dec_tick <= 0:
        raise RiskValidationError(f"Invalid tick size: {tick_size}")

    ratio = dec_price / dec_tick
    # Stop/TP rounding can be side-aware in certain exchange/order-type combinations.
    # Keep explicit behavior (SHORT rounds up, others round down) to preserve legacy intent.
    if side == "SHORT":
        rounded = ratio.to_integral_value(rounding=ROUND_UP) * dec_tick
    else:
        rounded = ratio.to_integral_value(rounding=ROUND_DOWN) * dec_tick
    return float(rounded)


def extract_precision_rules(symbol_filters: dict) -> PrecisionRules:
    if not isinstance(symbol_filters, dict):
        raise RiskValidationError("Invalid symbol filters payload: expected dict")

    lot_filter = symbol_filters.get("LOT_SIZE") or {}
    market_lot_filter = symbol_filters.get("MARKET_LOT_SIZE") or {}
    price_filter = symbol_filters.get("PRICE_FILTER") or {}
    notional_filter = symbol_filters.get("MIN_NOTIONAL") or symbol_filters.get("NOTIONAL") or {}

    min_qty = _to_decimal(lot_filter.get("minQty") or market_lot_filter.get("minQty"))
    max_qty = _to_decimal(lot_filter.get("maxQty") or market_lot_filter.get("maxQty"))
    step_size = _to_decimal(lot_filter.get("stepSize") or market_lot_filter.get("stepSize"))
    tick_size = _to_decimal(price_filter.get("tickSize"))
    min_notional = _to_decimal(notional_filter.get("notional") or notional_filter.get("minNotional"))

    missing_fields: list[str] = []
    if min_qty <= 0:
        missing_fields.append("minQty")
    if max_qty <= 0:
        missing_fields.append("maxQty")
    if step_size <= 0:
        missing_fields.append("stepSize")
    if tick_size <= 0:
        missing_fields.append("tickSize")

    if missing_fields:
        raise RiskValidationError(
            "Missing or invalid required exchange precision fields: " + ", ".join(missing_fields)
        )

    return PrecisionRules(
        min_qty=min_qty,
        max_qty=max_qty,
        step_size=step_size,
        tick_size=tick_size,
        min_notional=min_notional if min_notional > 0 else None,
    )


def normalize_order_values(
    qty: float,
    sl: float,
    tp: float,
    symbol_filters: dict,
    side: str,
) -> dict:
    rules = extract_precision_rules(symbol_filters)

    normalized_qty = round_to_step(qty, float(rules.step_size))
    normalized_sl = round_price_to_tick(sl, float(rules.tick_size), side=side)
    normalized_tp = round_price_to_tick(tp, float(rules.tick_size), side=side)

    warnings: list[str] = []
    if normalized_qty <= 0:
        warnings.append(f"qty became non-positive after step normalization: raw={qty}, normalized={normalized_qty}")
    if normalized_qty != qty:
        warnings.append(f"qty adjusted by stepSize: raw={qty} -> normalized={normalized_qty}")
    if normalized_sl != sl:
        warnings.append(f"sl adjusted by tickSize: raw={sl} -> normalized={normalized_sl}")
    if normalized_tp != tp:
        warnings.append(f"tp adjusted by tickSize: raw={tp} -> normalized={normalized_tp}")

    return {
        "normalized_qty": normalized_qty,
        "normalized_sl": normalized_sl,
        "normalized_tp": normalized_tp,
        "warnings": warnings,
        "rules": rules,
    }


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


def validate_position_size(
    qty: float,
    min_qty: float = 0.001,
    max_qty: float = 100.0,
    step_size: float | None = None,
    min_notional: float | None = None,
    price: float | None = None,
) -> tuple[bool, str]:
    dec_qty = _to_decimal(qty)
    dec_min_qty = _to_decimal(min_qty)
    dec_max_qty = _to_decimal(max_qty)

    if dec_qty <= 0:
        return False, "Quantity must be > 0"
    if dec_qty < dec_min_qty:
        return False, f"Quantity below minimum threshold: {qty} < {min_qty}"
    if dec_qty > dec_max_qty:
        return False, f"Quantity above maximum threshold: {qty} > {max_qty}"

    if step_size is not None:
        dec_step = _to_decimal(step_size)
        if dec_step <= 0:
            return False, f"Invalid step size: {step_size}"
        rounded = _to_decimal(round_to_step(qty, step_size))
        if rounded != dec_qty:
            return False, f"Quantity does not align with step size: qty={qty}, step={step_size}"

    if min_notional is not None:
        dec_min_notional = _to_decimal(min_notional)
        if dec_min_notional > 0:
            if price is None or price <= 0:
                return False, "Price must be supplied and > 0 when min_notional validation is enabled"
            notional = dec_qty * _to_decimal(price)
            if notional < dec_min_notional:
                return False, f"Notional below minimum threshold: {float(notional)} < {min_notional}"

    return True, "Quantity valid"


def apply_exchange_precision(qty: float, price: float, symbol_filters: dict | None) -> tuple[float, float]:
    """Apply exchange quantity/price precision from symbol filters."""
    if symbol_filters is None:
        raise RiskValidationError("Missing symbol precision metadata")
    rules = extract_precision_rules(symbol_filters)
    normalized_qty = round_to_step(qty, float(rules.step_size))
    normalized_price = round_price_to_tick(price, float(rules.tick_size), side=None)
    if normalized_qty <= 0:
        raise RiskValidationError(f"Normalized quantity is non-positive after precision apply: {normalized_qty}")
    return normalized_qty, normalized_price
