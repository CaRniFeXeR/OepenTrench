#!/usr/bin/env python3
"""Seed the local DB with a dummy project using example GeoJSON and images."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from sqlmodel import Session, col, select

from scripts.seed_fixtures import (
    GEOJSON_BASE,
    SEED_SCENARIOS,
    build_seed_locations,
    expected_category_counts,
)
from scripts.seed_persist import persist_geojson_file, persist_image
from src.api.database import engine
from src.api.helpers.photo_documentation_category import automated_category
from src.api.helpers.time import utc_now
from src.api.models import (
    AssetKind,
    PhotoAnalysis,
    Project,
    ProjectAsset,
    ProjectStatus,
)
from src.api.services.project_service import create_project

DEFAULT_GEOJSON_DIR = REPO_ROOT / "data" / "example_geojson"
DEFAULT_IMAGE = REPO_ROOT / "data" / "example_img" / "1_IMG-20240813-WA0036.jpg"
EXAMPLE_IMAGE_STEM = "IMG-20240813-WA0036.jpg"

GEOJSON_FILES = (
    f"{GEOJSON_BASE}_Trenches.geojson",
    f"{GEOJSON_BASE}_FCP_Polygons.geojson",
)


def _upload_geojson(
    session: Session,
    *,
    project_id: str,
    geojson_dir: Path,
    filename: str,
) -> None:
    path = geojson_dir / filename
    if not path.is_file():
        raise FileNotFoundError(f"GeoJSON not found: {path}")
    persist_geojson_file(session, project_id=project_id, path=path)


def _upload_images(
    session: Session,
    *,
    project_id: str,
    image_path: Path,
    locations: list[dict],
) -> None:
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image_bytes = image_path.read_bytes()

    for index, scenario in enumerate(SEED_SCENARIOS, start=1):
        label = f"{index:02d}_{EXAMPLE_IMAGE_STEM}"
        gps = locations[scenario.location_index]
        asset = persist_image(
            session,
            project_id=project_id,
            filename=label,
            content=image_bytes,
        )
        fields = scenario.to_analysis_fields(gps)
        now = utc_now()
        row = PhotoAnalysis(
            asset_id=asset.id,
            created_at=now,
            updated_at=now,
            **fields,
        )
        row.category = automated_category(row)
        session.add(row)
        session.commit()


def _category_counts(session: Session, project_id: str) -> Counter[str]:
    statement = (
        select(PhotoAnalysis)
        .join(ProjectAsset, col(ProjectAsset.id) == col(PhotoAnalysis.asset_id))
        .where(ProjectAsset.project_id == project_id)
        .where(ProjectAsset.kind == AssetKind.image)
    )
    counts: Counter[str] = Counter()
    for row in session.exec(statement).all():
        cat = row.category or automated_category(row)
        counts[cat.value if hasattr(cat, "value") else str(cat)] += 1
    return counts


def seed_dummy_project(
    *,
    geojson_dir: Path,
    image_path: Path,
) -> tuple[str, str, Counter[str]]:
    locations = build_seed_locations(geojson_dir)
    if len(locations) < len(SEED_SCENARIOS):
        raise ValueError(
            f"need {len(SEED_SCENARIOS)} GPS locations, got {len(locations)}"
        )

    with Session(engine) as session:
        now = utc_now()
        project = create_project(
            session,
            name=f"Seed CLP20417A {now:%Y-%m-%d %H:%M}",
            region="Maria Rain",
            project_date=date(2024, 8, 13),
        )
        project_id = project.id

        for filename in GEOJSON_FILES:
            _upload_geojson(
                session,
                project_id=project_id,
                geojson_dir=geojson_dir,
                filename=filename,
            )

        _upload_images(
            session,
            project_id=project_id,
            image_path=image_path,
            locations=locations,
        )

        project = session.get(Project, project_id)
        if project is None:
            raise RuntimeError("project disappeared after seeding")
        project.photo_count = len(SEED_SCENARIOS)
        project.status = ProjectStatus.complete
        project.updated_at = utc_now()
        session.add(project)
        session.commit()

        counts = _category_counts(session, project_id)
        return project_id, project.name, counts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--geojson-dir",
        type=Path,
        default=DEFAULT_GEOJSON_DIR,
        help=f"directory with example GeoJSON (default: {DEFAULT_GEOJSON_DIR})",
    )
    parser.add_argument(
        "--image-path",
        type=Path,
        default=DEFAULT_IMAGE,
        help=f"JPEG to duplicate for each photo (default: {DEFAULT_IMAGE})",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    expected = expected_category_counts()

    try:
        project_id, name, counts = seed_dummy_project(
            geojson_dir=args.geojson_dir.resolve(),
            image_path=args.image_path.resolve(),
        )
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1

    print(f"Seeded project: {name}")
    print(f"  project_id: {project_id}")
    print(f"  photos: {sum(counts.values())}")
    print(
        "  categories: "
        f"green={counts.get('green', 0)}, "
        f"yellow={counts.get('yellow', 0)}, "
        f"red={counts.get('red', 0)}"
    )
    print(
        "  expected: "
        f"green={expected['green']}, "
        f"yellow={expected['yellow']}, "
        f"red={expected['red']}"
    )
    print(f"  open: /projects/{project_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
