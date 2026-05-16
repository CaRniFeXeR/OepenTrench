"""Core data types and Labeller ABC for the labelling harness.

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §5.5.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from src.labelling.config import LabellerConfig


@dataclass
class Detection:
    cls: str
    bbox: Tuple[float, float, float, float]  # (xc, yc, w, h), all in [0,1], YOLO
    confidence: float


@dataclass
class LabelOutput:
    filename: str
    image_size: Tuple[int, int]
    detections: List[Detection]
    rationale: str
    image_quality: str  # "ok" | "poor"
    latency_ms: int


class LabellerError(Exception):
    """Permanent labeller failure (after retries exhausted, or non-retryable per §8)."""


class Labeller(ABC):
    """Abstract base for all labellers in the harness."""

    config: "LabellerConfig"

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def label(self, image_path: Path) -> LabelOutput:
        """Pre: image_path exists, readable. Post: LabelOutput with detections
        normalised to YOLO bbox in [0,1]. Raises LabellerError on permanent
        failure; transient failures are retried internally per config.retries.
        """

    def health_check(self) -> bool:
        """Override for backends that can probe. Default: assume healthy."""
        return True
