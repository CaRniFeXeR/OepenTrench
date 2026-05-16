"""Runner — iterates a list of image paths through a Labeller and writes outputs.

Per-image: YOLO ``<stem>.txt`` + meta ``<stem>.json`` written atomically.
Per-run: ``run_manifest.json`` always written, even on interrupt or every-image failure.
Resume: a photo whose ``.txt`` AND ``.json`` both exist is skipped.

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §3, §6.2, §6.3, §6.4, §7, §8.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from tqdm import tqdm

from src.labelling.base import Detection, LabelOutput, Labeller, LabellerError
from src.labelling.config import LabellerConfig
from src.labelling.remote_labeller import MalformedResponseError

logger = logging.getLogger(__name__)


@dataclass
class _ErrorRecord:
    filename: str
    kind: str  # "image_error" | "labeller_error" | "malformed_response"
    message: str


@dataclass
class RunResult:
    run_dir: Path
    images_total: int
    images_completed: int
    images_skipped_resume: int
    images_failed: int
    wallclock_seconds: float
    latencies_ms: List[int] = field(default_factory=list)
    errors: List[_ErrorRecord] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.images_failed == 0


def _iso_utc(t: datetime) -> str:
    return t.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_state(repo_root: Path) -> Tuple[str, bool]:
    try:
        rev = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root, stderr=subprocess.DEVNULL,
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        rev = "unknown"
    try:
        dirty_out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=repo_root, stderr=subprocess.DEVNULL,
        ).decode().strip()
        dirty = bool(dirty_out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        dirty = False
    return rev, dirty


def _percentile(values: List[int], p: float) -> int:
    if not values:
        return 0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round(p * (len(s) - 1)))))
    return s[k]


def _format_yolo_line(det: Detection, classes: List[str]) -> str:
    try:
        cls_id = classes.index(det.cls)
    except ValueError:
        raise ValueError(
            f"detection class {det.cls!r} not in configured classes {classes!r}"
        )
    xc, yc, w, h = det.bbox
    return f"{cls_id} {xc:.4f} {yc:.4f} {w:.4f} {h:.4f}\n"


def _atomic_write_text(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content)
    os.replace(tmp, path)


def _build_meta(
    output: LabelOutput, run_id: str, model: str
) -> dict:
    return {
        "filename": output.filename,
        "image_size": list(output.image_size),
        "run_id": run_id,
        "model": model,
        "bboxes": [
            {"cls": d.cls, "bbox": list(d.bbox), "confidence": d.confidence}
            for d in output.detections
        ],
        "image_quality": output.image_quality,
        "rationale": output.rationale,
        "latency_ms": output.latency_ms,
    }


class _Interrupted(Exception):
    """Raised internally when SIGINT/SIGTERM fires; ensures manifest still writes."""


def _make_run_dir(out_root: Path, profile: str) -> Tuple[Path, str]:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run_id = f"{profile}_{ts}"
    run_dir = out_root / run_id
    (run_dir / "labels").mkdir(parents=True, exist_ok=True)
    (run_dir / "meta").mkdir(parents=True, exist_ok=True)
    return run_dir, run_id


def _is_resumable(labels_dir: Path, meta_dir: Path, stem: str) -> bool:
    return (labels_dir / f"{stem}.txt").is_file() and (meta_dir / f"{stem}.json").is_file()


def run(
    config: LabellerConfig,
    labeller: Labeller,
    image_paths: List[Path],
    out_root: Path,
    repo_root: Path,
    batches_selected: Optional[List[int]] = None,
    progress: bool = True,
) -> RunResult:
    """Label every image in ``image_paths`` serially under a fresh run dir.

    The runner always writes ``run_manifest.json`` — on normal completion, on
    every-image failure, and on SIGINT/SIGTERM. Resume skips photos whose
    ``.txt`` AND ``.json`` both already exist in the run dir.
    """
    run_dir, run_id = _make_run_dir(out_root, config.name)
    labels_dir = run_dir / "labels"
    meta_dir = run_dir / "meta"

    started_at = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    result = RunResult(
        run_dir=run_dir,
        images_total=len(image_paths),
        images_completed=0,
        images_skipped_resume=0,
        images_failed=0,
        wallclock_seconds=0.0,
    )

    interrupted = {"flag": False}

    def _on_signal(signum, _frame):
        logger.warning("received signal %d — draining and writing run_manifest.json", signum)
        interrupted["flag"] = True

    prior_int = signal.signal(signal.SIGINT, _on_signal)
    prior_term = signal.signal(signal.SIGTERM, _on_signal)

    try:
        iterator = image_paths
        pbar = tqdm(iterator, desc=f"label[{config.name}]", disable=not progress)
        for img_path in pbar:
            if interrupted["flag"]:
                raise _Interrupted()

            stem = img_path.stem
            if _is_resumable(labels_dir, meta_dir, stem):
                result.images_skipped_resume += 1
                continue

            try:
                output = labeller.label(img_path)
            except MalformedResponseError as e:
                logger.warning("malformed response on %s: %s", img_path.name, e)
                _atomic_write_text(labels_dir / f"{stem}.txt", "")
                stub_meta = {
                    "filename": img_path.name,
                    "image_size": [0, 0],
                    "run_id": run_id,
                    "model": config.model,
                    "bboxes": [],
                    "image_quality": "malformed_response",
                    "rationale": "",
                    "latency_ms": 0,
                }
                _atomic_write_text(
                    meta_dir / f"{stem}.json", json.dumps(stub_meta, indent=2) + "\n",
                )
                result.errors.append(
                    _ErrorRecord(img_path.name, "malformed_response", str(e))
                )
                continue
            except LabellerError as e:
                logger.warning("labeller error on %s: %s", img_path.name, e)
                result.images_failed += 1
                result.errors.append(
                    _ErrorRecord(img_path.name, "labeller_error", str(e))
                )
                continue
            except FileNotFoundError as e:
                logger.warning("image not found on %s: %s", img_path.name, e)
                result.images_failed += 1
                result.errors.append(
                    _ErrorRecord(img_path.name, "image_error", str(e))
                )
                continue

            try:
                yolo_lines = "".join(
                    _format_yolo_line(d, config.classes) for d in output.detections
                )
            except ValueError as e:
                logger.warning("bad detection on %s: %s", img_path.name, e)
                result.images_failed += 1
                result.errors.append(
                    _ErrorRecord(img_path.name, "labeller_error", str(e))
                )
                continue

            _atomic_write_text(labels_dir / f"{stem}.txt", yolo_lines)
            meta = _build_meta(output, run_id, config.model)
            _atomic_write_text(
                meta_dir / f"{stem}.json", json.dumps(meta, indent=2) + "\n",
            )

            result.images_completed += 1
            result.latencies_ms.append(output.latency_ms)

            if progress and result.latencies_ms:
                pbar.set_postfix(
                    p50=_percentile(result.latencies_ms, 0.5),
                    err=result.images_failed,
                    skip=result.images_skipped_resume,
                )

    except _Interrupted:
        pass  # fall through to manifest write
    finally:
        signal.signal(signal.SIGINT, prior_int)
        signal.signal(signal.SIGTERM, prior_term)
        result.wallclock_seconds = time.perf_counter() - t0
        _write_run_manifest(
            run_dir=run_dir,
            run_id=run_id,
            config=config,
            repo_root=repo_root,
            started_at=started_at,
            result=result,
            batches_selected=batches_selected or [],
        )

    return result


def _write_run_manifest(
    run_dir: Path,
    run_id: str,
    config: LabellerConfig,
    repo_root: Path,
    started_at: datetime,
    result: RunResult,
    batches_selected: List[int],
) -> None:
    git_rev, git_dirty = _git_state(repo_root)
    finished_at = datetime.now(timezone.utc)
    manifest = {
        "run_id": run_id,
        "profile": config.name,
        "config": config.model_dump(),
        "git_rev": git_rev,
        "git_dirty": git_dirty,
        "started_at": _iso_utc(started_at),
        "finished_at": _iso_utc(finished_at),
        "wallclock_seconds": round(result.wallclock_seconds, 3),
        "images_total": result.images_total,
        "images_completed": result.images_completed,
        "images_skipped_resume": result.images_skipped_resume,
        "images_failed": result.images_failed,
        "batches_selected": batches_selected,
        "latency_p50_ms": _percentile(result.latencies_ms, 0.5),
        "latency_p95_ms": _percentile(result.latencies_ms, 0.95),
        "errors": [asdict(e) for e in result.errors],
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
