"""Deterministic keyword-based news scoring and gating."""

from __future__ import annotations

RISK_OFF_KEYWORDS = {
    "hack": -2,
    "exploit": -2,
    "liquidation": -2,
    "war": -3,
    "exchange issue": -3,
    "outage": -2,
    "cpi": -2,
    "fomc": -2,
    "hot inflation": -3,
    "tariff": -2,
}

RISK_ON_KEYWORDS = {
    "etf inflow": 2,
    "approval": 1,
    "institutional buy": 2,
    "treasury buy": 2,
}


def score_news(headlines: list[dict]) -> dict:
    score = 0
    matched_keywords: list[str] = []
    matched_titles: list[str] = []

    for item in headlines:
        title = item.get("title", "")
        norm = title.lower()

        title_hit = False
        for kw, weight in RISK_OFF_KEYWORDS.items():
            if kw in norm:
                score += weight
                matched_keywords.append(kw)
                title_hit = True
        for kw, weight in RISK_ON_KEYWORDS.items():
            if kw in norm:
                score += weight
                matched_keywords.append(kw)
                title_hit = True

        if title_hit:
            matched_titles.append(title)

    return {
        "score": score,
        "matched_keywords": matched_keywords,
        "matched_headlines": matched_titles,
    }


def news_gate(score: int, side: str) -> dict:
    if score <= -4:
        return {
            "allowed": False,
            "reason": "Strong risk-off headlines detected; blocking entries",
        }
    if score >= 3:
        return {
            "allowed": True,
            "reason": f"Favorable headline tone for {side}, but chart rules still required",
        }
    return {
        "allowed": True,
        "reason": "News neutral/mixed; chart rules dominate",
    }
