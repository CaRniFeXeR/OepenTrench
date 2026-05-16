"""Drop has_sand_bedding and has_pipe_end_seal from photoanalysis."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "006_drop_sand_seal"
down_revision = "005_drop_item_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("photoanalysis"):
        return
    columns = {col["name"] for col in inspector.get_columns("photoanalysis")}
    if "has_sand_bedding" in columns:
        op.drop_column("photoanalysis", "has_sand_bedding")
    if "has_pipe_end_seal" in columns:
        op.drop_column("photoanalysis", "has_pipe_end_seal")


def downgrade() -> None:
    pass
