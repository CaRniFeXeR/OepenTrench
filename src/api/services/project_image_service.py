from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from src.api.models import AssetKind, ProjectAsset
from src.api.uploads import ensure_upload_root_exists, project_asset_abs_path

_MEDIA_TYPE_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def media_type_for_asset_path(stored_relpath: str) -> str:
    suffix = Path(stored_relpath).suffix.lower()
    return _MEDIA_TYPE_BY_SUFFIX.get(suffix, "application/octet-stream")


def resolve_project_image_path(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> tuple[ProjectAsset, Path, str]:
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise LookupError("asset not found")
    if asset.project_id != project_id:
        raise LookupError("asset not found")
    if asset.kind != AssetKind.image:
        raise ValueError("asset is not an image")

    upload_root = ensure_upload_root_exists()
    abs_path = project_asset_abs_path(
        upload_root=upload_root,
        stored_relpath=asset.stored_relpath,
    )
    if not abs_path.is_file():
        raise LookupError("image file missing on disk")

    return asset, abs_path, media_type_for_asset_path(asset.stored_relpath)
