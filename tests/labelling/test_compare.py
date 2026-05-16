"""Spec §10 unit tests — compare.py greedy matching + diff summary."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.labelling.compare import _Bbox, _greedy_match, compare_runs

CLASSES_YAML = textwrap.dedent(
    """
    path: /x
    train: images/train
    val: images/test
    test: images/test
    names:
      0: duct
      1: ruler
      2: whitepaper
    """
)


def _b(cls: str, xc: float, yc: float, w: float, h: float) -> _Bbox:
    return _Bbox(cls, xc, yc, w, h)


def test_greedy_match_pairs_largest_first():
    # Two a-boxes: a_big (area 0.09) and a_small (area 0.01).
    # Two b-boxes: b_overlaps_big perfectly, b_overlaps_small partially.
    a = [
        _b("duct", 0.5, 0.5, 0.1, 0.1),  # small, area 0.01
        _b("duct", 0.3, 0.3, 0.3, 0.3),  # big, area 0.09
    ]
    b = [
        _b("duct", 0.3, 0.3, 0.3, 0.3),  # matches big perfectly
        _b("duct", 0.5, 0.5, 0.08, 0.08),  # partial overlap with small
    ]
    ious = _greedy_match(a, b)
    # Result order matches input order of a.
    assert ious[1] == pytest.approx(1.0)  # big got its perfect match
    assert 0 < ious[0] < 1.0               # small got the partial leftover


def test_greedy_match_unmatched_records_minus_one():
    a = [_b("duct", 0.5, 0.5, 0.1, 0.1)]
    b = [_b("duct", 0.9, 0.9, 0.05, 0.05)]  # disjoint
    assert _greedy_match(a, b) == [-1.0]


def test_greedy_match_empty_sides():
    assert _greedy_match([], []) == []
    assert _greedy_match([], [_b("duct", 0.5, 0.5, 0.1, 0.1)]) == []
    assert _greedy_match([_b("duct", 0.5, 0.5, 0.1, 0.1)], []) == [-1.0]


def test_greedy_match_b_can_match_only_once():
    # Two a-boxes both compete for the same b-box.
    a = [
        _b("duct", 0.5, 0.5, 0.4, 0.4),  # bigger area → matched first
        _b("duct", 0.5, 0.5, 0.2, 0.2),  # smaller, same centre
    ]
    b = [_b("duct", 0.5, 0.5, 0.4, 0.4)]  # only one b-box
    ious = _greedy_match(a, b)
    # Bigger a (area 0.16) is sorted first, takes b. Smaller a gets -1.
    assert ious[0] == pytest.approx(1.0)
    assert ious[1] == -1.0


def test_compare_runs_full_flow(tmp_path):
    yaml_p = tmp_path / "data.yaml"
    yaml_p.write_text(CLASSES_YAML)

    a_dir = tmp_path / "run_a" / "labels"
    a_dir.mkdir(parents=True)
    (a_dir / "photo1.txt").write_text("1 0.5 0.5 0.2 0.6\n")  # ruler

    b_dir = tmp_path / "run_b" / "labels"
    b_dir.mkdir(parents=True)
    (b_dir / "photo1.txt").write_text("1 0.5 0.5 0.2 0.6\n")  # ruler, exact

    result = compare_runs(a_dir, b_dir, yaml_p)
    assert result.classes == ["duct", "ruler", "whitepaper"]
    assert result.summary["photos_compared"] == 1
    assert result.summary["class_presence_agreement_rate"] == 1.0
    assert result.summary["per_class_mean_iou_when_both_present"]["ruler"] == 1.0
    # No duct present anywhere, so 0.0.
    assert result.summary["per_class_mean_iou_when_both_present"]["duct"] == 0.0


def test_compare_runs_accepts_parent_dir(tmp_path):
    """compare auto-resolves labels/ subdir per ledger D-015."""
    yaml_p = tmp_path / "data.yaml"
    yaml_p.write_text(CLASSES_YAML)

    (tmp_path / "run_a" / "labels").mkdir(parents=True)
    (tmp_path / "run_b" / "labels").mkdir(parents=True)
    (tmp_path / "run_a" / "labels" / "x.txt").write_text("")
    (tmp_path / "run_b" / "labels" / "x.txt").write_text("")

    # Pass the parent dirs, not labels/.
    result = compare_runs(tmp_path / "run_a", tmp_path / "run_b", yaml_p)
    assert result.summary["photos_compared"] == 1


def test_compare_runs_handles_disjoint_class_sets(tmp_path):
    yaml_p = tmp_path / "data.yaml"
    yaml_p.write_text(CLASSES_YAML)

    a_dir = tmp_path / "a" / "labels"
    a_dir.mkdir(parents=True)
    (a_dir / "p.txt").write_text("0 0.5 0.5 0.2 0.2\n")  # duct

    b_dir = tmp_path / "b" / "labels"
    b_dir.mkdir(parents=True)
    (b_dir / "p.txt").write_text("2 0.5 0.5 0.4 0.3\n")  # whitepaper

    result = compare_runs(a_dir, b_dir, yaml_p)
    assert result.summary["class_presence_agreement_rate"] == 0.0
    rec = result.per_photo[0]
    assert rec["a_classes"]["duct"] is True
    assert rec["b_classes"]["whitepaper"] is True
    assert rec["class_agreement"] is False
