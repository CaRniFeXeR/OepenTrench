"""Add FCP trench coverage persistence tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "010_fcp_coverage"
down_revision = "009_online_learning_training"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("projectfcpcoverage"):
        return

    op.create_table(
        "projectfcpcoverage",
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_table(
        "fcpcoveragesummary",
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("fcp_id", sa.String(length=128), nullable=False),
        sa.Column("fcp_code", sa.String(length=128), nullable=True),
        sa.Column("fcp_label", sa.String(length=500), nullable=True),
        sa.Column("compartment_count", sa.Integer(), nullable=False),
        sa.Column("covered_count", sa.Integer(), nullable=False),
        sa.Column("coverage_ratio", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("project_id", "fcp_id"),
    )
    op.create_table(
        "fcpcoveragecompartment",
        sa.Column("id", sa.String(length=256), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("fcp_id", sa.String(length=128), nullable=False),
        sa.Column("covered", sa.Boolean(), nullable=False),
        sa.Column("length_m", sa.Float(), nullable=False),
        sa.Column("center", sa.JSON(), nullable=False),
        sa.Column("geometry", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fcpcoveragecompartment_project_id",
        "fcpcoveragecompartment",
        ["project_id"],
    )
    op.create_index(
        "ix_fcpcoveragecompartment_fcp_id",
        "fcpcoveragecompartment",
        ["fcp_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("fcpcoveragecompartment"):
        op.drop_index("ix_fcpcoveragecompartment_fcp_id", table_name="fcpcoveragecompartment")
        op.drop_index("ix_fcpcoveragecompartment_project_id", table_name="fcpcoveragecompartment")
        op.drop_table("fcpcoveragecompartment")
    if inspector.has_table("fcpcoveragesummary"):
        op.drop_table("fcpcoveragesummary")
    if inspector.has_table("projectfcpcoverage"):
        op.drop_table("projectfcpcoverage")
