"""Trench / no-trench gate classifier.

Frozen DINOv2 image encoder + sklearn logistic regression head.

Loads on demand. Use MPS on Apple Silicon, CUDA where available, CPU otherwise.
Designed to be hosted in the same process as a YOLO detector — kept lightweight.

Usage:
    clf = TrenchClassifier.from_artifact("artifacts/trench_classifier")
    is_trench, score = clf.predict("path/to/image.jpg")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import joblib
import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from torchvision import transforms
from transformers import AutoImageProcessor, AutoModel

ImageInput = Union[str, Path, Image.Image]


@dataclass
class ClassifierMeta:
    model_id: str
    threshold: float
    embed_dim: int
    image_size: int
    train_counts: dict[str, int]
    cv_metrics: dict[str, float]
    notes: str = ""


def select_device(prefer: Optional[str] = None) -> torch.device:
    if prefer:
        return torch.device(prefer)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class TrenchClassifier:
    """Two-stage gate: DINOv2 frozen encoder → logistic regression."""

    def __init__(
        self,
        model_id: str,
        head: LogisticRegression,
        meta: ClassifierMeta,
        device: Optional[torch.device] = None,
        use_fp16: bool = True,
    ) -> None:
        self.model_id = model_id
        self.head = head
        self.meta = meta
        self.device = device or select_device()
        # FP16 only helps on GPU/MPS; CPU stays FP32 (FP16 ops are slow on CPU).
        self.dtype = torch.float16 if use_fp16 and self.device.type in ("cuda", "mps") else torch.float32

        self._processor = AutoImageProcessor.from_pretrained(model_id)
        self._model = AutoModel.from_pretrained(model_id).to(self.device, dtype=self.dtype).eval()
        for p in self._model.parameters():
            p.requires_grad_(False)

    # --- factory --------------------------------------------------------------
    @classmethod
    def from_artifact(
        cls,
        artifact_dir: Union[str, Path],
        device: Optional[str] = None,
        use_fp16: bool = True,
    ) -> "TrenchClassifier":
        artifact_dir = Path(artifact_dir)
        meta = ClassifierMeta(**json.loads((artifact_dir / "meta.json").read_text(encoding="utf-8")))
        head: LogisticRegression = joblib.load(artifact_dir / "head.joblib")
        # Cross-sklearn-version compat: sklearn ≥1.8 removed `multi_class`, but
        # older predict_proba implementations still read it. "auto" picks the
        # correct branch for binary LR with any solver.
        if not hasattr(head, "multi_class"):
            head.multi_class = "auto"
        return cls(
            model_id=meta.model_id,
            head=head,
            meta=meta,
            device=select_device(device),
            use_fp16=use_fp16,
        )

    # --- inference ------------------------------------------------------------
    @torch.inference_mode()
    def embed(self, img: ImageInput) -> np.ndarray:
        pil = self._to_pil(img)
        inputs = self._processor(images=pil, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device, dtype=self.dtype)
        out = self._model(pixel_values=pixel_values)
        # DINOv2 returns last_hidden_state with CLS token at position 0; use pooler_output if available.
        if getattr(out, "pooler_output", None) is not None:
            emb = out.pooler_output[0]
        else:
            emb = out.last_hidden_state[0, 0]
        return emb.float().cpu().numpy()

    def predict(self, img: ImageInput) -> tuple[bool, float]:
        """Return (is_trench, score_in_0_1)."""
        emb = self.embed(img).reshape(1, -1)
        score = float(self.head.predict_proba(emb)[0, self._trench_index()])
        return score >= self.meta.threshold, score

    def predict_batch(self, images: list[ImageInput]) -> list[tuple[bool, float]]:
        embs = np.stack([self.embed(im) for im in images])
        probs = self.head.predict_proba(embs)[:, self._trench_index()]
        return [(float(p) >= self.meta.threshold, float(p)) for p in probs]

    # --- helpers --------------------------------------------------------------
    def _trench_index(self) -> int:
        classes = list(self.head.classes_)
        return classes.index("trench")

    @staticmethod
    def _to_pil(img: ImageInput) -> Image.Image:
        if isinstance(img, Image.Image):
            return img.convert("RGB")
        return Image.open(img).convert("RGB")


def build_train_augmentation(image_size: int = 224) -> transforms.Compose:
    """Augmentation pipeline applied BEFORE the HF processor in training.

    Kept moderate because trenches are visually distinctive — heavy distortions
    create unrealistic samples and hurt rather than help.
    """
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(image_size, scale=(0.75, 1.0), ratio=(0.85, 1.15)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomApply([transforms.RandomRotation(degrees=10)], p=0.5),
            transforms.RandomApply(
                [transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.03)],
                p=0.7,
            ),
            transforms.RandomGrayscale(p=0.05),
        ]
    )
