"""google/owlv2-large-patch14-ensemble — open-vocab object detection via HF Transformers.

Supports two modes per class:
- **Image-query**: takes 3–5 exemplar crops from disk, finds visually-similar
  regions in the target image. Best for fine-grained classes (R14 §2.4).
- **Text-prompt**: classic open-vocab fallback for classes without exemplars.

Per-class mode is decided at adapter construction time by ``EXEMPLARS``; if a
class has exemplars, image-query wins. Otherwise the adapter falls back to the
text prompt from ``DetectRequest.prompts``.

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §4.5.
"""
from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple

import torch
from PIL import Image

from server.adapters.base import Adapter
from server.schema import Detection, DetectRequest, DetectResponse

logger = logging.getLogger(__name__)

DEFAULT_CLASSES = ["duct", "ruler", "whitepaper"]

# Per-class exemplar paths on the VM filesystem. Image-query mode is used for
# any class with a non-empty list; classes with an empty list fall back to
# text-prompt mode using the prompt from the request.
EXEMPLARS: Dict[str, List[str]] = {
    "duct": [
        "/home/user/data/Beispiele/duct/IMG-20240808-WA0018.jpg",
        "/home/user/data/Beispiele/duct/IMG-20240810-WA0020.jpg",
        "/home/user/data/Beispiele/duct/IMG-20240817-WA0010.jpg",
        "/home/user/data/Beispiele/duct/IMG-20240817-WA0011.jpg",
    ],
    "ruler": [
        "/home/user/data/Beispiele/depth/1_IMG-20240731-WA0030.jpg",
        "/home/user/data/Beispiele/depth/1_IMG-20240813-WA0028.jpg",
        "/home/user/data/Beispiele/depth/1_IMG-20240813-WA0031.jpg",
        "/home/user/data/Beispiele/depth/1_IMG-20240813-WA0034.jpg",
    ],
    "whitepaper": [],  # no exemplars yet; falls back to text-prompt
}

DEFAULT_PROMPTS = {
    "duct": "HDPE conduit . fibre cable in trench",
    "ruler": "folding rule . tape measure",
    "whitepaper": (
        "white paper held in frame with handwritten or printed address . "
        "paper note with coordinates . white sheet with text"
    ),
}
DEFAULT_THRESHOLDS = {"duct": 0.20, "ruler": 0.15, "whitepaper": 0.10}


