"""Telegram notifier wrapper."""

from __future__ import annotations

from telegram import Bot


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self.enabled = bool(token and chat_id)
        self.bot = Bot(token=token) if self.enabled else None

    async def send_telegram(self, message: str) -> bool:
        if not self.enabled:
            return False
        try:
            assert self.bot is not None
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except Exception:
            return False
