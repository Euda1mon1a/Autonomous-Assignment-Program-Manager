"""Tests for SQLAlchemy model ↔ database schema drift detection."""

from sqlalchemy import inspect

from app.db.base import Base

# Ensure all models are registered before tables are created in the db fixture.
import app.models  # noqa: F401
import app.webhooks.models  # noqa: F401


def test_model_tables_match_database(db):
    """All model tables should exist in the database, and no extra tables should exist."""
    inspector = inspect(db.bind)
    db_tables = set(inspector.get_table_names())
    model_tables = set(Base.metadata.tables.keys())

    model_tables.discard("alembic_version")
    db_tables.discard("sqlite_sequence")

    missing_tables = model_tables - db_tables
    extra_tables = db_tables - model_tables

    assert not missing_tables, f"Missing tables in database: {sorted(missing_tables)}"
    assert not extra_tables, f"Extra tables in database: {sorted(extra_tables)}"
