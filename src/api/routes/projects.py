from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from src.api.database import get_session
from src.api.helpers.pagination import clamp_limit, clamp_offset
from src.api.models import (
    MapPhotosRead,
    PhotoAnalysisReviewUpdate,
    ProjectAsset,
    ProjectAssetRead,
    ProjectCreate,
    ProjectDetailRead,
    ProjectRead,
    ProjectUpdate,
)
from src.api.services import project_service
from src.api.services import photo_analysis_service
from src.api.services.map_photos_service import list_map_photo_markers
from src.api.services.project_asset_service import (
    PayloadTooLarge,
    load_merged_project_geojson,
    save_project_geojson,
    save_project_image,
)
from src.api.services.project_image_service import resolve_project_image_path

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
    project = project_service.create_project(
        session,
        name=payload.name,
        region=payload.region,
        project_date=payload.project_date,
    )
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


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project_route(
    project_id: str,
    payload: ProjectUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectRead:
    project = project_service.update_project(session, project_id, name=payload.name)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetailRead)
def read_project(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectDetailRead:
    result = project_service.get_project_with_assets(session, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="project not found")
    project, assets = result
    reads = project_service.project_assets_reads(session, assets)
    return ProjectDetailRead(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        region=project.region,
        updated_at=project.updated_at,
        photo_count=project.photo_count,
        status=project.status,
        geojson_status=project.geojson_status,
        project_date=project.project_date,
        assets=reads,
    )


@router.get("/{project_id}/geojson")
def read_project_geojson(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    try:
        return load_merged_project_geojson(session, project_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="project not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/map-photos", response_model=MapPhotosRead)
def read_project_map_photos(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> MapPhotosRead:
    try:
        photos = list_map_photo_markers(session, project_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="project not found") from None
    return MapPhotosRead(photos=photos)


@router.get("/{project_id}/images/{asset_id}/content")
def read_project_image_content(
    project_id: str,
    asset_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> FileResponse:
    try:
        _asset, abs_path, media_type = resolve_project_image_path(
            session,
            project_id=project_id,
            asset_id=asset_id,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FileResponse(abs_path, media_type=media_type)


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
    return project_service.project_asset_read(session, asset)


@router.post(
    "/{project_id}/images/{asset_id}/analyze",
    response_model=ProjectAssetRead,
)
def analyze_project_image(
    project_id: str,
    asset_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectAssetRead:
    try:
        photo_analysis_service.analyze_image_asset(
            session,
            project_id=project_id,
            asset_id=asset_id,
        )
        session.commit()
    except LookupError:
        raise HTTPException(status_code=404, detail="not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")
    return project_service.project_asset_read(session, asset)


@router.patch(
    "/{project_id}/images/{asset_id}/analysis",
    response_model=ProjectAssetRead,
)
def review_project_image_analysis(
    project_id: str,
    asset_id: str,
    payload: PhotoAnalysisReviewUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectAssetRead:
    try:
        photo_analysis_service.review_image_analysis(
            session,
            project_id=project_id,
            asset_id=asset_id,
            payload=payload,
        )
        session.commit()
    except LookupError:
        raise HTTPException(status_code=404, detail="not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")
    return project_service.project_asset_read(session, asset)


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
    return project_service.project_asset_read(session, asset)
