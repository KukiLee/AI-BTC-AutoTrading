"""Telegram and human-readable signal formatting."""

from __future__ import annotations


def _fmt_blockers(blockers: list[str]) -> str:
    if not blockers:
        return "None"
    return "\n".join(f"- {item}" for item in blockers[:3])


def _fmt_keywords(matches: list[dict]) -> str:
    if not matches:
        return "None"
    seen = []
    for item in matches:
        kw = item.get("keyword")
        if kw and kw not in seen:
            seen.append(kw)
    return ", ".join(seen[:6]) if seen else "None"


def format_signal_message(signal: dict, mode: str, symbol: str) -> str:
    status = signal.get("status", "UNKNOWN")
    header = f"[{status}] {symbol} | mode={mode}"

    if status == "READY":
        rr = "n/a"
        if signal.get("entry") and signal.get("sl") and signal.get("tp"):
            risk = abs(signal["entry"] - signal["sl"])
            reward = abs(signal["tp"] - signal["entry"])
            rr = f"{(reward / risk):.2f}" if risk > 0 else "n/a"
        return (
            f"{header}\n"
            f"Bias/Side: {signal.get('bias')} / {signal.get('side')}\n"
            f"Entry type: {signal.get('entry_type')}\n"
            f"Entry/SL/TP: {signal.get('entry')} / {signal.get('sl')} / {signal.get('tp')}\n"
            f"RR: {rr}\n"
            f"News score: {signal.get('news_score')} | keywords: {_fmt_keywords(signal.get('news_matches', []))}\n"
            f"Reason: {signal.get('reason')}\n"
            f"Blockers: {_fmt_blockers(signal.get('blockers', []))}"
        )

    if status == "NO_TRADE":
        return (
            f"{header}\n"
            f"Reason: {signal.get('reason')}\n"
            f"Retest: {signal.get('entry_type')}\n"
            f"News: score={signal.get('news_score')} ({signal.get('news_reason')})\n"
            f"Blockers:\n{_fmt_blockers(signal.get('blockers', []))}"
        )

    return (
        f"{header}\n"
        f"ErrorType: {signal.get('error_type', 'UnknownError')}\n"
        f"Reason: {signal.get('reason', 'Unexpected error')}\n"
        f"Symbol: {symbol}\n"
        f"Mode: {mode}\n"
        f"Blockers:\n{_fmt_blockers(signal.get('blockers', []))}"
    )
