"""Order placement manager with explicit safety gates."""

from __future__ import annotations

from config import ExecutionMode
from execution.exchange import BinanceFuturesAdapter
from strategy.risk_manager import normalize_order_values
from utils.exceptions import ExchangeAdapterError, RiskValidationError
from utils.logger import get_logger


def place_entry_order(
    adapter: BinanceFuturesAdapter,
    symbol: str,
    side_word: str,
    qty: float,
    dry_run: bool = False,
) -> dict:
    if dry_run:
        return adapter.client.futures_create_test_order(symbol=symbol, side=side_word, type="MARKET", quantity=qty)
    return adapter.create_futures_order(symbol=symbol, side=side_word, type="MARKET", quantity=qty)


def legacy_conditional_order_path(
    adapter: BinanceFuturesAdapter,
    symbol: str,
    reduce_side: str,
    sl: float,
    tp: float,
) -> dict:
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
    return {"sl": sl_order, "tp": tp_order}


def algo_conditional_order_path(*_, **__) -> dict:
    raise RiskValidationError(
        "Conditional order mode 'algo' selected, but algo conditional order path is not implemented yet. "
        "Validate latest Binance Algo Service API before live usage."
    )


def place_protective_orders(
    adapter: BinanceFuturesAdapter,
    symbol: str,
    reduce_side: str,
    sl: float,
    tp: float,
    conditional_order_mode: str,
) -> dict:
    if conditional_order_mode == "algo":
        return algo_conditional_order_path(adapter, symbol=symbol, reduce_side=reduce_side, sl=sl, tp=tp)
    return legacy_conditional_order_path(adapter, symbol=symbol, reduce_side=reduce_side, sl=sl, tp=tp)


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
    conditional_order_mode: str = "legacy",
    dry_run: bool = False,
) -> dict:
    logger = get_logger()
    if execution_mode == ExecutionMode.ALERT_ONLY:
        raise RiskValidationError("Order blocked: alert_only mode")
    if execution_mode == ExecutionMode.LIVE_AUTO and not enable_live_trading:
        raise RiskValidationError("Order blocked: ENABLE_LIVE_TRADING is false")
    if symbol_filters is None:
        raise RiskValidationError("Order blocked: missing symbol precision metadata")

    normalized = normalize_order_values(qty=qty, sl=sl, tp=tp, symbol_filters=symbol_filters, side=side)
    for warning in normalized["warnings"]:
        logger.warning(f"Precision normalize warning: {warning}")

    side_word = "BUY" if side == "LONG" else "SELL"
    reduce_side = "SELL" if side == "LONG" else "BUY"

    try:
        entry_order = place_entry_order(
            adapter=adapter,
            symbol=symbol,
            side_word=side_word,
            qty=normalized["normalized_qty"],
            dry_run=dry_run,
        )
        protective_orders = place_protective_orders(
            adapter=adapter,
            symbol=symbol,
            reduce_side=reduce_side,
            sl=normalized["normalized_sl"],
            tp=normalized["normalized_tp"],
            conditional_order_mode=conditional_order_mode,
        )
    except ExchangeAdapterError as exc:
        message = str(exc)
        if "-4120" in message:
            raise RiskValidationError(
                "Conditional order rejected (-4120). Binance conditional order endpoint may have moved; "
                "switch CONDITIONAL_ORDER_MODE or verify latest Algo Service path."
            ) from exc
        raise

    return {"entry": entry_order, **protective_orders, "normalized": normalized}
