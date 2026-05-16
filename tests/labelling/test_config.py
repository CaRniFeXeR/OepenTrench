"""Spec §10 unit tests — YAML config load + Pydantic validation."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.labelling import ConfigError, LabellerConfig, load_config

VALID_YAML = textwrap.dedent(
    """
    name: grounding-dino
    mode: remote-vlm
    endpoint: http://localhost:8000
    model: grounding-dino-base
    remote_image_root: /home/user/data
    local_image_root: /tmp
    classes: [duct, ruler, whitepaper]
    prompts:
      duct: "HDPE conduit"
      ruler: "folding rule"
      whitepaper: "paper"
    per_class_threshold:
      duct: 0.25
      ruler: 0.20
      whitepaper: 0.30
    """
)


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "cfg.yaml"
    p.write_text(body)
    return p


def test_valid_config_loads(tmp_path):
    cfg = load_config(_write(tmp_path, VALID_YAML))
    assert isinstance(cfg, LabellerConfig)
    assert cfg.name == "grounding-dino"
    assert cfg.mode == "remote-vlm"
    assert cfg.classes == ["duct", "ruler", "whitepaper"]
    assert cfg.iou_nms == 0.5  # default
    assert cfg.retries == 2  # default


def test_missing_file_raises_config_error():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/foo.yaml")


def test_bad_yaml_syntax_raises_config_error(tmp_path):
    p = _write(tmp_path, "name: [unclosed")
    with pytest.raises(ConfigError, match="YAML parse"):
        load_config(p)


def test_non_mapping_top_level_raises_config_error(tmp_path):
    p = _write(tmp_path, "- a\n- b\n")
    with pytest.raises(ConfigError, match="must be a mapping"):
        load_config(p)


def test_missing_required_field_raises_config_error(tmp_path):
    body = VALID_YAML.replace("name: grounding-dino\n", "")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, body))


def test_unknown_field_rejected_by_extra_forbid(tmp_path):
    body = VALID_YAML + "extra_typo_field: 42\n"
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, body))


def test_prompts_missing_class_key_raises(tmp_path):
    body = VALID_YAML.replace('  whitepaper: "paper"\n', "")
    with pytest.raises(ConfigError, match="prompts keys"):
        load_config(_write(tmp_path, body))


def test_threshold_out_of_range_raises(tmp_path):
    body = VALID_YAML.replace("  duct: 0.25", "  duct: 1.5")
    with pytest.raises(ConfigError, match=r"per_class_threshold\['duct'\]=1.5"):
        load_config(_write(tmp_path, body))


def test_iou_nms_out_of_range_raises(tmp_path):
    body = VALID_YAML + "iou_nms: 1.5\n"
    with pytest.raises(ConfigError, match="iou_nms"):
        load_config(_write(tmp_path, body))


def test_negative_retries_raises(tmp_path):
    body = VALID_YAML + "retries: -1\n"
    with pytest.raises(ConfigError, match="retries"):
        load_config(_write(tmp_path, body))
