"""Deterministic keyword-based news scoring and gating."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

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


@dataclass
class MatchedNewsItem:
    keyword: str
    weight: int
    title: str
    source: str


def score_news(headlines: list[dict], lookback_minutes: int | None = None) -> dict:
    score = 0
    matched_keywords: list[str] = []
    matched_titles: list[str] = []
    matched_items: list[dict] = []

    cutoff = None
    if lookback_minutes is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)

    for item in headlines:
        title = item.get("title", "")
        norm = title.lower()
        published_ts = item.get("published_ts")
        if cutoff and published_ts:
            try:
                dt = datetime.fromisoformat(str(published_ts))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt.astimezone(timezone.utc) < cutoff:
                    continue
            except Exception:
                pass

        title_hit = False
        source = item.get("source", "unknown")
        for kw, weight in RISK_OFF_KEYWORDS.items():
            if kw in norm:
                score += weight
                matched_keywords.append(kw)
                matched_items.append(asdict(MatchedNewsItem(keyword=kw, weight=weight, title=title, source=source)))
                title_hit = True
        for kw, weight in RISK_ON_KEYWORDS.items():
            if kw in norm:
                score += weight
                matched_keywords.append(kw)
                matched_items.append(asdict(MatchedNewsItem(keyword=kw, weight=weight, title=title, source=source)))
                title_hit = True

        if title_hit:
            matched_titles.append(title)

    return {
        "score": score,
        "matched_keywords": matched_keywords,
        "matched_headlines": matched_titles,
        "matched_items": matched_items,
    }


def news_gate(score: int, side: str) -> dict:
    if score <= -4:
        return {
            "allowed": False,
            "reason": "Blocked by news filter",
            "policy": "strong_risk_off_block_all",
        }
    if score >= 3 and side == "LONG":
        return {
            "allowed": True,
            "reason": "Positive news favors long bias",
            "policy": "risk_on_long_favorable",
        }
    return {
        "allowed": True,
        "reason": "News neutral/mixed; chart rules dominate",
        "policy": "neutral",
    }
