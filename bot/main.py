"""Main loop for staged BTCUSDT futures bot."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import asdict

from .config import ExecutionMode, settings
from .data.market_data import fetch_multi_timeframe_data
from .data.news_data import fetch_recent_headlines
from .execution.exchange import BinanceFuturesAdapter
from .execution.order_manager import place_market_order_with_sl_tp
from .execution.position_guard import (
    StateStore,
    daily_loss_exceeded,
    has_open_position,
    in_cooldown,
    register_order_opened,
    roll_day_if_needed,
)
from .indicators.ta import add_indicators
from .intelligence.evaluator import evaluate_setup
from .intelligence.feature_builder import build_setup_feature_row
from .intelligence.policy import resolve_trade_policy
from .notifier.telegram_bot import TelegramNotifier
from .storage.trade_logger import log_ai_evaluation, log_setup_row
from .strategy.risk_manager import calc_position_size, extract_precision_rules, validate_position_size
from .strategy.signal_builder import build_trade_setup
from .utils.formatting import format_signal_message
from .utils.logger import configure_logger, get_logger


STABLE_SIGNAL_HASH_FIELDS = {
    "status",
    "reason",
    "side",
    "bias",
    "entry",
    "sl",
    "tp",
    "risk_per_unit",
    "news_score",
    "news_reason",
    "blockers",
    "chase_info",
    "entry_type",
    "news_matches",
    "structure_summary",
    "baseline_decision",
    "baseline_reason",
    "setup_id",
    "ai_evaluation",
    "error_type",
}


def signal_hash(signal: dict, exclude_timestamp: bool = True) -> str:
    payload = {k: signal.get(k) for k in STABLE_SIGNAL_HASH_FIELDS if k in signal}
    if not exclude_timestamp and "timestamp" in signal:
        payload["timestamp"] = signal.get("timestamp")
    encoded = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
    state = roll_day_if_needed(state_store.load())

    symbol_filters = None
    try:
        symbol_filters = adapter.get_symbol_filters(settings.symbol)
        logger.info("Symbol metadata cached at startup")
    except Exception as exc:
        logger.warning(f"Failed to cache symbol metadata at startup: {exc}")

    while True:
        try:
            frames = fetch_multi_timeframe_data(adapter, settings.symbol)
            df_15m = add_indicators(frames["15m"])
            df_1h = add_indicators(frames["1h"])
            df_4h = add_indicators(frames["4h"])
            headlines = fetch_recent_headlines(settings.news_sources, settings.news_lookback_minutes)
            signal = build_trade_setup(df_15m, df_1h, df_4h, headlines, settings)
            logger.info(f"Signal result: {signal['status']} | reason={signal['reason']}")

            feature_row = build_setup_feature_row(signal, df_15m, df_1h, df_4h, settings)
            if settings.dataset_logging_enabled and settings.setup_log_jsonl:
                if not log_setup_row(feature_row, settings.dataset_dir):
                    logger.warning("Setup row logging failed; continuing with execution flow")

            ai_eval = evaluate_setup(feature_row, settings)
            signal["ai_evaluation"] = asdict(ai_eval)
            if settings.dataset_logging_enabled:
                ai_payload = {"setup_id": feature_row.setup_id, "timestamp": feature_row.timestamp, **asdict(ai_eval)}
                if not log_ai_evaluation(ai_payload, settings.dataset_dir):
                    logger.warning("AI evaluation logging failed; continuing with execution flow")

            policy = resolve_trade_policy(signal, ai_eval, settings)

            state = roll_day_if_needed(state)
            current_hash = signal_hash(signal, exclude_timestamp=settings.alert_dedup_exclude_timestamp)
            should_alert = signal["status"] in {"READY", "ERROR"}
            if settings.alert_on_no_trade and signal["status"] == "NO_TRADE":
                should_alert = current_hash != state.last_signal_hash

            if should_alert:
                key = signal["status"]
                previous_hash = state.last_ready_hash if key == "READY" else state.last_error_hash
                if key == "NO_TRADE":
                    previous_hash = state.last_signal_hash
                if current_hash != previous_hash:
                    msg = format_signal_message(signal, settings.execution_mode.value, settings.symbol)
                    sent = await notifier.send_telegram(msg)
                    logger.info(f"Telegram sent={sent}")
                    if key == "READY":
                        state.last_ready_hash = current_hash
                    elif key == "ERROR":
                        state.last_error_hash = current_hash
                    elif key == "NO_TRADE":
                        state.last_signal_hash = current_hash

            if policy["final_execute"] and settings.execution_mode != ExecutionMode.ALERT_ONLY:
                if symbol_filters is None:
                    try:
                        symbol_filters = adapter.get_symbol_filters(settings.symbol)
                        logger.info("Symbol metadata refreshed for execution")
                    except Exception as exc:
                        logger.warning(f"Order blocked: symbol precision metadata unavailable ({exc})")

                if has_open_position(adapter, settings.symbol):
                    logger.info("Order blocked: open position exists")
                elif in_cooldown(state, settings.cooldown_minutes):
                    logger.info("Order blocked: cooldown active")
                elif daily_loss_exceeded(state, settings.max_daily_loss_r):
                    logger.info("Order blocked: daily loss exceeded")
                else:
                    if symbol_filters is None:
                        logger.warning("Order blocked: symbol precision metadata unavailable")
                    else:
                        mark_price = adapter.get_mark_price(settings.symbol)
                        balance = adapter.get_futures_balance("USDT")
                        qty = calc_position_size(balance, settings.risk_pct, signal["entry"], signal["sl"])
                        rules = extract_precision_rules(symbol_filters)
                        valid, reason = validate_position_size(
                            qty=qty,
                            min_qty=float(rules.min_qty),
                            max_qty=float(rules.max_qty),
                            step_size=float(rules.step_size),
                            min_notional=float(rules.min_notional) if rules.min_notional else None,
                            price=mark_price,
                        )
                        if not valid:
                            logger.warning(f"Order blocked by qty validation: {reason}")
                        else:
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
                                conditional_order_mode=settings.conditional_order_mode,
                                dry_run=settings.execution_mode == ExecutionMode.TESTNET_AUTO,
                            )
                            state = register_order_opened(
                                state,
                                timestamp=signal.get("timestamp", ""),
                                side=signal.get("side") or "",
                                entry=float(signal.get("entry") or 0.0),
                                sl=float(signal.get("sl") or 0.0),
                                tp=float(signal.get("tp") or 0.0),
                                setup_id=signal.get("setup_id", ""),
                                baseline_decision=signal.get("baseline_decision", ""),
                                ai_score=ai_eval.score,
                                ai_decision=ai_eval.recommendation,
                                trade_metadata_ref=str(result.get("order_id", "")) if isinstance(result, dict) else "",
                            )
                            logger.info(f"Order attempted successfully: {result}")

            state_store.save(state)
        except Exception as exc:
            logger.exception("Loop error", exc_info=exc)
            await notifier.send_telegram(f"[ERROR] Bot loop failed: {type(exc).__name__}: {exc}")

        await asyncio.sleep(settings.loop_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run())
