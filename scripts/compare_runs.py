"""CLI for ``src.labelling.compare`` — diff two labelling runs.

Usage::

    python scripts/compare_runs.py <run_a> <run_b> --classes <data.yaml> [--out diff.json] [--fiftyone]

``run_a`` and ``run_b`` may point either at a ``labels/`` directory or at the
run directory that contains one.

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §5.6, §6.6.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.labelling.compare import (
    compare_runs,
    open_fiftyone_side_by_side,
    write_diff_json,
)

DEFAULT_FOTOS_ROOT = (
    Path(__file__).resolve().parent.parent
    / "project-resources"
    / "Fotos"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_a", type=Path, help="labels/ dir or run dir for run A")
    parser.add_argument("run_b", type=Path, help="labels/ dir or run dir for run B")
    parser.add_argument(
        "--classes",
        type=Path,
        required=True,
        help="path to data.yaml (provides class names + ids)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write diff JSON to this path (default: print to stdout)",
    )
    parser.add_argument(
        "--fiftyone",
        action="store_true",
        help="open a FiftyOne side-by-side dataset after the diff",
    )
    parser.add_argument(
        "--images-root",
        type=Path,
        default=DEFAULT_FOTOS_ROOT,
        help=f"images directory (default: {DEFAULT_FOTOS_ROOT})",
    )
    args = parser.parse_args()

    if not args.classes.is_file():
        print(f"error: classes file not found: {args.classes}", file=sys.stderr)
        return 2

    result = compare_runs(args.run_a, args.run_b, args.classes)

    if args.out:
        write_diff_json(result, args.out)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(json.dumps(result.to_json(), indent=2))

    print(
        f"\nSummary: {result.summary['photos_compared']} photos, "
        f"class-presence agreement {result.summary['class_presence_agreement_rate']:.1%}",
        file=sys.stderr,
    )
    for cls, miou in result.summary[
        "per_class_mean_iou_when_both_present"
    ].items():
        print(f"  {cls}: mean IoU = {miou:.3f}", file=sys.stderr)

    if args.fiftyone:
        open_fiftyone_side_by_side(result, args.images_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
