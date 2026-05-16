# Labelling harness — operator runbook

One-pager for running the v3 labelling harness. Companion to:

- `docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md` — design spec
- `docs/superpowers/decisions/2026-05-15-labelling-harness-v3.md` — decision ledger

## Modes at a glance

| Mode | Where the model runs | How to invoke | Output dir |
|---|---|---|---|
| `remote-vlm` | VM (`threenicorn`) | `python scripts/label.py --config configs/labelling/<profile>.yaml` | `labelling/runs/<profile>_<ts>/` |
| operator-mediated Claude | Claude Code session (Agent dispatch) | ask Claude to label (no Python entry point) | `labelling/runs/claude-opus_<ts>/` |
| `hybrid` | both — next session | (not implemented this session) | `labelling/runs/hybrid-<profile>_<ts>/` |

## First-time VM setup

```bash
# One-time corpus upload — tar pipe avoids needing rsync on the VM.
cd project-resources
tar -cf - Fotos Beispiele | ssh threenicorn 'mkdir -p ~/data && tar xf - -C ~/data'
ssh threenicorn 'find ~/data -name "._*" -delete'    # purge macOS metadata

# Deploy the vm-server scaffold (mirrored from local vm-server/).
cd ..
tar -C vm-server -cf - . | ssh threenicorn 'cd ~/repos/vision && tar xf -'

# Install uv on the VM if not present.
ssh threenicorn 'command -v uv || (curl -LsSf https://astral.sh/uv/install.sh | sh)'

# Install Python deps (torch cu128 etc; ~2 GB; one-off).
ssh threenicorn 'cd ~/repos/vision && export PATH=$HOME/.local/bin:$PATH && uv sync'
```

## Per-session workflow

```bash
# 1. Start the model on the VM.
ssh threenicorn 'cd ~/repos/vision && export PATH=$HOME/.local/bin:$PATH && make grounding-dino'
# (Switch models any time:  make stop && make qwen-vl)
# Currently functional:  grounding-dino. The qwen-vl / owlv2 / florence2 / t-rex2
# targets bind stub adapters that fail-load cleanly — useful for verifying the
# Makefile pipeline; not useful for labelling.

# 2. Open the SSH tunnel from your laptop (leave this open).
ssh -L 8000:localhost:8000 threenicorn

# 3. From a separate local shell, sanity-check the tunnel.
python scripts/label.py --config configs/labelling/grounding-dino.yaml --health-check

# 4. Round-trip one Beispiele image (AC #5).
python scripts/label.py --config configs/labelling/grounding-dino.yaml \
    --image-path project-resources/Beispiele/duct/IMG-20240808-WA0018.jpg

# 5. Label a single batch and compare against the v2 baseline (AC #6, #7).
python scripts/label.py --config configs/labelling/grounding-dino.yaml --batches 0

RUN=labelling/runs/grounding-dino_<ts>            # paste from the runner's stdout
DATASET=project-resources/custom-datasets/duct-and-ruler/detection
python scripts/compare_runs.py \
    "$DATASET/labelling/labels/" \
    "$DATASET/$RUN/labels/" \
    --classes "$DATASET/data.yaml" \
    --out "$DATASET/$RUN/diff-vs-v2.json"

# 6. Inspect either run visually.
python scripts/inspect_labels.py --run "$DATASET/$RUN/"

# 7. Stop the VM model when done.
ssh threenicorn 'cd ~/repos/vision && make stop'
```

Exit codes (per spec §7): `0` ok · `1` any image failed · `2` config error · `3` server unreachable.

## Operator-mediated Claude run

When the VM is down or you want a second opinion from Claude (Opus 4.7 via the Max subscription, no API spend), the workflow is operator-mediated — Claude dispatches Agent calls in the Claude Code session and writes outputs directly. The harness has no `claude-pure` mode; instead the on-disk artefact layout is what `compare_runs.py` reads, so a Claude-produced run sits next to a `remote-vlm` run identically.

Procedure (in the Claude Code session):

