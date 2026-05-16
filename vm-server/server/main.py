"""FastAPI app — POST /detect, GET /health, GET /info.

Loads the adapter named by env var ``MODEL`` at startup; one model per process.
Image root is set by env var ``IMAGE_ROOT`` (default ``/home/threenicorn/data``);
all incoming ``image_path`` values must resolve under this root.

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §4.4, §5.1-§5.3.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from server.adapters import get_adapter
from server.adapters.grounding_dino import (
    DEFAULT_PROMPTS,
    DEFAULT_THRESHOLDS,
)
from server.schema import (
    DetectRequest,
    DetectResponse,
    HealthResponse,
    InfoResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL = os.environ.get("MODEL", "grounding-dino")
IMAGE_ROOT = Path(os.environ.get("IMAGE_ROOT", "/home/threenicorn/data")).resolve()

app = FastAPI(title=f"vision-server ({MODEL})")
adapter = get_adapter(MODEL)
_started_at = time.monotonic()


@app.on_event("startup")
def _load_model() -> None:
    logger.info("loading adapter %s", MODEL)
    adapter.load_model()
    logger.info("ready: %s @ image_root=%s", adapter.model_id, IMAGE_ROOT)


def _validate_image_path(image_path: str) -> Path:
    p = Path(image_path).resolve()
    try:
        p.relative_to(IMAGE_ROOT)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"image_path {p} not under IMAGE_ROOT {IMAGE_ROOT}",
        )
    if not p.is_file():
        raise HTTPException(status_code=400, detail=f"image_path {p} does not exist")
    return p


def _count_images_under(root: Path) -> int:
    if not root.is_dir():
        return 0
    count = 0
    for p in root.rglob("*"):
        if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            count += 1
    return count


@app.post("/detect", response_model=DetectResponse)
def detect(req: DetectRequest) -> DetectResponse:
    resolved = _validate_image_path(req.image_path)
    # Replace the request's path with the resolved absolute one before adapter
    # call — defensive against symlink edge cases.
    req_resolved = req.model_copy(update={"image_path": str(resolved)})
    try:
        import torch  # local import; available because adapters depend on it
        return adapter.detect(req_resolved)
    except Exception as e:
        # Distinguish CUDA OOM (retryable on the client side) from other bugs.
        try:
            cuda_oom = isinstance(e, torch.cuda.OutOfMemoryError)
        except AttributeError:
            cuda_oom = False
        if cuda_oom:
            torch.cuda.empty_cache()
            return JSONResponse(  # type: ignore[return-value]
                status_code=503, content={"error": "oom"}
            )
        logger.exception("/detect error on %s", req_resolved.image_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=adapter.model_id,
        uptime_s=int(time.monotonic() - _started_at),
        image_root=str(IMAGE_ROOT),
        images_under_root=_count_images_under(IMAGE_ROOT),
    )


@app.get("/info", response_model=InfoResponse)
def info() -> InfoResponse:
    return InfoResponse(
        model=adapter.model_id,
        classes=adapter.classes,
        default_prompts=DEFAULT_PROMPTS,
        default_thresholds=DEFAULT_THRESHOLDS,
    )
