# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Hackathon mode (overrides global defaults)

This is a hackathon project (Europe Tech Hackathon 2026, AI-QC for fiber trench docs). Speed matters more than process.

- **Skip the heavy planning pipeline.** Do NOT invoke `brainstorming` / `decision-journal` / `subagent-driven-development` here unless I explicitly ask. For new work, reason it through yourself and start implementing. A short plan in chat is fine; a full spec + decision ledger is not.
- **Decide, don't negotiate.** When the spec is ambiguous, pick the obvious default, state your choice in one sentence, and proceed. Only ask when the choice would burn meaningful time to reverse (e.g., a schema change that breaks `compare_runs.py`).
- **TDD remains the default for new modules in `src/labelling/`.** It's cheap here because the modules are small and pure. Skip TDD for one-off scripts, EDA, prompts, and the VM adapter glue.
- **`docs/superpowers/` is historical.** The decision ledger and v3 spec describe what was already shipped on `feat/labelling-harness-v3`. Don't extend that flow for new features unless I ask.

## What this repo is

Two-process labelling harness + downstream QC pipeline (TBD) for fiber-trench construction photos.

- **Local laptop:** Python harness in `src/labelling/` that drives a manifest of photos through a `Labeller`, writes YOLO-format outputs to `labelling/runs/<profile>_<ts>/`. CLI at `scripts/label.py`. Compare two runs with `scripts/compare_runs.py`. Visual QC with `scripts/inspect_labels.py` (FiftyOne).
- **Remote VM (`threenicorn`, 2× RTX 5090):** FastAPI single-model detection server in `vm-server/` (deployed to `~/repos/vision/`). One adapter per process; restart to swap models. Only `grounding-dino` is implemented; `qwen-vl` / `owlv2` / `florence2` / `t-rex2` are fail-loading stubs.
- **Transport:** SSH local-forward tunnel `ssh -L 8000:localhost:8000 threenicorn`. Photos are rsynced once to `~/data` on the VM; requests carry paths, not bytes.

Downstream QC (geo-matching photos → route segments, compliance scoring, risk map) is the actual hackathon deliverable and is not yet built. See `README.md` for the product framing.

## Commands

All Python work runs through `uv`. Python 3.9–3.12.

```bash
# Setup
uv sync                                    # install pinned deps
uv pip install -e ".[inspect]"             # add FiftyOne for inspect_labels.py
uv pip install -e ".[dev]"                 # add pytest + respx + ruff

# Tests + lint (local harness)
uv run pytest tests/labelling/ -q
uv run pytest tests/labelling/test_resume.py -q       # one file
uv run pytest tests/labelling/test_resume.py::test_skips_when_both_outputs_exist
uv run ruff check src/ scripts/ tests/

# Labelling harness — needs SSH tunnel up (see below)
uv run python scripts/label.py --config configs/labelling/grounding-dino.yaml --health-check
uv run python scripts/label.py --config configs/labelling/grounding-dino.yaml --batches 0
uv run python scripts/label.py --config configs/labelling/grounding-dino.yaml --image-path <path>   # ad-hoc

# Compare two runs (greedy per-class IoU)
uv run python scripts/compare_runs.py <run_a> <run_b> --classes <data.yaml> --out diff.json

# Visual QC
uv run python scripts/inspect_labels.py --run <run-dir>     # → http://localhost:5151

# VM-side (run on threenicorn, from ~/repos/vision/)
make grounding-dino       # start server on :8000 (logs → server.log)
make stop                 # kill it
make health               # curl localhost:8000/health
```

`scripts/label.py` exit codes: `0` ok · `1` ≥1 image failed · `2` config error · `3` server unreachable.

## Architecture you can't infer from one file

### Labelling pipeline data flow

`scripts/label.py` → `load_config()` → `RemoteVlmLabeller` (httpx client) → VM `POST /detect` → adapter inference → `LabelOutput` → `runner.run()` writes per-image `<stem>.txt` (YOLO) + `<stem>.json` (meta) atomically + `run_manifest.json` (always, even on SIGINT or every-image failure).

Resume is intra-run only: a photo is skipped iff **both** `.txt` and `.json` already exist in the run dir. Cross-run cache is explicitly out of scope.

### Path translation (the non-obvious bit)

