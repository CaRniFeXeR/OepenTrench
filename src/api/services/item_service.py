from __future__ import annotations

from sqlmodel import Session, select

from src.api.helpers.time import utc_now
from src.api.models import Item


def create_item(session: Session, *, name: str) -> Item:
    item = Item(name=name.strip(), created_at=utc_now())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_items(session: Session, *, limit: int, offset: int) -> list[Item]:
    statement = select(Item).order_by(Item.id).offset(offset).limit(limit)
    return list(session.exec(statement).all())
