"""Rollback management module for state restoration and recovery."""

from app.rollback.manager import (
    EntitySnapshot,
    RollbackManager,
    RollbackPoint,
    RollbackResult,
    RollbackStatus,
    RollbackVerificationResult,
)

__all__ = [
    "RollbackManager",
    "RollbackPoint",
    "RollbackResult",
    "RollbackVerificationResult",
    "EntitySnapshot",
    "RollbackStatus",
]
