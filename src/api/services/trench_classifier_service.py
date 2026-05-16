"""Trench / no-trench gate for photo analysis.

Frozen DINOv2 image encoder + sklearn logistic regression head. Loaded once,
cached, used to decide whether downstream object detection should run.

Env vars:
  OEPENTRENCH_TRENCH_CLASSIFIER_DIR     artifact dir with head.joblib + meta.json
                                        (default: artifacts/trench_classifier_tuned)
  OEPENTRENCH_TRENCH_CLASSIFIER_DEVICE  cuda / mps / cpu (default: auto-detect)
  OEPENTRENCH_TRENCH_CLASSIFIER_NO_FP16 set any non-empty value to force FP32
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from src.classifier.trench_classifier import TrenchClassifier

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ARTIFACT_DIR = _REPO_ROOT / "artifacts" / "trench_classifier_tuned"

_classifier: Optional[TrenchClassifier] = None


def _load_classifier() -> TrenchClassifier:
    global _classifier
    if _classifier is None:
        artifact_dir = Path(
            os.environ.get("OEPENTRENCH_TRENCH_CLASSIFIER_DIR") or _DEFAULT_ARTIFACT_DIR
        ).expanduser().resolve()
        if not artifact_dir.is_dir():
            raise FileNotFoundError(
                f"Trench classifier artifact dir not found at {artifact_dir}. "
                "Train it with scripts/train_trench_classifier.py or set "
                "OEPENTRENCH_TRENCH_CLASSIFIER_DIR."
            )
        device = os.environ.get("OEPENTRENCH_TRENCH_CLASSIFIER_DEVICE") or None
        use_fp16 = not os.environ.get("OEPENTRENCH_TRENCH_CLASSIFIER_NO_FP16")
        logger.info("loading trench classifier from %s (device=%s, fp16=%s)", artifact_dir, device, use_fp16)
        _classifier = TrenchClassifier.from_artifact(artifact_dir, device=device, use_fp16=use_fp16)
    return _classifier


def is_trench(image_path: Path) -> bool:
    """Return True if the calibrated classifier scores this image as a trench."""
    clf = _load_classifier()
    label, _score = clf.predict(image_path)
    return bool(label)


def predict_trench(image_path: Path) -> tuple[bool, float]:
    """Return (is_trench, score) — score is P(trench) in [0, 1]. Useful for logging/UI."""
    clf = _load_classifier()
    label, score = clf.predict(image_path)
    return bool(label), float(score)
