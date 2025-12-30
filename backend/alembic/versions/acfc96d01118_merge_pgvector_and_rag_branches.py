"""merge_pgvector_and_rag_branches

Revision ID: acfc96d01118
Revises: 20251227_pgvector, 20251229_rag_documents
Create Date: 2025-12-29 20:37:15.246800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acfc96d01118'
down_revision: Union[str, None] = ('20251227_pgvector', '20251229_rag_documents')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
