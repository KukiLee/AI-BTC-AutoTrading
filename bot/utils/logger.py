"""Loguru-based logging setup."""

from __future__ import annotations

from pathlib import Path
import sys

from loguru import logger


def configure_logger(log_dir: str = "logs") -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stdout, level="INFO", enqueue=True, backtrace=False, diagnose=False)
    logger.add(
        Path(log_dir) / "bot.log",
        rotation="10 MB",
        retention="14 days",
        level="INFO",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )


def get_logger():
    return logger
