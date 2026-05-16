"""YAML → LabellerConfig loader (Pydantic v2).

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §6.5.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic import ValidationError as PydanticValidationError


class ConfigError(Exception):
    """YAML loading or validation failed. Maps to exit code 2 per spec §7."""


class LabellerConfig(BaseModel):
    """Labelling-profile config, loaded from configs/labelling/<name>.yaml."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    mode: Literal["remote-vlm"]
    endpoint: str = Field(min_length=1)
    model: str = Field(min_length=1)
    remote_image_root: str = Field(min_length=1)
    local_image_root: str = Field(min_length=1)
    classes: List[str] = Field(min_length=1)
    prompts: Dict[str, str]
    per_class_threshold: Dict[str, float]
    iou_nms: float = 0.5
    max_detections_per_class: int = 5
    timeout_seconds: float = 60.0
    retries: int = 2

    @model_validator(mode="after")
    def _check_class_coverage(self) -> "LabellerConfig":
        cls_set = set(self.classes)
        prompt_keys = set(self.prompts.keys())
        thresh_keys = set(self.per_class_threshold.keys())
        if prompt_keys != cls_set:
            raise ValueError(
                f"prompts keys {sorted(prompt_keys)} must match classes {sorted(cls_set)}"
            )
        if thresh_keys != cls_set:
            raise ValueError(
                f"per_class_threshold keys {sorted(thresh_keys)} must match classes "
                f"{sorted(cls_set)}"
            )
        for c, t in self.per_class_threshold.items():
            if not 0.0 <= t <= 1.0:
                raise ValueError(f"per_class_threshold[{c!r}]={t} must be in [0,1]")
        if not 0.0 <= self.iou_nms <= 1.0:
            raise ValueError(f"iou_nms={self.iou_nms} must be in [0,1]")
        if self.max_detections_per_class < 1:
            raise ValueError(
                f"max_detections_per_class={self.max_detections_per_class} must be ≥ 1"
            )
        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds={self.timeout_seconds} must be > 0")
        if self.retries < 0:
            raise ValueError(f"retries={self.retries} must be ≥ 0")
        return self


def load_config(path: Union[Path, str]) -> LabellerConfig:
    """Load and validate a labelling-profile YAML.

    Raises ConfigError on file-not-found, YAML parse error, or schema validation failure.
    """
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"config file not found: {p}")
    try:
        raw = yaml.safe_load(p.read_text())
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML parse error in {p}: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(
            f"{p}: top-level must be a mapping, got {type(raw).__name__}"
        )
    try:
        return LabellerConfig.model_validate(raw)
    except PydanticValidationError as e:
        raise ConfigError(f"invalid config in {p}:\n{e}") from e
