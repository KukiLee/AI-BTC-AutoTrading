"""Position and state guardrails."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from execution.exchange import BinanceFuturesAdapter


@dataclass
class BotState:
    last_signal_hash: str = ""
    last_stop_out_time: str = ""
    day_key: str = ""
    realized_r_today: float = 0.0
    last_order_timestamp: str = ""


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> BotState:
        if not self.path.exists():
            return BotState(day_key=datetime.now(UTC).date().isoformat())
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return BotState(**payload)

    def save(self, state: BotState) -> None:
        self.path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")


def has_open_position(adapter: BinanceFuturesAdapter, symbol: str) -> bool:
    positions = adapter.get_open_positions(symbol=symbol)
    return len(positions) > 0


def in_cooldown(state: BotState, cooldown_minutes: int) -> bool:
    if not state.last_stop_out_time:
        return False
    stop_time = datetime.fromisoformat(state.last_stop_out_time)
    return datetime.now(UTC) < (stop_time + timedelta(minutes=cooldown_minutes))


def daily_loss_exceeded(state: BotState, max_daily_loss_r: float) -> bool:
    day = datetime.now(UTC).date().isoformat()
    if state.day_key != day:
        return False
    return state.realized_r_today <= (-1 * max_daily_loss_r)
