"""Add photoanalysis.gps_coordinates (GeoJSON Point JSON)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "004_photo_analysis_gps"
down_revision = "003_geojson_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("photoanalysis"):
        return
    columns = {col["name"] for col in inspector.get_columns("photoanalysis")}
    if "gps_coordinates" not in columns:
        op.add_column(
            "photoanalysis",
            sa.Column("gps_coordinates", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    pass
