"""CLI entry point — drive a labelling run end-to-end.

Usage::

    python scripts/label.py --config configs/labelling/<profile>.yaml \\
        [--batches 0,1,2] [--limit 20] \\
        [--image-path <abs-path>] \\
        [--out labelling/runs/] [--health-check] [--no-progress]

Exit codes per spec §7:
    0 — images_failed == 0 (or health-check passed)
    1 — at least one image failed
    2 — ConfigError (invalid YAML, missing file, validation failure)
    3 — ServerUnreachable (`/health` returned non-200 or connect-timeout)

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §5.6, §7.
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import List, Optional, Set

from src.labelling import ConfigError, LabellerConfig, load_config
from src.labelling.remote_labeller import RemoteVlmLabeller
from src.labelling.runner import RunResult, run

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = (
    REPO_ROOT
    / "project-resources"
    / "custom-datasets"
    / "duct-and-ruler"
    / "detection"
)
DEFAULT_MANIFEST = DATASET_ROOT / "labelling" / "manifest.csv"
DEFAULT_OUT = DATASET_ROOT / "labelling" / "runs"
FOTOS_ROOT = REPO_ROOT / "project-resources" / "Fotos"


def _resolve_image(filename: str, local_image_root: Path) -> Path:
    """Resolve a manifest filename → absolute local path.

    Try ``local_image_root / Fotos / filename`` first (most likely), then
    ``local_image_root / filename`` (treat the root as already pointing at Fotos).
    """
    candidates = [
        local_image_root / "Fotos" / filename,
        local_image_root / filename,
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    # Return the first candidate so the error surfaces at label() with the
    # path the operator can act on.
    return candidates[0]


def _load_manifest(
    manifest_path: Path,
    batches: Optional[Set[int]],
    limit: Optional[int],
    local_image_root: Path,
) -> List[Path]:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    paths: List[Path] = []
    with manifest_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch = int(row["batch"])
            if batches is not None and batch not in batches:
                continue
            paths.append(_resolve_image(row["filename"], local_image_root))
            if limit is not None and len(paths) >= limit:
                break
    return paths


def _build_labeller(config: LabellerConfig) -> RemoteVlmLabeller:
    return RemoteVlmLabeller(config)


def _parse_batches(spec: str) -> Set[int]:
    out: Set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        out.add(int(chunk))
    if not out:
        raise ValueError(f"--batches got no values: {spec!r}")
    return out


def _summary_line(result: RunResult) -> str:
    return (
        f"run_dir={result.run_dir.name} "
        f"total={result.images_total} done={result.images_completed} "
        f"skipped={result.images_skipped_resume} failed={result.images_failed} "
        f"wall={result.wallclock_seconds:.1f}s"
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="ÖpenTrench labelling harness CLI.")
    parser.add_argument(
        "--config", type=Path, required=True,
        help="path to labelling profile YAML (configs/labelling/<name>.yaml)",
    )
    parser.add_argument(
        "--batches", type=str, default=None,
        help="comma-separated batch IDs to label (default: all batches)",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="cap at the first N images after batch filtering",
    )
    parser.add_argument(
        "--image-path", type=Path, default=None,
        help="ad-hoc: label exactly this image, bypassing the manifest",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help=f"output root for run dirs (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST,
        help=f"manifest.csv (default: {DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--health-check", action="store_true",
        help="hit /health, print result, exit 0 or 3",
    )
    parser.add_argument(
        "--no-progress", action="store_true",
        help="disable the tqdm progress bar",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    labeller = _build_labeller(config)

    if args.health_check:
        ok = labeller.health_check()
        print(f"{labeller.config.endpoint}/health → {'ok' if ok else 'unreachable'}")
        return 0 if ok else 3

    if not labeller.health_check():
        print(
            f"error: {labeller.config.endpoint}/health unreachable — "
            f"is the SSH tunnel up?",
            file=sys.stderr,
        )
        return 3

    if args.image_path is not None:
        if not args.image_path.is_file():
            print(f"error: --image-path not found: {args.image_path}", file=sys.stderr)
            return 1
        images = [args.image_path.resolve()]
        batches_used: List[int] = []
    else:
        batches = _parse_batches(args.batches) if args.batches else None
        try:
            images = _load_manifest(
                args.manifest, batches, args.limit, Path(config.local_image_root),
            )
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        batches_used = sorted(batches) if batches else []

    if not images:
        print("error: zero images selected — check --batches / --limit / manifest", file=sys.stderr)
        return 1

    result = run(
        config=config,
        labeller=labeller,
        image_paths=images,
        out_root=args.out,
        repo_root=REPO_ROOT,
        batches_selected=batches_used,
        progress=not args.no_progress,
    )
    print(_summary_line(result), file=sys.stderr)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
