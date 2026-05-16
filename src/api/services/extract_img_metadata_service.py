from __future__ import annotations

from sqlmodel import Session


def extract_img_metadata(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> dict:
    """Image metadata from OCR/EXIF (stub)."""
    return {}
