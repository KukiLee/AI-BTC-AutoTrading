"""Main loop for staged BTCUSDT futures bot."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time

from config import ExecutionMode, settings
from data.market_data import fetch_multi_timeframe_data
from data.news_data import fetch_recent_headlines
from execution.exchange import BinanceFuturesAdapter
from execution.order_manager import place_market_order_with_sl_tp
from execution.position_guard import StateStore, daily_loss_exceeded, has_open_position, in_cooldown
from indicators.ta import add_indicators
from notifier.telegram_bot import TelegramNotifier
from strategy.risk_manager import calc_position_size, validate_position_size
from strategy.signal_builder import build_trade_setup
from utils.formatting import format_signal_message
from utils.logger import configure_logger, get_logger


def signal_hash(signal: dict) -> str:
    payload = json.dumps(signal, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def run() -> None:
    configure_logger("logs")
    logger = get_logger()
    logger.info("Bot startup")
    logger.info(f"Execution mode: {settings.execution_mode}")

    adapter = BinanceFuturesAdapter(
        api_key=settings.binance_api_key,
        api_secret=settings.binance_api_secret,
        testnet=settings.binance_testnet,
    )
    notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    state_store = StateStore(settings.state_file)
    state = state_store.load()

    while True:
        try:
            frames = fetch_multi_timeframe_data(adapter, settings.symbol)
            df_15m = add_indicators(frames["15m"])
            df_1h = add_indicators(frames["1h"])
            df_4h = add_indicators(frames["4h"])
            logger.info("Data fetch + indicator calculation success")

            headlines = fetch_recent_headlines(settings.news_sources, settings.news_lookback_minutes)
            signal = build_trade_setup(df_15m, df_1h, df_4h, headlines, settings)
            logger.info(f"Signal result: {signal['status']} | reason={signal['reason']}")

            current_hash = signal_hash(signal)
            should_alert = signal["status"] in {"READY", "ERROR"}
            if settings.alert_on_no_trade and signal["status"] == "NO_TRADE":
                should_alert = True

            if should_alert and current_hash != state.last_signal_hash:
                msg = format_signal_message(signal, settings.execution_mode.value, settings.symbol)
                sent = await notifier.send_telegram(msg)
                logger.info(f"Telegram sent={sent}")
                state.last_signal_hash = current_hash

            if signal["status"] == "READY" and settings.execution_mode != ExecutionMode.ALERT_ONLY:
                if has_open_position(adapter, settings.symbol):
                    logger.info("Order blocked: open position exists")
                elif in_cooldown(state, settings.cooldown_minutes):
                    logger.info("Order blocked: cooldown active")
                elif daily_loss_exceeded(state, settings.max_daily_loss_r):
                    logger.info("Order blocked: daily loss exceeded")
                else:
                    balance = adapter.get_futures_balance("USDT")
                    qty = calc_position_size(balance, settings.risk_pct, signal["entry"], signal["sl"])
                    valid, reason = validate_position_size(qty)
                    if not valid:
                        logger.warning(f"Order blocked by qty validation: {reason}")
                    else:
                        info = adapter.get_exchange_info()
                        symbol_filters = next(
                            (s for s in info.get("symbols", []) if s.get("symbol") == settings.symbol),
                            None,
                        )
                        result = place_market_order_with_sl_tp(
                            adapter=adapter,
                            symbol=settings.symbol,
                            side=signal["side"],
                            qty=qty,
                            sl=signal["sl"],
                            tp=signal["tp"],
                            execution_mode=settings.execution_mode,
                            enable_live_trading=settings.enable_live_trading,
                            symbol_filters=symbol_filters,
                        )
                        state.last_order_timestamp = signal["timestamp"]
                        logger.info(f"Order attempted successfully: {result}")

            state_store.save(state)
        except Exception as exc:
            logger.exception(f"Loop error: {exc}")
            await notifier.send_telegram(f"[ERROR] Bot loop failed: {type(exc).__name__}: {exc}")

        time.sleep(settings.loop_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run())
