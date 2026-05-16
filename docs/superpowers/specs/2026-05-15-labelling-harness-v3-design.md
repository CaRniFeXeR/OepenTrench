# Labelling Harness v3 — Design Spec

**Status:** Draft
**Date:** 2026-05-15
**Next stage:** `decision-journal`

## 1. Goal & Context

Replace the ad-hoc Claude-subagent batch-dispatch labelling workflow used for v2 of the duct-and-ruler detection dataset with a configurable two-process system: a Python harness on the operator's laptop, and a single-model FastAPI detection server on the user's VM (`threenicorn`, 2× RTX 5090). The harness produces YOLO-format labels for four classes — `duct` (0), `ruler` (1), `whitepaper` (2), `sitetag` (3) — across the 500 sampled photos and supports head-to-head comparison of model outputs so the user can pick the labeller that best replaces the current loose-bbox VLM pass.

The hackathon end-state is: one validated remote-vlm round-trip on Grounding DINO Base, a 20-photo `batch_00` labelled with it, and a per-photo diff against the v2 baseline shown to the user before any larger run.

## 2. Non-Goals

- Training YOLOv11 / RF-DETR / any student detector (R14 work, later phase).
- Replacing the v2 labels in `labelling/labels/` (frozen baseline).
- Running all 500 photos through any new model in this session — wait for user sign-off on the `batch_00` diff first.
- Building OWLv2 / Florence-2 / T-Rex2 / Qwen2.5-VL VM adapters this session (only Grounding DINO Base + an `Adapter` base class).
- Building `HybridLabeller` this session (skeleton only; concrete implementation deferred).
- Building `ClaudeApiLabeller` ever — Claude labelling is operator-mediated via Agent dispatch in the Claude Code session, not an SDK call.
- No `anthropic` Python SDK dependency. No Anthropic API spend.
- Base64 image transport — corpus is rsync'd to the VM once; requests carry paths only.
- Cross-run content-addressable cache. Intra-run resume only (skip if `<stem>.txt` AND `<stem>.json` both exist).
- Multi-tenancy, auth, secret management.
- Parallel / concurrent HTTP workers from the local harness. Serial only.
- Hot-swap of models on the VM. One model per server lifetime; `make stop && make <other>` to swap.
- Persistent metrics, traces, structured-log emitters. stdout + per-run JSON manifest is the whole observability surface.
- Per-bbox rationale strings. One global rationale per image.
- Updating Ultralytics training configs. Training is out of scope; the 4-class `data.yaml` will fail training on the 2-class v2 labels but no training runs this session.
- A web UI for labelling.

## 3. Architecture Overview

Two processes connected by an SSH local-forward tunnel.

```
                  LOCAL                                        VM (threenicorn)
   ┌──────────────────────────────────┐         ┌──────────────────────────────────┐
   │ scripts/label.py --config X.yaml │   SSH   │ FastAPI :8000                    │
   │   │                              │ tunnel  │   POST /detect                   │
   │   └─ RemoteVlmLabeller ──────────┼─────────┼─►  GET  /health                  │
   │       (httpx → :8000)            │  :8000  │   GET  /info                     │
   │                                  │         │     └─► adapter (one of):       │
   │ outputs:                         │         │       grounding_dino.py         │
   │   labelling/runs/<profile>_<ts>/ │         │       (other adapters: stubs)   │
   │     labels/  meta/               │         │                                  │
   │     run_manifest.json            │         │ image_root = /home/<user>/data  │
   │                                  │         │   ├── Fotos/                    │
   │ tests/labelling/                 │         │   └── Beispiele/                │
   └──────────────────────────────────┘         └──────────────────────────────────┘
```

Claude labelling (when the VM is unavailable or as a hybrid arbiter) is **operator-mediated**: the user asks Claude in the Claude Code session, Claude dispatches Agent calls, and Claude writes outputs into `labelling/runs/claude-opus_<ts>/` using the same on-disk layout. `compare_runs.py` reads run directories by directory shape and is indifferent to who produced them.

## 4. Components & Responsibilities

