"""Spec §10 unit tests — bbox conversion + IoU computation.

The harness has no standalone bbox-utility module; the math lives inside
``compare.py`` (IoU, xyxy conversion) and ``remote_labeller.py`` (range
validation). Tests exercise the math through those entry points.
"""
from __future__ import annotations

import math

import pytest

from src.labelling.compare import _Bbox, _iou


def _b(xc: float, yc: float, w: float, h: float) -> _Bbox:
    return _Bbox("duct", xc, yc, w, h)


def test_xyxy_round_trip():
    b = _b(0.5, 0.5, 0.4, 0.2)
    x1, y1, x2, y2 = b.to_xyxy()
    assert math.isclose(x1, 0.3)
    assert math.isclose(y1, 0.4)
    assert math.isclose(x2, 0.7)
    assert math.isclose(y2, 0.6)


def test_iou_identical_is_one():
    b = _b(0.5, 0.5, 0.2, 0.2)
    assert _iou(b, b) == pytest.approx(1.0)


def test_iou_disjoint_is_zero():
    assert _iou(_b(0.2, 0.2, 0.1, 0.1), _b(0.8, 0.8, 0.1, 0.1)) == 0.0


def test_iou_touching_edges_is_zero():
    # box A: x in [0.2, 0.4]; box B: x in [0.4, 0.6]
    a = _b(0.3, 0.3, 0.2, 0.2)
    b = _b(0.5, 0.3, 0.2, 0.2)
    assert _iou(a, b) == 0.0


def test_iou_half_overlap_in_x():
    # Two boxes identical except A shifted by half-width to the right.
    # Overlap area = 0.5*w * h; union = 1.5*w * h. IoU = 1/3.
    a = _b(0.5, 0.5, 0.2, 0.2)
    b = _b(0.6, 0.5, 0.2, 0.2)
    assert _iou(a, b) == pytest.approx(1 / 3, abs=1e-6)


def test_iou_one_box_inside_other():
    big = _b(0.5, 0.5, 0.4, 0.4)  # area 0.16
    small = _b(0.5, 0.5, 0.2, 0.2)  # area 0.04
    # Intersection = small, union = big. IoU = 0.04 / 0.16 = 0.25
    assert _iou(big, small) == pytest.approx(0.25)
    assert _iou(small, big) == pytest.approx(0.25)  # symmetric
