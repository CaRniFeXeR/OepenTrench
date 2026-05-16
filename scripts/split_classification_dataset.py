"""Split classification/{trench,no-trench}/ into classification/{train,test}/{trench,no-trench}/.

Stratified split: 10 trench + 10 no-trench go to test/; the rest to train/.
Moves (not copies) to keep the dataset directory canonical. Idempotent on re-run.

Picks a deterministic test set (seed=0) and writes the chosen filenames to
classification/test/_test_manifest.json so a re-run reproduces the same split.

Run from repo root:
    uv run python scripts/split_classification_dataset.py
"""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLS = REPO / "project-resources" / "custom-datasets" / "duct-and-ruler" / "classification"
TRENCH = CLS / "trench"
NO_TRENCH = CLS / "no-trench"
TRAIN = CLS / "train"
TEST = CLS / "test"
MANIFEST = TEST / "_test_manifest.json"

TEST_PER_CLASS = 10
SEED = 0
IMG_EXTS = {".jpg", ".jpeg", ".png"}


def list_images(d: Path) -> list[Path]:
    return sorted([p for p in d.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS])


def ensure_subdirs() -> None:
    for parent in (TRAIN, TEST):
        for cls in ("trench", "no-trench"):
            (parent / cls).mkdir(parents=True, exist_ok=True)


def main() -> None:
    if not TRENCH.is_dir() or not NO_TRENCH.is_dir():
        raise SystemExit("Run aggregate_trench_classifications.py first.")

    ensure_subdirs()

    # Honor an existing test manifest so the split is stable across reruns.
    if MANIFEST.exists():
        chosen = json.loads(MANIFEST.read_text(encoding="utf-8"))
        test_trench = set(chosen.get("trench", []))
        test_no_trench = set(chosen.get("no-trench", []))
    else:
        rng = random.Random(SEED)
        trench_imgs = list_images(TRENCH)
        no_trench_imgs = list_images(NO_TRENCH)
        if len(trench_imgs) < TEST_PER_CLASS or len(no_trench_imgs) < TEST_PER_CLASS:
            raise SystemExit(
                f"Not enough images for split: trench={len(trench_imgs)}, no-trench={len(no_trench_imgs)}"
            )
        test_trench = {p.name for p in rng.sample(trench_imgs, TEST_PER_CLASS)}
        test_no_trench = {p.name for p in rng.sample(no_trench_imgs, TEST_PER_CLASS)}
        MANIFEST.write_text(
            json.dumps(
                {"seed": SEED, "trench": sorted(test_trench), "no-trench": sorted(test_no_trench)},
                indent=2,
            ),
            encoding="utf-8",
        )

    def move_class(src_dir: Path, cls: str, test_names: set[str]) -> tuple[int, int]:
        train_moved = 0
        test_moved = 0
        for p in list_images(src_dir):
            target_parent = TEST if p.name in test_names else TRAIN
            dst = target_parent / cls / p.name
            if dst.exists():
                p.unlink()  # already split; remove the duplicate at the source
            else:
                shutil.move(str(p), str(dst))
            (train_moved if target_parent is TRAIN else test_moved) and None  # noqa
            if target_parent is TRAIN:
                train_moved += 1
            else:
                test_moved += 1
        return train_moved, test_moved

    t_train, t_test = move_class(TRENCH, "trench", test_trench)
    n_train, n_test = move_class(NO_TRENCH, "no-trench", test_no_trench)

    # Clean up empty source dirs so future tools don't get confused.
    for d in (TRENCH, NO_TRENCH):
        if d.exists() and not any(d.iterdir()):
            d.rmdir()

    print(f"train: trench={t_train}, no-trench={n_train}")
    print(f"test:  trench={t_test}, no-trench={n_test}")
    print(f"test manifest: {MANIFEST.relative_to(REPO)}")


if __name__ == "__main__":
    main()
