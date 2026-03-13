"""Time helper utilities."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_iso(ts: datetime | None = None) -> str:
    value = ts or utc_now()
    return value.isoformat()
