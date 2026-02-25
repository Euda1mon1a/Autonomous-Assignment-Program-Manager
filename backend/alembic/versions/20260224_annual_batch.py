"""Add academic_year and parent_batch_id to import_batches.

Revision ID: 20260224_annual_batch
Revises: 20260224_blk12_act_reqs
Create Date: 2026-02-24 11:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260224_annual_batch"
down_revision = "20260225_fix_nf_combo_reqs"
branch_labels = None
depends_on = None


def upgrade():
    # Add academic_year column
    op.add_column(
        "import_batches", sa.Column("academic_year", sa.Integer(), nullable=True)
    )

    # Add parent_batch_id column
    op.add_column(
        "import_batches",
        sa.Column("parent_batch_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_import_batches_parent_batch_id",
        "import_batches",
        "import_batches",
        ["parent_batch_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint(
        "fk_import_batches_parent_batch_id", "import_batches", type_="foreignkey"
    )

    # Remove columns
    op.drop_column("import_batches", "parent_batch_id")
    op.drop_column("import_batches", "academic_year")
