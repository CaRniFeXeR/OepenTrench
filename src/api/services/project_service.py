from __future__ import annotations

from datetime import date
from typing import Optional

from sqlmodel import Session, col, select

from src.api.helpers.time import utc_now
from src.api.ids import new_nanoid
from src.api.helpers.photo_documentation_category import photo_analysis_to_read
from src.api.models import (
    AssetKind,
    PhotoAnalysis,
    Project,
    ProjectAsset,
    ProjectAssetRead,
)


def create_project(
    session: Session,
    *,
    name: str,
    region: str | None = None,
    project_date: date | None = None,
) -> Project:
    region_norm = region.strip() if region else None
    if region_norm == "":
        region_norm = None
    project = Project(
        id=new_nanoid(),
        name=name.strip(),
        created_at=utc_now(),
        region=region_norm,
        project_date=project_date,
    )
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
        .order_by(col(ProjectAsset.created_at))
    )
    assets = list(session.exec(statement).all())
    return project, assets


def photo_analyses_by_asset_ids(
    session: Session, asset_ids: list[str]
) -> dict[str, PhotoAnalysis]:
    if not asset_ids:
        return {}
    statement = select(PhotoAnalysis).where(col(PhotoAnalysis.asset_id).in_(asset_ids))
    return {row.asset_id: row for row in session.exec(statement).all()}


def _project_asset_to_read(
    asset: ProjectAsset, analysis: PhotoAnalysis | None
) -> ProjectAssetRead:
    row = analysis if asset.kind == AssetKind.image else None
    return ProjectAssetRead(
        id=asset.id,
        project_id=asset.project_id,
        kind=asset.kind,
        original_label=asset.original_label,
        stored_relpath=asset.stored_relpath,
        created_at=asset.created_at,
        analysis=photo_analysis_to_read(row) if row is not None else None,
    )


def project_assets_reads(session: Session, assets: list[ProjectAsset]) -> list[ProjectAssetRead]:
    analyses = photo_analyses_by_asset_ids(session, [a.id for a in assets])
    return [_project_asset_to_read(a, analyses.get(a.id)) for a in assets]


def project_asset_read(session: Session, asset: ProjectAsset) -> ProjectAssetRead:
    analysis: PhotoAnalysis | None = None
    if asset.kind == AssetKind.image:
        analysis = session.get(PhotoAnalysis, asset.id)
    return _project_asset_to_read(asset, analysis)


def update_project(session: Session, project_id: str, *, name: str) -> Optional[Project]:
    project = session.get(Project, project_id)
    if project is None:
        return None
    project.name = name.strip()
    project.updated_at = utc_now()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def list_projects(session: Session, *, limit: int, offset: int) -> list[Project]:
    statement = (
        select(Project)
        .order_by(Project.created_at.asc())  # type: ignore[arg-type,attr-defined]
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(statement).all())
