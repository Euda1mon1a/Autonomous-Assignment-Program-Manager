"""Add lesson columns to task_history.

Revision ID: 20260313_task_hist_4cols
Revises: d3245f3e2c2f
Create Date: 2026-03-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20260313_task_hist_4cols"
down_revision = "d3245f3e2c2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_history", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("task_history", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.add_column(
        "task_history",
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "task_history",
        sa.Column("files_touched", postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("task_history", "files_touched")
    op.drop_column("task_history", "tags")
    op.drop_column("task_history", "failure_reason")
    op.drop_column("task_history", "notes")
