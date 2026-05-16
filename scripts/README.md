# scripts/

Standalone utilities. Run each from the repo root.

## `inspect_labels.py` — visual bbox QC

Browser app for inspecting the duct + ruler labels produced by the
Claude vision subagents (or the verified train/test split, if already
finalised).

Setup once:

```bash
uv pip install -e ".[inspect]"
```

Run:

```bash
uv run python scripts/inspect_labels.py
```

What you get:

- A FiftyOne dataset built from the YOLO `.txt` labels + meta JSON.
- The FiftyOne App at <http://localhost:5151> — image grid, bbox overlay,
  filter sidebar (by class, by `has_duct` / `has_ruler` / `image_quality` /
  `*_confidence`), and tag-as-you-go.
- Auto-detects which stage of the dataset to load:
  - if `images/train` + `labels/train` exist (post-verification layout),
    prefers those;
  - otherwise loads from `labelling/labels` + `labelling/meta` and resolves
    image paths in `project-resources/Fotos/`.

Useful sample fields (visible in the App's sidebar):

| Field | Source |
|---|---|
| `predictions` | YOLO `.txt` → fo.Detections |
| `has_duct`, `has_ruler` | per-image meta JSON |
| `n_duct_bboxes`, `n_ruler_bboxes` | per-image meta JSON |
| `duct_confidence`, `ruler_confidence` | per-image meta JSON |
| `image_quality` | per-image meta JSON |
| `rationale` | per-image meta JSON (why the agent labelled what it did) |
| `notes` | per-image meta JSON (edge cases / uncertainty) |

Common review flows:

```python
# Inside the FiftyOne App, use the filter panel:
#   predictions.detections.label = "ruler"  + duct_confidence = "low"
# Then add the tag "fix" to anything that needs human cleanup.
# Export the tagged subset with:
view = dataset.match_tags("fix")
view.export(export_dir="...", dataset_type=fo.types.YOLOv5Dataset)
```

Flags:

- `--recreate` — wipe and rebuild the FiftyOne dataset (use after the
  agents add more labels).
- `--port 5152` — change the App port if 5151 is in use.
- `--no-launch` — build the dataset (e.g. for CI) without opening the App.

## `train_yolo.py` — finetune YOLO v11

Finetunes an Ultralytics YOLO v11 detector on
`project-resources/custom-datasets/duct-and-ruler/detection/data.yaml`.

Setup once:

```bash
uv pip install -e ".[train]"
```

Run:

```bash
# Smallest model, defaults (100 epochs, imgsz 640, batch 16)
uv run python scripts/train_yolo.py

# Pick a larger base, name the resulting weight, cap epochs
uv run python scripts/train_yolo.py --model yolo11s.pt --name v0_smoke --epochs 30

# Multi-GPU + extra ultralytics kwargs
uv run python scripts/train_yolo.py --model yolo11m.pt --device 0,1 \
    --extra lr0=0.001 mosaic=0.5 cos_lr=true
```

Output layout (`<base>` is the model stem, e.g. `yolo11n`):

```
project-resources/weights/duct-ruler-whitepaper-coarse/<base>/
├── <name>.pt              # the finetuned best.pt (timestamp by default)
└── _runs/<name>/          # full ultralytics run dir (metrics, plots, last.pt, ...)
```

Flags worth knowing:

- `--model` — base checkpoint. Ultralytics downloads pretrained weights on
  first use. Pass a local `.pt` to resume from a previous finetune.
- `--name` — weight filename stem. Defaults to a UTC timestamp; the script
  refuses to overwrite an existing file unless `--overwrite` is set.
- `--batch -1` — autobatch (ultralytics picks based on free VRAM).
- `--device` — `0`, `0,1`, or `cpu`. Default: ultralytics auto-detect.
- `--extra KEY=VALUE ...` — forwarded to `model.train()`. Values are
  coerced to bool / int / float / str.

The script exits non-zero if `data.yaml` is missing (`2`), ultralytics is
not installed (`2`), the target weight name already exists (`2`), or
training finishes without producing a `best.pt` (`1`).

## `build_notebooks.py`

Existing util for the EDA notebooks under `notebooks/`. Unrelated to
labelling.
