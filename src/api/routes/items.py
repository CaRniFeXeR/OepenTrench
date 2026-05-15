from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from src.api.database import get_session
from src.api.helpers.pagination import clamp_limit, clamp_offset
from src.api.models import ItemCreate, ItemRead
from src.api.services import item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemRead)
def create_item(
    payload: ItemCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ItemRead:
    item = item_service.create_item(session, name=payload.name)
    return ItemRead.model_validate(item)


@router.get("", response_model=list[ItemRead])
def list_items(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ItemRead]:
    lim = clamp_limit(limit)
    off = clamp_offset(offset)
    rows = item_service.list_items(session, limit=lim, offset=off)
    return [ItemRead.model_validate(r) for r in rows]