### 4.1 Local — `src/oepentrench/labelling/`

| Component | File | Responsibility | Depends on | Consumed by |
|---|---|---|---|---|
| Dataclasses | `base.py` | `Detection`, `LabelOutput` dataclasses + `Labeller` ABC | stdlib | all labellers, runner |
| Config | `config.py` | YAML → validated `LabellerConfig` (pydantic) | pyyaml, pydantic | runner, label.py |
| Remote labeller | `remote_labeller.py` | `RemoteVlmLabeller` — httpx client to `:8000/detect` | httpx, base | runner |
| Hybrid labeller | `hybrid_labeller.py` | `HybridLabeller` skeleton (importable class, raises NotImplementedError on `.label()`). Not selectable via YAML config this session — `LabellerConfig.mode` is `Literal["remote-vlm"]` only. The skeleton exists so the ABC's contract can be tested and the next session can fill it in without restructuring imports. | base | runner |
| Runner | `runner.py` | iterate a `Manifest`, call a `Labeller`, write per-image outputs atomically, resume on existing files, emit `run_manifest.json` | base, config | label.py |
| Compare | `compare.py` | diff two run dirs; emit per-photo agreement JSON; optional FiftyOne side-by-side | fiftyone (optional) | scripts/compare_runs.py |

### 4.2 Local — `scripts/`

| File | Responsibility |
|---|---|
| `label.py` | CLI: `--config`, `--batches`, `--limit`, `--out`, `--health-check`. Loads config + manifest, instantiates Labeller, runs Runner. |
| `compare_runs.py` | CLI wrapper around `compare.compare_runs(a, b, classes)`. |
| `inspect_labels.py` | **Extended in place**: reads class names from `data.yaml`, accepts `--run <dir>` to point at any `labelling/runs/<profile>_<ts>/`, still works on v2 layout. |

### 4.3 Local — `configs/labelling/`

| File | Purpose |
|---|---|
| `grounding-dino.yaml` | First VM target. Mode `remote-vlm`, model `grounding-dino-base`. |

Other config files (`qwen-vl.yaml`, etc.) are authored only when their adapter is implemented.

### 4.4 VM — `~/repos/vision/server/`

| Component | File | Responsibility |
|---|---|---|
| App | `main.py` | FastAPI app: `POST /detect`, `GET /health`, `GET /info`. Loads adapter named by `MODEL` env var on startup. |
| Schema | `schema.py` | Pydantic `DetectRequest`, `DetectResponse`, `Detection`, `HealthResponse`, `InfoResponse`. |
| Adapter base | `adapters/base.py` | `Adapter` ABC: `load_model() -> None`, `detect(req: DetectRequest) -> DetectResponse`. |
| Grounding DINO | `adapters/grounding_dino.py` | `IDEA-Research/grounding-dino-base` via HF Transformers. |
| Stubs | `adapters/{qwen_vl,owlv2,florence2,trex2}.py` | Skeleton files with `Adapter` subclass + `NotImplementedError`; importable so the registry compiles. |

### 4.5 VM — `~/repos/vision/`

| File | Responsibility |
|---|---|
| `Makefile` | Targets: `grounding-dino`, `qwen-vl`, `owlv2`, `florence2`, `t-rex2`, `health`, `stop`. Only `grounding-dino` works this session; others bound to stubs. |
| `pyproject.toml` | uv-managed; deps: torch (cu128), transformers≥4.45, accelerate, fastapi, uvicorn, pydantic≥2.6, pillow. |
| `README.md` | One-page operator runbook: SSH, tunnel, make targets, /health, /info. |

## 5. Public Interfaces

### 5.1 HTTP — VM `POST /detect`

**Request body (Pydantic `DetectRequest`):**
```python
class DetectRequest(BaseModel):
    image_path: str                              # absolute path on the VM filesystem
    prompts: dict[str, str]                      # class name → natural-language prompt
    per_class_threshold: dict[str, float]        # class name → confidence floor [0,1]
    iou_nms: float = 0.5
    max_detections_per_class: int = 5
```

