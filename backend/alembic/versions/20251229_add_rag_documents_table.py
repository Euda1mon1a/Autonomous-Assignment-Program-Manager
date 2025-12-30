"""Add RAG documents table for retrieval-augmented generation

Revision ID: 20251229_rag_documents
Revises: 20251227_pgvector
Create Date: 2025-12-29

This migration creates the rag_documents table for storing document chunks with
vector embeddings for semantic search and retrieval-augmented generation (RAG).

Features:
- Document chunking with overlap for improved retrieval
- 384-dimensional embeddings from sentence-transformers (all-MiniLM-L6-v2)
- Efficient vector similarity search using pgvector indexes (HNSW and IVFFlat)
- Metadata storage with JSON for flexible document attributes
- Support for multiple document types (ACGME rules, policies, guides, etc.)

Indexes:
- HNSW index for fast approximate nearest neighbor search (best for queries)
- IVFFlat index as alternative (faster build time, slightly slower queries)
- GIN index for JSON metadata queries
- B-tree index on doc_type for filtering
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID as PGUUID
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '20251229_rag_documents'
down_revision: Union[str, None] = '20251227_pgvector'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create rag_documents table for RAG system."""
    # Note: pgvector extension already enabled in 20251227_pgvector migration

    # Create rag_documents table
    op.create_table(
        'rag_documents',
        sa.Column(
            'id',
            PGUUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            comment='Unique document chunk identifier',
        ),
        sa.Column(
            'content',
            sa.Text(),
            nullable=False,
            comment='Text content of the document chunk',
        ),
        sa.Column(
            'embedding',
            Vector(384),
            nullable=False,
            comment='384-dimensional embedding from sentence-transformers (all-MiniLM-L6-v2)',
        ),
        sa.Column(
            'doc_type',
            sa.String(100),
            nullable=False,
            comment='Document type: acgme_rules, scheduling_policy, user_guide, etc.',
        ),
        sa.Column(
            'metadata_',
            JSON,
            nullable=False,
            server_default='{}',
            comment='Additional metadata: source_file, page_number, section, author, etc.',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Timestamp when chunk was created',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment='Timestamp of last update',
        ),
    )

    # Create B-tree index on doc_type for filtering
    op.create_index(
        'ix_rag_documents_doc_type',
        'rag_documents',
        ['doc_type'],
    )

    # Create GIN index for metadata JSON queries
    # Allows efficient queries like: WHERE metadata_->>'source_file' = 'acgme_2024.pdf'
    op.execute(
        """
        CREATE INDEX ix_rag_documents_metadata
        ON rag_documents
        USING gin (metadata_)
        """
    )

    # Create HNSW index for vector similarity search
    # HNSW (Hierarchical Navigable Small World) is optimal for high-recall queries
    # m=16: number of bi-directional links per node (higher = better recall, more memory)
    # ef_construction=64: size of dynamic candidate list during index build
    # vector_cosine_ops: use cosine distance (best for normalized embeddings)
    op.execute(
        """
        CREATE INDEX ix_rag_documents_embedding_hnsw
        ON rag_documents
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # Create IVFFlat index as alternative
    # IVFFlat (Inverted File with Flat compression) builds faster but queries slower
    # lists=100: number of clusters (rule of thumb: sqrt(num_rows), minimum 100)
    # Useful during development or for smaller datasets
    op.execute(
        """
        CREATE INDEX ix_rag_documents_embedding_ivfflat
        ON rag_documents
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )

    # Create updated_at trigger
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_rag_documents_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER rag_documents_updated_at_trigger
        BEFORE UPDATE ON rag_documents
        FOR EACH ROW
        EXECUTE FUNCTION update_rag_documents_updated_at();
        """
    )


def downgrade() -> None:
    """Drop rag_documents table and related objects."""
    # Drop trigger first
    op.execute('DROP TRIGGER IF EXISTS rag_documents_updated_at_trigger ON rag_documents')
    op.execute('DROP FUNCTION IF EXISTS update_rag_documents_updated_at()')

    # Drop indexes (some may be dropped with table, but be explicit)
    op.execute('DROP INDEX IF EXISTS ix_rag_documents_embedding_ivfflat')
    op.execute('DROP INDEX IF EXISTS ix_rag_documents_embedding_hnsw')
    op.execute('DROP INDEX IF EXISTS ix_rag_documents_metadata')
    op.drop_index('ix_rag_documents_doc_type', 'rag_documents')

    # Drop table
    op.drop_table('rag_documents')
