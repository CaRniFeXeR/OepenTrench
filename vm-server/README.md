# vision-server — VM-side detection adapter for ÖpenTrench

Single-model FastAPI server. One adapter loaded per process; restart to switch.

## Operator runbook

```
ssh threenicorn
cd ~/repos/vision
uv sync                     # one-time
make grounding-dino         # start server on :8000
make health                 # curl localhost:8000/health (run in another shell)
make stop                   # kill the server
```

From the operator's laptop:
```
ssh -L 8000:localhost:8000 threenicorn      # leave this open
curl localhost:8000/health
```

## Models

| make target | adapter | status |
|---|---|---|
| `grounding-dino` | `IDEA-Research/grounding-dino-base` (HF Transformers) | implemented |
| `qwen-vl` | `Qwen/Qwen2.5-VL-7B-Instruct` | stub |
| `owlv2` | `google/owlv2-large-patch14-ensemble` | stub |
| `florence2` | `microsoft/Florence-2-large` | stub |
| `t-rex2` | T-Rex2 image-prompt | stub |

Stubs raise `NotImplementedError` at `load_model()` so `make <stub>` reports the failure cleanly.

## Image root

Set via `IMAGE_ROOT` env var (default `/home/threenicorn/data`). All `POST /detect` requests must reference image paths under this root; out-of-root paths return HTTP 400.

```
# Upload Fotos + Beispiele once, before any /detect call.
tar -C /Users/rezafuru/repos/personal/OepenTrench/project-resources -cf - Fotos Beispiele \
    | ssh threenicorn 'mkdir -p ~/data && tar xf - -C ~/data'
```

## API

- `POST /detect` — Pydantic request/response per `server/schema.py`.
- `GET /health` — `{"status":"ok","model":...,"uptime_s":...,"image_root":...,"images_under_root":...}`.
- `GET /info` — adapter's class list + default prompts/thresholds.

## Development

```
make sync                   # uv sync (uses cu128 PyTorch wheels)
PORT=9000 make grounding-dino
make stop
tail -f server.log
```
