"""SAM 2-assisted multi-class YOLO bbox labelling tool.

Same on-disk contract as ``manual_label.py`` (mirror dataset at
``project-resources/custom-datasets/duct-and-ruler-manual/detection/`` with
``images/{train,test}``, ``labels/{train,test}``, ``data.yaml``) — but the
primary labelling action is a single click per object: SAM 2 segments the
clicked thing, the script derives a tight bbox from the mask, and the box
is tagged with the currently-active class.

This script reuses the dataset bootstrap, manifest resolution, resume,
and save logic from ``manual_label.py``; only the browser UX and the
SAM-2 segmentation endpoint are new here.

Usage:
    uv run python scripts/sam_label.py \\
        --manifest project-resources/custom-datasets/duct-and-ruler/detection/labelling/manifest.csv \\
        --limit 50

    # On a beefy box (or CUDA available):
    uv run python scripts/sam_label.py --images a.jpg b.jpg --device cuda

In the browser:
- 1..9 select the active class.
- Click an object → SAM 2 segments it → bbox is added in the active class colour.
- Drag still creates a manual bbox (fallback when SAM misses).
- U undo · C clear · N mark "no objects" · ←/→ navigate · Save & exit.
"""
from __future__ import annotations

import argparse
import http.server
import json
import sys
import threading
import time
import webbrowser
from pathlib import Path

from PIL import Image

# Reuse infra from manual_label.py — scripts/ is on sys.path[0] when uv runs the file.
from manual_label import (  # type: ignore
    PROJECT_ROOT,
    _CLASS_COLORS,
    _DEFAULT_MIRROR,
    _find_free_port,
    collect_from_manifest,
    ensure_mirror,
    filter_done,
    save_outputs,
)


