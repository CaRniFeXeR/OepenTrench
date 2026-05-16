from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlmodel import Session

from src.api.database import get_session
from src.api.helpers.pagination import clamp_limit, clamp_offset
from src.api.models import (
    OnlineLearningDisagreementsPage,
    OnlineLearningTrainingRunRead,
    OnlineLearningTrainingRunsPage,
)
from src.api.services import online_learning_service
from src.api.services import online_learning_training_service

router = APIRouter(prefix="/online-learning", tags=["online-learning"])


@router.get("/disagreements", response_model=OnlineLearningDisagreementsPage)
def list_disagreements(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OnlineLearningDisagreementsPage:
    lim = clamp_limit(limit)
    off = clamp_offset(offset)
    return online_learning_service.list_disagreements(session, limit=lim, offset=off)


@router.get("/trainings", response_model=OnlineLearningTrainingRunsPage)
def list_trainings(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OnlineLearningTrainingRunsPage:
    lim = clamp_limit(limit)
    off = clamp_offset(offset)
    return online_learning_training_service.list_trainings(session, limit=lim, offset=off)


@router.post(
    "/trainings",
    response_model=OnlineLearningTrainingRunRead,
    status_code=status.HTTP_201_CREATED,
)
def start_training(
    session: Annotated[Session, Depends(get_session)],
    background_tasks: BackgroundTasks,
) -> OnlineLearningTrainingRunRead:
    return online_learning_training_service.start_training(session, background_tasks)
