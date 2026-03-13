"""Telegram and human-readable signal formatting."""

from __future__ import annotations


def _fmt_blockers(blockers: list[str]) -> str:
    if not blockers:
        return "None"
    return "\n".join(f"- {item}" for item in blockers)


def format_signal_message(signal: dict, mode: str, symbol: str) -> str:
    status = signal.get("status", "UNKNOWN")
    header = f"[{status}] {symbol} | mode={mode}"

    if status == "READY":
        return (
            f"{header}\n"
            f"Side: {signal.get('side')}\n"
            f"Bias: {signal.get('bias')}\n"
            f"Entry: {signal.get('entry')}\n"
            f"SL: {signal.get('sl')}\n"
            f"TP: {signal.get('tp')}\n"
            f"Reason: {signal.get('reason')}\n"
            f"News: score={signal.get('news_score')} ({signal.get('news_reason')})\n"
            f"Blockers:\n{_fmt_blockers(signal.get('blockers', []))}"
        )

    if status == "NO_TRADE":
        return (
            f"{header}\n"
            f"Reason: {signal.get('reason')}\n"
            f"Bias: {signal.get('bias')}\n"
            f"News: score={signal.get('news_score')} ({signal.get('news_reason')})\n"
            f"Blockers:\n{_fmt_blockers(signal.get('blockers', []))}"
        )

    return (
        f"{header}\n"
        f"Reason: {signal.get('reason', 'Unexpected error')}\n"
        f"Blockers:\n{_fmt_blockers(signal.get('blockers', []))}"
    )