1. Ask Claude: "Label batch 0 with Claude Opus 4.7, write outputs under `labelling/runs/claude-opus_<ts>/`."
2. Claude dispatches one Agent per photo (or per batch of ~5 photos, depending on prompt size).
3. Each Agent reads the image, emits a YOLO `.txt` and a meta `.json` in the spec §6.2/§6.3 shape.
4. Claude assembles `run_manifest.json` at the end with the same fields as a `remote-vlm` run's manifest (`run_id`, `profile: "claude-opus"`, `git_rev`, etc.).
5. `compare_runs.py` works against the resulting directory without modification.

This procedure is what produced the v2 baseline at `labelling/labels/`; v3 just gives it a structured output directory.

## Hybrid mode — next session

`HybridLabeller` is a stub (`src/labelling/hybrid_labeller.py`) and not selectable via config this session.

Planned mechanics:
1. Run `remote-vlm` first → `labelling/runs/grounding-dino_<ts>/`.
2. In the Claude Code session, ask Claude to arbitrate the difficult photos: read each image + the corresponding `meta.json`, decide keep/tighten/drop per bbox, add missed detections.
3. Output to `labelling/runs/hybrid-grounding-dino_<ts>/` with the same on-disk shape.
4. `compare_runs.py` against the original `remote-vlm` run shows what Claude changed.

## VM ops cheatsheet

```bash
# Server-side status.
ssh threenicorn 'tail -20 ~/repos/vision/server.log'
ssh threenicorn 'curl -sf localhost:8000/health'
ssh threenicorn 'curl -sf localhost:8000/info'

# Server-side restart.
ssh threenicorn 'cd ~/repos/vision && make stop && make grounding-dino'

# Re-deploy after editing vm-server/ locally.
tar -C vm-server -cf - . | ssh threenicorn 'cd ~/repos/vision && tar xf -'
ssh threenicorn 'find ~/repos/vision -name "._*" -delete'
ssh threenicorn 'cd ~/repos/vision && make stop && make grounding-dino'
```

## Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `python scripts/label.py …` exit 3 | SSH tunnel down | Re-open `ssh -L 8000:localhost:8000 threenicorn` |
| `python scripts/label.py …` exit 2 | YAML typo or unknown key | Check the error message — `extra="forbid"` rejects unknown keys |
| `image_path not under local_image_root` | local_image_root in YAML doesn't match where the image lives | Edit `configs/labelling/<profile>.yaml` → set `local_image_root` to the parent dir |
| Server `images_under_root: 0` in `/health` | Corpus not uploaded | Re-run the tar-pipe upload (first-time setup §1) |
| Server 500 on `/detect` | Adapter exception | `ssh threenicorn 'tail -50 ~/repos/vision/server.log'` |
| Server 503 on `/detect` | CUDA OOM | Wait, retry; if persistent, restart the server |

## File layout (reference)

```
OepenTrench/
├── configs/labelling/grounding-dino.yaml      # remote-vlm profile
├── docs/
│   ├── labelling-harness.md                   # this file
│   └── superpowers/
│       ├── specs/2026-05-15-…-design.md       # design spec
│       └── decisions/2026-05-15-….md          # decision ledger
├── project-resources/custom-datasets/duct-and-ruler/detection/
│   ├── data.yaml                              # 3-class schema (gitignored — lives on disk)
│   ├── labelling/
│   │   ├── labels/                            # v2 baseline (frozen)
│   │   ├── meta/                              # v2 meta
│   │   ├── manifest.csv                       # 500 sampled photos
│   │   ├── batches/batch_NN.txt
│   │   └── runs/<profile>_<ts>/               # v3 outputs land here
│   │       ├── labels/                        # YOLO .txt per image
│   │       ├── meta/                          # v3 meta JSON per image
│   │       └── run_manifest.json
├── scripts/
│   ├── label.py                               # local CLI
│   ├── compare_runs.py                        # diff two run dirs
│   └── inspect_labels.py                      # FiftyOne viewer
├── src/labelling/
│   ├── base.py, config.py, remote_labeller.py, runner.py, hybrid_labeller.py, compare.py
├── tests/labelling/
│   └── test_*.py                              # pytest tests/labelling/ -q
└── vm-server/                                 # mirror of ~/repos/vision/ on threenicorn
    ├── Makefile, pyproject.toml, README.md
    └── server/main.py + server/adapters/
```
