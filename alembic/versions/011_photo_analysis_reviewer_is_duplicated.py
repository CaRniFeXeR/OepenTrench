"""Add reviewer_is_duplicated to photoanalysis."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "011_reviewer_is_duplicated"
down_revision = "010_fcp_coverage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("photoanalysis"):
        return
    columns = {col["name"] for col in inspector.get_columns("photoanalysis")}
    if "reviewer_is_duplicated" not in columns:
        op.add_column(
            "photoanalysis",
            sa.Column("reviewer_is_duplicated", sa.Boolean(), nullable=True),
        )


def downgrade() -> None:
    pass
