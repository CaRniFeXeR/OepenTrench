from __future__ import annotations

from sqlalchemy import and_, func, or_
from sqlmodel import Session, col, select

from src.api.helpers.photo_documentation_category import (
    mismatch_field_keys,
    photo_analysis_to_read,
)
from src.api.models import (
    AssetKind,
    OnlineLearningDisagreementsPage,
    OnlineLearningMismatchItemRead,
    OnlineLearningStatsRead,
    PhotoAnalysis,
    Project,
    ProjectAsset,
)


def _mismatch_condition():
    pa = PhotoAnalysis
    return or_(
        and_(
            col(pa.reviewer_has_duct).is_not(None),
            col(pa.reviewer_has_duct) != col(pa.has_duct),
        ),
        and_(
            col(pa.reviewer_has_ruler).is_not(None),
            col(pa.reviewer_has_ruler) != col(pa.has_ruler),
        ),
        and_(
            col(pa.reviewer_is_in_domain).is_not(None),
            col(pa.reviewer_is_in_domain) != col(pa.is_in_domain),
        ),
        and_(
            col(pa.reviewer_has_gdpr_problems).is_not(None),
            col(pa.reviewer_has_gdpr_problems) != col(pa.has_gdpr_problems),
        ),
        and_(
            col(pa.reviewer_gps_matches_route).is_not(None),
            col(pa.reviewer_gps_matches_route) != col(pa.gps_matches_route),
        ),
        and_(
            col(pa.reviewer_override_category).is_not(None),
            col(pa.category).is_not(None),
            col(pa.reviewer_override_category) != col(pa.category),
        ),
    )


def _base_join_statement():
    return (
        select(PhotoAnalysis, ProjectAsset, Project)
        .join(ProjectAsset, col(PhotoAnalysis.asset_id) == col(ProjectAsset.id))
        .join(Project, col(ProjectAsset.project_id) == col(Project.id))
        .where(ProjectAsset.kind == AssetKind.image)
    )


def _reviewed_condition():
    return col(PhotoAnalysis.reviewed_at).is_not(None)


def list_disagreements(
    session: Session,
    *,
    limit: int,
    offset: int,
) -> OnlineLearningDisagreementsPage:
    mismatch = _mismatch_condition()
    reviewed = _reviewed_condition()

    total_reviewed = session.exec(
        select(func.count())
        .select_from(PhotoAnalysis)
        .join(ProjectAsset, col(PhotoAnalysis.asset_id) == col(ProjectAsset.id))
        .where(ProjectAsset.kind == AssetKind.image)
        .where(reviewed)
    ).one()

    total_mismatch = session.exec(
        select(func.count())
        .select_from(PhotoAnalysis)
        .join(ProjectAsset, col(PhotoAnalysis.asset_id) == col(ProjectAsset.id))
        .where(ProjectAsset.kind == AssetKind.image)
        .where(reviewed)
        .where(mismatch)
    ).one()

    projects_with_mismatch = session.exec(
        select(func.count(func.distinct(col(ProjectAsset.project_id))))
        .select_from(PhotoAnalysis)
        .join(ProjectAsset, col(PhotoAnalysis.asset_id) == col(ProjectAsset.id))
        .where(ProjectAsset.kind == AssetKind.image)
        .where(reviewed)
        .where(mismatch)
    ).one()

    mismatch_rate = (
        float(total_mismatch) / float(total_reviewed) if total_reviewed > 0 else 0.0
    )

    page_statement = (
        _base_join_statement()
        .where(reviewed)
        .where(mismatch)
        .order_by(col(PhotoAnalysis.reviewed_at).desc())
        .offset(offset)
        .limit(limit)
    )
    rows = session.exec(page_statement).all()

    items: list[OnlineLearningMismatchItemRead] = []
    for analysis, asset, project in rows:
        reviewed_at = analysis.reviewed_at
        if reviewed_at is None:
            continue
        items.append(
            OnlineLearningMismatchItemRead(
                asset_id=asset.id,
                project_id=project.id,
                project_name=project.name,
                original_label=asset.original_label,
                created_at=asset.created_at,
                reviewed_at=reviewed_at,
                analysis=photo_analysis_to_read(analysis),
                mismatch_fields=mismatch_field_keys(analysis),
            )
        )

    stats = OnlineLearningStatsRead(
        total_reviewed=total_reviewed,
        total_mismatch=total_mismatch,
        mismatch_rate=mismatch_rate,
        projects_with_mismatch=projects_with_mismatch,
    )

    return OnlineLearningDisagreementsPage(
        items=items,
        total=total_mismatch,
        limit=limit,
        offset=offset,
        stats=stats,
    )
