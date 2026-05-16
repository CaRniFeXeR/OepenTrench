"""Pydantic request/response models for the detection server.

Matches the harness client's expectations in
docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §5.1–§5.3.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Tuple

from pydantic import BaseModel, ConfigDict, Field


class DetectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_path: str = Field(min_length=1, description="absolute path on the VM filesystem")
    prompts: Dict[str, str]
    per_class_threshold: Dict[str, float]
    iou_nms: float = 0.5
    max_detections_per_class: int = 5


class Detection(BaseModel):
    cls: str
    bbox: Tuple[float, float, float, float]  # (xc, yc, w, h), all in [0,1]
    confidence: float


class DetectResponse(BaseModel):
    detections: List[Detection]
    model: str
    image_size: Tuple[int, int]
    latency_ms: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model: str
    uptime_s: int
    image_root: str
    images_under_root: int


class InfoResponse(BaseModel):
    model: str
    classes: List[str]
    default_prompts: Dict[str, str]
    default_thresholds: Dict[str, float]
