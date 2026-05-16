"""Regression test for _load_class_names — string-keyed YAML must sort numerically."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.labelling.compare import _load_class_names


def _yaml(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "data.yaml"
    p.write_text(body)
    return p


def test_int_keys_sort_numerically(tmp_path):
    p = _yaml(tmp_path, textwrap.dedent("""
        names:
          0: duct
          1: ruler
          2: whitepaper
          3: sitetag
    """))
    assert _load_class_names(p) == ["duct", "ruler", "whitepaper", "sitetag"]


def test_string_keys_sort_numerically_not_lexically(tmp_path):
    """Regression: pre-fix, sorted(['0','1','10','2']) gave ['0','1','10','2']
    which would misorder class IDs ≥ 10."""
    p = _yaml(tmp_path, textwrap.dedent("""
        names:
          "0": duct
          "1": ruler
          "10": tenth_class
          "2": whitepaper
    """))
    assert _load_class_names(p) == ["duct", "ruler", "whitepaper", "tenth_class"]


def test_list_form(tmp_path):
    p = _yaml(tmp_path, "names:\n  - duct\n  - ruler\n")
    assert _load_class_names(p) == ["duct", "ruler"]


def test_missing_names_key_raises_clean(tmp_path):
    p = _yaml(tmp_path, "path: /x\ntrain: y\n")
    with pytest.raises(ValueError, match="missing top-level 'names'"):
        _load_class_names(p)


def test_bad_yaml_raises_clean(tmp_path):
    p = _yaml(tmp_path, "names: [unclosed")
    with pytest.raises(ValueError, match="YAML parse"):
        _load_class_names(p)


def test_non_numeric_keys_raise_clean(tmp_path):
    p = _yaml(tmp_path, "names:\n  foo: duct\n  bar: ruler\n")
    with pytest.raises(ValueError, match="must be ints"):
        _load_class_names(p)
