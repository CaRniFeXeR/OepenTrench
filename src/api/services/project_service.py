from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from src.api.helpers.time import utc_now
from src.api.ids import new_nanoid
from src.api.models import Project, ProjectAsset


def create_project(session: Session, *, name: str) -> Project:
    project = Project(id=new_nanoid(), name=name.strip(), created_at=utc_now())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def get_project(session: Session, project_id: str) -> Optional[Project]:
    return session.get(Project, project_id)


def get_project_with_assets(
    session: Session, project_id: str
) -> Optional[tuple[Project, list[ProjectAsset]]]:
    project = session.get(Project, project_id)
    if project is None:
        return None
    statement = (
        select(ProjectAsset)
        .where(ProjectAsset.project_id == project_id)
        .order_by(ProjectAsset.created_at)
    )
    assets = list(session.exec(statement).all())
    return project, assets


def list_projects(session: Session, *, limit: int, offset: int) -> list[Project]:
    statement = select(Project).order_by(Project.created_at).offset(offset).limit(limit)
    return list(session.exec(statement).all())
