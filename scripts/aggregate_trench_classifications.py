"""Aggregate Opus subagent predictions and populate the trench/no-trench dataset.

Reads every batch_NNN.jsonl in classification/_predictions/, validates schema,
copies images into classification/{trench,no-trench}/ accordingly, and writes
a summary at classification/_predictions/SUMMARY.json.

Ambiguous predictions are NOT copied — they're listed in SUMMARY.json under
"ambiguous" so they can be reviewed manually (FiftyOne, etc).

Re-running is safe: skips destinations that already exist. Idempotent.

Run from repo root:
    uv run python scripts/aggregate_trench_classifications.py
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "project-resources" / "custom-datasets" / "duct-and-ruler" / "classification"
PREDS = OUT / "_predictions"
TRENCH = OUT / "trench"
NO_TRENCH = OUT / "no-trench"
BATCHES = OUT / "_batches"

VALID_LABELS = {"trench", "no-trench", "ambiguous"}
VALID_CONFS = {"high", "medium", "low"}


def main() -> None:
    if not PREDS.exists():
        raise SystemExit(f"No predictions dir: {PREDS}")

    counts: Counter[str] = Counter()
    conf_counts: Counter[tuple[str, str]] = Counter()
    ambiguous: list[dict] = []
    issues: list[str] = []
    seen_paths: set[str] = set()

    batch_files = sorted(PREDS.glob("batch_*.jsonl"))
    if not batch_files:
        raise SystemExit(f"No batch_*.jsonl in {PREDS}")

    expected_total = 0
    for bf in sorted(BATCHES.glob("batch_*.txt")):
        expected_total += sum(1 for _ in bf.open())

    for jf in batch_files:
        for lineno, raw in enumerate(jf.open(), start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                issues.append(f"{jf.name}:{lineno} JSON decode error: {e}")
                continue

            path = obj.get("path")
            label = obj.get("label")
            conf = obj.get("confidence", "")
            if not isinstance(path, str) or label not in VALID_LABELS or conf not in VALID_CONFS:
                issues.append(f"{jf.name}:{lineno} bad schema: {obj}")
                continue

            if path in seen_paths:
                issues.append(f"{jf.name}:{lineno} duplicate path: {path}")
                continue
            seen_paths.add(path)

            counts[label] += 1
            conf_counts[(label, conf)] += 1

            if label == "ambiguous":
                ambiguous.append(obj)
                continue

            src = REPO / path
            if not src.exists():
                issues.append(f"{jf.name}:{lineno} source missing: {src}")
                continue

            dst_dir = TRENCH if label == "trench" else NO_TRENCH
            dst = dst_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)

    # Final tallies — include bootstrapped images already in trench/ and no-trench/.
    final_trench = sum(1 for _ in TRENCH.iterdir() if _.is_file())
    final_no_trench = sum(1 for _ in NO_TRENCH.iterdir() if _.is_file())

    summary = {
        "predictions_total": sum(counts.values()),
        "expected_predictions": expected_total,
        "per_class": dict(counts),
        "per_class_confidence": {f"{k[0]}/{k[1]}": v for k, v in conf_counts.items()},
        "final_dataset": {
            "trench": final_trench,
            "no-trench": final_no_trench,
            "ratio": round(final_trench / max(final_no_trench, 1), 2),
        },
        "ambiguous_count": len(ambiguous),
        "ambiguous": ambiguous,
        "issues": issues,
    }
    (PREDS / "SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"predictions: {sum(counts.values())} / expected {expected_total}")
    for k, v in counts.most_common():
        print(f"  {k}: {v}")
    print(f"final dataset: trench={final_trench}, no-trench={final_no_trench}, "
          f"ratio={summary['final_dataset']['ratio']}:1")
    if issues:
        print(f"issues: {len(issues)} (see SUMMARY.json)")


if __name__ == "__main__":
    main()
