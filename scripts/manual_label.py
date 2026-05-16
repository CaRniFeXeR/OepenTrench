"""Manual multi-class YOLO bbox labelling tool.

Browser-based annotator (zero new deps; vanilla HTML+JS canvas served by
stdlib http.server) that writes full-image YOLO labels and copies source
photos into a mirror dataset whose shape matches ``duct-and-ruler/detection``
(images/{train,test}, labels/{train,test}, data.yaml). That layout is what
``compare_runs.py``, ``inspect_labels.py`` and ``train_yolo.py`` already
consume, so the manual labels drop straight into the existing tooling.

Default mirror dataset:
    project-resources/custom-datasets/duct-and-ruler-manual/detection/

On first run the mirror dir is bootstrapped: dir tree is created and a
``data.yaml`` is copied from ``duct-and-ruler/detection/data.yaml`` (same
class IDs) with ``path:`` re-rooted under the mirror. All saves go to the
``train`` split by default; use ``--split test`` to drop directly into test
or move files later with ``mv``.

Usage:
    # Walk through the existing 500-photo sample manifest:
    uv run python scripts/manual_label.py \\
        --manifest project-resources/custom-datasets/duct-and-ruler/detection/labelling/manifest.csv

    # Or label an explicit list:
    uv run python scripts/manual_label.py --images path1.jpg path2.jpg

    # Slice a manifest in chunks (resume-friendly across sessions):
    uv run python scripts/manual_label.py --manifest ... --start-idx 0 --limit 50

In the browser:
- Keys 1..9 select active class (also clickable buttons in the top bar).
- Drag on the image to draw a box in the active class's colour.
- U  undo last box on this image
- C  clear all boxes on this image
- N  mark this image as "no objects" (verified-empty)
- Left/Right arrows walk images
- "Save & exit" persists only verified images.
"""
from __future__ import annotations

import argparse
import csv
import http.server
import json
import shutil
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_FOTOS_ROOT = PROJECT_ROOT / "project-resources" / "Fotos"
_ORIGINAL_DATASET = (
    PROJECT_ROOT / "project-resources" / "custom-datasets" / "duct-and-ruler" / "detection"
)
_DEFAULT_MIRROR = (
    PROJECT_ROOT
    / "project-resources"
    / "custom-datasets"
    / "duct-and-ruler-manual"
    / "detection"
)

# Distinct hues per class id. Cycled if there are more classes than entries.
_CLASS_COLORS = [
    "#ffd54a",  # yellow
    "#5ad1ff",  # cyan
    "#ff7ad1",  # magenta
    "#7cff7c",  # green
    "#ffa45a",  # orange
    "#c490ff",  # purple
    "#ff5a5a",  # red
    "#9affd1",  # mint
    "#ffc59a",  # peach
]