**Preconditions:** `image_path` exists and is a readable JPEG/PNG; `prompts` keys are a subset of the adapter's declared classes; thresholds in `[0,1]`.

**Side effects:** none (idempotent for the same inputs and loaded weights).

**Response body (Pydantic `DetectResponse`):**
```python
class Detection(BaseModel):
    cls: str                                     # class name
    bbox: tuple[float, float, float, float]      # (xc, yc, w, h), all in [0,1], YOLO
    confidence: float                            # [0,1]

class DetectResponse(BaseModel):
    detections: list[Detection]
    model: str                                   # e.g. "grounding-dino-base"
    image_size: tuple[int, int]                  # (width_px, height_px)
    latency_ms: int
```

**Errors:**
- 400 — invalid path (does not exist / not under permitted root).
- 422 — schema validation failure (Pydantic).
- 503 — model OOM at runtime, body `{"error":"oom"}`.
- 500 — anything else, body `{"error":"...","detail":"..."}`.

### 5.2 HTTP — VM `GET /health`
```python
class HealthResponse(BaseModel):
    status: Literal["ok"]
    model: str                                   # the loaded adapter's model id
    uptime_s: int
    image_root: str                              # absolute path
    images_under_root: int                       # count of *.jpg / *.jpeg under image_root
```
The `images_under_root` lets the harness sanity-check that the corpus was rsync'd before it starts a run.

### 5.3 HTTP — VM `GET /info`
```python
class InfoResponse(BaseModel):
    model: str
    classes: list[str]                           # adapter's declared class names
    default_prompts: dict[str, str]
    default_thresholds: dict[str, float]
```

### 5.4 VM-side `Adapter` ABC
```python
# server/adapters/base.py
class Adapter(ABC):
    @abstractmethod
    def load_model(self) -> None: ...

    @abstractmethod
    def detect(self, req: DetectRequest) -> DetectResponse: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @property
    @abstractmethod
    def classes(self) -> list[str]: ...
```
Loading happens once at process startup. `detect` is the per-request entry point; it owns image I/O (`PIL.Image.open(req.image_path)`), preprocessing, inference, and conversion to YOLO-normalised bboxes.

### 5.5 Local `Labeller` ABC
```python
# src/oepentrench/labelling/base.py
class Labeller(ABC):
    config: LabellerConfig

    @property
    @abstractmethod
    def name(self) -> str: ...                   # e.g. "grounding-dino-base"

    @abstractmethod
    def label(self, image_path: Path) -> LabelOutput:
        """Pre: image_path exists, readable. Post: LabelOutput with detections
        normalised to YOLO bbox in [0,1]. Raises LabellerError on permanent
        failure; transient failures are retried internally per config.retries."""

    def health_check(self) -> bool: ...          # default: True

@dataclass
class Detection:
    cls: str
    bbox: tuple[float, float, float, float]      # (xc, yc, w, h), all in [0,1]
    confidence: float

@dataclass
class LabelOutput:
    filename: str
    image_size: tuple[int, int]
    detections: list[Detection]
    rationale: str
    image_quality: str                           # "ok" | "poor"
    latency_ms: int
```

### 5.6 CLI

```
python scripts/label.py
    --config configs/labelling/<profile>.yaml
    [--batches 0,1,2]            # default: all batches in manifest.csv
    [--limit 20]                 # default: no limit
    [--image-path <abs-path>]    # ad-hoc single-image run; bypasses manifest;
                                 # output goes to labelling/runs/<profile>_<ts>/
                                 # using the photo's stem as the filename
    [--out labelling/runs/]      # default
    [--health-check]             # just hit /health and exit 0/non-0

python scripts/compare_runs.py
    <run_a_dir>                  # e.g. labelling/labels/ (v2 baseline)
    <run_b_dir>                  # e.g. labelling/runs/grounding-dino_<ts>/labels/
    --classes data.yaml
    [--out diff.json]
    [--fiftyone]                 # open a side-by-side FiftyOne dataset

python scripts/inspect_labels.py
    [--run labelling/runs/<dir>] # NEW; defaults to v2 layout auto-detect
    [--data-yaml <path>]         # NEW; default ./project-resources/.../data.yaml
```

