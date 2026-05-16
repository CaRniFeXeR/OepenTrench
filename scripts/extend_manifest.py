"""Append N new entries to a labelling manifest, guaranteed duplicate-free.

Excludes from the candidate pool:
  1. Filenames already present in the target manifest (no re-adds).
  2. Stems already on disk under any ``labels/<split>/`` of the dataset.
     This covers the case where some images were labelled via ``--images``
     outside the manifest, or moved between splits — the stem comparison
     is robust to that.

Stem comparison mirrors ``manual_label._safe_stem`` (non-alphanumeric chars
replaced with ``_``), since that's how the labelling tools name on-disk
files.

Default targets the mirror dataset at
``project-resources/custom-datasets/duct-and-ruler-manual/detection/``.

Usage:
    # Add 250 new entries to the mirror's manifest, batches continue at 38 if
    # 37 is the last existing batch:
    uv run python scripts/extend_manifest.py --add 250

    # Custom seed / source label / batch size / output path:
    uv run python scripts/extend_manifest.py --add 100 --seed 99 \\
        --source v4_manual --batch-size 20
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FOTOS_ROOT = PROJECT_ROOT / "project-resources" / "Fotos"
_DEFAULT_DATASET = (
    PROJECT_ROOT
    / "project-resources"
    / "custom-datasets"
    / "duct-and-ruler-manual"
    / "detection"
)


def _safe_stem(name: str) -> str:
    """Match the on-disk naming used by manual_label._safe_stem."""
    stem = Path(name).stem
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in stem)


def labelled_stems(dataset_root: Path) -> set[str]:
    """Stems present under any labels/<split>/ — these are 'already labelled'."""
    out: set[str] = set()
    labels_root = dataset_root / "labels"
    if not labels_root.exists():
        return out
    for split_dir in labels_root.iterdir():
        if not split_dir.is_dir():
            continue
        for p in split_dir.glob("*.txt"):
            out.add(p.stem)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--add", type=int, required=True, help="number of NEW entries to append")
    ap.add_argument("--manifest", type=Path, default=_DEFAULT_DATASET / "manifest.csv",
                    help="manifest CSV to append to (default: mirror's manifest.csv)")
    ap.add_argument("--dataset", type=Path, default=_DEFAULT_DATASET,
                    help="dataset root used for on-disk dedup (default: mirror)")
    ap.add_argument("--fotos", type=Path, default=FOTOS_ROOT,
                    help=f"source image dir (default: {FOTOS_ROOT.relative_to(PROJECT_ROOT)})")
    ap.add_argument("--source", default="v3_manual",
                    help="source tag for new rows (default: v3_manual)")
    ap.add_argument("--batch-size", type=int, default=20)
    ap.add_argument("--seed", type=int, default=142857)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be added but don't write the file")
    args = ap.parse_args()

    if not args.fotos.exists():
        sys.exit(f"error: source images dir not found: {args.fotos}")
    if not args.manifest.exists():
        sys.exit(f"error: manifest not found: {args.manifest}")

    with args.manifest.open() as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames
        rows = list(reader)
    if fields is None or "filename" not in fields:
        sys.exit(f"error: {args.manifest} missing 'filename' column")

    manifest_filenames = {r["filename"] for r in rows}
    manifest_stems = {_safe_stem(n) for n in manifest_filenames}
    on_disk = labelled_stems(args.dataset)

    excluded_stems = manifest_stems | on_disk
    print(f"manifest entries:              {len(manifest_filenames)}")
    print(f"manifest unique stems:         {len(manifest_stems)}")
    print(f"on-disk labelled stems:        {len(on_disk)}")
    print(f"on-disk NOT in manifest:       {len(on_disk - manifest_stems)}")
    print(f"total excluded stems:          {len(excluded_stems)}")

    pool: list[str] = []
    for p in sorted(args.fotos.iterdir()):
        if not p.is_file():
            continue
        if _safe_stem(p.name) in excluded_stems:
            continue
        pool.append(p.name)
    print(f"Fotos/ candidates after exclusion: {len(pool)}")
    if len(pool) < args.add:
        sys.exit(f"error: only {len(pool)} candidates available, asked for {args.add}")

    rng = random.Random(args.seed)
    sample = sorted(rng.sample(pool, args.add))

    last_idx = max((int(r["idx"]) for r in rows), default=-1)
    last_batch = max((int(r["batch"]) for r in rows), default=-1)
    new_rows = []
    for i, name in enumerate(sample):
        new_rows.append({
            "idx": str(last_idx + 1 + i),
            "batch": str(last_batch + 1 + (i // args.batch_size)),
            "filename": name,
            "source": args.source,
        })
    print(f"appending {len(new_rows)} rows  ·  idx {new_rows[0]['idx']}–{new_rows[-1]['idx']}  "
          f"·  batches {new_rows[0]['batch']}–{new_rows[-1]['batch']}")

    if args.dry_run:
        print("(dry run — not writing)")
        return

    tmp = args.manifest.with_suffix(".csv.tmp")
    with tmp.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
        for r in new_rows:
            w.writerow(r)
    tmp.replace(args.manifest)
    print(f"wrote {args.manifest.relative_to(PROJECT_ROOT)}  ·  {len(rows) + len(new_rows)} total rows")


if __name__ == "__main__":
    main()
