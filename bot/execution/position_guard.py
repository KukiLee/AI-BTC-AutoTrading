"""Position and state guardrails."""

from __future__ import annotations

import json
import logging
from dataclasses import MISSING, asdict, dataclass, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .exchange import BinanceFuturesAdapter


logger = logging.getLogger(__name__)


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
    current_setup_id: str = ""
    current_candidate_id: str = ""
    current_policy_mode: str = ""
    last_ai_score: float | None = None
    last_ai_recommendation: str = ""
    last_baseline_decision: str = ""
    last_trade_metadata_ref: str = ""


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> BotState:
        default_day = datetime.now(timezone.utc).date().isoformat()
        defaults = self._bot_state_defaults(default_day=default_day)
        if not self.path.exists():
            return BotState(**defaults)
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            # Corrupted state file should not crash startup.
            logger.warning("State load failed due to invalid JSON; resetting state: %s", exc)
            return BotState(**defaults)

        if not isinstance(payload, dict):
            logger.warning("State file does not contain a JSON object; resetting state")
            return BotState(**defaults)

        defaults.update(self._filter_state_keys(payload))
        try:
            return BotState(**defaults)
        except Exception as exc:
            logger.warning("State payload incompatible with BotState; resetting state: %s", exc)
            return BotState(**self._bot_state_defaults(default_day=default_day))

    @staticmethod
    def _bot_state_defaults(*, default_day: str) -> dict[str, object]:
        defaults: dict[str, object] = {}
        for field in fields(BotState):
            if field.name == "day_key":
                defaults[field.name] = default_day
            elif field.default is not MISSING:
                defaults[field.name] = field.default
            elif field.default_factory is not MISSING:
                defaults[field.name] = field.default_factory()
        return defaults

    @staticmethod
    def _filter_state_keys(data: dict[str, object]) -> dict[str, object]:
        allowed_keys = {field.name for field in fields(BotState)}
        return {key: value for key, value in data.items() if key in allowed_keys}

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
    setup_id: str = "",
    candidate_id: str = "",
    policy_mode: str = "",
    baseline_decision: str = "",
    ai_score: float | None = None,
    ai_recommendation: str = "",
    trade_metadata_ref: str = "",
) -> BotState:
    """Record an order-open event from placement response (not fill-accurate PnL tracking)."""
    state = roll_day_if_needed(state)
    state.last_order_timestamp = timestamp
    state.last_trade_side = side
    state.last_entry = float(entry)
    state.last_sl = float(sl)
    state.last_tp = float(tp)
    state.last_position_status = "OPENED"
    state.current_setup_id = setup_id
    state.current_candidate_id = candidate_id
    state.current_policy_mode = policy_mode
    state.last_baseline_decision = baseline_decision
    state.last_ai_score = ai_score
    state.last_ai_recommendation = ai_recommendation
    state.last_trade_metadata_ref = trade_metadata_ref
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
