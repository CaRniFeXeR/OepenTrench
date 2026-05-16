"""Prepare the trench/no-trench ImageFolder dataset.

Phase 1 (this script):
- Copies the 28 known no-trench images to classification/no-trench/.
- Copies manifest images with NON-EMPTY detection labels to classification/trench/
  (these contain at least one duct/ruler/whitepaper detection — high confidence trench).
- Emits the to-classify list (manifest images with empty labels + unlabeled Fotos).
- Splits the to-classify list into batches for parallel Opus subagent classification.

Phase 2 (Opus subagents, dispatched separately): classify the to-classify list.
Phase 3 (aggregate_classifications.py): copy predicted images to trench/ or no-trench/.

Run from repo root:
    uv run python scripts/prepare_trench_classification_dataset.py
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FOTOS = REPO / "project-resources" / "Fotos"
NO_TRENCH = REPO / "project-resources" / "no-trench"
DETECTION = REPO / "project-resources" / "custom-datasets" / "duct-and-ruler" / "detection" / "labelling"
LABELS = DETECTION / "labels"
MANIFEST = DETECTION / "manifest.csv"

OUT = REPO / "project-resources" / "custom-datasets" / "duct-and-ruler" / "classification"
OUT_TRENCH = OUT / "trench"
OUT_NO_TRENCH = OUT / "no-trench"
OUT_BATCHES = OUT / "_batches"

BATCH_SIZE = 50


def read_manifest() -> list[str]:
    names: list[str] = []
    with MANIFEST.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            names.append(row["filename"])
    return names


def label_is_nonempty(stem: str) -> bool:
    f = LABELS / f"{stem}.txt"
    return f.exists() and f.stat().st_size > 0


def main() -> None:
    OUT_TRENCH.mkdir(parents=True, exist_ok=True)
    OUT_NO_TRENCH.mkdir(parents=True, exist_ok=True)
    OUT_BATCHES.mkdir(parents=True, exist_ok=True)

    no_trench_files = {p.name for p in NO_TRENCH.iterdir() if p.is_file()}
    manifest = read_manifest()
    manifest_set = set(manifest)

    overlap = no_trench_files & manifest_set
    print(f"no-trench files: {len(no_trench_files)}")
    print(f"manifest entries: {len(manifest)}")
    print(f"overlap (no-trench ∩ manifest): {len(overlap)}")

    fotos_all = {p.name for p in FOTOS.iterdir() if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png")}
    print(f"Fotos total: {len(fotos_all)}")

    # 1) Copy known no-trench (28 images, with the 4 overlap winning the no-trench label).
    for name in sorted(no_trench_files):
        src = NO_TRENCH / name
        dst = OUT_NO_TRENCH / name
        if not dst.exists():
            shutil.copy2(src, dst)

    # 2) Copy confident-trench: manifest images with non-empty detection labels AND not in no-trench.
    confident_trench: list[str] = []
    ambiguous_manifest: list[str] = []
    for name in manifest:
        if name in no_trench_files:
            continue
        stem = Path(name).stem
        if label_is_nonempty(stem):
            confident_trench.append(name)
        else:
            ambiguous_manifest.append(name)

    for name in confident_trench:
        src = FOTOS / name
        dst = OUT_TRENCH / name
        if not dst.exists() and src.exists():
            shutil.copy2(src, dst)

    # 3) Build the to-classify list: ambiguous manifest + unlabeled Fotos.
    unlabeled = sorted(fotos_all - manifest_set - no_trench_files)
    to_classify = ambiguous_manifest + unlabeled

    print(f"bootstrapped no-trench: {len(no_trench_files)}")
    print(f"bootstrapped trench (manifest, non-empty labels): {len(confident_trench)}")
    print(f"to classify with Opus: {len(to_classify)} "
          f"(ambiguous manifest: {len(ambiguous_manifest)}, unlabeled Fotos: {len(unlabeled)})")

    # 4) Split into batch files for parallel agents.
    for old in OUT_BATCHES.glob("batch_*.txt"):
        old.unlink()

    batches = [to_classify[i:i + BATCH_SIZE] for i in range(0, len(to_classify), BATCH_SIZE)]
    for idx, batch in enumerate(batches):
        out = OUT_BATCHES / f"batch_{idx:03d}.txt"
        out.write_text("\n".join(batch) + "\n", encoding="utf-8")
    print(f"wrote {len(batches)} batch files of up to {BATCH_SIZE} images each")


if __name__ == "__main__":
    main()