## 6. Data Contracts

### 6.1 `data.yaml` (Ultralytics format, updated)

```yaml
path: /Users/rezafuru/repos/personal/OepenTrench/project-resources/custom-datasets/duct-and-ruler/detection
train: images/train
val: images/test
test: images/test

names:
  0: duct
  1: ruler
  2: whitepaper
  3: sitetag
```

### 6.2 Per-image YOLO `<stem>.txt`

5-tuple per line, all values in `[0,1]`:
```
<class_id> <xc> <yc> <w> <h>
```
Empty file = no detections (the "neither" 4-bin equivalent for v3). Per-bbox confidence is NOT in the `.txt` (would break Ultralytics 5-tuple expectations); it lives in the meta JSON.

### 6.3 Per-image `<stem>.json` (v3 meta)

```json
{
  "filename": "1_IMG-20240809-WA0025.jpg",
  "image_size": [1200, 1600],
  "run_id": "grounding-dino_2026-05-15T18-30-00Z",
  "model": "grounding-dino-base",
  "bboxes": [
    {"cls": "ruler", "bbox": [0.475, 0.40, 0.15, 0.60], "confidence": 0.62}
  ],
  "image_quality": "ok",
  "rationale": "Open pit with vertical red-white segmented levelling rod.",
  "latency_ms": 87
}
```

Per-class rollup (was in v2 meta) is **derivable from `bboxes`** — compare.py and the inspector compute it on the fly.

### 6.4 `run_manifest.json` (per-run)

```json
{
  "run_id": "grounding-dino_2026-05-15T18-30-00Z",
  "profile": "grounding-dino",
  "config": { /* full inlined LabellerConfig */ },
  "git_rev": "abcdef0",
  "git_dirty": false,
  "started_at": "2026-05-15T18:30:00Z",
  "finished_at": "2026-05-15T18:34:05Z",
  "wallclock_seconds": 245.3,
  "images_total": 500,
  "images_completed": 500,
  "images_skipped_resume": 0,
  "images_failed": 0,
  "batches_selected": [0, 1, 2],
  "latency_p50_ms": 78,
  "latency_p95_ms": 210,
  "errors": []
}
```

### 6.5 `LabellerConfig` (YAML schema)

```python
class LabellerConfig(BaseModel):
    name: str                                    # "grounding-dino"
    mode: Literal["remote-vlm"]                  # "hybrid" added later
    endpoint: str                                # e.g. "http://localhost:8000"
    model: str                                   # e.g. "grounding-dino-base"
    remote_image_root: str                       # e.g. "/home/<user>/data"
    local_image_root: str                        # for filename resolution at the local side
    classes: list[str]                           # ["duct","ruler","whitepaper","sitetag"]
    prompts: dict[str, str]                      # per-class prompts
    per_class_threshold: dict[str, float]
    iou_nms: float = 0.5
    max_detections_per_class: int = 5
    timeout_seconds: float = 60.0
    retries: int = 2
```

### 6.6 `compare.py` output (`diff.json`)

```json
{
  "run_a": "labelling/labels/",
  "run_b": "labelling/runs/grounding-dino_<ts>/labels/",
  "classes": ["duct", "ruler", "whitepaper", "sitetag"],
  "per_photo": [
    {
      "filename": "1_IMG-20240809-WA0025.jpg",
      "a_classes": {"duct": false, "ruler": true,  "whitepaper": false, "sitetag": false},
      "b_classes": {"duct": false, "ruler": true,  "whitepaper": false, "sitetag": false},
      "class_agreement": true,
      "ruler_ious": [0.81],          // best IoU per a-bbox, -1 if unmatched
      "duct_ious": [], "whitepaper_ious": [], "sitetag_ious": []
    }
  ],
  "summary": {
    "class_presence_agreement_rate": 0.95,
    "per_class_mean_iou_when_both_present": {"duct": 0.71, "ruler": 0.66, "whitepaper": 0.0, "sitetag": 0.0}
  }
}
```