_HTML = r"""<!doctype html>
<html><head>
<meta charset="utf-8"/>
<title>Manual label</title>
<style>
  body { font: 14px system-ui, sans-serif; margin: 0; background: #1a1a1a; color: #ddd; }
  #topbar { padding: 8px 12px; background: #222; display: flex; gap: 8px; align-items: center;
            border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 10; flex-wrap: wrap; }
  #classes { display: flex; gap: 6px; }
  .cls { padding: 4px 10px; border-radius: 3px; cursor: pointer; border: 2px solid transparent;
         font: inherit; color: #111; font-weight: 600; }
  .cls.active { outline: 2px solid #fff; box-shadow: 0 0 0 2px #1a1a1a inset; }
  #stage { position: relative; display: inline-block; margin: 12px; }
  canvas { position: absolute; top: 0; left: 0; cursor: crosshair; }
  img { display: block; max-width: 95vw; max-height: 80vh; user-select: none; -webkit-user-drag: none; }
  button { padding: 4px 10px; background: #333; color: #ddd; border: 1px solid #555;
           cursor: pointer; border-radius: 3px; font: inherit; }
  button:hover { background: #444; }
  button.primary { background: #2a5; border-color: #2a5; color: #fff; }
  button.warn { background: #a52; border-color: #a52; color: #fff; }
  #counter { font-variant-numeric: tabular-nums; min-width: 80px; }
  #filename { color: #aaa; font-size: 12px; }
  #verify { font-size: 12px; min-width: 120px; }
  .ok { color: #6c6; } .empty { color: #cb6; } .none { color: #777; }
  #status { color: #6a6; margin-left: 8px; }
  .hint { color: #777; font-size: 12px; margin-left: 12px; }
</style>
</head><body>
<div id="topbar">
  <button onclick="prev()" title="← arrow">&larr; Prev</button>
  <span id="counter">0 / 0</span>
  <button onclick="next()" title="→ arrow">Next &rarr;</button>
  <span id="classes"></span>
  <button onclick="undo()" title="U">Undo</button>
  <button onclick="clearAll()" title="C">Clear</button>
  <button class="warn" onclick="markEmpty()" title="N">No objects</button>
  <span id="verify" class="none">unverified</span>
  <span id="filename"></span>
  <span style="flex:1"></span>
  <button class="primary" onclick="save()">Save &amp; exit</button>
  <span id="status"></span>
  <span class="hint">1–9 = class · drag = box · U undo · C clear · N no-objects · ←/→ navigate</span>
</div>
<div id="stage">
  <img id="img" alt=""/>
  <canvas id="canvas"></canvas>
</div>
<script>
const MANIFEST = __MANIFEST__;
const CLASSES = __CLASSES__;    // [{id:int, name:str, color:str}, ...]
let activeCls = CLASSES.length ? CLASSES[0].id : 0;
let idx = 0;
// Per-image:
//   boxes: [{x, y, w, h, cls}], in displayed-canvas pixel space
//   markedEmpty: bool (true ⇒ explicit "no objects" press)
const state = MANIFEST.map(() => ({ boxes: [], markedEmpty: false }));
let drag = null;
let saved = false;

const img = document.getElementById('img');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

function colorFor(clsId) {
  const c = CLASSES.find(c => c.id === clsId);
  return c ? c.color : '#ff0';
}
function nameFor(clsId) {
  const c = CLASSES.find(c => c.id === clsId);
  return c ? c.name : String(clsId);
}

function renderClassBar() {
  const root = document.getElementById('classes');
  root.innerHTML = '';
  CLASSES.forEach((c, i) => {
    const b = document.createElement('button');
    b.className = 'cls' + (c.id === activeCls ? ' active' : '');
    b.style.background = c.color;
    b.textContent = `${i+1}: ${c.name}`;
    b.onclick = () => { activeCls = c.id; renderClassBar(); render(); };
    root.appendChild(b);
  });
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.lineWidth = 2;
  for (const b of state[idx].boxes) {
    const col = colorFor(b.cls);
    ctx.strokeStyle = col;
    ctx.fillStyle = col + '22';   // ~13% alpha
    ctx.fillRect(b.x, b.y, b.w, b.h);
    ctx.strokeRect(b.x, b.y, b.w, b.h);
    // class tag
    ctx.fillStyle = col;
    const label = nameFor(b.cls);
    ctx.font = 'bold 12px system-ui';
    const tw = ctx.measureText(label).width + 6;
    ctx.fillRect(b.x, Math.max(0, b.y - 16), tw, 16);
    ctx.fillStyle = '#111';
    ctx.fillText(label, b.x + 3, Math.max(12, b.y - 4));
  }
  if (drag) {
    ctx.strokeStyle = colorFor(activeCls);
    ctx.strokeRect(drag.x, drag.y, drag.w, drag.h);
  }
  // status line
  const s = state[idx];
  const v = document.getElementById('verify');
  if (s.boxes.length > 0) {
    v.textContent = `verified · ${s.boxes.length} box(es)`;
    v.className = 'ok';
  } else if (s.markedEmpty) {
    v.textContent = 'verified · no objects';
    v.className = 'empty';
  } else {
    v.textContent = 'unverified';
    v.className = 'none';
  }
  document.getElementById('counter').textContent = `${idx+1} / ${MANIFEST.length}`;
  document.getElementById('filename').textContent = MANIFEST[idx].name;
}

function load() {
  img.onload = () => {
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    render();
  };
  img.src = MANIFEST[idx].url;
}

function prev() { if (idx > 0) { idx--; load(); } }
function next() { if (idx < MANIFEST.length - 1) { idx++; load(); } }
function undo() {
  state[idx].boxes.pop();
  if (state[idx].boxes.length === 0) state[idx].markedEmpty = false;
  render();
}
function clearAll() { state[idx].boxes = []; state[idx].markedEmpty = false; render(); }
function markEmpty() {
  if (state[idx].boxes.length > 0) return;   // boxes already make it verified
  state[idx].markedEmpty = true;
  render();
  next();
}

function pos(e) {
  const r = canvas.getBoundingClientRect();
  return { x: e.clientX - r.left, y: e.clientY - r.top };
}
canvas.addEventListener('mousedown', (e) => {
  e.preventDefault();
  const p = pos(e);
  drag = { x: p.x, y: p.y, w: 0, h: 0 };
});
canvas.addEventListener('mousemove', (e) => {
  if (!drag) return;
  const p = pos(e);
  drag.w = p.x - drag.x;
  drag.h = p.y - drag.y;
  render();
});
window.addEventListener('mouseup', () => {
  if (!drag) return;
  let { x, y, w, h } = drag;
  if (w < 0) { x += w; w = -w; }
  if (h < 0) { y += h; h = -h; }
  if (w > 4 && h > 4) {
    state[idx].boxes.push({ x, y, w, h, cls: activeCls });
    state[idx].markedEmpty = false;
  }
  drag = null;
  render();
});
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowLeft') prev();
  else if (e.key === 'ArrowRight') next();
  else if (e.key.toLowerCase() === 'u') undo();
  else if (e.key.toLowerCase() === 'c') clearAll();
  else if (e.key.toLowerCase() === 'n') markEmpty();
  else if (/^[1-9]$/.test(e.key)) {
    const i = parseInt(e.key, 10) - 1;
    if (i < CLASSES.length) { activeCls = CLASSES[i].id; renderClassBar(); render(); }
  }
});
window.addEventListener('beforeunload', (e) => {
  const verified = state.some(s => s.boxes.length > 0 || s.markedEmpty);
  if (verified && !saved) { e.preventDefault(); e.returnValue = ''; }
});

async function save() {
  const payload = MANIFEST.map((m, i) => ({
    name: m.name,
    canvas_w: canvas.width,
    canvas_h: canvas.height,
    marked_empty: state[i].markedEmpty,
    boxes: state[i].boxes.map(b => ({
      cls: b.cls,
      x_norm: b.x / canvas.width,
      y_norm: b.y / canvas.height,
      w_norm: b.w / canvas.width,
      h_norm: b.h / canvas.height,
    })),
  }));
  document.getElementById('status').textContent = 'saving…';
  try {
    const r = await fetch('/save', { method: 'POST',
                                     headers: {'Content-Type': 'application/json'},
                                     body: JSON.stringify(payload) });
    const j = await r.json();
    saved = true;
    const msg = `saved ${j.saved_labels} label(s), copied ${j.copied_images} image(s)`
              + (j.skipped ? ` · skipped ${j.skipped} unverified` : '');
    document.getElementById('status').textContent = msg + '. you can close this tab.';
  } catch (err) {
    document.getElementById('status').textContent = `save failed: ${err}`;
  }
}

renderClassBar();
load();
</script>
</body></html>
"""


