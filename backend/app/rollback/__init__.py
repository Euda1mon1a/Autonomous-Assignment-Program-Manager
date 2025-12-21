"""Rollback management module for state restoration and recovery."""

from app.rollback.manager import (
    RollbackManager,
    RollbackPoint,
    RollbackResult,
    RollbackVerificationResult,
    EntitySnapshot,
    RollbackStatus,
)

__all__ = [
    "RollbackManager",
    "RollbackPoint",
    "RollbackResult",
    "RollbackVerificationResult",
    "EntitySnapshot",
    "RollbackStatus",
]
