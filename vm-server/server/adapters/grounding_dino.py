"""IDEA-Research/grounding-dino-base — open-vocab object detector via HF Transformers."""
from __future__ import annotations

import logging
import time
from typing import List

import torch
from PIL import Image

from server.adapters.base import Adapter
from server.schema import Detection, DetectRequest, DetectResponse

logger = logging.getLogger(__name__)

DEFAULT_CLASSES = ["duct", "ruler", "whitepaper"]
DEFAULT_PROMPTS = {
    "duct": (
        "HDPE conduit . Schutzrohr . fibre optic cable . bundled coloured ducts . "
        "end caps . corrugated black pipe in trench"
    ),
    "ruler": (
        "folding rule . Zollstock . Meterstab . tape measure . levelling rod . "
        "painted ruler stake"
    ),
    "whitepaper": (
        "handwritten address note . printed address sheet . "
        "postal address with street and city . "
        "site identifier paper slip with contractor reference number"
    ),
}
DEFAULT_THRESHOLDS = {"duct": 0.25, "ruler": 0.20, "whitepaper": 0.30}


class GroundingDinoAdapter(Adapter):
    MODEL_NAME = "IDEA-Research/grounding-dino-base"

    def __init__(self) -> None:
        self._processor = None
        self._model = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    @property
    def model_id(self) -> str:
        return "grounding-dino-base"

    @property
    def classes(self) -> List[str]:
        return list(DEFAULT_CLASSES)

    def load_model(self) -> None:
        from transformers import (
            AutoModelForZeroShotObjectDetection,
            AutoProcessor,
        )

        logger.info("loading %s on %s", self.MODEL_NAME, self._device)
        self._processor = AutoProcessor.from_pretrained(self.MODEL_NAME)
        # Load in fp32; rely on autocast at inference time for bf16 speed-up.
        # Manual bf16 weights cause "Float vs BFloat16" mismatches in the
        # text-enhancer cross-attention because the processor emits fp32
        # text tensors that the model would otherwise need re-casting.
        self._model = (
            AutoModelForZeroShotObjectDetection.from_pretrained(self.MODEL_NAME)
            .to(self._device)
            .eval()
        )
        logger.info("loaded %s (fp32 weights, bf16 autocast at inference)", self.MODEL_NAME)

    def detect(self, req: DetectRequest) -> DetectResponse:
        if self._model is None or self._processor is None:
            raise RuntimeError("Adapter.load_model() must run before detect()")
        t0 = time.perf_counter()

        image = Image.open(req.image_path).convert("RGB")
        w, h = image.size

        # Build a concatenated prompt with class markers.
        prompt, class_phrases = self._build_prompt(req.prompts)

        inputs = self._processor(images=image, text=prompt, return_tensors="pt").to(
            self._device
        )
        # fp32 weights + bf16 autocast keeps the text/image cross-attention
        # dtype-consistent without manual casts at every entry point.
        autocast_ctx = (
            torch.autocast(device_type="cuda", dtype=torch.bfloat16)
            if self._device == "cuda"
            else torch.autocast(device_type="cpu", enabled=False)
        )
        with torch.inference_mode(), autocast_ctx:
            outputs = self._model(**inputs)

        target_sizes = torch.tensor([[h, w]], device=self._device)
        threshold = (
            min(req.per_class_threshold.values()) if req.per_class_threshold else 0.2
        )
        results = self._processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=threshold,
            text_threshold=0.2,
            target_sizes=target_sizes,
        )[0]

        per_class: dict = {c: [] for c in req.prompts}
        for box, label, score in zip(
            results["boxes"].tolist(),
            results["labels"],
            results["scores"].tolist(),
        ):
            cls = self._match_label_to_class(label, class_phrases)
            if cls is None:
                continue
            if score < req.per_class_threshold.get(cls, 1.0):
                continue
            x1, y1, x2, y2 = box
            per_class[cls].append((
                (x1 + x2) / 2 / w,
                (y1 + y2) / 2 / h,
                (x2 - x1) / w,
                (y2 - y1) / h,
                float(score),
            ))

        detections: List[Detection] = []
        for cls, dets in per_class.items():
            if not dets:
                continue
            dets = self._nms_normalized(dets, req.iou_nms)
            dets.sort(key=lambda d: -d[4])
            for xc, yc, bw, bh, conf in dets[: req.max_detections_per_class]:
                bbox = (
                    max(0.0, min(1.0, xc)),
                    max(0.0, min(1.0, yc)),
                    max(0.0, min(1.0, bw)),
                    max(0.0, min(1.0, bh)),
                )
                detections.append(
                    Detection(cls=cls, bbox=bbox, confidence=conf)
                )

        return DetectResponse(
            detections=detections,
            model=self.model_id,
            image_size=(w, h),
            latency_ms=int((time.perf_counter() - t0) * 1000),
        )

    @staticmethod
    def _build_prompt(prompts: dict) -> "tuple[str, dict]":
        """Return ``(concatenated_prompt, {cls: [lowercase tokens]})``."""
        parts: list = []
        class_phrases: dict = {}
        for cls, phrase in prompts.items():
            cleaned = phrase.strip().rstrip(".").strip()
            parts.append(cleaned + " .")
            class_phrases[cls] = cleaned.lower()
        return " ".join(parts), class_phrases

    @staticmethod
    def _match_label_to_class(label: str, class_phrases: dict) -> "str | None":
        """Match a detected label to a class by longest-substring score.

        For each class, compute (a) whether ``label`` appears in full inside
        the class's prompt, and (b) the longest single token of ``label`` that
        appears in the class's prompt. Pick the class with the highest score
        ``(full_match_len, longest_token_match_len)``.
        """
        lab = label.lower().strip(" .").strip()
        if not lab:
            return None

        scores: list = []  # (full_match_len, longest_token_match_len, cls)
        for cls, phrase in class_phrases.items():
            full = len(lab) if lab in phrase else 0
            best_tok = max(
                (len(tok) for tok in lab.split() if tok and tok in phrase),
                default=0,
            )
            scores.append((full, best_tok, cls))

        scores.sort(key=lambda t: (-t[0], -t[1]))
        full, best_tok, cls = scores[0]
        if full == 0 and best_tok == 0:
            return None
        return cls

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
        """Per-class NMS on cxcywh-normalised boxes. ``dets`` is list of (xc, yc, w, h, conf)."""
        sorted_dets = sorted(dets, key=lambda d: -d[4])
        kept: list = []
        for d in sorted_dets:
            if all(cls._iou_norm(d, k) < iou_thresh for k in kept):
                kept.append(d)
        return kept
