"""Add pgvector extension and agent memory tables

Revision ID: 20251227_pgvector
Revises: 20251226_block0
Create Date: 2025-12-27

This migration enables pgvector for vector similarity search and creates tables for:
- Model tier configuration (agent -> model assignment)
- Agent embeddings (pre-computed from agent specifications)
- Task history with embeddings (for learning and similarity matching)

Context:
- pgvector enables efficient similarity search for agent selection
- Embeddings are pre-computed using sentence-transformers (384-dim)
- Task history allows the system to learn which agents work best for similar tasks
- Similarity search uses cosine distance (vector_cosine_ops index)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '20251227_pgvector'
down_revision: Union[str, None] = '20251226_block0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pgvector infrastructure for agent memory and learning."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Model tiers lookup table
    # Maps agent names to their default Claude model tier (haiku, sonnet, opus)
    op.create_table(
        'model_tiers',
        sa.Column('agent_name', sa.String(), primary_key=True),
        sa.Column('default_model', sa.String(), nullable=False, comment='Model tier: haiku, sonnet, opus'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('notes', sa.Text(), nullable=True, comment='Optional notes about tier selection'),
    )

    # Agent embeddings table
    # Pre-computed embeddings from agent specifications for semantic similarity
    op.create_table(
        'agent_embeddings',
        sa.Column('agent_name', sa.String(), primary_key=True),
        sa.Column('embedding', Vector(384), nullable=False, comment='384-dim sentence-transformers embedding'),
        sa.Column('spec_hash', sa.String(), nullable=False, comment='Hash of agent specification for versioning'),
        sa.Column('capabilities', sa.Text(), nullable=True, comment='Comma-separated list of agent capabilities'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Task history table
    # Tracks which agents handle which tasks for learning and optimization
    op.create_table(
        'task_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_description', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=True, comment='Embedding of task description'),
        sa.Column('agent_used', sa.String(), nullable=False, comment='Which agent handled this task'),
        sa.Column('model_used', sa.String(), nullable=False, comment='Which model was used (haiku, sonnet, opus)'),
        sa.Column('success', sa.Boolean(), nullable=False, comment='Whether the task completed successfully'),
        sa.Column('duration_ms', sa.Integer(), nullable=True, comment='Task execution duration in milliseconds'),
        sa.Column('session_id', sa.String(), nullable=True, comment='Claude Code session identifier'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create index for similarity search on task embeddings
    # Uses cosine distance (default for sentence embeddings)
    op.execute('CREATE INDEX task_history_embedding_idx ON task_history USING hnsw (embedding vector_cosine_ops)')

    # Create index for agent name lookups in task history
    op.execute('CREATE INDEX task_history_agent_idx ON task_history (agent_used, created_at DESC)')


def downgrade() -> None:
    """Remove pgvector infrastructure."""
    # Drop indexes first
    op.execute('DROP INDEX IF EXISTS task_history_agent_idx')
    op.execute('DROP INDEX IF EXISTS task_history_embedding_idx')

    # Drop tables
    op.drop_table('task_history')
    op.drop_table('agent_embeddings')
    op.drop_table('model_tiers')

    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
