from types import SimpleNamespace

from bot.intelligence.candidate_selector import select_ai_candidate


def _settings():
    return SimpleNamespace(ai_min_score_to_allow=0.7)


def test_selects_highest_valid_scored_candidate():
    candidates = [{"candidate_id": "a", "hard_blocked": False}, {"candidate_id": "b", "hard_blocked": False}]
    evals = {"a": {"score": 0.72}, "b": {"score": 0.91}}
    selected = select_ai_candidate(candidates, evals, _settings())
    assert selected["candidate_id"] == "b"


def test_ignores_hard_blocked_candidate():
    candidates = [{"candidate_id": "a", "hard_blocked": True}, {"candidate_id": "b", "hard_blocked": False}]
    evals = {"a": {"score": 0.99}, "b": {"score": 0.75}}
    selected = select_ai_candidate(candidates, evals, _settings())
    assert selected["candidate_id"] == "b"


def test_returns_none_if_all_fail_threshold():
    candidates = [{"candidate_id": "a", "hard_blocked": False}]
    evals = {"a": {"score": 0.5}}
    assert select_ai_candidate(candidates, evals, _settings()) is None
