"""Telegram notifier wrapper."""

from __future__ import annotations

from telegram import Bot

from ..utils.logger import get_logger

MAX_MESSAGE_LEN = 3900


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self.enabled = bool(token and chat_id)
        self.bot = Bot(token=token) if self.enabled else None

    async def send_telegram(self, message: str) -> bool:
        logger = get_logger()
        if not self.enabled:
            return False
        if len(message) > MAX_MESSAGE_LEN:
            message = message[:MAX_MESSAGE_LEN] + "\n...<truncated>"
        try:
            assert self.bot is not None
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except Exception as exc:
            logger.warning(f"Telegram send failed: {type(exc).__name__}: {exc}")
            return False