## 7. State & Lifecycle

**Local runner — single-threaded:**
1. Load `LabellerConfig` from YAML.
2. Load `manifest.csv` and filter by `--batches` / `--limit`.
3. Instantiate the Labeller; call `health_check()`. Abort on failure (exit 3).
4. For each photo serially: check resume (skip if both `<stem>.txt` and `<stem>.json` exist) → call `Labeller.label(path)` → write atomically (`<stem>.txt.tmp` + `<stem>.json.tmp` → rename) → update tqdm + latency stats.
5. On completion or interrupt (SIGTERM/SIGINT) → write `run_manifest.json` (always — even on partial completion).
6. Exit: 0 if `images_failed == 0`, 1 if any failures, 2 if config error, 3 if server unreachable.

**VM server — single uvicorn process:**
1. Read `MODEL` env var.
2. Dispatch to the matching adapter; call `Adapter.load_model()`. Abort the process if load fails (Makefile-visible).
3. Serve until killed by `make stop` (`pkill -f 'uvicorn server.main'`).

**No DB. No queue. No persistent state between runs except files on disk.**

## 8. Error Taxonomy

| Error | Source | Detection | Surface | Retry? |
|---|---|---|---|---|
| `ConfigError` | invalid YAML, missing required field, mode/endpoint mismatch | Pydantic validation at config load | abort at startup, exit 2 | no |
| `ServerUnreachable` | `/health` returns non-200 or connect timeout at run start | pre-run health probe | abort, exit 3 | no — operator fixes tunnel |
| `ImageError` | unreadable JPEG, missing file | `PIL.Image.open` fails | per-photo WARN; skip; append to `run_manifest.errors[]`; continue | no |
| `LabellerError` transient | 5xx, 429, `httpx.TimeoutException`, `httpx.ConnectError` | httpx response code / exception type | retry up to `config.retries` (default 2) with exponential backoff 1 s → 2 s; final failure → ERR + record | yes |
| `MalformedResponse` | non-parseable JSON, missing required keys, bbox outside [0,1] | Pydantic validation of response | per-photo WARN; emit empty detection list for that image; record in `run_manifest.errors[]`; continue | no |
| `OOM` server-side | adapter hits CUDA OOM during `detect` | adapter catches `torch.cuda.OutOfMemoryError`, returns 503 `{"error":"oom"}` | client treats as `LabellerError` transient | yes |
| Bug — every other unexpected exception | adapter raises | server returns 500 with traceback in detail | client treats as `LabellerError` (non-transient); record | no |

Class invariant: a run that started always produces `run_manifest.json` with a final state, even if every image failed. The runner registers a SIGINT/SIGTERM handler that drains state to disk before exiting.

## 9. Observability

- **stdout:** one tqdm progress bar with current filename, running latency p50, error count.
- **stderr:** WARN per skipped image, ERR per first-occurrence of each error category.
- **`run_manifest.json`:** per-run authoritative record (see §6.4).
- **Per-image `latency_ms`** in each `meta.json` — lets `compare.py` emit latency distributions per profile.
- **No metrics emitter, no traces, no structured-log stack.** stdout + JSON manifest is the whole observability surface.

## 10. Testing Strategy

| Level | Scope | Mock/real | Lives in |
|---|---|---|---|
| Unit | YAML config load (valid + invalid), bbox utilities (xyxy↔cxcywh, clip-to-[0,1]), resume skip-if-exists logic, IoU computation, compare diff function | pure stdlib | `tests/labelling/test_config.py`, `test_bbox.py`, `test_resume.py`, `test_compare.py` |
| Integration | `RemoteVlmLabeller` against `respx`-mocked `/detect`. Verifies: (a) successful request → LabelOutput with correct bbox/confidence/cls; (b) 503 → retry → success; (c) 503 × N+1 → LabellerError after retries exhausted; (d) timeout → retry → eventual abort; (e) malformed response body → MalformedResponse path → empty detection list | mocked httpx | `tests/labelling/test_remote_integration.py` |
| Smoke | VM: `curl :8000/health` returns 200 + correct model name | runs on VM | `~/repos/vision/tests/test_health.sh` |
| Manual gate | round-trip on `Beispiele/duct/<one>.jpeg` through Grounding DINO; visual bbox sanity check | manual | session log |
| Manual gate | label `batch_00.txt` (20 photos) with Grounding DINO; run `compare_runs.py` against v2 baseline; show user the diff | manual review | session log |