The local image path must live under `config.local_image_root`. `RemoteVlmLabeller._to_remote_path()` strips that prefix and re-roots under `config.remote_image_root` (typically `/home/user/data` on the VM). The VM's `_validate_image_path()` then rejects anything that doesn't resolve under `IMAGE_ROOT`. If a `--image-path` run fails with "not under local_image_root", edit `local_image_root` in the YAML — do not work around it in code.

### Run-dir layout (consumed by `compare_runs.py` and `inspect_labels.py`)

```
labelling/runs/<profile>_<ts>/
├── labels/<stem>.txt          # YOLO: "cls_id xc yc w h", normalized [0,1]
├── meta/<stem>.json           # per-image: bboxes, image_size, latency_ms, image_quality, rationale, model, run_id
└── run_manifest.json          # run_id, profile, config dump, git_rev/dirty, timings, p50/p95, errors[]
```

Anything that produces this shape (the v2 Claude-subagent baseline at `project-resources/custom-datasets/duct-and-ruler/detection/labelling/labels/`, a `remote-vlm` run, a future operator-mediated Claude run) is comparable via `compare_runs.py`. Preserve this layout.

### Error taxonomy (read `remote_labeller.py` before touching retries)

- `LabellerError` — permanent failure after retries exhausted; runner increments `images_failed`.
- `MalformedResponseError` (subclass) — 2xx with bad JSON shape; runner writes an **empty** `.txt` + stub `.json` so resume still works, logs to `errors[]` but does not count as a hard failure.
- Retryable HTTP: `{429, 500, 502, 503, 504}`. Exponential backoff `1s → 2s → 4s` (per `config.retries`, default 2).
- `FileNotFoundError` on image: counted as `image_error`, not retried.

### VM adapter contract

`server/adapters/base.py::Adapter` is the ABC. Each adapter owns image I/O, preprocessing, inference, and conversion to YOLO-normalized bboxes. Loaded once at startup via `MODEL` env var; **one adapter per process** — there is no hot-swap. To add a new model: implement the adapter in `vm-server/server/adapters/`, register it in `adapters/__init__.py::ADAPTERS`, add a Makefile target, rsync to the VM, restart.

### Frozen artifacts — don't overwrite

- `project-resources/custom-datasets/duct-and-ruler/detection/labelling/labels/` — v2 baseline. The whole point of a new run is to diff against this.
- `project-resources/custom-datasets/duct-and-ruler/detection/labelling/manifest.csv` — the 500-photo sample with batch IDs. Stable input.
- `data.yaml` schema — currently `[duct, ruler, whitepaper]`. Changing class IDs invalidates every existing label file.

### Test layout

`tests/labelling/` uses `respx` to mock httpx for `RemoteVlmLabeller` (no live VM needed). Tests assume the package layout `src.labelling.*` (note: `src/labelling/__init__.py` imports use `from src.labelling.…`, not a top-level `labelling` package). Don't "fix" this without also editing every test import.

## Repo-specific conventions

- **`src/labelling/` modules are pure-Python + Pydantic + httpx only.** No torch, no transformers, no fiftyone imports there — those live in `vm-server/` or behind optional-deps in `scripts/`.
- **Atomic writes** use `_atomic_write_text()` in `runner.py`: write to `.tmp`, `os.replace()`. Match this if you add new output files.
- **`extra="forbid"`** on every Pydantic model (`LabellerConfig`, `DetectRequest`). Adding a config key requires editing the model first.
- **`from __future__ import annotations`** at the top of every module in `src/labelling/`. Match it.
- **Ruff** `line-length = 100`, `target-version = "py39"`. Don't reformat unrelated files.

## When to NOT use the spec/decision ledger

The v3 harness is shipped. For:
- A new VM adapter (qwen-vl / owlv2 / florence2 / t-rex2): just implement it — the contract is in `adapters/base.py` and the Makefile target already exists.
- A new downstream QC component (geo-matching, segment scoring, map UI): new territory, just build it.
- Bug fixes / threshold tuning / prompt edits in `configs/labelling/`: just edit.

The exception: if you're about to make a change that breaks the on-disk run-dir shape, the `compare_runs.py` contract, or `data.yaml`'s class IDs — that's worth a one-line note in the PR / commit because it invalidates frozen artifacts.
