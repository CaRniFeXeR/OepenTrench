from __future__ import annotations

from typing import Literal

from src.api.models import PhotoAnalysis, PhotoAnalysisRead, PhotoDocumentationCategory

CategoryField = Literal[
    "has_duct",
    "has_ruler",
    "is_in_domain",
    "has_gdpr_problems",
    "gps_matches_route",
]

_REVIEWER_ATTR: dict[CategoryField, str] = {
    "has_duct": "reviewer_has_duct",
    "has_ruler": "reviewer_has_ruler",
    "is_in_domain": "reviewer_is_in_domain",
    "has_gdpr_problems": "reviewer_has_gdpr_problems",
    "gps_matches_route": "reviewer_gps_matches_route",
}

_MISMATCH_FIELD_KEYS: dict[CategoryField, str] = {
    "has_duct": "duct",
    "has_ruler": "ruler",
    "is_in_domain": "domain",
    "has_gdpr_problems": "privacy",
    "gps_matches_route": "gps",
}


def compute_category(
    *,
    has_duct: bool,
    has_ruler: bool,
    is_in_domain: bool,
    has_gdpr_problems: bool,
    gps_matches_route: bool,
    is_duplicated: bool = False,
) -> PhotoDocumentationCategory:
    if is_duplicated or not gps_matches_route or not is_in_domain:
        return PhotoDocumentationCategory.red
    if (
        has_duct
        and has_ruler
        and is_in_domain
        and not has_gdpr_problems
        and gps_matches_route
    ):
        return PhotoDocumentationCategory.green
    return PhotoDocumentationCategory.yellow


def effective_is_duplicated(analysis: PhotoAnalysis) -> bool:
    if analysis.reviewer_is_duplicated is not None:
        return bool(analysis.reviewer_is_duplicated)
    return bool(analysis.is_duplicated)


def effective_bool(analysis: PhotoAnalysis, field: CategoryField) -> bool:
    reviewer_val = getattr(analysis, _REVIEWER_ATTR[field])
    if reviewer_val is not None:
        return bool(reviewer_val)
    return bool(getattr(analysis, field))


def effective_category(analysis: PhotoAnalysis) -> PhotoDocumentationCategory | None:
    if analysis.reviewer_override_category is not None:
        return analysis.reviewer_override_category
    if effective_is_duplicated(analysis):
        return PhotoDocumentationCategory.red
    return compute_category(
        has_duct=effective_bool(analysis, "has_duct"),
        has_ruler=effective_bool(analysis, "has_ruler"),
        is_in_domain=effective_bool(analysis, "is_in_domain"),
        has_gdpr_problems=effective_bool(analysis, "has_gdpr_problems"),
        gps_matches_route=effective_bool(analysis, "gps_matches_route"),
    )


def automated_category(analysis: PhotoAnalysis) -> PhotoDocumentationCategory:
    return compute_category(
        has_duct=analysis.has_duct,
        has_ruler=analysis.has_ruler,
        is_in_domain=analysis.is_in_domain,
        has_gdpr_problems=analysis.has_gdpr_problems,
        gps_matches_route=analysis.gps_matches_route,
        is_duplicated=analysis.is_duplicated,
    )


def _reviewer_disagrees_with_ai(analysis: PhotoAnalysis, field: CategoryField) -> bool:
    reviewer_attr = _REVIEWER_ATTR[field]
    reviewer_val = getattr(analysis, reviewer_attr)
    if reviewer_val is None:
        return False
    return bool(reviewer_val) != bool(getattr(analysis, field))


def ai_reviewer_mismatch(analysis: PhotoAnalysis) -> bool:
    if analysis.reviewed_at is None:
        return False
    if any(_reviewer_disagrees_with_ai(analysis, field) for field in _REVIEWER_ATTR):
        return True
    if (
        analysis.reviewer_override_category is not None
        and analysis.category is not None
        and analysis.reviewer_override_category != analysis.category
    ):
        return True
    return False


def mismatch_field_keys(analysis: PhotoAnalysis) -> list[str]:
    keys: list[str] = []
    for field, key in _MISMATCH_FIELD_KEYS.items():
        if _reviewer_disagrees_with_ai(analysis, field):
            keys.append(key)
    if (
        analysis.reviewer_override_category is not None
        and analysis.category is not None
        and analysis.reviewer_override_category != analysis.category
    ):
        keys.append("category")
    return keys


def photo_analysis_to_read(row: PhotoAnalysis) -> PhotoAnalysisRead:
    return PhotoAnalysisRead(
        asset_id=row.asset_id,
        is_in_domain=row.is_in_domain,
        has_white_paper=row.has_white_paper,
        has_ruler=row.has_ruler,
        estimated_depth=row.estimated_depth,
        has_duct=row.has_duct,
        estimate_number_of_ducts=row.estimate_number_of_ducts,
        has_gdpr_problems=row.has_gdpr_problems,
        is_duplicated=row.is_duplicated,
        category=row.category,
        gps_matches_route=row.gps_matches_route,
        date_valid=row.date_valid,
        is_false_call=row.is_false_call,
        reviewer_override_category=row.reviewer_override_category,
        reviewer_has_duct=row.reviewer_has_duct,
        reviewer_has_ruler=row.reviewer_has_ruler,
        reviewer_is_in_domain=row.reviewer_is_in_domain,
        reviewer_has_gdpr_problems=row.reviewer_has_gdpr_problems,
        reviewer_gps_matches_route=row.reviewer_gps_matches_route,
        reviewer_is_duplicated=row.reviewer_is_duplicated,
        reviewed_at=row.reviewed_at,
        gps_coordinates=row.gps_coordinates,
        created_at=row.created_at,
        updated_at=row.updated_at,
        effective_has_duct=effective_bool(row, "has_duct"),
        effective_has_ruler=effective_bool(row, "has_ruler"),
        effective_is_in_domain=effective_bool(row, "is_in_domain"),
        effective_has_gdpr_problems=effective_bool(row, "has_gdpr_problems"),
        effective_gps_matches_route=effective_bool(row, "gps_matches_route"),
        effective_is_duplicated=effective_is_duplicated(row),
        effective_category=effective_category(row),
    )


REVIEWER_CLEAR_ATTRS = (
    "reviewer_has_duct",
    "reviewer_has_ruler",
    "reviewer_is_in_domain",
    "reviewer_has_gdpr_problems",
    "reviewer_gps_matches_route",
    "reviewer_is_duplicated",
    "reviewer_override_category",
    "reviewed_at",
)
