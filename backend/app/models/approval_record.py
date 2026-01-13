"""Tamper-evident approval record model for schedule change audit trail.

Implements a hash-chain pattern (similar to Certificate Transparency logs)
to create an append-only, cryptographically verifiable audit trail for
AI-proposed schedule changes and human approvals.

Each record stores:
- prev_hash: SHA-256 of the previous record (chain link)
- payload: The schedule change being approved
- record_hash: SHA-256(prev_hash || payload || actor || timestamp)

If anyone edits an old record, its record_hash changes and no longer
matches the prev_hash stored in the next record—instantly revealing tampering.

References:
- RFC 6962 (Certificate Transparency)
- AWS QLDB (append-only ledger pattern)
"""

import enum
import hashlib
import json
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType


class ApprovalAction(str, enum.Enum):
    """Types of approval actions in the chain."""

    # Schedule generation approvals
    SCHEDULE_GENERATED = "SCHEDULE_GENERATED"
    SCHEDULE_APPROVED = "SCHEDULE_APPROVED"
    SCHEDULE_PUBLISHED = "SCHEDULE_PUBLISHED"
    SCHEDULE_REJECTED = "SCHEDULE_REJECTED"

    # Assignment-level approvals
    ASSIGNMENT_CREATED = "ASSIGNMENT_CREATED"
    ASSIGNMENT_MODIFIED = "ASSIGNMENT_MODIFIED"
    ASSIGNMENT_DELETED = "ASSIGNMENT_DELETED"

    # ACGME override approvals (require justification)
    ACGME_OVERRIDE_REQUESTED = "ACGME_OVERRIDE_REQUESTED"
    ACGME_OVERRIDE_APPROVED = "ACGME_OVERRIDE_APPROVED"
    ACGME_OVERRIDE_DENIED = "ACGME_OVERRIDE_DENIED"

    # Swap approvals
    SWAP_REQUESTED = "SWAP_REQUESTED"
    SWAP_APPROVED = "SWAP_APPROVED"
    SWAP_EXECUTED = "SWAP_EXECUTED"
    SWAP_ROLLED_BACK = "SWAP_ROLLED_BACK"

    # System events (genesis, sealing)
    GENESIS = "GENESIS"  # First record in chain
    DAY_SEALED = "DAY_SEALED"  # Daily Merkle root seal


class ApprovalRecord(Base):
    """
    Tamper-evident approval record for schedule changes.

    Implements a hash chain where each record references the previous
    record's hash, creating a cryptographically verifiable audit trail.

    Security Properties:
    - Append-only: Records should never be modified or deleted
    - Tamper-evident: Any modification breaks the hash chain
    - Non-repudiation: Actor identity and timestamp are hashed
    - Verifiable: Chain can be verified from genesis to head

    The chain is keyed by `chain_id` to support multiple independent chains
    (e.g., per-block, per-schedule-run, or global).
    """

    __tablename__ = "approval_record"

    # Primary key and chain position
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    chain_id = Column(String(100), nullable=False, index=True)
    sequence_num = Column(Integer, nullable=False)

    # Hash chain links
    prev_record_id = Column(GUID(), ForeignKey("approval_record.id"), nullable=True)
    prev_hash = Column(
        String(64), nullable=True
    )  # SHA-256 hex, null only for genesis
    record_hash = Column(String(64), nullable=False)  # SHA-256 hex

    # Action and payload
    action = Column(String(50), nullable=False, index=True)
    payload = Column(JSONType, nullable=False)

    # Actor information (who approved)
    actor_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_type = Column(
        String(20), nullable=False, default="human"
    )  # human, system, ai

    # Justification (especially for ACGME overrides)
    reason = Column(Text, nullable=True)

    # Target entity references (optional, for linking)
    target_entity_type = Column(String(50), nullable=True)
    target_entity_id = Column(String(100), nullable=True)

    # Immutable timestamp (no updated_at - records never change)
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)

    # Relationships
    actor = relationship(
        "User",
        foreign_keys=[actor_id],
        backref="approval_records",
    )
    prev_record = relationship(
        "ApprovalRecord",
        foreign_keys=[prev_record_id],
        remote_side=[id],
        backref="next_records",
    )

    # Constraints
    __table_args__ = (
        # Each chain has unique sequence numbers
        UniqueConstraint(
            "chain_id", "sequence_num", name="uq_approval_record_chain_seq"
        ),
        # Index for chain traversal
        Index("ix_approval_record_chain_seq", "chain_id", "sequence_num"),
        # Index for target entity lookups
        Index(
            "ix_approval_record_target",
            "target_entity_type",
            "target_entity_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ApprovalRecord(id={self.id}, chain={self.chain_id}, "
            f"seq={self.sequence_num}, action={self.action})>"
        )

    @staticmethod
    def compute_hash(
        prev_hash: str | None,
        payload: dict,
        actor_id: uuid.UUID | None,
        actor_type: str,
        action: str,
        timestamp: datetime,
        reason: str | None = None,
    ) -> str:
        """
        Compute SHA-256 hash for record integrity verification.

        The hash includes all fields that define the record's identity
        and must not change. This ensures:
        - Payload integrity (what was approved)
        - Actor non-repudiation (who approved)
        - Temporal ordering (when it was approved)
        - Chain integrity (links to previous record)

        Args:
            prev_hash: SHA-256 hash of previous record (None for genesis)
            payload: The schedule change payload
            actor_id: UUID of the approving user (None for system)
            actor_type: Type of actor (human, system, ai)
            action: The approval action type
            timestamp: When the approval occurred
            reason: Optional justification text

        Returns:
            64-character hexadecimal SHA-256 hash
        """
        data = {
            "prev_hash": prev_hash or "GENESIS",
            "payload": payload,
            "actor_id": str(actor_id) if actor_id else None,
            "actor_type": actor_type,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "reason": reason,
        }
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    @classmethod
    def create_genesis(
        cls,
        chain_id: str,
        payload: dict | None = None,
        actor_id: uuid.UUID | None = None,
        reason: str = "Chain initialized",
    ) -> "ApprovalRecord":
        """
        Create the genesis (first) record for a new chain.

        Args:
            chain_id: Identifier for this chain
            payload: Optional initialization payload
            actor_id: User who initialized the chain
            reason: Reason for chain creation

        Returns:
            New ApprovalRecord instance (not yet added to session)
        """
        timestamp = datetime.utcnow()
        payload = payload or {"chain_initialized": True}

        record_hash = cls.compute_hash(
            prev_hash=None,
            payload=payload,
            actor_id=actor_id,
            actor_type="system",
            action=ApprovalAction.GENESIS.value,
            timestamp=timestamp,
            reason=reason,
        )

        return cls(
            id=uuid.uuid4(),
            chain_id=chain_id,
            sequence_num=0,
            prev_record_id=None,
            prev_hash=None,
            record_hash=record_hash,
            action=ApprovalAction.GENESIS.value,
            payload=payload,
            actor_id=actor_id,
            actor_type="system",
            reason=reason,
            created_at=timestamp,
        )

    def verify_hash(self) -> bool:
        """
        Verify that this record's hash matches its contents.

        Returns:
            True if hash is valid, False if tampered
        """
        expected = self.compute_hash(
            prev_hash=self.prev_hash,
            payload=self.payload,
            actor_id=self.actor_id,
            actor_type=self.actor_type,
            action=self.action,
            timestamp=self.created_at,
            reason=self.reason,
        )
        return self.record_hash == expected