def _find_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def ensure_mirror(dataset_root: Path) -> dict[int, str]:
    """Bootstrap the mirror dataset on first run; return class id → name."""
    for sub in ("images/train", "images/test", "labels/train", "labels/test"):
        (dataset_root / sub).mkdir(parents=True, exist_ok=True)
    data_yaml = dataset_root / "data.yaml"
    if not data_yaml.exists():
        src_yaml = _ORIGINAL_DATASET / "data.yaml"
        if not src_yaml.exists():
            sys.exit(
                f"error: cannot bootstrap {data_yaml}: source {src_yaml} not found. "
                "Pass --dataset to point at a dir that already has data.yaml."
            )
        cfg = yaml.safe_load(src_yaml.read_text())
        cfg["path"] = str(dataset_root)
        cfg["train"] = "images/train"
        cfg["val"] = "images/test"
        cfg["test"] = "images/test"
        data_yaml.write_text(yaml.safe_dump(cfg, sort_keys=False))
        print(f"bootstrapped mirror dataset at {dataset_root}")
    cfg = yaml.safe_load(data_yaml.read_text())
    names = cfg.get("names", {})
    if isinstance(names, list):
        names = dict(enumerate(names))
    if not names:
        sys.exit(f"error: {data_yaml} has no 'names' entry")
    return {int(k): str(v) for k, v in names.items()}


