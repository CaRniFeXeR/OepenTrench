"""HTTP client to a VM-hosted detection server.

Translates local image paths to the VM's filesystem layout, posts to ``/detect``,
parses the response into ``LabelOutput``. Implements the retry/backoff policy
from spec §8.

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §3, §5.1, §5.5, §8.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from src.labelling.base import Detection, LabelOutput, Labeller, LabellerError
from src.labelling.config import LabellerConfig

logger = logging.getLogger(__name__)


class MalformedResponseError(LabellerError):
    """Server returned a 2xx response that didn't parse to the expected schema.

    The runner converts this to an empty detection list per spec §8 instead of
    skipping the image — empty output unblocks resume, while the error still
    lands in ``run_manifest.errors[]``.
    """


class ServerUnreachableError(LabellerError):
    """``/health`` failed at run start. Maps to exit code 3 per spec §7."""


_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _to_remote_path(image_path: Path, config: LabellerConfig) -> str:
    """Translate a local image path to the absolute VM path the server expects.

    The image must live under ``local_image_root``; the remainder is appended
    to ``remote_image_root``.
    """
    local_root = Path(config.local_image_root).resolve()
    abs_local = image_path.resolve()
    try:
        rel = abs_local.relative_to(local_root)
    except ValueError as e:
        raise LabellerError(
            f"image_path {abs_local} is not under local_image_root {local_root}"
        ) from e
    return str(Path(config.remote_image_root) / rel)


def _backoff_seconds(attempt: int) -> float:
    """Exp backoff: 1 s → 2 s → 4 s. ``attempt`` is 0-indexed."""
    return 2.0 ** attempt


class RemoteVlmLabeller(Labeller):
    """``mode: remote-vlm`` — httpx client to the VM detection server."""

    def __init__(self, config: LabellerConfig, client: Optional[httpx.Client] = None) -> None:
        self.config = config
        self._client = client or httpx.Client(
            base_url=config.endpoint,
            timeout=config.timeout_seconds,
        )

    @property
    def name(self) -> str:
        return self.config.model

    def health_check(self) -> bool:
        """``GET /health``; True iff 200 and JSON ``{"status":"ok"}``.

        Does not raise on connect/timeout — returns False so the caller can
        decide whether to abort (exit 3) or continue.
        """
        try:
            r = self._client.get("/health")
        except httpx.HTTPError as e:
            logger.error("health check failed: %s", e)
            return False
        if r.status_code != 200:
            logger.error("health check returned %d: %s", r.status_code, r.text[:200])
            return False
        try:
            body = r.json()
        except ValueError:
            logger.error("health check body not JSON")
            return False
        return body.get("status") == "ok"

    def label(self, image_path: Path) -> LabelOutput:
        remote_path = _to_remote_path(image_path, self.config)
        payload = {
            "image_path": remote_path,
            "prompts": dict(self.config.prompts),
            "per_class_threshold": dict(self.config.per_class_threshold),
            "iou_nms": self.config.iou_nms,
            "max_detections_per_class": self.config.max_detections_per_class,
        }

        last_exc: Optional[Exception] = None
        for attempt in range(self.config.retries + 1):
            t0 = time.perf_counter()
            try:
                r = self._client.post("/detect", json=payload)
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                last_exc = e
                if attempt < self.config.retries:
                    sleep_for = _backoff_seconds(attempt)
                    logger.warning(
                        "transient error on %s (attempt %d/%d): %s — retrying in %.1fs",
                        image_path.name, attempt + 1, self.config.retries + 1, e, sleep_for,
                    )
                    time.sleep(sleep_for)
                    continue
                raise LabellerError(
                    f"transport error after {attempt + 1} attempts: {e}"
                ) from e

            wall_ms = int((time.perf_counter() - t0) * 1000)

            if r.status_code in _RETRYABLE_STATUS:
                last_exc = httpx.HTTPStatusError(
                    f"{r.status_code} {r.reason_phrase}: {r.text[:200]}",
                    request=r.request,
                    response=r,
                )
                if attempt < self.config.retries:
                    sleep_for = _backoff_seconds(attempt)
                    logger.warning(
                        "retryable %d on %s (attempt %d/%d) — retrying in %.1fs",
                        r.status_code, image_path.name, attempt + 1,
                        self.config.retries + 1, sleep_for,
                    )
                    time.sleep(sleep_for)
                    continue
                raise LabellerError(
                    f"server returned {r.status_code} after {attempt + 1} attempts"
                ) from last_exc

            if r.status_code != 200:
                raise LabellerError(
                    f"server returned {r.status_code}: {r.text[:200]}"
                )

            return self._parse_response(r.json(), image_path, wall_ms)

        # Defensive — loop above either returned or raised.
        raise LabellerError(f"retry loop exited without result: last={last_exc}")

    def _parse_response(
        self, body: Dict[str, Any], image_path: Path, wall_ms: int
    ) -> LabelOutput:
        try:
            raw_detections: List[Dict[str, Any]] = body["detections"]
            image_size = tuple(body["image_size"])
            latency_ms = int(body.get("latency_ms", wall_ms))
        except (KeyError, TypeError, ValueError) as e:
            raise MalformedResponseError(
                f"missing or wrong-shape required field in /detect response: {e}"
            ) from e

        if len(image_size) != 2:
            raise MalformedResponseError(
                f"image_size must be [w, h], got {body.get('image_size')!r}"
            )

        detections: List[Detection] = []
        valid_classes = set(self.config.classes)
        for d in raw_detections:
            try:
                cls = d["cls"]
                bbox = tuple(d["bbox"])
                conf = float(d["confidence"])
            except (KeyError, TypeError, ValueError) as e:
                raise MalformedResponseError(
                    f"bad detection entry {d!r}: {e}"
                ) from e
            if cls not in valid_classes:
                logger.warning(
                    "dropping detection with unknown class %r on %s", cls, image_path.name,
                )
                continue
            if len(bbox) != 4 or any(not (0.0 <= v <= 1.0) for v in bbox):
                raise MalformedResponseError(
                    f"bbox out of [0,1] on {image_path.name}: {bbox!r}"
                )
            if not (0.0 <= conf <= 1.0):
                raise MalformedResponseError(
                    f"confidence out of [0,1] on {image_path.name}: {conf}"
                )
            detections.append(Detection(cls=cls, bbox=bbox, confidence=conf))

        return LabelOutput(
            filename=image_path.name,
            image_size=image_size,  # type: ignore[arg-type]
            detections=detections,
            rationale="",
            image_quality="ok",
            latency_ms=latency_ms,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RemoteVlmLabeller":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
