"""Telegram and human-readable signal formatting."""

from __future__ import annotations


def _fmt_blockers(blockers: list[str]) -> str:
    if not blockers:
        return "None"
    return "\n".join(f"- {item}" for item in blockers[:4])


def _fmt_keywords(matches: list[dict]) -> str:
    if not matches:
        return "None"
    seen = []
    for item in matches:
        kw = item.get("keyword")
        if kw and kw not in seen:
            seen.append(kw)
    return ", ".join(seen[:6]) if seen else "None"


def _fmt_structure(structure_summary: dict) -> str:
    if not structure_summary:
        return "n/a"
    box_high = structure_summary.get("box_high")
    box_low = structure_summary.get("box_low")
    highs = structure_summary.get("swing_highs_count")
    lows = structure_summary.get("swing_lows_count")
    room_reason = structure_summary.get("room_reason", "n/a")
    return f"box=({box_low}, {box_high}) swings(H/L)={highs}/{lows} room={room_reason}"


def _fmt_ai(ai_eval: dict | None, baseline_decision: str) -> str:
    if not ai_eval:
        return "AI: n/a"
    score = ai_eval.get("score")
    reco = ai_eval.get("recommendation")
    reasons = ",".join(ai_eval.get("reasons", [])[:3]) or "none"
    agree = ai_eval.get("agree_with_baseline")
    if agree is None:
        agree_text = "n/a"
    else:
        agree_text = "yes" if agree else "no"
    return f"AI: score={score} reco={reco} agree={agree_text} reasons={reasons}"


def format_signal_message(signal: dict, mode: str, symbol: str) -> str:
    status = signal.get("status", "UNKNOWN")
    baseline_decision = signal.get("baseline_decision", status)
    header = f"[{status}] {symbol} | mode={mode} | baseline={baseline_decision}"

    if status == "READY":
        rr = "n/a"
        if signal.get("entry") and signal.get("sl") and signal.get("tp"):
            risk = abs(signal["entry"] - signal["sl"])
            reward = abs(signal["tp"] - signal["entry"])
            rr = f"{(reward / risk):.2f}" if risk > 0 else "n/a"
        return (
            f"{header}\n"
            f"Bias/Side: {signal.get('bias')} / {signal.get('side')}\n"
            f"Entry type: {signal.get('entry_type')} (retest={signal.get('retest_confirmed')})\n"
            f"Entry/SL/TP: {signal.get('entry')} / {signal.get('sl')} / {signal.get('tp')}\n"
            f"RR: {rr}\n"
            f"News score: {signal.get('news_score')} | keywords: {_fmt_keywords(signal.get('news_matches', []))}\n"
            f"Structure: {_fmt_structure(signal.get('structure_summary', {}))}\n"
            f"Reason: {signal.get('reason')}\n"
            f"{_fmt_ai(signal.get('ai_evaluation'), baseline_decision)}"
        )

    if status == "NO_TRADE":
        return (
            f"{header}\n"
            f"Reason: {signal.get('reason')}\n"
            f"Retest/Fallback: {signal.get('entry_type')}\n"
            f"News: score={signal.get('news_score')} ({signal.get('news_reason')})\n"
            f"Keywords: {_fmt_keywords(signal.get('news_matches', []))}\n"
            f"{_fmt_ai(signal.get('ai_evaluation'), baseline_decision)}\n"
            f"Blockers:\n{_fmt_blockers(signal.get('blockers', []))}"
        )

    return (
        f"{header}\n"
        f"ErrorType: {signal.get('error_type', 'UnknownError')}\n"
        f"Reason: {signal.get('reason', 'Unexpected error')}\n"
        f"Mode: {mode}\n"
        f"Symbol: {symbol}\n"
        f"{_fmt_ai(signal.get('ai_evaluation'), baseline_decision)}\n"
        f"Blockers:\n{_fmt_blockers(signal.get('blockers', []))}"
    )
