"""YOLO duct/ruler/whitepaper presence detector for photo analysis.

Runs an Ultralytics YOLO model trained on
``project-resources/custom-datasets/duct-and-ruler/detection/data.yaml`` and
returns per-class boolean flags (``has_duct``, ``has_ruler``,
``has_white_paper``). Bounding boxes are discarded.

Env vars:
  OEPENTRENCH_YOLO_WEIGHTS  .pt weights path
                            (default: project-resources/weights/duct-ruler-whitepaper-coarse/active.pt)
  OEPENTRENCH_YOLO_CONF     confidence threshold (default 0.25)
  OEPENTRENCH_YOLO_DEVICE   ultralytics device string, e.g. cpu / cuda:0 (default: auto-detect)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from ultralytics import YOLO

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_WEIGHTS = (
    _REPO_ROOT / "project-resources/weights/duct-ruler-whitepaper-coarse/active.pt"
)

# data.yaml class name -> PhotoAnalysis bool field.
_CLASS_TO_FIELD = {
    "duct": "has_duct",
    "ruler": "has_ruler",
    "whitepaper": "has_white_paper",
}

_model: Any = None


def _load_model() -> Any:
    global _model
    if _model is None:
        weights = Path(
            os.environ.get("OEPENTRENCH_YOLO_WEIGHTS") or _DEFAULT_WEIGHTS
        ).expanduser().resolve()
        if not weights.is_file():
            raise FileNotFoundError(
                f"YOLO weights not found at {weights}. "
                "Set OEPENTRENCH_YOLO_WEIGHTS or place a trained .pt at the default path."
            )
        logger.info("loading YOLO weights from %s", weights)
        _model = YOLO(str(weights))
    return _model


def detect_target_classes(image_path: Path) -> dict[str, bool]:
    """Return ``{has_duct, has_ruler, has_white_paper}`` for the given image."""
    model = _load_model()
    result = model.predict(
        source=str(image_path),
        conf=float(os.environ.get("OEPENTRENCH_YOLO_CONF", 0.25)),
        device=os.environ.get("OEPENTRENCH_YOLO_DEVICE") or None,
        verbose=False,
    )[0]

    presence = dict.fromkeys(_CLASS_TO_FIELD.values(), False)
    for cls_tensor in result.boxes.cls:
        field = _CLASS_TO_FIELD.get(result.names[int(cls_tensor.item())].lower())
        if field is not None:
            presence[field] = True
    return presence
