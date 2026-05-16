"""Face presence check via RetinaFace (same stack as ``analyze/face_recog.py``).

Used for automated ``has_gdpr_problems`` when a face is detected. The detector model
is loaded lazily and shared as a process singleton.
"""

from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

_model_lock = threading.Lock()
_model = None


def _get_retinaface_model():
    """Lazy singleton RetinaFace model (thread-safe)."""
    global _model
    with _model_lock:
        if _model is None:
            from retinaface.pre_trained_models import get_model

            m = get_model("resnet50_2020-07-20", max_size=2048, device="cpu")
            m.eval()
            _model = m
        return _model


def _annotations_indicate_face(annotations: list[dict]) -> bool:
    for ann in annotations:
        bbox = ann.get("bbox") or []
        if bbox and len(bbox) >= 4:
            return True
    return False


def image_path_has_detected_face(
    image_path: str | Path,
    *,
    confidence_threshold: float = 0.8,
) -> bool:
    """Return True if at least one face is detected above the confidence threshold."""
    path = Path(image_path)
    if not path.is_file():
        return False
    try:
        with Image.open(path) as im:
            rgb = np.array(im.convert("RGB"))
    except (UnidentifiedImageError, OSError, ValueError):
        return False
    try:
        model = _get_retinaface_model()
        annotations = model.predict_jsons(rgb, confidence_threshold=confidence_threshold)
    except Exception:
        return False
    return _annotations_indicate_face(annotations)
