"""Add person_id to User

Revision ID: d3245f3e2c2f
Revises: 004773c4ac06
Create Date: 2026-03-12 22:56:28.106

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app


# revision identifiers, used by Alembic.
revision: str = "d3245f3e2c2f"
down_revision: str | None = "004773c4ac06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "person_id",
            app.db.types.GUID(),
            nullable=True,
            comment="Optional link to a Person record (faculty or resident)",
        ),
    )
    op.create_index(op.f("ix_users_person_id"), "users", ["person_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_users_person_id_people"),
        "users",
        "people",
        ["person_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_users_person_id_people"), "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_person_id"), table_name="users")
    op.drop_column("users", "person_id")