_HTML = r"""<!doctype html>
<html><head>
<meta charset="utf-8"/>
<title>SAM 2 label</title>
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
  #verify { font-size: 12px; min-width: 130px; }
  .ok { color: #6c6; } .empty { color: #cb6; } .none { color: #777; }
  #status { color: #6a6; margin-left: 8px; min-width: 160px; }
  #status.err { color: #f66; }
  #status.busy { color: #ec6; }
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
  <span class="hint">click = SAM · drag = manual box · 1–9 class · U undo · C clear · N empty · ←/→</span>
</div>
<div id="stage">
  <img id="img" alt=""/>
  <canvas id="canvas"></canvas>
</div>
<script>
const MANIFEST = __MANIFEST__;
const CLASSES = __CLASSES__;
let activeCls = CLASSES.length ? CLASSES[0].id : 0;
let idx = 0;
const state = MANIFEST.map(() => ({ boxes: [], markedEmpty: false }));
let drag = null;
let dragStart = null;          // {x, y, t} at mousedown
let dragMoved = false;         // exceeded click-vs-drag threshold
let pendingPoint = null;       // {x, y} canvas-pixel of click awaiting SAM
let busy = false;
let saved = false;

const DRAG_PIX_THRESHOLD = 5;  // movement > this ⇒ drag, else ⇒ click

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

function setStatus(msg, klass) {
  const s = document.getElementById('status');
  s.textContent = msg || '';
  s.className = klass || '';
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.lineWidth = 2;
  for (const b of state[idx].boxes) {
    const col = colorFor(b.cls);
    ctx.strokeStyle = col;
    ctx.fillStyle = col + '22';
    ctx.fillRect(b.x, b.y, b.w, b.h);
    ctx.strokeRect(b.x, b.y, b.w, b.h);
    ctx.fillStyle = col;
    const label = nameFor(b.cls) + (b.src === 'sam' ? '◆' : '');
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
  if (pendingPoint) {
    // Ring at the click while SAM is thinking.
    ctx.strokeStyle = colorFor(activeCls);
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(pendingPoint.x, pendingPoint.y, 10, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.lineWidth = 2;
  }
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
  if (state[idx].boxes.length > 0) return;
  state[idx].markedEmpty = true;
  render();
  next();
}

function pos(e) {
  const r = canvas.getBoundingClientRect();
  return { x: e.clientX - r.left, y: e.clientY - r.top };
}

async function segmentAt(p) {
  if (busy) { setStatus('SAM busy — wait', 'busy'); return; }
  busy = true;
  pendingPoint = p;
  setStatus('SAM thinking…', 'busy');
  render();
  const imgIdx = idx;
  const cls = activeCls;
  try {
    const r = await fetch('/segment', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        idx: imgIdx,
        x_norm: p.x / canvas.width,
        y_norm: p.y / canvas.height,
      }),
    });
    const j = await r.json();
    if (j.error) {
      setStatus(`SAM: ${j.error}`, 'err');
    } else if (imgIdx !== idx) {
      // user navigated mid-inference — drop the box on the floor
      setStatus('(SAM result discarded: image changed)', 'busy');
    } else {
      state[imgIdx].boxes.push({
        x: j.x_norm * canvas.width,
        y: j.y_norm * canvas.height,
        w: j.w_norm * canvas.width,
        h: j.h_norm * canvas.height,
        cls: cls,
        src: 'sam',
      });
      state[imgIdx].markedEmpty = false;
      setStatus(`SAM ok (${(j.latency_ms||0).toFixed(0)} ms)`, '');
    }
  } catch (err) {
    setStatus(`SAM failed: ${err}`, 'err');
  } finally {
    busy = false;
    pendingPoint = null;
    render();
  }
}

canvas.addEventListener('mousedown', (e) => {
  e.preventDefault();
  const p = pos(e);
  dragStart = { x: p.x, y: p.y, t: performance.now() };
  dragMoved = false;
  drag = null;
});
canvas.addEventListener('mousemove', (e) => {
  if (!dragStart) return;
  const p = pos(e);
  const dx = p.x - dragStart.x, dy = p.y - dragStart.y;
  if (!dragMoved && (Math.abs(dx) > DRAG_PIX_THRESHOLD || Math.abs(dy) > DRAG_PIX_THRESHOLD)) {
    dragMoved = true;
    drag = { x: dragStart.x, y: dragStart.y, w: 0, h: 0 };
  }
  if (dragMoved && drag) {
    drag.w = dx; drag.h = dy;
    render();
  }
});
window.addEventListener('mouseup', (e) => {
  if (!dragStart) return;
  if (!dragMoved) {
    // Click → SAM
    segmentAt({ x: dragStart.x, y: dragStart.y });
  } else if (drag) {
    let { x, y, w, h } = drag;
    if (w < 0) { x += w; w = -w; }
    if (h < 0) { y += h; h = -h; }
    if (w > 4 && h > 4) {
      state[idx].boxes.push({ x, y, w, h, cls: activeCls, src: 'manual' });
      state[idx].markedEmpty = false;
    }
    drag = null;
    render();
  }
  dragStart = null;
  dragMoved = false;
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
  setStatus('saving…', 'busy');
  try {
    const r = await fetch('/save', { method: 'POST',
                                     headers: {'Content-Type': 'application/json'},
                                     body: JSON.stringify(payload) });
    const j = await r.json();
    saved = true;
    const msg = `saved ${j.saved_labels} label(s), copied ${j.copied_images} image(s)`
              + (j.skipped ? ` · skipped ${j.skipped} unverified` : '');
    setStatus(msg + '. you can close this tab.');
  } catch (err) {
    setStatus(`save failed: ${err}`, 'err');
  }
}

renderClassBar();
load();
</script>
</body></html>
"""


class _SamWrapper:
    """Single-instance SAM 2 model with a serialising lock for thread-safe inference."""

    def __init__(self, weights: str, device: str | None):
        from ultralytics import SAM
        import torch

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        print(f"loading {weights} on {device}…", flush=True)
        self.model = SAM(weights)
        self.model.to(device)
        self._lock = threading.Lock()

    def segment_point(self, img_path: Path, x_px: int, y_px: int) -> tuple[float, float, float, float] | None:
        """Return (xc, yc, w, h) normalised, or None if SAM produced no mask."""
        import numpy as np

        with self._lock:
            results = self.model(
                str(img_path),
                points=[[x_px, y_px]],
                labels=[1],
                verbose=False,
            )
        if not results or results[0].masks is None:
            return None
        masks = results[0].masks.data
        if masks.shape[0] == 0:
            return None
        mask = masks[0].cpu().numpy()
        mh, mw = mask.shape
        nz = np.nonzero(mask)
        if nz[0].size == 0 or nz[1].size == 0:
            return None
        x1, y1 = int(nz[1].min()), int(nz[0].min())
        x2, y2 = int(nz[1].max() + 1), int(nz[0].max() + 1)
        xc = (x1 + x2) / 2 / mw
        yc = (y1 + y2) / 2 / mh
        w = (x2 - x1) / mw
        h = (y2 - y1) / mh
        return xc, yc, w, h


