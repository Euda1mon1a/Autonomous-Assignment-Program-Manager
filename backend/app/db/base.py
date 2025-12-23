"""SQLAlchemy Base class for all models."""

from sqlalchemy.orm import DeclarativeBase

# Import audit configuration FIRST to initialize versioning
# This must happen before any models are defined
from app.db.audit import make_versioned  # noqa: F401 - imported for side effects


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass
