"""Tests for scripts/inspect_labels.py meta-loading helpers.

Covers the per-class rollup derivation that previously was duct/ruler-hardcoded
and silently empty on v3 runs. Helpers are pure-Python so we don't need fiftyone
installed for these tests; we import them via importlib because the script lives
outside the importable package layout.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "inspect_labels.py"


def _load_inspect_module():
    """Load scripts/inspect_labels.py without requiring fiftyone.

    The script imports fiftyone at module level (it's the whole point of the script);
    if it's not installed, skip — the helpers we test are reachable through that
    import only.
    """
    pytest.importorskip("fiftyone")
    spec = importlib.util.spec_from_file_location("inspect_labels", _SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["inspect_labels"] = mod
    spec.loader.exec_module(mod)
    return mod


# --- derive_class_counts ------------------------------------------------------

def test_derive_class_counts_three_class():
    mod = _load_inspect_module()
    out = mod.derive_class_counts(
        ["duct", "duct", "ruler"], ["duct", "ruler", "whitepaper"]
    )
    assert out == {
        "has_duct": True, "n_duct_bboxes": 2,
        "has_ruler": True, "n_ruler_bboxes": 1,
        "has_whitepaper": False, "n_whitepaper_bboxes": 0,
    }


def test_derive_class_counts_empty():
    mod = _load_inspect_module()
    out = mod.derive_class_counts([], ["duct", "ruler"])
    assert out == {
        "has_duct": False, "n_duct_bboxes": 0,
        "has_ruler": False, "n_ruler_bboxes": 0,
    }


def test_derive_class_counts_scales_to_arbitrary_class_set():
    mod = _load_inspect_module()
    out = mod.derive_class_counts(
        ["x", "y", "x", "z"], ["x", "y", "z", "w"],
    )
    assert out["n_x_bboxes"] == 2
    assert out["n_y_bboxes"] == 1
    assert out["n_z_bboxes"] == 1
    assert out["n_w_bboxes"] == 0
    assert out["has_w"] is False


# --- derive_class_confidence --------------------------------------------------

def test_derive_class_confidence_v3_max_per_class():
    mod = _load_inspect_module()
    meta = {
        "bboxes": [
            {"cls": "duct", "confidence": 0.7},
            {"cls": "duct", "confidence": 0.4},
            {"cls": "ruler", "confidence": 0.55},
        ],
    }
    out = mod.derive_class_confidence(meta, ["duct", "ruler", "whitepaper"])
    # Ruler max comes from its single bbox; whitepaper absent → omitted.
    assert out == {"duct_max_confidence": 0.7, "ruler_max_confidence": 0.55}


def test_derive_class_confidence_v3_empty_bboxes():
    mod = _load_inspect_module()
    out = mod.derive_class_confidence({"bboxes": []}, ["duct", "ruler"])
    assert out == {}  # v3 schema recognized, but nothing to roll up


def test_derive_class_confidence_v3_skips_non_numeric_confidence():
    mod = _load_inspect_module()
    meta = {"bboxes": [{"cls": "duct", "confidence": "high"}]}
    out = mod.derive_class_confidence(meta, ["duct"])
    assert out == {}  # not a real number → skipped, no key emitted


def test_derive_class_confidence_v2_string_passthrough():
    mod = _load_inspect_module()
    meta = {
        "has_duct": False, "duct_confidence": "n/a",
        "has_ruler": True, "ruler_confidence": "medium",
    }
    out = mod.derive_class_confidence(meta, ["duct", "ruler", "whitepaper"])
    # v2 schema (no `bboxes`) → string passthrough; whitepaper absent in meta → omitted.
    assert out == {"duct_confidence": "n/a", "ruler_confidence": "medium"}


def test_derive_class_confidence_neither_schema_yields_empty():
    mod = _load_inspect_module()
    out = mod.derive_class_confidence({"foo": "bar"}, ["duct", "ruler"])
    assert out == {}


# --- _meta_schema_known fingerprint -------------------------------------------

def test_schema_fingerprint_v3_recognized():
    mod = _load_inspect_module()
    assert mod._meta_schema_known(
        {"bboxes": [], "run_id": "r", "filename": "x.jpg"}
    )


def test_schema_fingerprint_v2_recognized():
    mod = _load_inspect_module()
    assert mod._meta_schema_known({"has_duct": False, "duct_confidence": "n/a"})


def test_schema_fingerprint_unknown_meta():
    mod = _load_inspect_module()
    assert not mod._meta_schema_known({"some_other_field": 1})


# --- build_samples end-to-end (only when fiftyone is installed) ---------------

def _write_jpeg(path: Path, size=(40, 30)) -> None:
    pytest.importorskip("PIL")
    from PIL import Image
    Image.new("RGB", size, color=(128, 128, 128)).save(path, format="JPEG")


def test_build_samples_v3_meta_populates_per_class_rollup(tmp_path):
    mod = _load_inspect_module()
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    meta = tmp_path / "meta"
    for d in (images, labels, meta):
        d.mkdir()

    _write_jpeg(images / "a.jpg")
    (labels / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n2 0.3 0.3 0.1 0.1\n")
    (meta / "a.json").write_text(
        '{"filename":"a.jpg","image_size":[40,30],"run_id":"r","model":"m",'
        '"bboxes":[{"cls":"duct","bbox":[0.5,0.5,0.2,0.2],"confidence":0.8},'
        '{"cls":"whitepaper","bbox":[0.3,0.3,0.1,0.1],"confidence":0.4}],'
        '"image_quality":"ok","rationale":"r","latency_ms":12}'
    )

    samples = mod.build_samples(labels, meta, images, ["duct", "ruler", "whitepaper"])
    assert len(samples) == 1
    s = samples[0]
    assert s["has_duct"] is True and s["n_duct_bboxes"] == 1
    assert s["has_ruler"] is False and s["n_ruler_bboxes"] == 0
    assert s["has_whitepaper"] is True and s["n_whitepaper_bboxes"] == 1
    assert s["duct_max_confidence"] == 0.8
    assert s["whitepaper_max_confidence"] == 0.4
    assert s["image_quality"] == "ok"
    assert s["model"] == "m"
    assert s["latency_ms"] == 12


def test_build_samples_v2_meta_populates_legacy_confidence(tmp_path):
    mod = _load_inspect_module()
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    meta = tmp_path / "meta"
    for d in (images, labels, meta):
        d.mkdir()

    _write_jpeg(images / "b.jpg")
    (labels / "b.txt").write_text("1 0.5 0.5 0.2 0.2\n")
    (meta / "b.json").write_text(
        '{"filename":"b.jpg","has_duct":false,"has_ruler":true,'
        '"n_duct_bboxes":0,"n_ruler_bboxes":1,'
        '"duct_confidence":"n/a","ruler_confidence":"medium",'
        '"image_quality":"ok","rationale":"r","notes":"n"}'
    )

    samples = mod.build_samples(labels, meta, images, ["duct", "ruler", "whitepaper"])
    assert len(samples) == 1
    s = samples[0]
    # Per-class rollup derived from YOLO .txt, not from v2 hardcoded keys.
    assert s["has_ruler"] is True and s["n_ruler_bboxes"] == 1
    assert s["has_duct"] is False and s["n_duct_bboxes"] == 0
    assert s["has_whitepaper"] is False and s["n_whitepaper_bboxes"] == 0
    # v2 legacy string confidence pass-through.
    assert s["duct_confidence"] == "n/a"
    assert s["ruler_confidence"] == "medium"
    assert s["notes"] == "n"
    assert s["rationale"] == "r"


def test_build_samples_warns_once_on_unknown_meta_schema(tmp_path, capsys):
    mod = _load_inspect_module()
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    meta = tmp_path / "meta"
    for d in (images, labels, meta):
        d.mkdir()

    for stem in ("a", "b"):
        _write_jpeg(images / f"{stem}.jpg")
        (labels / f"{stem}.txt").write_text("0 0.5 0.5 0.2 0.2\n")
        (meta / f"{stem}.json").write_text('{"unrelated": 1}')

    samples = mod.build_samples(labels, meta, images, ["duct", "ruler"])
    assert len(samples) == 2
    err = capsys.readouterr().err
    assert err.count("neither v2 nor v3 schema") == 1  # once per run dir
