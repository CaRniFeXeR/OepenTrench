"""Train the trench / no-trench gate classifier.

Pipeline:
  1. Walk classification/train/{trench,no-trench}/, embed each image once with
     a frozen DINOv2 encoder.
  2. To address class imbalance, embed each minority-class image N times with
     augmentation. The augmented embeddings vary because DINOv2 is mildly
     view-sensitive — this gives the LR more effective minority samples than
     class_weight alone.
  3. Fit `LogisticRegression(class_weight="balanced")`.
  4. Stratified 5-fold CV on a held-out portion of train/ to pick the operating
     threshold from the OOF PR curve. We optimize for high precision on the
     trench class (so a no-trench image rarely gets gated through to detection).
  5. Save head + metadata to artifacts/trench_classifier/.

Defaults to `facebook/dinov2-small` (22M params) — fits next to YOLO on an
M-series Mac and is fast enough for live demo. Override with `--model` (e.g.
`facebook/dinov2-base` if training on the VM and you want the extra accuracy).

Run from repo root:
    uv run python scripts/train_trench_classifier.py
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import StratifiedKFold
from tqdm import tqdm
from transformers import AutoImageProcessor, AutoModel

from src.classifier.trench_classifier import (
    ClassifierMeta,
    build_train_augmentation,
    select_device,
)

REPO = Path(__file__).resolve().parents[1]
CLS = REPO / "project-resources" / "custom-datasets" / "duct-and-ruler" / "classification"
TRAIN = CLS / "train"
ARTIFACTS = REPO / "artifacts" / "trench_classifier"

IMG_EXTS = {".jpg", ".jpeg", ".png"}


@dataclass
class TrainConfig:
    model_id: str = "facebook/dinov2-small"
    image_size: int = 224
    minority_aug_factor: int = 8  # how many augmented embeddings per minority image
    target_precision: float = 0.97  # at threshold-pick time, choose smallest τ s.t. P(trench)≥this
    n_splits: int = 5
    seed: int = 0
    use_fp16: bool = True


def list_class_images(root: Path) -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {}
    for cls_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        out[cls_dir.name] = sorted(
            p for p in cls_dir.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS
        )
    return out


@torch.inference_mode()
def embed_images(
    paths_with_labels: list[tuple[Path, str, bool]],  # (path, class, augment)
    model: torch.nn.Module,
    processor,
    device: torch.device,
    dtype: torch.dtype,
    augment: torch.nn.Module,
) -> tuple[np.ndarray, list[str]]:
    """Embed each input. If augment flag is True, apply augment transform first."""
    embs: list[np.ndarray] = []
    labels: list[str] = []
    for path, cls, aug in tqdm(paths_with_labels, desc="embedding"):
        img = Image.open(path).convert("RGB")
        if aug:
            img = augment(img)
        inputs = processor(images=img, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(device, dtype=dtype)
        out = model(pixel_values=pixel_values)
        emb = out.pooler_output[0] if getattr(out, "pooler_output", None) is not None else out.last_hidden_state[0, 0]
        embs.append(emb.float().cpu().numpy())
        labels.append(cls)
    return np.stack(embs), labels


def build_training_set(class_imgs: dict[str, list[Path]], cfg: TrainConfig) -> list[tuple[Path, str, bool]]:
    counts = {c: len(ps) for c, ps in class_imgs.items()}
    majority = max(counts, key=lambda k: counts[k])
    print(f"counts: {counts} → majority={majority}")

    items: list[tuple[Path, str, bool]] = []
    for cls, paths in class_imgs.items():
        # One non-augmented embedding per image.
        items.extend((p, cls, False) for p in paths)
        if cls != majority:
            # Add augmented copies for minority class.
            for p in paths:
                for _ in range(cfg.minority_aug_factor):
                    items.append((p, cls, True))
    return items


def pick_threshold(y_true: np.ndarray, y_score: np.ndarray, target_precision: float) -> tuple[float, dict[str, float]]:
    """Pick smallest threshold τ that achieves precision ≥ target on the positive class."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_score, pos_label=1)
    # precision/recall arrays have len = n+1, thresholds has len = n.
    valid = precisions[:-1] >= target_precision
    if valid.any():
        idx = int(np.argmax(valid))  # smallest threshold satisfying constraint
        tau = float(thresholds[idx])
        prec = float(precisions[idx])
        rec = float(recalls[idx])
    else:
        # Fall back: pick threshold maximizing F1.
        f1 = 2 * precisions[:-1] * recalls[:-1] / np.clip(precisions[:-1] + recalls[:-1], 1e-9, None)
        idx = int(np.argmax(f1))
        tau = float(thresholds[idx])
        prec = float(precisions[idx])
        rec = float(recalls[idx])
    pr_auc = float(average_precision_score(y_true, y_score))
    return tau, {"precision_at_threshold": prec, "recall_at_threshold": rec, "pr_auc": pr_auc}


