
"""Quick browser-based bbox annotation tool for curating exemplar crops.

Zero new dependencies — vanilla HTML+JS canvas served by stdlib http.server,
crops written via Pillow (already a project dep). Outputs PNG crops in a flat
directory plus a manifest.json with source + bbox traceability — directly
usable as OWLv2 image-query exemplars.

Usage:
    # Curate whitepaper exemplars from a list of photos:
    uv run python scripts/annotate_exemplars.py \\
        --images "project-resources/Fotos/2_WhatsApp Image 2024-09-23 at 19_21_35 (1).jpeg" \\
                 "project-resources/Fotos/3_WhatsApp Image 2024-08-30 at 19_09_24.jpeg" \\
        --out project-resources/exemplars/whitepaper/

    # Or pull every image a previous run flagged for a class:
    uv run python scripts/annotate_exemplars.py \\
        --from-run project-resources/custom-datasets/duct-and-ruler/detection/labelling/runs/hybrid-owlv2_2026-05-16T09-48-50Z \\
        --class whitepaper \\
        --out project-resources/exemplars/whitepaper/

In the browser: drag to draw a box, "Undo last" to drop the most recent box,
"Prev/Next" to walk photos (or Left/Right arrows), "Save & exit" when done.
Crops are written to <out>/crops/ and the server shuts itself down.
"""
from __future__ import annotations

import argparse
import http.server
import json
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_FOTOS_ROOT = PROJECT_ROOT / "project-resources" / "Fotos"

