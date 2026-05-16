#!/usr/bin/env python3
"""Finetune an Ultralytics YOLO v11 model on the duct-ruler-whitepaper dataset.

Persists the resulting `best.pt` as

    project-resources/weights/duct-ruler-whitepaper-coarse/<base_model>/<name>.pt

where `<base_model>` is derived from the model filename (e.g. `yolo11n`) and
`<name>` defaults to a UTC timestamp. Full ultralytics training artefacts are
kept under `<weights_dir>/<base_model>/_runs/<name>/` for inspection.

Requires the `[train]` extra:

    uv pip install -e ".[train]"

Example:

    uv run python scripts/train_yolo.py --model yolo11s.pt --epochs 100 --imgsz 640
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = (
    REPO_ROOT / "project-resources/custom-datasets/duct-and-ruler/detection/data.yaml"
)
WEIGHTS_ROOT = REPO_ROOT / "project-resources/weights/duct-ruler-whitepaper-coarse"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA,
        help=f"Path to data.yaml (default: {DEFAULT_DATA.relative_to(REPO_ROOT)})",
    )
    p.add_argument(
        "--model",
        default="yolo11n.pt",
        help=(
            "YOLO v11 base checkpoint: yolo11n.pt / yolo11s.pt / yolo11m.pt / "
            "yolo11l.pt / yolo11x.pt, or a path to a local .pt to resume from. "
            "Ultralytics downloads pretrained weights on first use."
        ),
    )
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size. Pass -1 for ultralytics autobatch.",
    )
    p.add_argument(
        "--device",
        default=None,
        help="cuda device id(s), e.g. '0' or '0,1', or 'cpu'. Default: ultralytics auto-detect.",
    )
    p.add_argument(
        "--name",
        default=None,
        help="Weight filename stem (no extension). Default: UTC timestamp.",
    )
    p.add_argument("--patience", type=int, default=50)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument(
        "--weights-root",
        type=Path,
        default=WEIGHTS_ROOT,
        help=f"Override the weights root (default: {WEIGHTS_ROOT.relative_to(REPO_ROOT)}).",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing target weight file with the same name.",
    )
    p.add_argument(
        "--extra",
        nargs="*",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Additional ultralytics train() kwargs, e.g. "
            "lr0=0.001 mosaic=0.5 cos_lr=true freeze=10."
        ),
    )
    return p.parse_args()


def _parse_extra(items: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--extra entries must be KEY=VALUE, got: {item!r}")
        key, raw = item.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"--extra entry has empty key: {item!r}")
        out[key] = _coerce(raw)
    return out


def _coerce(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def main() -> int:
    args = parse_args()

    if not args.data.is_file():
        print(f"[error] data.yaml not found: {args.data}", file=sys.stderr)
        return 2

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        print(
            f"[error] ultralytics not installed ({exc}). "
            f"Install with: uv pip install -e \".[train]\"",
            file=sys.stderr,
        )
        return 2

    base_stem = Path(args.model).stem
    weight_name = args.name or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    out_dir = args.weights_root / base_stem
    out_dir.mkdir(parents=True, exist_ok=True)
    final_weight = out_dir / f"{weight_name}.pt"
    if final_weight.exists() and not args.overwrite:
        print(
            f"[error] target weight already exists: {final_weight}. "
            f"Use --overwrite or pass a different --name.",
            file=sys.stderr,
        )
        return 2

    extra_kwargs = _parse_extra(args.extra)

    project_dir = out_dir / "_runs"
    project_dir.mkdir(exist_ok=True)

    model = YOLO(args.model)
    results = model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        patience=args.patience,
        seed=args.seed,
        workers=args.workers,
        project=str(project_dir),
        name=weight_name,
        exist_ok=args.overwrite,
        **extra_kwargs,
    )

    run_dir = Path(getattr(results, "save_dir", project_dir / weight_name))
    best = run_dir / "weights" / "best.pt"
    if not best.is_file():
        print(f"[error] best.pt not found at {best}", file=sys.stderr)
        return 1

    shutil.copy2(best, final_weight)
    print(f"[ok] saved finetuned weight: {final_weight}")
    print(f"[ok] training artefacts:    {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
