#!/usr/bin/env python3
"""Image-level binary presence metrics for YOLO predictions vs ground truth.

For each target class (default: duct, ruler — whitepaper excluded), reduce
both GT and predictions to a single yes/no per image:

    present_gt   = True iff GT has >=1 bbox of that class
    present_pred = True iff predictions has >=1 bbox of that class

Then report TP / FP / FN / TN, precision, recall, F1, accuracy. Bounding-box
geometry and instance counts are ignored — only class presence matters.

A prediction .txt missing for a GT stem is treated as "no detections at all"
for that image (all classes absent in predictions).

Usage:
    uv run python scripts/eval_presence.py \\
        --gt-labels   project-resources/custom-datasets/duct-and-ruler-manual/detection/labels/test \\
        --pred-labels project-resources/predictions/duct-ruler-whitepaper-coarse/latest/labels
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GT = (
    REPO_ROOT
    / "project-resources/custom-datasets/duct-and-ruler-manual/detection/labels/test"
)
DEFAULT_PRED = (
    REPO_ROOT
    / "project-resources/predictions/duct-ruler-whitepaper-coarse/latest/labels"
)
DEFAULT_DATA_YAML = (
    REPO_ROOT
    / "project-resources/custom-datasets/duct-and-ruler-manual/detection/data.yaml"
)
DEFAULT_TARGETS = ("duct", "ruler")  # whitepaper intentionally excluded


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--gt-labels", type=Path, default=DEFAULT_GT)
    p.add_argument("--pred-labels", type=Path, default=DEFAULT_PRED)
    p.add_argument("--data-yaml", type=Path, default=DEFAULT_DATA_YAML)
    p.add_argument(
        "--classes",
        nargs="+",
        default=list(DEFAULT_TARGETS),
        help=f"class names to score (default: {' '.join(DEFAULT_TARGETS)})",
    )
    return p.parse_args()


def _load_class_names(data_yaml: Path) -> list[str]:
    cfg = yaml.safe_load(data_yaml.read_text()) or {}
    names = cfg.get("names")
    if isinstance(names, dict):
        return [names[i] for i in range(max(int(k) for k in names) + 1)]
    if isinstance(names, list):
        return [str(n) for n in names]
    raise SystemExit(f"{data_yaml}: missing or malformed `names:`")


def _classes_in_label_file(path: Path, class_names: list[str]) -> set[str]:
    if not path.is_file():
        return set()
    present: set[str] = set()
    for line in path.read_text().splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        try:
            cls_id = int(parts[0])
        except ValueError:
            continue
        if 0 <= cls_id < len(class_names):
            present.add(class_names[cls_id])
    return present


def _div(num: float, den: float) -> float:
    return num / den if den else 0.0


def evaluate(
    gt_dir: Path, pred_dir: Path, class_names: list[str], targets: Iterable[str]
) -> tuple[int, dict[str, dict[str, int | float]]]:
    # Skip dotfiles (macOS `._*` resource-fork sidecars and similar) — they have
    # a .txt suffix but binary content and crash UTF-8 decoding.
    gt_files = sorted(
        p for p in gt_dir.iterdir()
        if p.suffix == ".txt" and not p.name.startswith(".")
    )
    if not gt_files:
        raise SystemExit(f"no .txt label files found in {gt_dir}")

    stats: dict[str, dict[str, int | float]] = {
        cls: {"tp": 0, "fp": 0, "fn": 0, "tn": 0} for cls in targets
    }
    for gt_path in gt_files:
        gt_present = _classes_in_label_file(gt_path, class_names)
        pred_present = _classes_in_label_file(pred_dir / gt_path.name, class_names)
        for cls in targets:
            g, p = (cls in gt_present), (cls in pred_present)
            if g and p:
                stats[cls]["tp"] += 1
            elif (not g) and p:
                stats[cls]["fp"] += 1
            elif g and (not p):
                stats[cls]["fn"] += 1
            else:
                stats[cls]["tn"] += 1

    for cls, s in stats.items():
        tp, fp, fn, tn = s["tp"], s["fp"], s["fn"], s["tn"]
        s["precision"] = _div(tp, tp + fp)
        s["recall"] = _div(tp, tp + fn)
        s["f1"] = _div(2 * tp, 2 * tp + fp + fn)
        s["accuracy"] = _div(tp + tn, tp + fp + fn + tn)
    return len(gt_files), stats


def _print_table(n_images: int, stats: dict[str, dict[str, int | float]]) -> None:
    header = f"{'class':<12} {'P_GT':>5} {'P_pred':>7} {'TP':>4} {'FP':>4} {'FN':>4} {'TN':>4} {'prec':>6} {'rec':>6} {'F1':>6} {'acc':>6}"
    print(f"# {n_images} images evaluated\n")
    print(header)
    print("-" * len(header))
    for cls, s in stats.items():
        present_gt = s["tp"] + s["fn"]
        present_pred = s["tp"] + s["fp"]
        print(
            f"{cls:<12} {present_gt:>5d} {present_pred:>7d} "
            f"{s['tp']:>4d} {s['fp']:>4d} {s['fn']:>4d} {s['tn']:>4d} "
            f"{s['precision']:>6.3f} {s['recall']:>6.3f} {s['f1']:>6.3f} {s['accuracy']:>6.3f}"
        )


def main() -> int:
    args = parse_args()

    if not args.gt_labels.is_dir():
        print(f"[error] GT labels dir not found: {args.gt_labels}", file=sys.stderr)
        return 2
    if not args.pred_labels.is_dir():
        print(f"[error] pred labels dir not found: {args.pred_labels}", file=sys.stderr)
        return 2

    class_names = _load_class_names(args.data_yaml)
    unknown = [c for c in args.classes if c not in class_names]
    if unknown:
        print(
            f"[error] unknown classes for this dataset: {unknown}. "
            f"Known: {class_names}",
            file=sys.stderr,
        )
        return 2

    n_images, stats = evaluate(args.gt_labels, args.pred_labels, class_names, args.classes)

    # Predictions in dirs that don't correspond to a GT stem are dropped silently.
    # Also count stale prediction files (predictions without GT) for visibility.
    gt_stems = {p.stem for p in args.gt_labels.iterdir() if p.suffix == ".txt"}
    pred_stems = {p.stem for p in args.pred_labels.iterdir() if p.suffix == ".txt"}
    orphan_preds = pred_stems - gt_stems
    if orphan_preds:
        sample = sorted(orphan_preds)[:3]
        print(
            f"[warn] {len(orphan_preds)} prediction file(s) have no matching GT stem "
            f"(ignored). Sample: {sample}",
            file=sys.stderr,
        )

    _print_table(n_images, stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
