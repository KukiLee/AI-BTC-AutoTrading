"""Order placement manager with explicit safety gates."""

from __future__ import annotations

from config import ExecutionMode
from execution.exchange import BinanceFuturesAdapter
from strategy.risk_manager import apply_exchange_precision
from utils.exceptions import RiskValidationError


def place_market_order_with_sl_tp(
    adapter: BinanceFuturesAdapter,
    symbol: str,
    side: str,
    qty: float,
    sl: float,
    tp: float,
    execution_mode: ExecutionMode,
    enable_live_trading: bool,
    symbol_filters: dict | None,
) -> dict:
    if execution_mode == ExecutionMode.ALERT_ONLY:
        raise RiskValidationError("Order blocked: alert_only mode")
    if execution_mode == ExecutionMode.LIVE_AUTO and not enable_live_trading:
        raise RiskValidationError("Order blocked: ENABLE_LIVE_TRADING is false")
    if symbol_filters is None:
        raise RiskValidationError("Order blocked: missing symbol precision metadata")

    qty, _ = apply_exchange_precision(qty, tp, symbol_filters)
    side_word = "BUY" if side == "LONG" else "SELL"
    reduce_side = "SELL" if side == "LONG" else "BUY"

    entry_order = adapter.create_futures_order(
        symbol=symbol,
        side=side_word,
        type="MARKET",
        quantity=qty,
    )

    # TODO(Stage-2 verification): ensure exchange-specific STOP_MARKET/TAKE_PROFIT_MARKET
    # fields are fully aligned with account one-way/hedge mode behavior.
    sl_order = adapter.create_futures_order(
        symbol=symbol,
        side=reduce_side,
        type="STOP_MARKET",
        stopPrice=sl,
        closePosition=True,
        workingType="CONTRACT_PRICE",
    )
    tp_order = adapter.create_futures_order(
        symbol=symbol,
        side=reduce_side,
        type="TAKE_PROFIT_MARKET",
        stopPrice=tp,
        closePosition=True,
        workingType="CONTRACT_PRICE",
    )
    return {"entry": entry_order, "sl": sl_order, "tp": tp_order}
