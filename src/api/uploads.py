from __future__ import annotations

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_UPLOAD_ROOT = _REPO_ROOT / "data" / "uploads"

IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})
GEOJSON_SUFFIXES = frozenset({".json", ".geojson"})


def get_upload_root() -> Path:
    """Resolve upload directory (override with OEPENTRENCH_UPLOAD_DIR)."""
    override = os.environ.get("OEPENTRENCH_UPLOAD_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return _DEFAULT_UPLOAD_ROOT.resolve()


def ensure_upload_root_exists() -> Path:
    root = get_upload_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def normalize_image_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        msg = f"unsupported image extension (allowed: {', '.join(sorted(IMAGE_SUFFIXES))})"
        raise ValueError(msg)
    return suffix


def normalize_geojson_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in GEOJSON_SUFFIXES:
        msg = f"unsupported geojson extension (allowed: {', '.join(sorted(GEOJSON_SUFFIXES))})"
        raise ValueError(msg)
    return suffix


def project_asset_abs_path(*, upload_root: Path, stored_relpath: str) -> Path:
    """Resolve a DB-stored relative path under the configured upload root."""
    rel = Path(stored_relpath)
    if rel.is_absolute() or rel.parts[:1] == ("..",) or ".." in rel.parts:
        raise ValueError("invalid stored path")
    return (upload_root / rel).resolve()


def stored_relpath_for_project_asset(*, project_id: str, asset_id: str, ext: str) -> str:
    ext = ext if ext.startswith(".") else f".{ext}"
    return f"{project_id}/{asset_id}{ext}"
