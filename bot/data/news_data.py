"""RSS news ingestion with resilient parsing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser


def _parse_published(entry: Any) -> datetime | None:
    for key in ("published", "updated"):
        value = entry.get(key)
        if not value:
            continue
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
        except Exception:
            continue
    return None


def fetch_recent_headlines(sources: list[str], lookback_minutes: int) -> list[dict]:
    cutoff = datetime.now(UTC) - timedelta(minutes=lookback_minutes)
    items: list[dict] = []

    for src in sources:
        try:
            feed = feedparser.parse(src)
            entries = getattr(feed, "entries", [])
        except Exception:
            entries = []

        for entry in entries:
            title = entry.get("title", "").strip()
            if not title:
                continue
            published_dt = _parse_published(entry)
            include = published_dt is None or published_dt >= cutoff
            if not include:
                continue
            items.append(
                {
                    "title": title,
                    "link": entry.get("link", ""),
                    "published": published_dt.isoformat() if published_dt else "missing",
                    "source": src,
                }
            )
    return items
