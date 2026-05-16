# Evaluation Statistics

## Face Recognition

**Sample:** 200 manually reviewed images.

### Confusion counts

| Outcome | Count | Meaning |
|--------:|------:|---------|
| **TP** | 5 | Face present — correctly detected |
| **FP** | 0 | No face — incorrectly flagged |
| **FN** | 1 | Face present — missed |
| **TN** | 194 | No face — correctly ignored |

### Summary

| Metric | Value |
|--------|------:|
| Accuracy | 99.5% (199 / 200) |
| Precision (faces) | 100% (5 / 5) |
| Recall (faces) | 83.3% (5 / 6) |

*Precision = TP / (TP + FP). Recall = TP / (TP + FN). Accuracy = (TP + TN) / N.*
