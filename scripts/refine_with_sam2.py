"""Refine an existing run's bboxes with SAM 2 segmentation masks.

For each (image, YOLO label) pair under the source dirs, feed each bbox to
SAM 2 as a box prompt, derive a tight bbox from the segmentation mask, and
write the refined label .txt to a new run dir. Empty input bboxes pass through
unchanged. If SAM 2 produces no usable mask the original bbox is kept.

Usage:
    uv run python scripts/refine_with_sam2.py \\
        --labels project-resources/.../detection/labels/test \\
        --images project-resources/.../detection/images/test \\
        --out   project-resources/.../labelling/runs/sam2-refined-test50_<ts> \\
        [--weights sam2_b.pt] [--device cpu|mps|cuda]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


def _yolo_to_pixel_xyxy(xc: float, yc: float, w: float, h: float, W: int, H: int) -> tuple[int, int, int, int]:
    x1 = max(0, int((xc - w / 2) * W))
    y1 = max(0, int((yc - h / 2) * H))
    x2 = min(W, int((xc + w / 2) * W))
    y2 = min(H, int((yc + h / 2) * H))
    if x2 <= x1: x2 = x1 + 1
    if y2 <= y1: y2 = y1 + 1
    return x1, y1, x2, y2


def _pixel_xyxy_to_yolo(x1: int, y1: int, x2: int, y2: int, W: int, H: int) -> tuple[float, float, float, float]:
    xc = (x1 + x2) / 2 / W
    yc = (y1 + y2) / 2 / H
    w = (x2 - x1) / W
    h = (y2 - y1) / H
    return xc, yc, w, h


def _mask_to_xyxy(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    """Tight bbox around non-zero mask pixels, or None if mask is empty."""
    nz = np.nonzero(mask)
    if nz[0].size == 0 or nz[1].size == 0:
        return None
    return int(nz[1].min()), int(nz[0].min()), int(nz[1].max() + 1), int(nz[0].max() + 1)


def _parse_yolo(line: str) -> tuple[int, float, float, float, float] | None:
    parts = line.strip().split()
    if len(parts) != 5:
        return None
    try:
        return int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
    except ValueError:
        return None


def refine_one(model, img_path: Path, lines: list[str]) -> tuple[list[str], list[dict]]:
    """Return (refined_yolo_lines, per_bbox_meta)."""
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        W, H = im.size
        boxes_in: list[tuple[int, int, int, int, int]] = []  # (cls, x1, y1, x2, y2)
        for ln in lines:
            parsed = _parse_yolo(ln)
            if parsed is None:
                continue
            cls, xc, yc, w, h = parsed
            x1, y1, x2, y2 = _yolo_to_pixel_xyxy(xc, yc, w, h, W, H)
            boxes_in.append((cls, x1, y1, x2, y2))
        if not boxes_in:
            return [], []
        # Run SAM 2 with all boxes as prompts in one call (batched).
        pixel_boxes = [[x1, y1, x2, y2] for _, x1, y1, x2, y2 in boxes_in]
        results = model(im, bboxes=pixel_boxes, verbose=False)
        # results is a list of length 1 (single image); .masks.data is (N, H, W) tensor.
        masks_tensor = results[0].masks.data.cpu().numpy() if results[0].masks is not None else None
        refined_lines: list[str] = []
        meta: list[dict] = []
        for i, (cls, x1, y1, x2, y2) in enumerate(boxes_in):
            entry = {
                "cls_id": cls,
                "orig_yolo": [
                    (x1 + x2) / 2 / W, (y1 + y2) / 2 / H, (x2 - x1) / W, (y2 - y1) / H,
                ],
                "orig_pixel_xyxy": [x1, y1, x2, y2],
            }
            new_xyxy = None
            if masks_tensor is not None and i < len(masks_tensor):
                new_xyxy = _mask_to_xyxy(masks_tensor[i])
            if new_xyxy is None:
                # SAM 2 returned no usable mask → keep original
                entry["status"] = "kept_original"
                xc, yc, w, h = (x1 + x2) / 2 / W, (y1 + y2) / 2 / H, (x2 - x1) / W, (y2 - y1) / H
            else:
                rx1, ry1, rx2, ry2 = new_xyxy
                # Clamp to image bounds (mask should already be, but be paranoid)
                rx1 = max(0, min(rx1, W - 1))
                ry1 = max(0, min(ry1, H - 1))
                rx2 = max(rx1 + 1, min(rx2, W))
                ry2 = max(ry1 + 1, min(ry2, H))
                xc, yc, w, h = _pixel_xyxy_to_yolo(rx1, ry1, rx2, ry2, W, H)
                entry["status"] = "refined"
                entry["refined_pixel_xyxy"] = [rx1, ry1, rx2, ry2]
                entry["refined_yolo"] = [xc, yc, w, h]
            refined_lines.append(f"{cls} {xc:.4f} {yc:.4f} {w:.4f} {h:.4f}\n")
            meta.append(entry)
        return refined_lines, meta


def main() -> None:
    ap = argparse.ArgumentParser(description="SAM 2 bbox refinement.")
    ap.add_argument("--labels", required=True, help="dir of source YOLO .txt label files")
    ap.add_argument("--images", required=True, help="dir of source images (matched by stem)")
    ap.add_argument("--out", required=True, help="output run dir (labels/, meta/, run_manifest.json)")
    ap.add_argument("--weights", default="sam2_b.pt",
                    help="ultralytics SAM 2 weights (auto-download). default: sam2_b.pt")
    ap.add_argument("--device", default=None, help="torch device: cpu | mps | cuda (default: auto)")
    args = ap.parse_args()

    from ultralytics import SAM
    import torch

    if args.device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    else:
        device = args.device

    print(f"loading {args.weights} on {device}")
    model = SAM(args.weights)
    model.to(device)

    labels_dir = Path(args.labels).resolve()
    images_dir = Path(args.images).resolve()
    out_dir = Path(args.out).resolve()
    (out_dir / "labels").mkdir(parents=True, exist_ok=True)
    (out_dir / "meta").mkdir(parents=True, exist_ok=True)

    images_by_stem = {p.stem: p for p in images_dir.iterdir() if p.is_file()}

    label_files = sorted(labels_dir.glob("*.txt"))
    n_total = len(label_files)
    print(f"refining {n_total} label files")

    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    refined_count = 0
    kept_count = 0
    empty_count = 0
    skipped = 0
    for i, label_path in enumerate(label_files):
        stem = label_path.stem
        img_path = images_by_stem.get(stem)
        if img_path is None:
            print(f"  [{i+1}/{n_total}] {stem}: no image, skipping", file=sys.stderr)
            skipped += 1
            continue
        lines = label_path.read_text().splitlines()
        non_empty = [ln for ln in lines if ln.strip()]
        if not non_empty:
            # Empty source label → write empty refined label
            (out_dir / "labels" / label_path.name).write_text("")
            (out_dir / "meta" / f"{stem}.json").write_text(
                json.dumps({"stem": stem, "n_boxes_in": 0, "boxes": []}, indent=2) + "\n"
            )
            empty_count += 1
            continue
        try:
            refined_lines, bbox_meta = refine_one(model, img_path, non_empty)
        except Exception as e:
            print(f"  [{i+1}/{n_total}] {stem}: SAM 2 failed ({e}); copying original", file=sys.stderr)
            (out_dir / "labels" / label_path.name).write_text(label_path.read_text())
            skipped += 1
            continue
        # Write refined .txt
        (out_dir / "labels" / label_path.name).write_text("".join(refined_lines))
        # Write per-image meta
        meta_obj = {
            "stem": stem,
            "image_path": str(img_path),
            "n_boxes_in": len(non_empty),
            "n_boxes_out": len(refined_lines),
            "boxes": bbox_meta,
        }
        (out_dir / "meta" / f"{stem}.json").write_text(json.dumps(meta_obj, indent=2) + "\n")
        for b in bbox_meta:
            if b["status"] == "refined":
                refined_count += 1
            else:
                kept_count += 1
        if (i + 1) % 10 == 0 or i + 1 == n_total:
            print(f"  [{i+1}/{n_total}] refined so far: {refined_count} bboxes (kept-original: {kept_count})")

    finished = datetime.now(timezone.utc)
    manifest = {
        "run_id": out_dir.name,
        "kind": "sam2-refinement",
        "source_labels": str(labels_dir),
        "source_images": str(images_dir),
        "weights": args.weights,
        "device": device,
        "started_at": started.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "finished_at": finished.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "wallclock_seconds": round(time.perf_counter() - t0, 2),
        "label_files_total": n_total,
        "label_files_skipped": skipped,
        "label_files_empty": empty_count,
        "bboxes_refined": refined_count,
        "bboxes_kept_original": kept_count,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
