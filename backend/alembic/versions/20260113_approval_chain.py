"""Add approval_record table for tamper-evident audit chain.

Implements hash-chained approval records (similar to Certificate Transparency)
for cryptographically verifiable schedule change tracking.

Each record stores:
- prev_hash: SHA-256 of previous record (chain link)
- payload: The schedule change being approved
- record_hash: SHA-256(prev_hash || payload || actor || timestamp)

If anyone edits an old record, the hash chain breaks, revealing tampering.

Revision ID: 20260113_approval_chain
Revises: 20260113_fix_req_hash
Create Date: 2026-01-13
"""

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260113_approval_chain"
down_revision: str | None = "20260113_fix_req_hash"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the approval_record table for tamper-evident audit chain."""
    op.create_table(
        "approval_record",
        # Primary key and chain position
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("chain_id", sa.String(100), nullable=False),
        sa.Column("sequence_num", sa.Integer(), nullable=False),
        # Hash chain links
        sa.Column(
            "prev_record_id",
            UUID(as_uuid=True),
            sa.ForeignKey("approval_record.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "prev_hash", sa.String(64), nullable=True
        ),  # SHA-256, null for genesis
        sa.Column("record_hash", sa.String(64), nullable=False),  # SHA-256
        # Action and payload
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column(
            "payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        # Actor information
        sa.Column(
            "actor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "actor_type", sa.String(20), nullable=False, server_default="human"
        ),
        # Justification (especially for ACGME overrides)
        sa.Column("reason", sa.Text(), nullable=True),
        # Target entity references
        sa.Column("target_entity_type", sa.String(50), nullable=True),
        sa.Column("target_entity_id", sa.String(100), nullable=True),
        # Immutable timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Request metadata
        sa.Column("ip_address", sa.String(45), nullable=True),  # IPv6 compatible
        sa.Column("user_agent", sa.String(500), nullable=True),
    )

    # Unique constraint: each chain has unique sequence numbers
    op.create_unique_constraint(
        "uq_approval_record_chain_seq",
        "approval_record",
        ["chain_id", "sequence_num"],
    )

    # Index for chain lookups
    op.create_index(
        "ix_approval_record_chain_id", "approval_record", ["chain_id"]
    )

    # Index for chain traversal (most common query pattern)
    op.create_index(
        "ix_approval_record_chain_seq",
        "approval_record",
        ["chain_id", "sequence_num"],
    )

    # Index for actor lookups
    op.create_index(
        "ix_approval_record_actor_id", "approval_record", ["actor_id"]
    )

    # Index for action type filtering
    op.create_index(
        "ix_approval_record_action", "approval_record", ["action"]
    )

    # Index for time-range queries (descending for recent-first)
    op.create_index(
        "ix_approval_record_created_at",
        "approval_record",
        [sa.text("created_at DESC")],
    )

    # Composite index for target entity lookups
    op.create_index(
        "ix_approval_record_target",
        "approval_record",
        ["target_entity_type", "target_entity_id"],
    )

    # Partial index for ACGME overrides (compliance auditing)
    op.execute("""
        CREATE INDEX ix_approval_record_acgme_overrides
        ON approval_record (created_at DESC)
        WHERE action LIKE 'ACGME_OVERRIDE%'
    """)

    # Partial index for daily seals (checkpoint verification)
    op.execute("""
        CREATE INDEX ix_approval_record_seals
        ON approval_record (chain_id, sequence_num DESC)
        WHERE action = 'DAY_SEALED'
    """)


def downgrade() -> None:
    """Drop the approval_record table."""
    op.execute("DROP INDEX IF EXISTS ix_approval_record_seals")
    op.execute("DROP INDEX IF EXISTS ix_approval_record_acgme_overrides")
    op.drop_index("ix_approval_record_target", table_name="approval_record")
    op.drop_index("ix_approval_record_created_at", table_name="approval_record")
    op.drop_index("ix_approval_record_action", table_name="approval_record")
    op.drop_index("ix_approval_record_actor_id", table_name="approval_record")
    op.drop_index("ix_approval_record_chain_seq", table_name="approval_record")
    op.drop_index("ix_approval_record_chain_id", table_name="approval_record")
    op.drop_constraint(
        "uq_approval_record_chain_seq", "approval_record", type_="unique"
    )
    op.drop_table("approval_record")
