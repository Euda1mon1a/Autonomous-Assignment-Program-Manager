"""
Audit logging configuration using SQLAlchemy-Continuum.

This module provides version history tracking for critical models,
enabling accountability for schedule changes.

Usage:
    - Import this module BEFORE importing models
    - Models with __versioned__ = {} will be tracked
    - Access history via: model_instance.versions
    - Query history via: ModelVersion class

Example:
    assignment = db.query(Assignment).first()
    for version in assignment.versions:
        print(f"Version {version.transaction_id}: changed at {version.transaction.issued_at}")
"""
from contextvars import ContextVar

from sqlalchemy_continuum import make_versioned
# PropertyModTrackerPlugin requires *_mod columns - disabled until migrations updated
# from sqlalchemy_continuum.plugins import PropertyModTrackerPlugin

from app.core.logging import get_logger

logger = get_logger(__name__)

# Context variable to store current user ID for audit trail
# This is set by the audit middleware on each request
_current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)


def get_current_user_id() -> str | None:
    """Get the current user ID from context (set by middleware)."""
    return _current_user_id.get()


def set_current_user_id(user_id: str | None) -> None:
    """Set the current user ID in context (called by middleware)."""
    _current_user_id.set(user_id)


def clear_current_user_id() -> None:
    """Clear the current user ID from context."""
    _current_user_id.set(None)


# Initialize versioning BEFORE models are imported
# NOTE: PropertyModTrackerPlugin disabled - requires *_mod columns in version tables
# which our manual migrations don't create. Can re-enable once migrations are updated.
make_versioned(
    plugins=[],  # PropertyModTrackerPlugin disabled to avoid missing *_mod columns
    options={
        "create_models": True,  # Auto-create version models
        "native_versioning": False,  # Use Python-based versioning (more compatible)
    }
)

logger.info("SQLAlchemy-Continuum audit versioning initialized")