**"Green" before claiming the harness works:**
1. `pytest tests/labelling/ -q` passes (unit + mocked integration).
2. `python scripts/label.py --config configs/labelling/grounding-dino.yaml --batches 0 --limit 1` writes one valid `<stem>.txt` and `<stem>.json` and a `run_manifest.json` with `images_failed: 0` — after a Beispiele/duct/ photo is staged in `manifest.csv` (or with a temp manifest).
3. `make health` on the VM returns 200.
4. End-to-end on one Beispiele/duct/ photo via Grounding DINO returns a non-empty bbox list with `cls: "duct"`.

No CI required for the hackathon — these are run manually as gates.

## 11. Integration Points

**Files to create:**

Local:
- `src/oepentrench/labelling/__init__.py`
- `src/oepentrench/labelling/base.py`
- `src/oepentrench/labelling/config.py`
- `src/oepentrench/labelling/remote_labeller.py`
- `src/oepentrench/labelling/hybrid_labeller.py` (skeleton — raise NotImplementedError)
- `src/oepentrench/labelling/runner.py`
- `src/oepentrench/labelling/compare.py`
- `scripts/label.py`
- `scripts/compare_runs.py`
- `configs/labelling/grounding-dino.yaml`
- `tests/labelling/__init__.py`
- `tests/labelling/test_config.py`
- `tests/labelling/test_bbox.py`
- `tests/labelling/test_resume.py`
- `tests/labelling/test_compare.py`
- `tests/labelling/test_remote_integration.py`
- `docs/labelling-harness.md` (operator runbook — one page)

VM (`~/repos/vision/`):
- `README.md`
- `Makefile`
- `pyproject.toml`
- `server/__init__.py`
- `server/main.py`
- `server/schema.py`
- `server/adapters/__init__.py`
- `server/adapters/base.py`
- `server/adapters/grounding_dino.py`
- `server/adapters/{qwen_vl,owlv2,florence2,trex2}.py` (stubs)
- `tests/test_health.sh`

**Files to modify:**
- `project-resources/custom-datasets/duct-and-ruler/detection/data.yaml` — add classes 2 + 3.
- `project-resources/custom-datasets/duct-and-ruler/detection/README.md` — reflect 4-class schema + harness layout (kept as a one-page change, not a rewrite).
- `scripts/inspect_labels.py` — read class names from `data.yaml`, accept `--run`/`--data-yaml`, support 4 classes.
- `pyproject.toml` — add `httpx`, `pyyaml`, `pydantic` to runtime deps; add `respx` to `dev` extras.

**Config keys added:** the `LabellerConfig` schema (§6.5).

**CLI surface added:** `scripts/label.py`, `scripts/compare_runs.py`, plus new flags on `scripts/inspect_labels.py`.

**External services touched:** the VM via SSH local-forward tunnel; no other.

## 12. Acceptance Criteria

The implementer is done when **all** of the following are observably true:

