from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlmodel import Session

from src.api.database import get_session
from src.api.helpers.pagination import clamp_limit, clamp_offset
from src.api.models import (
    ProjectAssetRead,
    ProjectCreate,
    ProjectDetailRead,
    ProjectRead,
)
from src.api.services import project_service
from src.api.services.project_asset_service import (
    PayloadTooLarge,
    save_project_geojson,
    save_project_image,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _payload_too_large_response(exc: PayloadTooLarge) -> HTTPException:
    return HTTPException(
        status_code=413,
        detail=f"file too large (max {exc.max_bytes} bytes)",
    )


@router.post("", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectRead:
    project = project_service.create_project(session, name=payload.name, region=payload.region)
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectRead])
def list_projects_route(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProjectRead]:
    lim = clamp_limit(limit)
    off = clamp_offset(offset)
    rows = project_service.list_projects(session, limit=lim, offset=off)
    return [ProjectRead.model_validate(r) for r in rows]


@router.get("/{project_id}", response_model=ProjectDetailRead)
def read_project(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectDetailRead:
    result = project_service.get_project_with_assets(session, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="project not found")
    project, assets = result
    reads = [ProjectAssetRead.model_validate(asset) for asset in assets]
    return ProjectDetailRead(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        region=project.region,
        updated_at=project.updated_at,
        photo_count=project.photo_count,
        status=project.status,
        assets=reads,
    )


@router.post("/{project_id}/images", response_model=ProjectAssetRead)
def upload_project_image(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File(...)],
    label: Annotated[Optional[str], Form()] = None,
) -> ProjectAssetRead:
    filename = file.filename or "upload.bin"
    original_label = ((label if label is not None else filename).strip()) or filename
    try:
        asset = save_project_image(
            session,
            project_id=project_id,
            upload_filename=filename,
            original_label=original_label,
            stream=file.file,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="project not found") from None
    except PayloadTooLarge as exc:
        raise _payload_too_large_response(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ProjectAssetRead.model_validate(asset)


@router.post("/{project_id}/geojson", response_model=ProjectAssetRead)
def upload_project_geojson(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File(...)],
    label: Annotated[Optional[str], Form()] = None,
) -> ProjectAssetRead:
    filename = file.filename or "upload.json"
    original_label = ((label if label is not None else filename).strip()) or filename
    try:
        asset = save_project_geojson(
            session,
            project_id=project_id,
            upload_filename=filename,
            original_label=original_label,
            stream=file.file,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="project not found") from None
    except PayloadTooLarge as exc:
        raise _payload_too_large_response(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ProjectAssetRead.model_validate(asset)
