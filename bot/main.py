"""Main loop for staged BTCUSDT futures bot."""

from __future__ import annotations

import asyncio
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
from .intelligence.ab_test import compare_baseline_vs_ai
from .intelligence.evaluator import evaluate_candidate, evaluate_setup
from .intelligence.feature_builder import build_candidate_feature_row, build_setup_feature_row
from .intelligence.policy import resolve_trade_policy
from .notifier.telegram_bot import TelegramNotifier
from .storage.schemas import PolicyDecisionRecord
from .storage.trade_logger import (
    log_ai_evaluations,
    log_candidate_feature_rows,
    log_policy_decision,
    log_setup_feature_row,
)
from .strategy.candidate_builder import build_trade_candidates
from .strategy.risk_manager import calc_position_size, extract_precision_rules, validate_position_size
from .strategy.signal_builder import build_trade_setup
from .utils.formatting import format_signal_message
from .utils.logger import configure_logger, get_logger


NON_ORDERING_POLICY_MODES = {"baseline_alert_only", "ai_shadow"}


def execution_mode_allows_orders(policy_mode: str, execution_mode: ExecutionMode) -> bool:
    return execution_mode != ExecutionMode.ALERT_ONLY and policy_mode not in NON_ORDERING_POLICY_MODES


async def run() -> None:
    configure_logger("logs")
    logger = get_logger()
    adapter = BinanceFuturesAdapter(settings.binance_api_key, settings.binance_api_secret, settings.binance_testnet)
    notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    state_store = StateStore(settings.state_file)
    state = roll_day_if_needed(state_store.load())

    while True:
        try:
            frames = fetch_multi_timeframe_data(adapter, settings.symbol)
            df_15m = add_indicators(frames["15m"])
            df_1h = add_indicators(frames["1h"])
            df_4h = add_indicators(frames["4h"])
            headlines = fetch_recent_headlines(settings.news_sources, settings.news_lookback_minutes)
            signal = build_trade_setup(df_15m, df_1h, df_4h, headlines, settings)
            candidates = build_trade_candidates(signal, df_15m, df_1h, df_4h, settings)

            setup_row = build_setup_feature_row(signal, df_15m, df_1h, df_4h, settings)
            candidate_rows = [build_candidate_feature_row(c, signal, df_15m, df_1h, df_4h, settings) for c in candidates]
            if settings.dataset_logging_enabled:
                log_setup_feature_row(setup_row, settings.dataset_dir)
                log_candidate_feature_rows(candidate_rows, settings.dataset_dir)

            ai_setup_eval = evaluate_setup(setup_row, settings)
            signal["ai_evaluation"] = asdict(ai_setup_eval)

            ai_candidate_evals = {}
            ai_eval_rows = [
                {
                    "setup_id": signal.get("setup_id"),
                    "candidate_id": None,
                    "timestamp": signal.get("timestamp"),
                    **asdict(ai_setup_eval),
                }
            ]
            for row in candidate_rows:
                eval_result = evaluate_candidate(row, settings)
                ai_candidate_evals[row.candidate_id] = asdict(eval_result)
                ai_eval_rows.append({"setup_id": row.setup_id, "candidate_id": row.candidate_id, **asdict(eval_result)})

            if settings.dataset_logging_enabled:
                log_ai_evaluations(ai_eval_rows, settings.dataset_dir)

            policy = resolve_trade_policy(signal, candidates, ai_setup_eval, ai_candidate_evals, settings)
            if settings.policy_mode.value == "baseline_vs_ai_ab_test":
                policy["ab_comparison"] = compare_baseline_vs_ai(signal, policy)

            decision_record = PolicyDecisionRecord(
                setup_id=signal.get("setup_id", ""),
                candidate_id=(policy.get("selected_candidate") or {}).get("candidate_id"),
                timestamp=signal.get("timestamp", ""),
                symbol=signal.get("symbol", settings.symbol),
                policy_mode=policy.get("policy_mode"),
                baseline_decision=signal.get("baseline_decision", "NO_TRADE"),
                final_decision=policy.get("final_decision", "NO_TRADE"),
                execute=policy.get("execute", False),
                reason=policy.get("reason", ""),
                ai_setup_score=ai_setup_eval.score,
                ai_candidate_score=ai_candidate_evals.get((policy.get("selected_candidate") or {}).get("candidate_id"), {}).get("score"),
                ai_selected_candidate_type=(policy.get("selected_candidate") or {}).get("candidate_type"),
                baseline_vs_ai_agree=(policy.get("ab_comparison") or {}).get("disagreement_reason") == "none" if policy.get("ab_comparison") else None,
            )
            if settings.dataset_logging_enabled:
                log_policy_decision(decision_record, settings.dataset_dir)

            should_execute = policy.get("execute", False) and execution_mode_allows_orders(
                policy_mode=settings.policy_mode.value,
                execution_mode=settings.execution_mode,
            )
            if settings.policy_mode.value in NON_ORDERING_POLICY_MODES:
                should_execute = False
                logger.info("Execution skipped: execution mode non-ordering", extra={"policy_mode": settings.policy_mode.value})

            selected = policy.get("selected_candidate") if settings.policy_mode.value == "ai_testnet_auto" else signal
            if not policy.get("execute", False):
                logger.info("Execution skipped: policy blocked", extra={"reason": policy.get("reason", "")})
            elif not selected:
                logger.info("Execution skipped: no candidate selected")
            elif not should_execute:
                logger.info("Execution skipped: execution mode non-ordering")
            else:
                if has_open_position(adapter, settings.symbol):
                    logger.info("Execution skipped: hard blockers", extra={"blocker": "open_position"})
                elif in_cooldown(state, settings.cooldown_minutes):
                    logger.info("Execution skipped: hard blockers", extra={"blocker": "cooldown"})
                elif daily_loss_exceeded(state, settings.max_daily_loss_r):
                    logger.info("Execution skipped: hard blockers", extra={"blocker": "daily_loss_limit"})
                else:
                    symbol_filters = adapter.get_symbol_filters(settings.symbol)
                    mark_price = adapter.get_mark_price(settings.symbol)
                    balance = adapter.get_futures_balance("USDT")
                    qty = calc_position_size(balance, settings.risk_pct, selected["entry"], selected["sl"])
                    rules = extract_precision_rules(symbol_filters)
                    valid, _ = validate_position_size(qty=qty, min_qty=float(rules.min_qty), max_qty=float(rules.max_qty), step_size=float(rules.step_size), min_notional=float(rules.min_notional) if rules.min_notional else None, price=mark_price)
                    if valid:
                        place_market_order_with_sl_tp(
                            adapter=adapter,
                            symbol=settings.symbol,
                            side=selected["side"],
                            qty=qty,
                            sl=selected["sl"],
                            tp=selected["tp"],
                            execution_mode=settings.execution_mode,
                            enable_live_trading=settings.enable_live_trading,
                            symbol_filters=symbol_filters,
                            conditional_order_mode=settings.conditional_order_mode,
                            dry_run=settings.enable_dry_run,
                        )
                        await notifier.send_telegram(
                            f"{format_signal_message(signal, policy, settings.symbol)}\n"
                            f"\n[ORDER] Entry/SL/TP order placement succeeded"
                        )
                        state = register_order_opened(
                            state,
                            timestamp=signal.get("timestamp", ""),
                            side=selected.get("side") or "",
                            entry=float(selected.get("entry") or 0.0),
                            sl=float(selected.get("sl") or 0.0),
                            tp=float(selected.get("tp") or 0.0),
                            setup_id=signal.get("setup_id", ""),
                            candidate_id=selected.get("candidate_id", ""),
                            policy_mode=settings.policy_mode.value,
                            baseline_decision=signal.get("baseline_decision", ""),
                            ai_score=ai_setup_eval.score,
                            ai_recommendation=ai_setup_eval.recommendation,
                        )

            state_store.save(state)
        except Exception as exc:
            logger.exception("Loop error", exc_info=exc)
            await notifier.send_telegram(f"[ERROR] Bot loop failed: {type(exc).__name__}")

        await asyncio.sleep(settings.loop_interval_seconds)


if __name__ == "__main__":
    asyncio.run(run())