def collect_from_manifest(manifest_csv: Path, start: int) -> list[Path]:
    """Resolve manifest.csv 'filename' column against Fotos/, skipping the first ``start`` rows."""
    if not _FOTOS_ROOT.exists():
        sys.exit(f"error: source images dir not found: {_FOTOS_ROOT}")
    by_name = {p.name: p for p in _FOTOS_ROOT.iterdir() if p.is_file()}
    out: list[Path] = []
    with manifest_csv.open() as fh:
        for row in csv.DictReader(fh):
            name = row.get("filename")
            if not name:
                continue
            src = by_name.get(name)
            if src is None:
                print(f"warn: manifest entry not in Fotos/: {name}", file=sys.stderr)
                continue
            out.append(src)
    return out[start:]


def _safe_stem(p: Path) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in p.stem)


def filter_done(images: list[Path], dataset_root: Path, split: str) -> tuple[list[Path], int]:
    """Drop images that already have a label file in ANY split under labels/.

    The ``split`` argument is accepted for callsite compatibility but is no
    longer used for filtering: an image labelled in any split (train, test, …)
    is treated as "done". This prevents items previously moved to test from
    re-appearing in a labelling session and being silently duplicated back
    into train.
    """
    labels_root = dataset_root / "labels"
    done_stems: set[str] = set()
    if labels_root.exists():
        for split_dir in labels_root.iterdir():
            if not split_dir.is_dir():
                continue
            for p in split_dir.glob("*.txt"):
                done_stems.add(p.stem)
    todo: list[Path] = []
    done = 0
    for p in images:
        if _safe_stem(p) in done_stems:
            done += 1
            continue
        todo.append(p)
    return todo, done


