"""Bootstrap schema: fresh DB via SQLModel metadata; existing DB gets additive project columns."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlmodel import SQLModel

revision = "001_bootstrap"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("project"):
        import src.api.models  # noqa: F401

        SQLModel.metadata.create_all(bind=bind)
        return

    columns = {col["name"] for col in inspector.get_columns("project")}
    if "region" not in columns:
        op.add_column("project", sa.Column("region", sa.String(length=128), nullable=True))
    if "updated_at" not in columns:
        op.add_column("project", sa.Column("updated_at", sa.DateTime(), nullable=True))
    if "photo_count" not in columns:
        op.add_column("project", sa.Column("photo_count", sa.Integer(), nullable=True))
    if "status" not in columns:
        op.add_column(
            "project",
            sa.Column(
                "status",
                sa.String(length=32),
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
        )


def downgrade() -> None:
    # SQLite column drops are version-dependent; not supported for typical dev rollback here.
    pass
