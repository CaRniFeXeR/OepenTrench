"""Evaluate the trained trench classifier on classification/test/.

Reports accuracy, precision, recall, F1, PR-AUC, confusion matrix at the
calibrated threshold AND at threshold=0.5 for comparison. Prints per-image
mistakes so you can eyeball them.

Run from repo root:
    uv run python scripts/evaluate_trench_classifier.py
    uv run python scripts/evaluate_trench_classifier.py --threshold 0.5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from src.classifier.trench_classifier import TrenchClassifier

REPO = Path(__file__).resolve().parents[1]
CLS = REPO / "project-resources" / "custom-datasets" / "duct-and-ruler" / "classification"
TEST = CLS / "test"
ARTIFACTS = REPO / "artifacts" / "trench_classifier"

IMG_EXTS = {".jpg", ".jpeg", ".png"}


def list_test_images(root: Path) -> list[tuple[Path, str]]:
    items: list[tuple[Path, str]] = []
    for cls_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        for p in sorted(cls_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in IMG_EXTS:
                items.append((p, cls_dir.name))
    return items


def report(y_true: np.ndarray, scores: np.ndarray, threshold: float, label: str) -> None:
    preds = (scores >= threshold).astype(int)
    print(f"\n=== {label} (threshold = {threshold:.4f}) ===")
    print(f"accuracy:  {accuracy_score(y_true, preds):.3f}")
    print(f"precision: {precision_score(y_true, preds, zero_division=0):.3f}  (trench class)")
    print(f"recall:    {recall_score(y_true, preds, zero_division=0):.3f}  (trench class)")
    print(f"F1:        {f1_score(y_true, preds, zero_division=0):.3f}")
    cm = confusion_matrix(y_true, preds, labels=[0, 1])
    print(f"confusion matrix (rows=true, cols=pred, order [no-trench, trench]):\n{cm}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", default=str(ARTIFACTS))
    parser.add_argument("--threshold", type=float, default=None, help="override saved threshold")
    parser.add_argument("--device", default=None)
    parser.add_argument("--show-mistakes", action="store_true")
    args = parser.parse_args()

    if not TEST.is_dir():
        raise SystemExit("Run scripts/split_classification_dataset.py first.")

    clf = TrenchClassifier.from_artifact(args.artifact, device=args.device)
    items = list_test_images(TEST)
    if not items:
        raise SystemExit(f"No test images found in {TEST}.")
    print(f"loaded classifier: model={clf.meta.model_id} threshold={clf.meta.threshold:.4f}")
    print(f"test set: {len(items)} images")

    y_true: list[int] = []
    scores: list[float] = []
    for path, cls in items:
        _, s = clf.predict(path)
        y_true.append(1 if cls == "trench" else 0)
        scores.append(s)

    y_true_arr = np.array(y_true)
    scores_arr = np.array(scores)

    pr_auc = average_precision_score(y_true_arr, scores_arr)
    print(f"\nPR-AUC: {pr_auc:.3f}")

    # Saved threshold from training-time calibration.
    report(y_true_arr, scores_arr, clf.meta.threshold, "calibrated threshold")
    # Default 0.5 for comparison.
    report(y_true_arr, scores_arr, 0.5, "default threshold 0.5")
    if args.threshold is not None:
        report(y_true_arr, scores_arr, args.threshold, "user-specified threshold")

    if args.show_mistakes:
        preds = (scores_arr >= clf.meta.threshold).astype(int)
        wrong = [(p, t, pr, sc) for (p, t), pr, sc in zip(items, preds, scores_arr) if pr != (1 if t == "trench" else 0)]
        if wrong:
            print(f"\n{len(wrong)} mistake(s) at calibrated threshold:")
            for path, cls, pred, sc in wrong:
                pred_cls = "trench" if pred == 1 else "no-trench"
                print(f"  {cls} → {pred_cls} (score={sc:.3f})  {path.relative_to(REPO)}")

    # Append eval metrics to artifact for traceability.
    out = Path(args.artifact) / "eval.json"
    payload = {
        "test_size": len(items),
        "pr_auc": float(pr_auc),
        "threshold_calibrated": float(clf.meta.threshold),
        "scores": [{"path": str(p.relative_to(REPO)), "true": c, "score": float(s)} for (p, c), s in zip(items, scores)],
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\neval results saved: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
