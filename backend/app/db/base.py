"""SQLAlchemy Base class for all models."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Import audit configuration FIRST to initialize versioning
# This must happen before any models are defined
from app.db.audit import make_versioned  # noqa: F401 - imported for side effects


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
