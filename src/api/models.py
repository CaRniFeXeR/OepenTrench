from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class Item(SQLModel, table=True):
    """Example table; all SQLModel tables live in this module."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=500, index=True)
    created_at: datetime


class ItemCreate(SQLModel):
    name: str = Field(max_length=500, min_length=1)


class ItemRead(SQLModel):
    id: int
    name: str
    created_at: datetime