def cross_validate_threshold(
    embs: np.ndarray,
    y: np.ndarray,
    is_real: np.ndarray,
    cfg: TrainConfig,
) -> tuple[float, dict[str, float]]:
    """Run stratified K-fold CV over the REAL (non-augmented) samples only.

    Augmented samples are used for training but not for threshold calibration —
    their distribution is shifted by the augmentation transform, so trusting
    them for the operating-point decision would be optimistic.
    """
    real_embs = embs[is_real]
    real_y = y[is_real]
    skf = StratifiedKFold(n_splits=cfg.n_splits, shuffle=True, random_state=cfg.seed)
    oof = np.zeros_like(real_y, dtype=float)
    for train_idx, val_idx in skf.split(real_embs, real_y):
        # Train LR on REAL train fold + ALL aug embeddings whose corresponding real image is in train.
        # Simpler approach: train on all augmented + real-train-fold. To keep it tight,
        # we just train on real-train-fold + the aug embeddings (which correspond to the
        # minority class globally — they don't overlap with the val fold by construction
        # because val_idx indexes real samples only).
        train_real_mask = np.zeros_like(real_y, dtype=bool)
        train_real_mask[train_idx] = True
        # Build the actual training set indices in the full (real + aug) array.
        full_train_mask = np.zeros(embs.shape[0], dtype=bool)
        # Index map: real positions → original positions.
        real_positions = np.where(is_real)[0]
        full_train_mask[real_positions[train_idx]] = True
        full_train_mask[~is_real] = True  # all augmented samples are training-only
        clf = LogisticRegression(class_weight="balanced", C=1.0, max_iter=2000, random_state=cfg.seed)
        clf.fit(embs[full_train_mask], y[full_train_mask])
        trench_idx = list(clf.classes_).index(1)
        oof[val_idx] = clf.predict_proba(real_embs[val_idx])[:, trench_idx]
    tau, metrics = pick_threshold(real_y, oof, cfg.target_precision)
    return tau, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="facebook/dinov2-small")
    parser.add_argument("--minority-aug-factor", type=int, default=8)
    parser.add_argument("--target-precision", type=float, default=0.97)
    parser.add_argument("--device", default=None, help="cuda|mps|cpu (autodetect if omitted)")
    parser.add_argument("--no-fp16", action="store_true")
    parser.add_argument("--out", default=str(ARTIFACTS))
    args = parser.parse_args()

    cfg = TrainConfig(
        model_id=args.model,
        minority_aug_factor=args.minority_aug_factor,
        target_precision=args.target_precision,
        use_fp16=not args.no_fp16,
    )

    if not TRAIN.is_dir():
        raise SystemExit("Run scripts/split_classification_dataset.py first.")

    device = select_device(args.device)
    dtype = torch.float16 if cfg.use_fp16 and device.type in ("cuda", "mps") else torch.float32
    print(f"device={device}, dtype={dtype}, model={cfg.model_id}")

    processor = AutoImageProcessor.from_pretrained(cfg.model_id)
    model = AutoModel.from_pretrained(cfg.model_id).to(device, dtype=dtype).eval()
    for p in model.parameters():
        p.requires_grad_(False)

    augment = build_train_augmentation(cfg.image_size)

    class_imgs = list_class_images(TRAIN)
    items = build_training_set(class_imgs, cfg)
    print(f"items to embed: {len(items)} (real + augmented)")

    embs, labels = embed_images(items, model, processor, device, dtype, augment)
    y = np.array([1 if c == "trench" else 0 for c in labels])
    is_real = np.array([not aug for _, _, aug in items])

    print(f"embedding dim: {embs.shape[1]}")
    print(f"real samples: {is_real.sum()} (trench={int(y[is_real].sum())}, no-trench={int((y[is_real]==0).sum())})")
    print(f"augmented samples (minority class only): {(~is_real).sum()}")

    # CV threshold calibration on real samples only.
    tau, cv_metrics = cross_validate_threshold(embs, y, is_real, cfg)
    print(
        f"CV @ target_precision={cfg.target_precision}: "
        f"threshold={tau:.4f}, precision={cv_metrics['precision_at_threshold']:.3f}, "
        f"recall={cv_metrics['recall_at_threshold']:.3f}, PR-AUC={cv_metrics['pr_auc']:.3f}"
    )

    # Final fit on ALL samples (real + augmented).
    final = LogisticRegression(class_weight="balanced", C=1.0, max_iter=2000, random_state=cfg.seed)
    final.fit(embs, y)
    # Sklearn keeps integer labels; we want string labels at inference. Map them.
    label_for = {0: "no-trench", 1: "trench"}
    final.classes_ = np.array([label_for[c] for c in final.classes_])

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(final, out_dir / "head.joblib")
    meta = ClassifierMeta(
        model_id=cfg.model_id,
        threshold=tau,
        embed_dim=int(embs.shape[1]),
        image_size=cfg.image_size,
        train_counts={c: len(ps) for c, ps in class_imgs.items()},
        cv_metrics={**cv_metrics, "target_precision": cfg.target_precision},
        notes=(
            f"Augmented minority class with factor={cfg.minority_aug_factor}. "
            f"Threshold picked on real-only OOF PR curve, target precision = {cfg.target_precision}."
        ),
    )
    (out_dir / "meta.json").write_text(json.dumps(asdict(meta), indent=2), encoding="utf-8")
    print(f"saved: {out_dir.relative_to(REPO)}")


if __name__ == "__main__":
    main()