def save_outputs(
    dataset_root: Path,
    split: str,
    images: list[Path],
    payload: list[dict],
    class_names: dict[int, str],
) -> dict:
    """Write YOLO .txt + copy image for each verified entry."""
    images_dir = dataset_root / "images" / split
    labels_dir = dataset_root / "labels" / split
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    saved_labels = 0
    copied_images = 0
    skipped = 0
    valid_ids = set(class_names.keys())

    # Stems already present in any OTHER split — never write a duplicate.
    other_split_stems: set[str] = set()
    labels_root = dataset_root / "labels"
    if labels_root.exists():
        for split_dir in labels_root.iterdir():
            if not split_dir.is_dir() or split_dir.name == split:
                continue
            for p in split_dir.glob("*.txt"):
                other_split_stems.add(p.stem)

    for i, entry in enumerate(payload):
        src = images[i]
        boxes = entry.get("boxes") or []
        marked_empty = bool(entry.get("marked_empty"))
        if not boxes and not marked_empty:
            skipped += 1
            continue

        stem = _safe_stem(src)
        if stem in other_split_stems:
            print(f"warn: {stem} already labelled in another split — refusing to duplicate",
                  file=sys.stderr)
            skipped += 1
            continue
        # write YOLO label (xc, yc, w, h normalised — clipped to [0, 1])
        lines: list[str] = []
        for b in boxes:
            cls = int(b.get("cls", -1))
            if cls not in valid_ids:
                print(f"warn: box on {src.name} has unknown class id {cls}; dropping",
                      file=sys.stderr)
                continue
            x = float(b["x_norm"])
            y = float(b["y_norm"])
            w = float(b["w_norm"])
            h = float(b["h_norm"])
            xc = max(0.0, min(1.0, x + w / 2))
            yc = max(0.0, min(1.0, y + h / 2))
            w = max(0.0, min(1.0, w))
            h = max(0.0, min(1.0, h))
            if w <= 0 or h <= 0:
                continue
            lines.append(f"{cls} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
        (labels_dir / f"{stem}.txt").write_text("\n".join(lines) + ("\n" if lines else ""))
        saved_labels += 1

        # copy image bytes verbatim (preserve original encoding)
        dest = images_dir / f"{stem}{src.suffix.lower()}"
        if not dest.exists() or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
            copied_images += 1

    return {
        "saved_labels": saved_labels,
        "copied_images": copied_images,
        "skipped": skipped,
    }


def _make_handler(images, dataset_root, split, class_names, shutdown_event):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                manifest = [{"name": p.name, "url": f"/img/{i}"} for i, p in enumerate(images)]
                classes = [
                    {"id": cid, "name": class_names[cid],
                     "color": _CLASS_COLORS[i % len(_CLASS_COLORS)]}
                    for i, cid in enumerate(sorted(class_names))
                ]
                html = (_HTML
                        .replace("__MANIFEST__", json.dumps(manifest))
                        .replace("__CLASSES__", json.dumps(classes)))
                self._send(200, "text/html; charset=utf-8", html.encode())
            elif self.path.startswith("/img/"):
                try:
                    idx = int(self.path.removeprefix("/img/"))
                    src = images[idx]
                    data = src.read_bytes()
                except (ValueError, IndexError):
                    self.send_error(404)
                    return
                ctype = "image/jpeg" if src.suffix.lower() in (".jpg", ".jpeg") else "image/png"
                self._send(200, ctype, data)
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path == "/save":
                n = int(self.headers.get("Content-Length", "0"))
                try:
                    payload = json.loads(self.rfile.read(n))
                    result = save_outputs(dataset_root, split, images, payload, class_names)
                    self._send(200, "application/json", json.dumps(result).encode())
                except Exception as e:
                    self._send(500, "application/json",
                               json.dumps({"error": str(e)}).encode())
                    return
                threading.Thread(
                    target=lambda: (time.sleep(0.5), shutdown_event.set()),
                    daemon=True,
                ).start()
            else:
                self.send_error(404)

        def log_message(self, fmt, *args):
            pass

        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Manual multi-class YOLO bbox labelling tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--images", nargs="+", help="explicit list of source image paths")
    src.add_argument("--manifest", metavar="CSV",
                     help="manifest.csv (uses 'filename' column, resolves against Fotos/)")
    ap.add_argument("--dataset", default=str(_DEFAULT_MIRROR),
                    help=f"mirror dataset root (default: {_DEFAULT_MIRROR.relative_to(PROJECT_ROOT)})")
    ap.add_argument("--split", choices=("train", "test"), default="train",
                    help="which split to write to (default: train)")
    ap.add_argument("--start-idx", type=int, default=0,
                    help="skip the first N entries of --manifest (applied before resume filter)")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the number of NEW images to walk (applied after resume filter)")
    ap.add_argument("--include-done", action="store_true",
                    help="don't skip images that already have a label in the target split")
    ap.add_argument("--port", type=int, default=None,
                    help="HTTP port (default: random free port)")
    ap.add_argument("--no-open", action="store_true",
                    help="don't auto-open the browser")
    args = ap.parse_args()

    dataset_root = Path(args.dataset).resolve()
    class_names = ensure_mirror(dataset_root)

    if args.manifest:
        images = collect_from_manifest(Path(args.manifest).resolve(), args.start_idx)
    else:
        images = [Path(p).resolve() for p in args.images]

    missing = [p for p in images if not p.exists()]
    if missing:
        for p in missing:
            print(f"warn: not found: {p}", file=sys.stderr)
    images = [p for p in images if p.exists()]
    if not images:
        sys.exit("error: no source images to label")

    if not args.include_done:
        images, done = filter_done(images, dataset_root, args.split)
        if done:
            print(f"skipped {done} image(s) already labelled in {args.split}/ "
                  "(pass --include-done to re-label)")
    if args.limit is not None:
        images = images[:args.limit]
    if not images:
        sys.exit("error: nothing to do — all candidates already labelled")

    port = args.port or _find_free_port()
    shutdown_event = threading.Event()
    handler = _make_handler(images, dataset_root, args.split, class_names, shutdown_event)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)

    url = f"http://127.0.0.1:{port}/"
    print(f"labelling {len(images)} image(s) at {url}")
    print(f"dataset:  {dataset_root}")
    print(f"split:    {args.split}")
    print("classes:  " + ", ".join(f"{i}={class_names[i]}" for i in sorted(class_names)))
    print("click 'Save & exit' in the browser when done (Ctrl-C here aborts without saving).")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    if not args.no_open:
        webbrowser.open(url)

    try:
        shutdown_event.wait()
    except KeyboardInterrupt:
        print("\ninterrupted — no labels written unless you clicked Save first")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