1. **Schema updated.** `data.yaml` lists 4 classes (duct, ruler, whitepaper, sitetag) at IDs 0–3.
2. **Inspector adapted.** `scripts/inspect_labels.py` reads class names from `data.yaml`, accepts `--run <dir>`, and still opens cleanly on the existing v2 layout (`labelling/labels/` + `labelling/meta/` + `Fotos/`).
3. **Operator-mediated Claude runs document.** `docs/labelling-harness.md` describes the operator workflow that produces `labelling/runs/claude-opus_<ts>/{labels,meta,run_manifest.json}` so `compare_runs.py` works on it identically to a remote-vlm run.
4. **VM server reachable.** Through `ssh -L 8000:localhost:8000 threenicorn`, `curl localhost:8000/health` returns `{"status":"ok","model":"grounding-dino-base", …}`.
5. **Remote round-trip on one Beispiel.** `python scripts/label.py --config configs/labelling/grounding-dino.yaml --image-path project-resources/Beispiele/duct/<filename>.jpeg` against a known-positive `Beispiele/duct/` photo returns a non-empty `bboxes` list with `cls: "duct"`. The `<filename>` is chosen by the implementer from the 20 reference images.
6. **Batch round-trip.** `python scripts/label.py --config configs/labelling/grounding-dino.yaml --batches 0` labels the 20 photos in `batch_00.txt`.
7. **Comparison.** `python scripts/compare_runs.py labelling/labels/ labelling/runs/grounding-dino_<ts>/labels/ --classes data.yaml --out batch_00_diff.json` emits a per-photo agreement JSON the user can read.
8. **Tests green.** `pytest tests/labelling/ -q` exits 0 (unit + mocked integration).
9. **Run manifest is honest.** A `run_manifest.json` produced by the runner contains the actual `git_rev`, accurate `images_completed` / `images_failed` counters, and `latency_p50_ms` / `latency_p95_ms` derived from the per-image latencies.
10. **No backward-compat damage.** Running `scripts/inspect_labels.py` with no flags on the existing v2 layout still produces the same kind of FiftyOne dataset it did before (2 classes, 500 samples), with no errors and no regressed behaviour.

## 13. Known Gaps / Implementer Judgment

Each entry below is a decision the implementer will face that the spec intentionally does not pin. Each must be logged in the decision journal as it gets resolved.

| Gap | Guidance | Out-of-bounds |
|---|---|---|
| Exact Grounding DINO prompt strings per class | Start from EN+DE phrasing inspired by R14 (e.g. "HDPE conduit . Schutzrohr . fibre cable . end caps" for duct; "folding rule . Zollstock . Meterstab . tape measure" for ruler). Iterate on the first 20 photos before locking. Whitepaper / sitetag prompts have no R14 precedent — implementer judges. Record each iteration in the run_manifest's `config.prompts`. | Don't ship class names alone as prompts — phrasal disambiguation matters for Grounding DINO. |
| Per-class confidence threshold defaults | R14 numbers (0.25 / 0.20 / 0.30 / 0.25 for duct / ruler / whitepaper / sitetag) are starting points. Tune on batch_00 before any larger run. | Don't hardcode anywhere except the YAML — keep tunable. |
| `compare.py` output JSON field names | Required content: per-photo class-presence agreement + per-class bbox IoU matching + a summary block. The exact field names in §6.6 are illustrative — implementer may rename for clarity. | Don't emit a flat list of mismatches — group by photo so the user can act on it. |
| Whether `inspect_labels.py` is rewritten or extended | Extend in place. The existing `pick_layout()` already handles two paths; add a third for `labelling/runs/<dir>/` and read `data.yaml` for class names. | Don't break v2 inspection. |
| Image-root path on the VM | Suggest `/home/<user>/data/Fotos` and `/home/<user>/data/Beispiele` after `tar | ssh threenicorn 'tar xz -C ~/data'`. Implementer picks the final layout after SSH'ing in and confirms in the config. | Don't hardcode — keep `remote_image_root` in the YAML. |
| HF model revision pinning | Default: no pin (use the HF default revision). If the implementer pins, add a `revision:` field to the YAML and document in the manifest. | If pinned, the value MUST appear in `run_manifest.config`. |
| How operator (Claude) runs write `run_manifest.json` | Default: hand-written into the run dir by the operator (= Claude) at the end of the dispatch loop. No new tooling. | Don't make the harness's runner reach into operator runs to retroactively manifest them. |
| Whether the runner exposes `--workers N` for parallel HTTP from the start | Default: no, serial. Add only if the user explicitly asks. | Don't add multi-worker speculatively; serialised retry/backoff logic is much simpler. |
| Resume behaviour when only `<stem>.txt` exists but not `<stem>.json` (or vice versa) | Treat as "incomplete" → re-label. Both must exist for a skip. | Don't skip on `.txt` alone; that's the historical Ultralytics file format and could be present from elsewhere. |
| `HybridLabeller` arbitration prompt | Not implemented this session. The skeleton class lives in `hybrid_labeller.py` and raises NotImplementedError; the dispatch loop sketch lives in `docs/labelling-harness.md`. | Don't dispatch Agent calls from Python — Claude arbitration is operator-mediated. |
| How `compare.py` matches a-bboxes to b-bboxes within a class | Greedy IoU matching per class: sort a-bboxes by area desc; for each, pick the highest-IoU unmatched b-bbox; record IoU; remaining a-bboxes get IoU -1 (unmatched). | Don't run a full Hungarian assignment unless greedy proves wrong on data. |
| Test fixtures (where do test images come from) | Use 2–3 small JPEGs from `Beispiele/duct/`; if they're > 50 KB each, downscale to fixtures. | Don't check in 1200×1600 raw photos. |
| Whether the `remote-vlm` server-side path-validation rejects requests where `image_path` is not under `image_root` | Default: yes — 400 with `{"error":"path_outside_root"}`. Defense in depth even on an SSH-tunneled-only port. | Don't blindly open arbitrary paths. |

