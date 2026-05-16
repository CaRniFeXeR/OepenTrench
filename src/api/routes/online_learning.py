from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from src.api.database import get_session
from src.api.helpers.pagination import clamp_limit, clamp_offset
from src.api.models import OnlineLearningDisagreementsPage
from src.api.services import online_learning_service

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