class OWLv2Adapter(Adapter):
    MODEL_NAME = "google/owlv2-large-patch14-ensemble"

    def __init__(self) -> None:
        self._processor = None
        self._model = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._exemplar_cache: Dict[str, List[Image.Image]] = {}

    @property
    def model_id(self) -> str:
        return "owlv2-large-patch14-ensemble"

    @property
    def classes(self) -> List[str]:
        return list(DEFAULT_CLASSES)

    def load_model(self) -> None:
        from transformers import Owlv2ForObjectDetection, Owlv2Processor

        logger.info("loading %s on %s", self.MODEL_NAME, self._device)
        self._processor = Owlv2Processor.from_pretrained(self.MODEL_NAME)
        self._model = (
            Owlv2ForObjectDetection.from_pretrained(self.MODEL_NAME)
            .to(self._device)
            .eval()
        )
        logger.info("loaded %s (fp32 weights, bf16 autocast at inference)", self.MODEL_NAME)

        # Pre-load exemplar images so the per-request hot path doesn't reopen.
        for cls, paths in EXEMPLARS.items():
            imgs: List[Image.Image] = []
            for p in paths:
                try:
                    imgs.append(Image.open(p).convert("RGB"))
                except FileNotFoundError:
                    logger.warning("exemplar missing for %s: %s", cls, p)
            self._exemplar_cache[cls] = imgs
            logger.info("class %s: %d exemplars loaded", cls, len(imgs))

    def detect(self, req: DetectRequest) -> DetectResponse:
        if self._model is None or self._processor is None:
            raise RuntimeError("Adapter.load_model() must run before detect()")
        t0 = time.perf_counter()

        image = Image.open(req.image_path).convert("RGB")
        w, h = image.size

        autocast_ctx = (
            torch.autocast(device_type="cuda", dtype=torch.bfloat16)
            if self._device == "cuda"
            else torch.autocast(device_type="cpu", enabled=False)
        )

        per_class: Dict[str, List[Tuple[float, float, float, float, float]]] = {
            c: [] for c in req.prompts
        }

        for cls in req.prompts:
            threshold = req.per_class_threshold.get(cls, 0.2)
            exemplars = self._exemplar_cache.get(cls, [])

            if exemplars:
                cls_dets = self._detect_image_query(
                    image, exemplars, threshold, autocast_ctx,
                )
            else:
                text = req.prompts.get(cls) or DEFAULT_PROMPTS.get(cls, cls)
                cls_dets = self._detect_text_prompt(
                    image, text, threshold, autocast_ctx,
                )

            per_class[cls].extend(cls_dets)

        detections: List[Detection] = []
        for cls, dets in per_class.items():
            if not dets:
                continue
            dets = self._nms_normalized(dets, req.iou_nms)
            dets.sort(key=lambda d: -d[4])
            for xc, yc, bw, bh, conf in dets[: req.max_detections_per_class]:
                bbox = (
                    max(0.0, min(1.0, xc / w)),
                    max(0.0, min(1.0, yc / h)),
                    max(0.0, min(1.0, bw / w)),
                    max(0.0, min(1.0, bh / h)),
                )
                detections.append(Detection(cls=cls, bbox=bbox, confidence=conf))

        return DetectResponse(
            detections=detections,
            model=self.model_id,
            image_size=(w, h),
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )

    def _detect_image_query(
        self,
        image: Image.Image,
        exemplars: List[Image.Image],
        threshold: float,
        autocast_ctx,
    ) -> List[Tuple[float, float, float, float, float]]:
        """Image-guided detection: each exemplar is a separate query; merge results."""
        w, h = image.size
        merged: List[Tuple[float, float, float, float, float]] = []

        for exemplar in exemplars:
            inputs = self._processor(
                images=image, query_images=exemplar, return_tensors="pt"
            ).to(self._device)
            with torch.inference_mode(), autocast_ctx:
                outputs = self._model.image_guided_detection(**inputs)
            target_sizes = torch.tensor([[h, w]], device=self._device)
            results = self._processor.post_process_image_guided_detection(
                outputs=outputs,
                threshold=threshold,
                nms_threshold=0.3,
                target_sizes=target_sizes,
            )[0]

            for box, score in zip(results["boxes"].tolist(), results["scores"].tolist()):
                if score < threshold:
                    continue
                x1, y1, x2, y2 = box
                merged.append((
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    x2 - x1,
                    y2 - y1,
                    float(score),
                ))
        return merged

    def _detect_text_prompt(
        self,
        image: Image.Image,
        text: str,
        threshold: float,
        autocast_ctx,
    ) -> List[Tuple[float, float, float, float, float]]:
        """Text-prompted detection — classic OWLv2 mode."""
        w, h = image.size
        # OWLv2 takes a list-of-lists: outer = batch, inner = candidate labels.
        queries = [[phrase.strip() for phrase in text.split(".") if phrase.strip()]]
        if not queries[0]:
            return []
        inputs = self._processor(
            text=queries, images=image, return_tensors="pt"
        ).to(self._device)
        with torch.inference_mode(), autocast_ctx:
            outputs = self._model(**inputs)
        target_sizes = torch.tensor([[h, w]], device=self._device)
        results = self._processor.post_process_object_detection(
            outputs=outputs, threshold=threshold, target_sizes=target_sizes,
        )[0]

        merged: List[Tuple[float, float, float, float, float]] = []
        for box, score in zip(results["boxes"].tolist(), results["scores"].tolist()):
            x1, y1, x2, y2 = box
            merged.append((
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                x2 - x1,
                y2 - y1,
                float(score),
            ))
        return merged

    @staticmethod
    def _iou_norm(a, b) -> float:
        ax1, ay1 = a[0] - a[2] / 2, a[1] - a[3] / 2
        ax2, ay2 = a[0] + a[2] / 2, a[1] + a[3] / 2
        bx1, by1 = b[0] - b[2] / 2, b[1] - b[3] / 2
        bx2, by2 = b[0] + b[2] / 2, b[1] + b[3] / 2
        iw = max(0.0, min(ax2, bx2) - max(ax1, bx1))
        ih = max(0.0, min(ay2, by2) - max(ay1, by1))
        inter = iw * ih
        if inter <= 0:
            return 0.0
        union = a[2] * a[3] + b[2] * b[3] - inter
        return inter / union if union > 0 else 0.0

    @classmethod
    def _nms_normalized(cls, dets: list, iou_thresh: float) -> list:
        sorted_dets = sorted(dets, key=lambda d: -d[4])
        kept: list = []
        for d in sorted_dets:
            if all(cls._iou_norm(d, k) < iou_thresh for k in kept):
                kept.append(d)
        return kept
