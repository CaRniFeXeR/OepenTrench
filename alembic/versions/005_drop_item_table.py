"""Drop unused item table from bootstrap scaffolding."""

from alembic import op
from sqlalchemy import inspect

revision = "005_drop_item_table"
down_revision = "004_photo_analysis_gps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("item"):
        op.drop_table("item")


def downgrade() -> None:
    pass
