#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to openapi/openapi.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "openapi" / "openapi.json"


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT))
    from src.api.main import app

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(app.openapi(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
