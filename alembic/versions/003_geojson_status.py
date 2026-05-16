"""Add project.geojson_status; backfill ready when both required GeoJSON suffixes exist."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "003_geojson_status"
down_revision = "002_photo_analysis"
branch_labels = None
depends_on = None

TRENCHES_SUFFIX = "trenches.geojson"
FCP_POLYGONS_SUFFIX = "fcp_polygons.geojson"


def _label_has_suffix(label: str, suffix: str) -> bool:
    return label.strip().lower().endswith(suffix)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    project_columns = {col["name"] for col in inspector.get_columns("project")}

    if "geojson_status" not in project_columns:
        op.add_column(
            "project",
            sa.Column(
                "geojson_status",
                sa.String(length=32),
                nullable=False,
                server_default=sa.text("'missing'"),
            ),
        )

    if not inspector.has_table("projectasset"):
        return

    rows = bind.execute(
        text(
            "SELECT project_id, original_label FROM projectasset "
            "WHERE kind = 'geojson'"
        )
    ).fetchall()

    by_project: dict[str, set[str]] = {}
    for project_id, original_label in rows:
        label = original_label or ""
        flags = by_project.setdefault(project_id, set())
        if _label_has_suffix(label, TRENCHES_SUFFIX):
            flags.add("trenches")
        if _label_has_suffix(label, FCP_POLYGONS_SUFFIX):
            flags.add("fcp_polygons")

    for project_id, flags in by_project.items():
        if flags >= {"trenches", "fcp_polygons"}:
            bind.execute(
                text(
                    "UPDATE project SET geojson_status = 'ready' WHERE id = :id"
                ),
                {"id": project_id},
            )


def downgrade() -> None:
    pass
