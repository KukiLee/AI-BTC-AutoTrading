"""Telegram and human-readable signal formatting."""

from __future__ import annotations


def _fmt_blockers(blockers: list[str]) -> str:
    if not blockers:
        return "None"
    return "\n".join(f"- {item}" for item in blockers[:4])


def _fmt_ai(ai_eval: dict | None) -> str:
    if not ai_eval:
        return "AI: n/a"
    return f"AI: score={ai_eval.get('score')} reco={ai_eval.get('recommendation')} reasons={','.join(ai_eval.get('reasons', [])[:2]) or 'none'}"


def format_signal_message(signal: dict, policy_result: dict, symbol: str) -> str:
    status = signal.get("status", "UNKNOWN")
    ai_eval = signal.get("ai_evaluation")
    selected = policy_result.get("selected_candidate") or {}
    return (
        f"[{status}] {symbol}\n"
        f"Policy: {policy_result.get('policy_mode')} | execute={policy_result.get('execute')}\n"
        f"Baseline: {signal.get('baseline_decision')} ({signal.get('baseline_reason')})\n"
        f"AI setup: {_fmt_ai(ai_eval)}\n"
        f"AI selected candidate: {selected.get('candidate_type', 'none')}\n"
        f"Reason: {policy_result.get('reason')}\n"
        f"Blockers:\n{_fmt_blockers(signal.get('blockers', []))}"
    )
