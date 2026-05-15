"""Add photoanalysis table and project.project_date."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "002_photo_analysis"
down_revision = "001_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    project_columns = {col["name"] for col in inspector.get_columns("project")}

    if not inspector.has_table("photoanalysis"):
        op.create_table(
            "photoanalysis",
            sa.Column("asset_id", sa.String(length=64), nullable=False),
            sa.Column("is_in_domain", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("has_white_paper", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("has_ruler", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("estimated_depth", sa.Float(), nullable=True),
            sa.Column("has_duct", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("estimate_number_of_ducts", sa.Integer(), nullable=True),
            sa.Column("has_gdpr_problems", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("is_duplicated", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("category", sa.String(length=32), nullable=True),
            sa.Column("has_sand_bedding", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("has_pipe_end_seal", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("gps_matches_route", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("date_valid", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("is_false_call", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("reviewer_override_category", sa.String(length=32), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["asset_id"], ["projectasset.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("asset_id"),
        )

    if "project_date" not in project_columns:
        op.add_column("project", sa.Column("project_date", sa.Date(), nullable=True))


def downgrade() -> None:
    pass
