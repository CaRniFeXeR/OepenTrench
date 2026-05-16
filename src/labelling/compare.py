"""Compare two labelling runs — per-photo class-presence agreement + greedy IoU matching.

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §6.6, §13 ("greedy IoU matching" gap).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


@dataclass
class _Bbox:
    cls: str
    xc: float
    yc: float
    w: float
    h: float

    @property
    def area(self) -> float:
        return self.w * self.h

    def to_xyxy(self) -> Tuple[float, float, float, float]:
        return (
            self.xc - self.w / 2,
            self.yc - self.h / 2,
            self.xc + self.w / 2,
            self.yc + self.h / 2,
        )


def _load_class_names(data_yaml: Path) -> List[str]:
    raw = yaml.safe_load(data_yaml.read_text())
    names = raw["names"]
    if isinstance(names, dict):
        return [names[i] for i in sorted(names.keys())]
    if isinstance(names, list):
        return list(names)
    raise ValueError(f"unrecognised 'names' shape in {data_yaml}: {type(names).__name__}")


def _load_yolo_file(path: Path, classes: List[str]) -> List[_Bbox]:
    if not path.is_file():
        return []
    bboxes: List[_Bbox] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            continue
        try:
            cls_id = int(parts[0])
            xc, yc, w, h = (float(p) for p in parts[1:])
        except ValueError:
            continue
        if not (0 <= cls_id < len(classes)):
            continue
        bboxes.append(_Bbox(classes[cls_id], xc, yc, w, h))
    return bboxes


def _iou(a: _Bbox, b: _Bbox) -> float:
    ax1, ay1, ax2, ay2 = a.to_xyxy()
    bx1, by1, bx2, by2 = b.to_xyxy()
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    union = a.area + b.area - inter
    if union <= 0:
        return 0.0
    return inter / union


def _greedy_match(a_boxes: List[_Bbox], b_boxes: List[_Bbox]) -> List[float]:
    """Greedy IoU matching per spec §13.

    For each a-box (sorted by area desc), pick the highest-IoU unmatched b-box.
    Record the IoU; b-boxes can match at most once. Unmatched a-boxes get -1.
    Returns one IoU per a-box in input order (not sort order).
    """
    if not a_boxes:
        return []
    if not b_boxes:
        return [-1.0] * len(a_boxes)

    indexed_a = sorted(enumerate(a_boxes), key=lambda x: -x[1].area)
    matched_b: set = set()
    result: List[Optional[float]] = [None] * len(a_boxes)

    for orig_idx, a in indexed_a:
        best_iou = -1.0
        best_b_idx = -1
        for j, b in enumerate(b_boxes):
            if j in matched_b:
                continue
            iou = _iou(a, b)
            if iou > best_iou:
                best_iou = iou
                best_b_idx = j
        if best_b_idx >= 0 and best_iou > 0.0:
            matched_b.add(best_b_idx)
            result[orig_idx] = best_iou
        else:
            result[orig_idx] = -1.0

    return [r if r is not None else -1.0 for r in result]


def _resolve_labels_dir(p: Path) -> Path:
    """Accept either a `labels/` dir or its parent (the run dir)."""
    if (p / "labels").is_dir():
        return p / "labels"
    return p


def _enumerate_stems(*dirs: Path) -> List[str]:
    stems: set = set()
    for d in dirs:
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.suffix == ".txt":
                stems.add(f.stem)
    return sorted(stems)


@dataclass
class CompareResult:
    run_a: str
    run_b: str
    classes: List[str]
    per_photo: List[dict] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "run_a": self.run_a,
            "run_b": self.run_b,
            "classes": self.classes,
            "per_photo": self.per_photo,
            "summary": self.summary,
        }


def compare_runs(run_a: Path, run_b: Path, data_yaml: Path) -> CompareResult:
    """Compute the per-photo diff between two label dirs.

    ``run_a``/``run_b`` may point at either a ``labels/`` dir or its parent.
    Returns a ``CompareResult`` matching the shape in spec §6.6.
    """
    a_labels = _resolve_labels_dir(run_a)
    b_labels = _resolve_labels_dir(run_b)
    classes = _load_class_names(data_yaml)

    stems = _enumerate_stems(a_labels, b_labels)

    per_photo: List[dict] = []
    presence_agreement_hits = 0
    per_class_iou_sum: Dict[str, float] = {c: 0.0 for c in classes}
    per_class_iou_count: Dict[str, int] = {c: 0 for c in classes}

    for stem in stems:
        a_boxes = _load_yolo_file(a_labels / f"{stem}.txt", classes)
        b_boxes = _load_yolo_file(b_labels / f"{stem}.txt", classes)

        a_classes = {c: any(b.cls == c for b in a_boxes) for c in classes}
        b_classes = {c: any(b.cls == c for b in b_boxes) for c in classes}
        class_agreement = a_classes == b_classes
        if class_agreement:
            presence_agreement_hits += 1

        photo_record: dict = {
            "filename": stem,
            "a_classes": a_classes,
            "b_classes": b_classes,
            "class_agreement": class_agreement,
        }

        for cls in classes:
            a_of_cls = [b for b in a_boxes if b.cls == cls]
            b_of_cls = [b for b in b_boxes if b.cls == cls]
            ious = _greedy_match(a_of_cls, b_of_cls)
            photo_record[f"{cls}_ious"] = ious
            if a_classes[cls] and b_classes[cls]:
                for iou in ious:
                    if iou >= 0:
                        per_class_iou_sum[cls] += iou
                        per_class_iou_count[cls] += 1

        per_photo.append(photo_record)

    total = max(1, len(stems))
    summary = {
        "class_presence_agreement_rate": round(presence_agreement_hits / total, 4),
        "per_class_mean_iou_when_both_present": {
            cls: round(per_class_iou_sum[cls] / per_class_iou_count[cls], 4)
            if per_class_iou_count[cls] > 0
            else 0.0
            for cls in classes
        },
        "photos_compared": len(stems),
    }

    return CompareResult(
        run_a=str(run_a),
        run_b=str(run_b),
        classes=classes,
        per_photo=per_photo,
        summary=summary,
    )


def write_diff_json(result: CompareResult, out: Path) -> None:
    out.write_text(json.dumps(result.to_json(), indent=2) + "\n")


def open_fiftyone_side_by_side(
    result: CompareResult,
    images_root: Path,
    name: str = "labelling-runs-diff",
) -> None:
    """Open a FiftyOne dataset showing run_a and run_b predictions side-by-side.

    Lazily imports FiftyOne so the rest of the harness has no hard dep on it.
    """
    import fiftyone as fo  # type: ignore

    if fo.dataset_exists(name):
        fo.delete_dataset(name)

    samples: list = []
    a_labels = _resolve_labels_dir(Path(result.run_a))
    b_labels = _resolve_labels_dir(Path(result.run_b))

    by_stem: Dict[str, Path] = {p.stem: p for p in images_root.iterdir() if p.is_file()}

    for record in result.per_photo:
        stem = record["filename"]
        img = by_stem.get(stem)
        if img is None:
            continue
        sample = fo.Sample(filepath=str(img))
        for side, labels_dir in (("a", a_labels), ("b", b_labels)):
            txt = labels_dir / f"{stem}.txt"
            if not txt.is_file():
                continue
            dets: list = []
            for box in _load_yolo_file(txt, result.classes):
                x = max(0.0, box.xc - box.w / 2)
                y = max(0.0, box.yc - box.h / 2)
                dets.append(
                    fo.Detection(label=box.cls, bounding_box=[x, y, box.w, box.h])
                )
            sample[f"run_{side}"] = fo.Detections(detections=dets)
        sample["class_agreement"] = record["class_agreement"]
        samples.append(sample)

    ds = fo.Dataset(name, persistent=True)
    ds.add_samples(samples)
    ds.default_classes = result.classes
    ds.save()
    fo.launch_app(ds)
