from __future__ import annotations

import logging
import subprocess
import uuid
from datetime import timezone
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import func
from sqlmodel import Session, col, select

from src.api.database import engine
from src.api.helpers.time import utc_now
from src.api.models import (
    OnlineLearningTrainingRun,
    OnlineLearningTrainingRunRead,
    OnlineLearningTrainingRunsPage,
    OnlineLearningTrainingStatus,
)
from src.api.services.online_learning_export_service import export_mismatch_photos

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LOG_DIR = _REPO_ROOT / "logs" / "online-learning"
_ERROR_TAIL_CHARS = 2000


def _training_log_path(run_id: str) -> Path:
    return _LOG_DIR / f"{run_id}.log"


def _log_relpath(run_id: str) -> str:
    return f"online-learning/{run_id}.log"


def _run_to_read(row: OnlineLearningTrainingRun) -> OnlineLearningTrainingRunRead:
    return OnlineLearningTrainingRunRead.model_validate(row)


def list_trainings(
    session: Session,
    *,
    limit: int,
    offset: int,
) -> OnlineLearningTrainingRunsPage:
    total = session.exec(select(func.count()).select_from(OnlineLearningTrainingRun)).one()
    rows = session.exec(
        select(OnlineLearningTrainingRun)
        .order_by(col(OnlineLearningTrainingRun.started_at).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return OnlineLearningTrainingRunsPage(
        items=[_run_to_read(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def start_training(session: Session, background_tasks: BackgroundTasks) -> OnlineLearningTrainingRunRead:
    running = session.exec(
        select(OnlineLearningTrainingRun).where(
            col(OnlineLearningTrainingRun.status) == OnlineLearningTrainingStatus.running,
        )
    ).first()
    if running is not None:
        raise HTTPException(status_code=409, detail="training already in progress")

    run_id = str(uuid.uuid4())
    row = OnlineLearningTrainingRun(
        id=run_id,
        status=OnlineLearningTrainingStatus.running,
        photo_count=0,
        started_at=utc_now(),
        log_relpath=_log_relpath(run_id),
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    background_tasks.add_task(run_training_job, run_id)
    return _run_to_read(row)


def _append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(message)
        if not message.endswith("\n"):
            fh.write("\n")


def _finish_run(
    session: Session,
    row: OnlineLearningTrainingRun,
    *,
    status: OnlineLearningTrainingStatus,
    error_message: str | None = None,
) -> None:
    now = utc_now()
    row.status = status
    row.finished_at = now
    started = row.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    row.duration_sec = max(0, int((now - started).total_seconds()))
    if error_message is not None:
        row.error_message = error_message[:_ERROR_TAIL_CHARS]
    session.add(row)
    session.commit()


def _read_log_tail(log_path: Path) -> str:
    if not log_path.is_file():
        return "training failed (no log file)"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= _ERROR_TAIL_CHARS:
        return text.strip() or "training failed"
    return text[-_ERROR_TAIL_CHARS:].strip()


def run_training_job(run_id: str) -> None:
    log_path = _training_log_path(run_id)
    _append_log(log_path, f"=== training run {run_id} started ===")

    with Session(engine) as session:
        row = session.get(OnlineLearningTrainingRun, run_id)
        if row is None:
            logger.error("training run not found run_id=%s", run_id)
            return

        try:
            _append_log(log_path, "--- phase: export mismatch photos ---")
            export_result = export_mismatch_photos(session)
            row.photo_count = export_result.photo_count
            session.add(row)
            session.commit()
            _append_log(
                log_path,
                f"exported photo_count={export_result.photo_count} "
                f"classification={export_result.classification_copied} "
                f"detection={export_result.detection_copied}",
            )

            if export_result.photo_count == 0:
                _finish_run(
                    session,
                    row,
                    status=OnlineLearningTrainingStatus.failed,
                    error_message="no mismatch photos to export",
                )
                _append_log(log_path, "aborted: no mismatch photos")
                return

            scripts = [
                ("yolo", ["uv", "run", "python", "scripts/train_yolo.py"]),
                (
                    "classifier",
                    ["uv", "run", "python", "scripts/train_trench_classifier.py"],
                ),
            ]
            for phase_name, cmd in scripts:
                _append_log(log_path, f"--- phase: {phase_name} ---")
                _append_log(log_path, f"$ {' '.join(cmd)}")
                with log_path.open("a", encoding="utf-8") as log_fh:
                    proc = subprocess.run(
                        cmd,
                        cwd=str(_REPO_ROOT),
                        stdout=log_fh,
                        stderr=subprocess.STDOUT,
                        check=False,
                    )
                if proc.returncode != 0:
                    msg = _read_log_tail(log_path)
                    _finish_run(
                        session,
                        row,
                        status=OnlineLearningTrainingStatus.failed,
                        error_message=f"{phase_name} failed (exit {proc.returncode}): {msg}",
                    )
                    _append_log(log_path, f"=== training run {run_id} failed ===")
                    return

            _finish_run(session, row, status=OnlineLearningTrainingStatus.completed)
            _append_log(log_path, f"=== training run {run_id} completed ===")
        except Exception as exc:
            logger.exception("training run failed run_id=%s", run_id)
            session.rollback()
            row = session.get(OnlineLearningTrainingRun, run_id)
            if row is not None:
                tail = _read_log_tail(log_path)
                _finish_run(
                    session,
                    row,
                    status=OnlineLearningTrainingStatus.failed,
                    error_message=f"{exc}: {tail}",
                )
            _append_log(log_path, f"=== training run {run_id} failed: {exc} ===")
