"""Load the duct-and-ruler labels into FiftyOne and launch the app for visual inspection.

Auto-detects which stage of the dataset to load:
  - if --run <dir> is given, uses that run dir's labels/ + meta/ subdirectories;
  - else if the verified `images/train` + `labels/train` layout exists, prefers that;
  - else falls back to the in-progress `labelling/labels` + `labelling/meta`
    output of the labelling agents (resolves image paths in `Fotos/`).

Class names are read from data.yaml (the `names:` map) rather than hardcoded.

Usage:
    uv pip install -e ".[inspect]"
    uv run python scripts/inspect_labels.py
    uv run python scripts/inspect_labels.py --run labelling/runs/grounding-dino_2026-05-15T18-30-00Z
    uv run python scripts/inspect_labels.py --data-yaml /path/to/data.yaml
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import fiftyone as fo
import yaml
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = PROJECT_ROOT / "project-resources" / "custom-datasets" / "duct-and-ruler" / "detection"
FOTOS_ROOT = PROJECT_ROOT / "project-resources" / "Fotos"
_DEFAULT_DATA_YAML = DATASET_ROOT / "data.yaml"


def load_class_names(data_yaml: Path) -> list[str]:
    """Parse the `names:` map from a YOLO data.yaml and return a list indexed by class id.

    Accepts both dict form ({0: duct, 1: ruler, ...}) and list form ([duct, ruler, ...]).
    Exits with an error message if the file is missing or malformed.
    """
    if not data_yaml.exists():
        sys.exit(f"error: data.yaml not found at {data_yaml}")
    try:
        cfg = yaml.safe_load(data_yaml.read_text())
    except yaml.YAMLError as exc:
        sys.exit(f"error: cannot parse {data_yaml}: {exc}")

    names = cfg.get("names")
    if names is None:
        sys.exit(f"error: no `names:` key in {data_yaml}")

    if isinstance(names, dict):
        try:
            max_id = max(int(k) for k in names)
            return [names[i] for i in range(max_id + 1)]
        except (KeyError, ValueError) as exc:
            sys.exit(f"error: malformed `names:` dict in {data_yaml}: {exc}")
    elif isinstance(names, list):
        return [str(n) for n in names]
    else:
        sys.exit(f"error: `names:` in {data_yaml} must be a dict or list, got {type(names)}")


def yolo_line_to_detection(
    line: str, img_w: int, img_h: int, class_names: list[str]
) -> fo.Detection | None:
    """`<class> <xc> <yc> <w> <h>` (YOLO, all normalised) → fiftyone.Detection.

    FiftyOne stores bboxes as `[x_top_left, y_top_left, w, h]`, all normalised to [0, 1].
    Lines with a class id outside the loaded class list are dropped with a warning.
    """
    parts = line.strip().split()
    if len(parts) != 5:
        return None
    try:
        cls_id = int(parts[0])
        xc, yc, w, h = (float(p) for p in parts[1:])
    except ValueError:
        return None
    if cls_id < 0 or cls_id >= len(class_names):
        print(
            f"warn: class id {cls_id} outside known range [0, {len(class_names) - 1}] — skipping",
            file=sys.stderr,
        )
        return None
    x = max(0.0, xc - w / 2)
    y = max(0.0, yc - h / 2)
    w = min(w, 1.0 - x)
    h = min(h, 1.0 - y)
    return fo.Detection(label=class_names[cls_id], bounding_box=[x, y, w, h])


def discover_pairs(labels_dir: Path, images_root: Path) -> list[tuple[Path, Path]]:
    """Return (image_path, label_txt) pairs. Skips labels with no image match."""
    pairs: list[tuple[Path, Path]] = []
    by_stem: dict[str, Path] = {p.stem: p for p in images_root.iterdir() if p.is_file()}
    for label_path in labels_dir.iterdir():
        if label_path.suffix.lower() != ".txt":
            continue
        img = by_stem.get(label_path.stem)
        if img is None:
            print(f"warn: no image for label {label_path.name}", file=sys.stderr)
            continue
        pairs.append((img, label_path))
    return pairs


def load_meta(meta_dir: Path, stem: str) -> dict:
    p = meta_dir / f"{stem}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        print(f"warn: malformed meta JSON {p.name}", file=sys.stderr)
        return {}


def build_samples(
    labels_dir: Path,
    meta_dir: Path | None,
    images_root: Path,
    class_names: list[str],
) -> list[fo.Sample]:
    pairs = discover_pairs(labels_dir, images_root)
    samples: list[fo.Sample] = []
    for img_path, label_path in sorted(pairs):
        try:
            with Image.open(img_path) as im:
                img_w, img_h = im.size
        except Exception as e:
            print(f"warn: cannot open {img_path.name}: {e}", file=sys.stderr)
            continue

        detections: list[fo.Detection] = []
        for line in label_path.read_text().splitlines():
            if not line.strip():
                continue
            d = yolo_line_to_detection(line, img_w, img_h, class_names)
            if d is not None:
                detections.append(d)

        sample = fo.Sample(filepath=str(img_path))
        sample["predictions"] = fo.Detections(detections=detections)

        if meta_dir is not None:
            meta = load_meta(meta_dir, label_path.stem)
            for k in (
                "has_duct",
                "has_ruler",
                "n_duct_bboxes",
                "n_ruler_bboxes",
                "duct_confidence",
                "ruler_confidence",
                "image_quality",
                "rationale",
                "notes",
                # v3 meta fields
                "run_id",
                "model",
                "bboxes",
                "latency_ms",
            ):
                if k in meta:
                    sample[k] = meta[k]
        samples.append(sample)
    return samples


def pick_layout(
    run_dir: Path | None = None, dataset_root: Path | None = None
) -> tuple[Path, Path | None, Path]:
    """Return (labels_dir, meta_dir_or_None, images_root) based on what exists on disk.

    Resolution order:
      1. --run <dir>  → <dir>/labels/ + sibling <dir>/meta/
      2. verified `labels/train/` layout (non-empty) under ``dataset_root``
      3. in-progress `labelling/labels/` + `labelling/meta/` under ``dataset_root``
    """
    root = dataset_root if dataset_root is not None else DATASET_ROOT
    if run_dir is not None:
        labels_dir = run_dir / "labels"
        if not labels_dir.exists():
            sys.exit(f"error: {labels_dir} does not exist (expected <run_dir>/labels/)")
        meta_dir = run_dir / "meta"
        return labels_dir, (meta_dir if meta_dir.exists() else None), FOTOS_ROOT

    verified_labels_train = root / "labels" / "train"
    if verified_labels_train.exists() and any(verified_labels_train.iterdir()):
        labels_dir = verified_labels_train
        images_root = root / "images" / "train"
        if not images_root.exists():
            sys.exit(f"error: {labels_dir} exists but {images_root} does not")
        return labels_dir, None, images_root

    bootstrap_labels = root / "labelling" / "labels"
    bootstrap_meta = root / "labelling" / "meta"
    if bootstrap_labels.exists() and any(bootstrap_labels.iterdir()):
        return bootstrap_labels, (bootstrap_meta if bootstrap_meta.exists() else None), FOTOS_ROOT

    sys.exit(f"error: no labels found under {root}. Have the labelling agents run?")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect duct-and-ruler labels in FiftyOne."
    )
    parser.add_argument(
        "--name",
        default="openrtrench-duct-ruler",
        help="FiftyOne dataset name (will be overwritten if --recreate)",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="delete and rebuild even if the dataset already exists",
    )
    parser.add_argument(
        "--port", type=int, default=5151, help="FiftyOne App port (default 5151)"
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="build the dataset but do not open the App (CI / headless use)",
    )
    parser.add_argument(
        "--run",
        metavar="DIR",
        help=(
            "path to a v3 run dir (e.g. labelling/runs/grounding-dino_<ts>). "
            "Its labels/ and meta/ subdirectories are used instead of the auto-detected layout."
        ),
    )
    parser.add_argument(
        "--data-yaml",
        metavar="PATH",
        default=None,
        help=(
            f"path to data.yaml (default: {_DEFAULT_DATA_YAML}). "
            "Class names are read from the `names:` map."
        ),
    )
    args = parser.parse_args()

    data_yaml_path = Path(args.data_yaml).resolve() if args.data_yaml else _DEFAULT_DATA_YAML
    class_names = load_class_names(data_yaml_path)
    # When --data-yaml is given, use its parent dir as the dataset root so the
    # mirror dataset (duct-and-ruler-manual/) resolves images/labels correctly.
    dataset_root = data_yaml_path.parent if args.data_yaml else DATASET_ROOT

    run_dir = Path(args.run).resolve() if args.run else None

    if args.recreate and fo.dataset_exists(args.name):
        fo.delete_dataset(args.name)

    if fo.dataset_exists(args.name):
        dataset = fo.load_dataset(args.name)
        print(f"loaded existing dataset '{args.name}' with {len(dataset)} samples")
    else:
        labels_dir, meta_dir, images_root = pick_layout(run_dir, dataset_root)
        print(f"building from labels={labels_dir} meta={meta_dir} images={images_root}")
        samples = build_samples(labels_dir, meta_dir, images_root, class_names)
        if not samples:
            sys.exit("error: 0 samples built — nothing to inspect")
        dataset = fo.Dataset(args.name, persistent=True)
        dataset.add_samples(samples)
        dataset.default_classes = class_names
        dataset.save()
        print(f"built dataset '{args.name}' with {len(dataset)} samples")

    # per-class bbox stats so the user sees something before the App boots
    for cls_name in class_names:
        n = len(dataset.match(fo.ViewField("predictions.detections.label").contains(cls_name)))
        print(f"  with {cls_name} bbox(es): {n}")
    n_neither = len(dataset.match(fo.ViewField("predictions.detections").length() == 0))
    print(f"  with neither:        {n_neither}")

    if args.no_launch:
        return

    # Disable analytics chatter on first launch
    os.environ.setdefault("FIFTYONE_DO_NOT_TRACK", "true")
    session = fo.launch_app(dataset, port=args.port)
    print(
        f"\nFiftyOne App is up at http://localhost:{args.port}\n"
        "Tip: Use the filter panel to show only ruler / only duct / wrong_subject.\n"
        "     Add tags ('reviewed', 'fix', 'drop') as you go — they persist.\n"
        "     Ctrl-C in this terminal to exit.\n"
    )
    session.wait()


if __name__ == "__main__":
    main()
