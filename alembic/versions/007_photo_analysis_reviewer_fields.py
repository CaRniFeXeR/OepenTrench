"""Add reviewer field overrides and reviewed_at to photoanalysis."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "007_reviewer_fields"
down_revision = "006_drop_sand_seal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("photoanalysis"):
        return
    columns = {col["name"] for col in inspector.get_columns("photoanalysis")}
    if "reviewer_has_duct" not in columns:
        op.add_column("photoanalysis", sa.Column("reviewer_has_duct", sa.Boolean(), nullable=True))
    if "reviewer_has_ruler" not in columns:
        op.add_column("photoanalysis", sa.Column("reviewer_has_ruler", sa.Boolean(), nullable=True))
    if "reviewer_is_in_domain" not in columns:
        op.add_column("photoanalysis", sa.Column("reviewer_is_in_domain", sa.Boolean(), nullable=True))
    if "reviewer_has_gdpr_problems" not in columns:
        op.add_column(
            "photoanalysis", sa.Column("reviewer_has_gdpr_problems", sa.Boolean(), nullable=True)
        )
    if "reviewer_gps_matches_route" not in columns:
        op.add_column(
            "photoanalysis", sa.Column("reviewer_gps_matches_route", sa.Boolean(), nullable=True)
        )
    if "reviewed_at" not in columns:
        op.add_column("photoanalysis", sa.Column("reviewed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    pass
