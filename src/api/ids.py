from __future__ import annotations

from nanoid import generate


def new_nanoid() -> str:
    return generate()
