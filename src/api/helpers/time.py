from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """UTC timestamp for persisted fields."""
    return datetime.now(timezone.utc)
