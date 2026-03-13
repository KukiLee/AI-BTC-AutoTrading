"""Position and state guardrails."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .exchange import BinanceFuturesAdapter


@dataclass
class BotState:
    last_signal_hash: str = ""
    last_ready_hash: str = ""
    last_error_hash: str = ""
    last_stop_out_time: str = ""
    day_key: str = ""
    realized_r_today: float = 0.0
    last_order_timestamp: str = ""
    last_trade_side: str = ""
    last_entry: float = 0.0
    last_sl: float = 0.0
    last_tp: float = 0.0
    last_position_status: str = ""


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> BotState:
        default_day = datetime.now(timezone.utc).date().isoformat()
        if not self.path.exists():
            return BotState(day_key=default_day)
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            # Corrupted state file should not crash startup.
            return BotState(day_key=default_day)

        defaults = asdict(BotState(day_key=default_day))
        defaults.update(payload if isinstance(payload, dict) else {})
        return BotState(**defaults)

    def save(self, state: BotState) -> None:
        self.path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")


def roll_day_if_needed(state: BotState) -> BotState:
    day = datetime.now(timezone.utc).date().isoformat()
    if state.day_key != day:
        state.day_key = day
        state.realized_r_today = 0.0
    return state


def register_order_opened(
    state: BotState,
    *,
    timestamp: str,
    side: str,
    entry: float,
    sl: float,
    tp: float,
) -> BotState:
    """Record an order-open event from placement response (not fill-accurate PnL tracking)."""
    state = roll_day_if_needed(state)
    state.last_order_timestamp = timestamp
    state.last_trade_side = side
    state.last_entry = float(entry)
    state.last_sl = float(sl)
    state.last_tp = float(tp)
    state.last_position_status = "OPENED"
    return state


def register_stop_out(state: BotState, r_loss: float = 1.0) -> BotState:
    # R-based stop tracking is an operational approximation unless fill events are wired.
    state = roll_day_if_needed(state)
    state.realized_r_today -= abs(r_loss)
    state.last_stop_out_time = datetime.now(timezone.utc).isoformat()
    state.last_position_status = "STOP_OUT"
    return state


def register_take_profit(state: BotState, r_gain: float = 2.0) -> BotState:
    # R-based TP tracking is an operational approximation unless fill events are wired.
    state = roll_day_if_needed(state)
    state.realized_r_today += abs(r_gain)
    state.last_position_status = "TAKE_PROFIT"
    return state


def has_open_position(adapter: BinanceFuturesAdapter, symbol: str) -> bool:
    positions = adapter.get_open_positions(symbol=symbol)
    return len(positions) > 0


def in_cooldown(state: BotState, cooldown_minutes: int) -> bool:
    if not state.last_stop_out_time:
        return False
    stop_time = datetime.fromisoformat(state.last_stop_out_time)
    return datetime.now(timezone.utc) < (stop_time + timedelta(minutes=cooldown_minutes))


def daily_loss_exceeded(state: BotState, max_daily_loss_r: float) -> bool:
    state = roll_day_if_needed(state)
    return state.realized_r_today <= (-1 * max_daily_loss_r)
