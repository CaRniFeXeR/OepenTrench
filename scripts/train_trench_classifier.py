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


class _EmbedDataset(torch.utils.data.Dataset):
    """Loads + optionally augments + processor-preprocesses on worker processes."""

    def __init__(self, items, processor, augment):
        self.items = items
        self.processor = processor
        self.augment = augment

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx):
        path, cls, aug = self.items[idx]
        img = Image.open(path).convert("RGB")
        if aug:
            img = self.augment(img)
        pixel_values = self.processor(images=img, return_tensors="pt")["pixel_values"][0]
        return pixel_values, cls


def _collate(batch):
    px = torch.stack([b[0] for b in batch])
    classes = [b[1] for b in batch]
    return px, classes


@torch.inference_mode()
def embed_images(
    paths_with_labels: list[tuple[Path, str, bool]],
    model: torch.nn.Module,
    processor,
    device: torch.device,
    dtype: torch.dtype,
    augment: torch.nn.Module,
    batch_size: int = 64,
    num_workers: int = 4,
) -> tuple[np.ndarray, list[str]]:
    """Embed in GPU batches with parallel CPU-side image loading."""
    ds = _EmbedDataset(paths_with_labels, processor, augment)
    loader = torch.utils.data.DataLoader(
        ds,
        batch_size=batch_size,
        num_workers=num_workers,
        shuffle=False,
        collate_fn=_collate,
        pin_memory=device.type == "cuda",
    )
    embs: list[np.ndarray] = []
    labels: list[str] = []
    pbar = tqdm(total=len(paths_with_labels), desc="embedding")
    for pixel_values, classes in loader:
        pixel_values = pixel_values.to(device, dtype=dtype, non_blocking=True)
        out = model(pixel_values=pixel_values)
        batch_embs = out.pooler_output if getattr(out, "pooler_output", None) is not None else out.last_hidden_state[:, 0]
        embs.append(batch_embs.float().cpu().numpy())
        labels.extend(classes)
        pbar.update(len(classes))
    pbar.close()
    return np.concatenate(embs, axis=0), labels


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


DEFAULT_LR_PARAMS: dict = {"C": 1.0, "penalty": "l2", "solver": "lbfgs", "class_weight": "balanced"}

# Grid for HP search. Each entry is a complete LR config (so penalty/solver stay consistent).
LR_GRID: list[dict] = [
    *({"C": c, "penalty": "l2", "solver": "lbfgs", "class_weight": "balanced"} for c in [0.01, 0.1, 1.0, 10.0, 100.0]),
    *({"C": c, "penalty": "l1", "solver": "liblinear", "class_weight": "balanced"} for c in [0.01, 0.1, 1.0, 10.0, 100.0]),
    # Control: no class weighting, to see if the augmented oversampling alone suffices.
    {"C": 1.0, "penalty": "l2", "solver": "lbfgs", "class_weight": None},
    {"C": 10.0, "penalty": "l2", "solver": "lbfgs", "class_weight": None},
]


