"""Add call overrides table for post-release call coverage changes.

Revision ID: 20260129_add_call_overrides
Revises: 20260129_link_activities_to_procedures
Create Date: 2026-01-29
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260129_add_call_overrides"
down_revision = "20260129_link_activities_to_procedures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "call_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("call_assignments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "original_person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "replacement_person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "override_type",
            sa.String(length=20),
            nullable=False,
            server_default="coverage",
        ),
        sa.Column("reason", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("call_type", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column(
            "deactivated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "supersedes_override_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("call_overrides.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "override_type IN ('coverage')",
            name="ck_call_override_type",
        ),
        sa.CheckConstraint(
            "replacement_person_id IS NOT NULL",
            name="ck_call_override_replacement",
        ),
    )

    op.create_index(
        "idx_call_overrides_effective",
        "call_overrides",
        ["effective_date", "call_type"],
        unique=False,
    )
    op.create_index(
        "idx_call_overrides_call_assignment",
        "call_overrides",
        ["call_assignment_id"],
        unique=False,
    )
    op.create_index(
        "idx_call_overrides_active",
        "call_overrides",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "uq_call_overrides_active_assignment",
        "call_overrides",
        ["call_assignment_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_call_overrides_active_assignment", table_name="call_overrides")
    op.drop_index("idx_call_overrides_active", table_name="call_overrides")
    op.drop_index("idx_call_overrides_call_assignment", table_name="call_overrides")
    op.drop_index("idx_call_overrides_effective", table_name="call_overrides")
    op.drop_table("call_overrides")
