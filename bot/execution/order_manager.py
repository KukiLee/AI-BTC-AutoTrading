"""Order placement manager with explicit safety gates."""

from __future__ import annotations

from ..config import ExecutionMode
from .exchange import BinanceFuturesAdapter
from ..strategy.risk_manager import normalize_order_values
from ..utils.exceptions import ExchangeAdapterError, RiskValidationError
from ..utils.logger import get_logger


def _build_entry_payload(symbol: str, side_word: str, qty: float) -> dict:
    return {
        "symbol": symbol,
        "side": side_word,
        "type": "MARKET",
        "quantity": qty,
    }


def _build_conditional_payload(symbol: str, side_word: str, stop_price: float, order_type: str) -> dict:
    return {
        "symbol": symbol,
        "side": side_word,
        "type": order_type,
        "stopPrice": stop_price,
        "closePosition": True,
        "workingType": "CONTRACT_PRICE",
        # TODO: evaluate reduceOnly support by account mode and endpoint behavior.
        # TODO: add explicit positionSide for hedge mode compatibility.
    }


def place_entry_order(
    adapter: BinanceFuturesAdapter,
    symbol: str,
    side_word: str,
    qty: float,
    dry_run: bool = False,
) -> dict:
    payload = _build_entry_payload(symbol=symbol, side_word=side_word, qty=qty)
    if dry_run:
        # Optional test-order branch for safer validation in testnet_auto.
        return adapter.client.futures_create_test_order(**payload)
    return adapter.create_futures_order(**payload)


def legacy_conditional_order_path(
    adapter: BinanceFuturesAdapter,
    symbol: str,
    reduce_side: str,
    sl: float,
    tp: float,
) -> dict:
    """Compatibility path for legacy conditional endpoints."""
    sl_order = adapter.create_futures_order(
        **_build_conditional_payload(symbol=symbol, side_word=reduce_side, stop_price=sl, order_type="STOP_MARKET")
    )
    tp_order = adapter.create_futures_order(
        **_build_conditional_payload(
            symbol=symbol,
            side_word=reduce_side,
            stop_price=tp,
            order_type="TAKE_PROFIT_MARKET",
        )
    )
    return {"sl": sl_order, "tp": tp_order}


def algo_conditional_order_path(*_, **kwargs) -> dict:
    mode = kwargs.get("conditional_order_mode", "algo")
    raise RiskValidationError(
        f"Conditional order mode '{mode}' selected but blocked: Binance USDⓈ-M Futures conditional "
        "orders are migrating to Algo Service endpoints; this path is intentionally disabled until "
        "exchange-current endpoint validation is completed."
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
        # TODO: integrate with Binance Algo Service endpoint migration once validated.
        return algo_conditional_order_path(
            adapter,
            symbol=symbol,
            reduce_side=reduce_side,
            sl=sl,
            tp=tp,
            conditional_order_mode=conditional_order_mode,
        )
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
                "Conditional order rejected (-4120) after entry placement attempt. "
                f"mode={execution_mode.value}, conditional_order_mode={conditional_order_mode}, symbol={symbol}. "
                "This matches Binance conditional order migration constraints; verify legacy compatibility or "
                "implement/validate Algo Service endpoint flow before auto execution."
            ) from exc
        raise

    return {"entry": entry_order, **protective_orders, "normalized": normalized}