def cv_oof_predictions(
    embs: np.ndarray,
    y: np.ndarray,
    is_real: np.ndarray,
    lr_params: dict,
    cfg: TrainConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Stratified K-fold over REAL samples only.

    Augmented samples land in every training fold but never appear in a val fold —
    their distribution is shifted by the augmentation transform, so trusting them
    for the operating-point decision would be optimistic.
    """
    real_embs = embs[is_real]
    real_y = y[is_real]
    real_positions = np.where(is_real)[0]
    skf = StratifiedKFold(n_splits=cfg.n_splits, shuffle=True, random_state=cfg.seed)
    oof = np.zeros_like(real_y, dtype=float)
    for train_idx, val_idx in skf.split(real_embs, real_y):
        full_train_mask = np.zeros(embs.shape[0], dtype=bool)
        full_train_mask[real_positions[train_idx]] = True
        full_train_mask[~is_real] = True
        clf = LogisticRegression(**lr_params, max_iter=2000, random_state=cfg.seed)
        clf.fit(embs[full_train_mask], y[full_train_mask])
        trench_idx = list(clf.classes_).index(1)
        oof[val_idx] = clf.predict_proba(real_embs[val_idx])[:, trench_idx]
    return real_y, oof


def cross_validate_threshold(
    embs: np.ndarray,
    y: np.ndarray,
    is_real: np.ndarray,
    cfg: TrainConfig,
    lr_params: dict = None,
) -> tuple[float, dict[str, float]]:
    real_y, oof = cv_oof_predictions(embs, y, is_real, lr_params or DEFAULT_LR_PARAMS, cfg)
    tau, metrics = pick_threshold(real_y, oof, cfg.target_precision)
    return tau, metrics


def hp_search(
    embs: np.ndarray,
    y: np.ndarray,
    is_real: np.ndarray,
    cfg: TrainConfig,
) -> tuple[dict, float, dict[str, float]]:
    """Sweep LR hyperparameters, pick best by CV PR-AUC. Returns (best_params, tau, metrics)."""
    print(f"\nHP search over {len(LR_GRID)} LR configs (K-fold over real samples only):")
    print(f"{'C':<8}{'penalty':<10}{'cw':<12}{'PR-AUC':<10}{'P@τ':<8}{'R@τ':<8}{'τ':<8}")
    rows: list[tuple[float, dict, float, dict]] = []
    for params in LR_GRID:
        real_y, oof = cv_oof_predictions(embs, y, is_real, params, cfg)
        pr_auc = float(average_precision_score(real_y, oof))
        tau, metrics = pick_threshold(real_y, oof, cfg.target_precision)
        rows.append((pr_auc, params, tau, metrics))
        cw = str(params.get("class_weight") or "None")
        print(
            f"{params['C']:<8}{params['penalty']:<10}{cw:<12}"
            f"{pr_auc:<10.4f}{metrics['precision_at_threshold']:<8.3f}"
            f"{metrics['recall_at_threshold']:<8.3f}{tau:<8.4f}"
        )
    rows.sort(reverse=True, key=lambda r: r[0])
    best_pr_auc, best_params, best_tau, best_metrics = rows[0]
    print(f"\nBest: PR-AUC={best_pr_auc:.4f}, params={best_params}")
    best_metrics["pr_auc"] = best_pr_auc
    return best_params, best_tau, best_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="facebook/dinov2-small")
    parser.add_argument("--minority-aug-factor", type=int, default=8)
    parser.add_argument("--target-precision", type=float, default=0.97)
    parser.add_argument("--device", default=None, help="cuda|mps|cpu (autodetect if omitted)")
    parser.add_argument("--no-fp16", action="store_true")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--hp-tune", action="store_true", help="sweep LR hyperparameters by CV PR-AUC")
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

    embs, labels = embed_images(
        items, model, processor, device, dtype, augment,
        batch_size=args.batch_size, num_workers=args.num_workers,
    )
    y = np.array([1 if c == "trench" else 0 for c in labels])
    is_real = np.array([not aug for _, _, aug in items])

    print(f"embedding dim: {embs.shape[1]}")
    print(f"real samples: {is_real.sum()} (trench={int(y[is_real].sum())}, no-trench={int((y[is_real]==0).sum())})")
    print(f"augmented samples (minority class only): {(~is_real).sum()}")

    # CV threshold calibration on real samples only — optionally with HP search.
    if args.hp_tune:
        best_params, tau, cv_metrics = hp_search(embs, y, is_real, cfg)
    else:
        best_params = DEFAULT_LR_PARAMS
        tau, cv_metrics = cross_validate_threshold(embs, y, is_real, cfg, lr_params=best_params)
        print(
            f"CV @ target_precision={cfg.target_precision}: "
            f"threshold={tau:.4f}, precision={cv_metrics['precision_at_threshold']:.3f}, "
            f"recall={cv_metrics['recall_at_threshold']:.3f}, PR-AUC={cv_metrics['pr_auc']:.3f}"
        )

    # Final fit on ALL samples (real + augmented) with the chosen LR params.
    final = LogisticRegression(**best_params, max_iter=2000, random_state=cfg.seed)
    final.fit(embs, y)
    # Sklearn keeps integer labels; we want string labels at inference. Map them.
    label_for = {0: "no-trench", 1: "trench"}
    final.classes_ = np.array([label_for[c] for c in final.classes_])

    out_dir = Path(args.out).resolve()
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
            f"Threshold picked on real-only OOF PR curve, target precision = {cfg.target_precision}. "
            f"LR params: {best_params}."
        ),
    )
    (out_dir / "meta.json").write_text(json.dumps(asdict(meta), indent=2), encoding="utf-8")
    print(f"saved: {out_dir.relative_to(REPO)}")


if __name__ == "__main__":
    main()