_HTML = r"""<!doctype html>
<html><head>
<meta charset="utf-8"/>
<title>Annotate exemplars</title>
<style>
  body { font: 14px system-ui, sans-serif; margin: 0; background: #1a1a1a; color: #ddd; }
  #topbar { padding: 8px 12px; background: #222; display: flex; gap: 8px; align-items: center;
            border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 10; flex-wrap: wrap; }
  #stage { position: relative; display: inline-block; margin: 12px; }
  canvas { position: absolute; top: 0; left: 0; cursor: crosshair; }
  img { display: block; max-width: 95vw; max-height: 80vh; user-select: none; -webkit-user-drag: none; }
  button { padding: 4px 10px; background: #333; color: #ddd; border: 1px solid #555;
           cursor: pointer; border-radius: 3px; font: inherit; }
  button:hover { background: #444; }
  button.primary { background: #2a5; border-color: #2a5; color: #fff; }
  #counter { font-variant-numeric: tabular-nums; min-width: 80px; }
  #filename { color: #aaa; font-size: 12px; }
  #boxes { font-size: 12px; color: #999; min-width: 140px; }
  #status { color: #6a6; margin-left: 8px; }
  .hint { color: #777; font-size: 12px; margin-left: 12px; }
</style>
</head><body>
<div id="topbar">
  <button onclick="prev()" title="← arrow">&larr; Prev</button>
  <span id="counter">0 / 0</span>
  <button onclick="next()" title="→ arrow">Next &rarr;</button>
  <button onclick="undo()" title="U">Undo last</button>
  <button onclick="clearAll()">Clear image</button>
  <span id="filename"></span>
  <span style="flex:1"></span>
  <span id="boxes"></span>
  <button class="primary" onclick="save()">Save &amp; exit</button>
  <span id="status"></span>
  <span class="hint">drag to draw · arrows to navigate · U=undo</span>
</div>
<div id="stage">
  <img id="img" alt=""/>
  <canvas id="canvas"></canvas>
</div>
<script>
const MANIFEST = __MANIFEST__;
let idx = 0;
// Per-image list of pixel-space boxes on the *displayed* canvas: {x, y, w, h}
const boxes = MANIFEST.map(() => []);
let drag = null;
let saved = false;

const img = document.getElementById('img');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.lineWidth = 2;
  ctx.strokeStyle = '#ff0';
  ctx.fillStyle = 'rgba(255, 255, 0, 0.10)';
  for (const b of boxes[idx]) {
    ctx.fillRect(b.x, b.y, b.w, b.h);
    ctx.strokeRect(b.x, b.y, b.w, b.h);
  }
  if (drag) {
    ctx.strokeStyle = '#0f0';
    ctx.strokeRect(drag.x, drag.y, drag.w, drag.h);
  }
  document.getElementById('boxes').textContent = `boxes on this image: ${boxes[idx].length}`;
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
function undo() { boxes[idx].pop(); render(); }
function clearAll() { boxes[idx] = []; render(); }

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
  if (w > 4 && h > 4) boxes[idx].push({ x, y, w, h });
  drag = null;
  render();
});
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowLeft') prev();
  else if (e.key === 'ArrowRight') next();
  else if (e.key.toLowerCase() === 'u') undo();
});
window.addEventListener('beforeunload', (e) => {
  const total = boxes.reduce((n, b) => n + b.length, 0);
  if (total > 0 && !saved) { e.preventDefault(); e.returnValue = ''; }
});

async function save() {
  const payload = MANIFEST.map((m, i) => ({
    name: m.name,
    boxes: boxes[i].map(b => ({
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
    document.getElementById('status').textContent = `saved ${j.saved} crops. you can close this tab.`;
  } catch (err) {
    document.getElementById('status').textContent = `save failed: ${err}`;
  }
}

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


def collect_from_run(run_dir: Path, cls: str) -> list[Path]:
    """Return source image paths for photos whose run-meta has a bbox of ``cls``."""
    meta_dir = run_dir / "meta"
    if not meta_dir.exists():
        sys.exit(f"error: no meta/ dir under {run_dir}")
    if not _FOTOS_ROOT.exists():
        sys.exit(f"error: source images dir not found: {_FOTOS_ROOT}")
    by_stem = {p.stem: p for p in _FOTOS_ROOT.iterdir() if p.is_file()}
    out: list[Path] = []
    for meta_path in sorted(meta_dir.glob("*.json")):
        try:
            meta = json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            print(f"warn: skipping malformed {meta_path.name}", file=sys.stderr)
            continue
        if any(b.get("cls") == cls for b in meta.get("bboxes", [])):
            stem = meta_path.stem
            if stem in by_stem:
                out.append(by_stem[stem])
            else:
                print(f"warn: meta {meta_path.name} has class {cls} but no image with stem {stem!r}",
                      file=sys.stderr)
    return out


def save_crops(out_dir: Path, images: list[Path], cls: str, payload: list[dict]) -> int:
    """Write per-box PNG crops + manifest.json under ``out_dir``. Returns crop count."""
    crops_dir = out_dir / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    n = 0
    for i, entry in enumerate(payload):
        if not entry.get("boxes"):
            continue
        src = images[i]
        with Image.open(src) as im:
            im_rgb = im.convert("RGB")
            W, H = im_rgb.size
            for k, b in enumerate(entry["boxes"]):
                left = max(0, min(int(b["x_norm"] * W), W - 1))
                top = max(0, min(int(b["y_norm"] * H), H - 1))
                right = max(left + 1, min(int((b["x_norm"] + b["w_norm"]) * W), W))
                bot = max(top + 1, min(int((b["y_norm"] + b["h_norm"]) * H), H))
                crop = im_rgb.crop((left, top, right, bot))
                safe_stem = "".join(c if c.isalnum() or c in "._-" else "_" for c in src.stem)
                crop_path = crops_dir / f"{safe_stem}_crop_{k}.png"
                crop.save(crop_path, format="PNG")
                manifest.append({
                    "class": cls,
                    "source": str(src),
                    "bbox_norm_xyxy": [
                        b["x_norm"],
                        b["y_norm"],
                        b["x_norm"] + b["w_norm"],
                        b["y_norm"] + b["h_norm"],
                    ],
                    "bbox_pixel_xyxy": [left, top, right, bot],
                    "crop": str(crop_path.relative_to(out_dir)),
                })
                n += 1
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return n


def _make_handler(images, out_dir, cls, shutdown_event):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                manifest = [
                    {"name": p.name, "url": f"/img/{i}"} for i, p in enumerate(images)
                ]
                html = _HTML.replace("__MANIFEST__", json.dumps(manifest))
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
                    n_crops = save_crops(out_dir, images, cls, payload)
                    body = json.dumps({"saved": n_crops}).encode()
                    self._send(200, "application/json", body)
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
            pass  # silence stderr access log

        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Browser-based bbox annotation tool for exemplar curation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--images", nargs="+", help="explicit list of source image paths")
    src.add_argument("--from-run", metavar="DIR",
                     help="pull all images flagged for --class in this run dir")
    ap.add_argument("--out", required=True, help="output dir (crops/ + manifest.json)")
    ap.add_argument("--class", dest="cls", default="whitepaper",
                    help="class label recorded in manifest (default: whitepaper)")
    ap.add_argument("--port", type=int, default=None,
                    help="HTTP port (default: random free port)")
    ap.add_argument("--no-open", action="store_true",
                    help="don't auto-open the browser")
    args = ap.parse_args()

    if args.from_run:
        images = collect_from_run(Path(args.from_run).resolve(), args.cls)
    else:
        images = [Path(p).resolve() for p in args.images]

    missing = [p for p in images if not p.exists()]
    if missing:
        for p in missing:
            print(f"warn: not found: {p}", file=sys.stderr)
    images = [p for p in images if p.exists()]
    if not images:
        sys.exit("error: no source images to annotate")

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    port = args.port or _find_free_port()
    shutdown_event = threading.Event()
    handler = _make_handler(images, out_dir, args.cls, shutdown_event)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)

    url = f"http://127.0.0.1:{port}/"
    print(f"annotating {len(images)} image(s) at {url}")
    print(f"output dir: {out_dir}")
    print("click 'Save & exit' in the browser when done (Ctrl-C here aborts without saving).")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    if not args.no_open:
        webbrowser.open(url)

    try:
        shutdown_event.wait()
    except KeyboardInterrupt:
        print("\ninterrupted — no crops written unless you clicked Save first")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
