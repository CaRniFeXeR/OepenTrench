from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session, col, select

from src.api.helpers.photo_documentation_category import (
    effective_bool,
    mismatch_field_keys,
)
from src.api.models import AssetKind, PhotoAnalysis, ProjectAsset
from src.api.services.online_learning_service import _mismatch_condition, _reviewed_condition
from src.api.uploads import get_upload_root, project_asset_abs_path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATASET_ROOT = _REPO_ROOT / "project-resources" / "custom-datasets" / "duct-and-ruler"
_CLASSIFICATION_TRAIN = _DATASET_ROOT / "classification" / "train"
_DETECTION_IMAGES_TRAIN = _DATASET_ROOT / "detection" / "images" / "train"
_DETECTION_LABELS_TRAIN = _DATASET_ROOT / "detection" / "labels" / "train"

_DETECTION_MISMATCH_KEYS = frozenset({"duct", "ruler"})


@dataclass(frozen=True)
class ExportResult:
    photo_count: int
    classification_copied: int
    detection_copied: int


def _needs_detection_export(analysis: PhotoAnalysis) -> bool:
    fields = set(mismatch_field_keys(analysis))
    if fields & _DETECTION_MISMATCH_KEYS:
        return True
    return analysis.reviewer_has_duct is not None or analysis.reviewer_has_ruler is not None


def _write_yolo_labels(
    label_path: Path,
    *,
    boxes: list[tuple[int, float, float, float, float]],
    allow_class: set[int],
) -> None:
    lines: list[str] = []
    for class_id, xc, yc, w, h in boxes:
        if class_id not in allow_class:
            continue
        lines.append(f"{class_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
    label_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def export_mismatch_photos(session: Session) -> ExportResult:
    """Copy reviewer-corrected mismatch photos into canonical training datasets."""
    statement = (
        select(PhotoAnalysis, ProjectAsset)
        .join(ProjectAsset, col(PhotoAnalysis.asset_id) == col(ProjectAsset.id))
        .where(ProjectAsset.kind == AssetKind.image)
        .where(_reviewed_condition())
        .where(_mismatch_condition())
    )
    rows = session.exec(statement).all()

    upload_root = get_upload_root()
    classification_copied = 0
    detection_copied = 0

    for analysis, asset in rows:
        try:
            src = project_asset_abs_path(
                upload_root=upload_root,
                stored_relpath=asset.stored_relpath,
            )
        except ValueError:
            logger.warning("skip export invalid path asset_id=%s", asset.id)
            continue
        if not src.is_file():
            logger.warning("skip export missing file asset_id=%s path=%s", asset.id, src)
            continue

        ext = src.suffix.lower() or ".jpg"
        dest_name = f"{asset.id}{ext}"

        in_domain = effective_bool(analysis, "is_in_domain")
        cls_subdir = "trench" if in_domain else "no-trench"
        cls_dest = _CLASSIFICATION_TRAIN / cls_subdir / dest_name
        cls_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, cls_dest)
        classification_copied += 1

        if not _needs_detection_export(analysis):
            continue

        img_dest = _DETECTION_IMAGES_TRAIN / dest_name
        label_dest = _DETECTION_LABELS_TRAIN / f"{asset.id}.txt"
        img_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, img_dest)

        allow_class: set[int] = set()
        if effective_bool(analysis, "has_duct"):
            allow_class.add(0)
        if effective_bool(analysis, "has_ruler"):
            allow_class.add(1)
        if analysis.has_white_paper:
            allow_class.add(2)

        from src.api.services.yolo_detection_service import detect_boxes

        boxes = detect_boxes(src)
        _write_yolo_labels(label_dest, boxes=boxes, allow_class=allow_class)
        detection_copied += 1

    photo_count = len(rows)
    logger.info(
        "export complete photo_count=%d classification=%d detection=%d",
        photo_count,
        classification_copied,
        detection_copied,
    )
    return ExportResult(
        photo_count=photo_count,
        classification_copied=classification_copied,
        detection_copied=detection_copied,
    )