def _image_size_cached(cache: dict[int, tuple[int, int]], idx: int, path: Path) -> tuple[int, int]:
    if idx not in cache:
        with Image.open(path) as im:
            cache[idx] = im.size  # (W, H)
    return cache[idx]


def _make_handler(images, dataset_root, split, class_names, sam, shutdown_event):
    dims_cache: dict[int, tuple[int, int]] = {}

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
            if self.path == "/segment":
                n = int(self.headers.get("Content-Length", "0"))
                try:
                    req = json.loads(self.rfile.read(n))
                    idx = int(req["idx"])
                    x_norm = float(req["x_norm"])
                    y_norm = float(req["y_norm"])
                    if idx < 0 or idx >= len(images):
                        self._json(400, {"error": "bad image index"})
                        return
                    src = images[idx]
                    W, H = _image_size_cached(dims_cache, idx, src)
                    x_px = max(0, min(W - 1, int(round(x_norm * W))))
                    y_px = max(0, min(H - 1, int(round(y_norm * H))))
                    t0 = time.perf_counter()
                    box = sam.segment_point(src, x_px, y_px)
                    latency_ms = (time.perf_counter() - t0) * 1000
                    if box is None:
                        self._json(200, {"error": "no mask"})
                        return
                    xc, yc, w, h = box
                    x = max(0.0, xc - w / 2)
                    y = max(0.0, yc - h / 2)
                    self._json(200, {
                        "x_norm": x, "y_norm": y,
                        "w_norm": min(w, 1.0 - x), "h_norm": min(h, 1.0 - y),
                        "latency_ms": latency_ms,
                    })
                except Exception as e:
                    self._json(500, {"error": str(e)})
                return

            if self.path == "/save":
                n = int(self.headers.get("Content-Length", "0"))
                try:
                    payload = json.loads(self.rfile.read(n))
                    result = save_outputs(dataset_root, split, images, payload, class_names)
                    self._json(200, result)
                except Exception as e:
                    self._json(500, {"error": str(e)})
                    return
                threading.Thread(
                    target=lambda: (time.sleep(0.5), shutdown_event.set()),
                    daemon=True,
                ).start()
                return

            self.send_error(404)

        def log_message(self, fmt, *args):
            pass

        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, "application/json", json.dumps(obj).encode())

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(
        description="SAM 2-assisted multi-class YOLO bbox labelling tool.",
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
                    help="don't skip images already labelled in the target split")
    ap.add_argument("--weights", default=str(PROJECT_ROOT / "sam2_b.pt"),
                    help="ultralytics SAM 2 weights (auto-download if missing). default: sam2_b.pt")
    ap.add_argument("--device", default=None, help="torch device: cpu | mps | cuda (default: auto)")
    ap.add_argument("--port", type=int, default=None,
                    help="HTTP port (default: random free port)")
    ap.add_argument("--no-open", action="store_true", help="don't auto-open the browser")
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

    sam = _SamWrapper(args.weights, args.device)

    port = args.port or _find_free_port()
    shutdown_event = threading.Event()
    handler = _make_handler(images, dataset_root, args.split, class_names, sam, shutdown_event)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)

    url = f"http://127.0.0.1:{port}/"
    print(f"labelling {len(images)} image(s) at {url}")
    print(f"dataset:  {dataset_root}")
    print(f"split:    {args.split}")
    print("classes:  " + ", ".join(f"{i}={class_names[i]}" for i in sorted(class_names)))
    print(f"sam:      {args.weights} on {sam.device}")
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
