"""Add explainability columns to assignments table

Revision ID: 20251222_explain
Revises: 020_rotation_halfday
Create Date: 2025-12-22 00:00:00.000000

Adds transparency/explainability columns to assignments table:
- explain_json: Full DecisionExplanation as JSON (why this assignment was made)
- confidence: Confidence score 0-1 for the scheduling decision
- score: Objective score for this assignment
- alternatives_json: Top alternatives considered (AlternativeCandidate[])
- audit_hash: SHA-256 of inputs+outputs for integrity verification

These columns support schedule auditing and help users understand
why specific assignments were made by the scheduling algorithm.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251222_explain"
down_revision: str | None = "020_rotation_halfday"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add explainability columns to assignments table."""
    op.add_column(
        "assignments", sa.Column("explain_json", postgresql.JSONB(), nullable=True)
    )
    op.add_column("assignments", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("assignments", sa.Column("score", sa.Float(), nullable=True))
    op.add_column(
        "assignments", sa.Column("alternatives_json", postgresql.JSONB(), nullable=True)
    )
    op.add_column("assignments", sa.Column("audit_hash", sa.String(64), nullable=True))


def downgrade() -> None:
    """Remove explainability columns from assignments table."""
    op.drop_column("assignments", "audit_hash")
    op.drop_column("assignments", "alternatives_json")
    op.drop_column("assignments", "score")
    op.drop_column("assignments", "confidence")
    op.drop_column("assignments", "explain_json")
