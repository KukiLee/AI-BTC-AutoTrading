"""Candidate selection for constrained AI testnet auto mode."""

from __future__ import annotations


def select_ai_candidate(candidates: list[dict], candidate_evaluations: dict[str, dict], settings) -> dict | None:
    best = None
    best_score = -1.0
    for candidate in candidates:
        if candidate.get("hard_blocked"):
            continue
        eval_row = candidate_evaluations.get(candidate.get("candidate_id")) or {}
        score = eval_row.get("score")
        if score is None or score < settings.ai_min_score_to_allow:
            continue
        if score > best_score:
            best = candidate
            best_score = score
    return best
