"""Add hash_sha256 to projectasset."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "008_project_asset_hash"
down_revision = "007_reviewer_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("projectasset"):
        return
    columns = {col["name"] for col in inspector.get_columns("projectasset")}
    if "hash_sha256" not in columns:
        # Sentinel for existing rows (64 hex chars); SQLite requires a default for NOT NULL adds.
        op.add_column(
            "projectasset",
            sa.Column(
                "hash_sha256",
                sa.String(length=64),
                nullable=False,
                server_default=sa.text(
                    "'0000000000000000000000000000000000000000000000000000000000000000'"
                ),
            ),
        )


def downgrade() -> None:
    pass
