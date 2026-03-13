"""RSS news ingestion with resilient parsing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import feedparser

MAX_ITEMS_PER_SOURCE = 50


def _parse_published(entry: Any) -> datetime | None:
    for key in ("published", "updated"):
        value = entry.get(key)
        if not value:
            continue
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def _extract_source_name(src: str) -> str:
    try:
        host = urlparse(src).hostname or src
        return host.replace("www.", "")
    except Exception:
        return src


def fetch_recent_headlines(sources: list[str], lookback_minutes: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
    items: list[dict] = []

    for src in sources:
        try:
            feed = feedparser.parse(src)
            entries = getattr(feed, "entries", [])
        except Exception:
            entries = []

        source = _extract_source_name(src)
        per_source_count = 0

        for entry in entries:
            try:
                title = str(entry.get("title", "")).strip()
                if not title:
                    continue
                published_dt = _parse_published(entry)
                # Intentionally include missing timestamps to avoid dropping source signal.
                include = published_dt is None or published_dt >= cutoff
                if not include:
                    continue
                items.append(
                    {
                        "title": title,
                        "link": str(entry.get("link", "")),
                        "published": published_dt.isoformat() if published_dt else "missing",
                        "published_ts": published_dt.isoformat() if published_dt else "",
                        "source": source,
                    }
                )
                per_source_count += 1
                if per_source_count >= MAX_ITEMS_PER_SOURCE:
                    break
            except Exception:
                # Skip malformed entry only.
                continue
    return items
