"""Deterministic candidate generation for constrained AI action space."""

from __future__ import annotations

import hashlib


def _candidate_id(setup_id: str, candidate_type: str, entry: float | None) -> str:
    raw = f"{setup_id}|{candidate_type}|{entry}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _hard_block_reasons(signal: dict) -> list[str]:
    reasons = []
    blockers = signal.get("blockers") or []
    for blocker in blockers:
        lower = str(blocker).lower()
        if "news" in lower and "blocked" in lower:
            reasons.append("strong_risk_off_news")
        if "stop distance" in lower:
            reasons.append("invalid_stop_distance")
        if "room check" in lower:
            reasons.append("room_check_fail")
        if "higher timeframe neutral" in lower:
            reasons.append("missing_mandatory_structure")
    if signal.get("status") == "ERROR":
        reasons.append("risk_manager_invalidation")
    return sorted(set(reasons))


def build_trade_candidates(signal, df_15m, df_1h, df_4h, settings) -> list[dict]:
    allowed_prefixes = set(settings.allowed_candidate_types)
    candidates: list[dict] = []

    if signal.get("symbol") != settings.symbol:
        return candidates

    side = signal.get("side")
    if side not in {"LONG", "SHORT"}:
        return candidates

    base_type = f"{signal.get('entry_type', 'retest')}_{side.lower()}"
    hard_reasons = _hard_block_reasons(signal)
    hard_blocked = len(hard_reasons) > 0

    if signal.get("status") == "READY":
        if signal.get("entry_type") in allowed_prefixes:
            candidates.append(
                {
                    "candidate_id": _candidate_id(signal.get("setup_id", ""), base_type, signal.get("entry")),
                    "setup_id": signal.get("setup_id", ""),
                    "candidate_type": base_type,
                    "side": side,
                    "entry": signal.get("entry"),
                    "sl": signal.get("sl"),
                    "tp": signal.get("tp"),
                    "rr": signal.get("rr"),
                    "reason": "baseline_ready_candidate",
                    "hard_blocked": hard_blocked,
                    "hard_block_reasons": hard_reasons,
                }
            )

    if signal.get("status") == "NO_TRADE" and signal.get("entry") is not None and settings.ai_max_candidates_per_cycle > 1:
        structure = signal.get("structure_summary") or {}
        used_breakout_fallback = structure.get("used_breakout_fallback", False)
        if used_breakout_fallback and "breakout_fallback" in allowed_prefixes:
            fallback_type = f"breakout_fallback_{side.lower()}"
            candidates.append(
                {
                    "candidate_id": _candidate_id(signal.get("setup_id", ""), fallback_type, signal.get("entry")),
                    "setup_id": signal.get("setup_id", ""),
                    "candidate_type": fallback_type,
                    "side": side,
                    "entry": signal.get("entry"),
                    "sl": signal.get("sl"),
                    "tp": signal.get("tp"),
                    "rr": signal.get("rr"),
                    "reason": "deterministic_near_ready_variant",
                    "hard_blocked": hard_blocked,
                    "hard_block_reasons": hard_reasons,
                }
            )

    return candidates[: settings.ai_max_candidates_per_cycle]
