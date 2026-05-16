"""Add onlinelearningtrainingrun table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "009_online_learning_training"
down_revision = "008_project_asset_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("onlinelearningtrainingrun"):
        return
    op.create_table(
        "onlinelearningtrainingrun",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("photo_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(length=2048), nullable=True),
        sa.Column("log_relpath", sa.String(length=256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("onlinelearningtrainingrun"):
        op.drop_table("onlinelearningtrainingrun")