## 14. Risks & Open Questions

### Resolved during brainstorming
- Whitepaper class scope → **two classes**: `whitepaper` (printed/handwritten address or coordinates) and `sitetag` (F-numbered contractor codes, DataMatrix slips).
- First VM model → **Grounding DINO Base** (Apache 2.0, ~50 ms/image on a 5090, text-prompted, covers all 4 classes via per-class prompts).
- Hybrid mode shape → per-image arbitration (Claude sees image + remote bboxes), **built in the next session**, operator-mediated via Agent dispatch.
- Cache scope → **intra-run resume only**; no cross-run content-addressable cache.
- Concurrency → **serial only**.
- Image transport → **`image_path` only** (corpus rsync'd to VM); no base64.
- Claude labelling → **operator-mediated via Agent dispatch in this Claude Code session**, model = Opus 4.7; no anthropic SDK; no API spend.

### Risks (mitigations stated; implementer should monitor)
- **Grounding DINO Base may not localise `sitetag` well** — F-tag slips have small text; the model is object-shaped, not text-aware. If batch_00 sitetag recall is < 0.5, flag it and prioritise T-Rex2 image-prompt next session. Mitigation lives in the next-session backlog, not this one.
- **SSH tunnel can drop mid-run.** Mitigation: pre-run `/health` probe aborts cleanly; operator restarts the tunnel and re-runs (resume picks up where it left off).
- **VM unreachable.** Mitigation: operator-mediated Claude run path keeps working.
- **WhatsApp recompression destroys sitetag DataMatrix detail.** Already known from R8; not a detection-side problem. Detection only needs the slip bbox, not the decoded payload.
- **Updated `data.yaml` breaks any subsequent Ultralytics training run.** Mitigation: training is out of scope; when verified labels move into `labels/train/`, they'll be 4-class and consistent.
- **Disk on VM.** Corpus tar is ~1.2 GB, Beispiele < 100 MB. Negligible.
- **Path mismatch between local manifest filenames and VM filesystem** if some files were renamed during tar/extract. Mitigation: `/health` returns `images_under_root`; the harness logs a WARN if it differs from `manifest.csv` row count and asks the operator to confirm.

### Open questions (NOT blockers for this design; flag at session end)
1. Are there F-tag exemplars on disk anywhere (e.g. in `Beispiele/`), or does the user need to manually crop 3–5 from the corpus before T-Rex2 can be useful in the next session? A `ls Beispiele/` plus a glance at filenames would answer.
2. Should each v3 run also write a per-run `data.yaml` (with the exact class IDs it used) into the run dir, so the inspector / compare can self-describe a run? Default this session: one global `data.yaml`; revisit if the class set ever forks per profile.
