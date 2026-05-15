from __future__ import annotations


def clamp_limit(value: int, *, default: int = 50, maximum: int = 200) -> int:
    """Keep list endpoints from requesting huge pages."""
    if value < 1:
        return default
    return min(value, maximum)


def clamp_offset(value: int) -> int:
    if value < 0:
        return 0
    return value
