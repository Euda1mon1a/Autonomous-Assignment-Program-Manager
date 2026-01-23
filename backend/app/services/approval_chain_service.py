"""Approval chain service for tamper-evident schedule change tracking.

This service manages hash-chained approval records, providing:
- Chain creation and record appending
- Chain verification (detect tampering)
- Chain querying and traversal
- Daily sealing for snapshot proofs

The hash chain pattern ensures that any modification to historical records
is immediately detectable by verifying the chain from genesis.

Security Model:
- Each record's hash includes the previous record's hash
- Modifying any record breaks all subsequent hashes
- Genesis record anchors the chain
- Optional daily seals create verifiable checkpoints
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.approval_record import ApprovalAction, ApprovalRecord

logger = get_logger(__name__)

# Default chain ID for global schedule approvals
DEFAULT_CHAIN_ID = "global"


@dataclass
class ChainVerificationResult:
    """Result of chain verification."""

    valid: bool
    chain_id: str
    total_records: int
    verified_count: int
    first_invalid_seq: int | None = None
    first_invalid_id: str | None = None
    error_message: str | None = None
    head_hash: str | None = None
    genesis_hash: str | None = None
    verified_at: str | None = None


@dataclass
class ChainStats:
    """Statistics about an approval chain."""

    chain_id: str
    total_records: int
    head_sequence: int
    head_hash: str
    genesis_hash: str
    first_record_at: datetime | None
    last_record_at: datetime | None
    actions_by_type: dict[str, int]


class ApprovalChainService:
    """Service for managing tamper-evident approval chains."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_chain(
        self,
        chain_id: str = DEFAULT_CHAIN_ID,
        actor_id: uuid.UUID | None = None,
    ) -> ApprovalRecord:
        """
        Get the head of an existing chain or create a new genesis record.

        Args:
            chain_id: Identifier for the chain
            actor_id: User creating the chain (if new)

        Returns:
            The head (latest) record of the chain
        """
        head = self._get_chain_head(chain_id)
        if head:
            return head

        # Create genesis record
        genesis = ApprovalRecord.create_genesis(
            chain_id=chain_id,
            actor_id=actor_id,
            reason=f"Chain '{chain_id}' initialized",
        )
        self.db.add(genesis)
        self.db.flush()

        logger.info(
            f"Created genesis record for chain '{chain_id}' "
            f"with hash {genesis.record_hash[:16]}..."
        )
        return genesis

    def append_record(
        self,
        action: ApprovalAction | str,
        payload: dict,
        chain_id: str = DEFAULT_CHAIN_ID,
        actor_id: uuid.UUID | None = None,
        actor_type: Literal["human", "system", "ai"] = "human",
        reason: str | None = None,
        target_entity_type: str | None = None,
        target_entity_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ApprovalRecord:
        """
        Append a new record to the approval chain.

        This is the primary method for recording schedule changes.
        Each record is cryptographically linked to its predecessor.

        Args:
            action: Type of approval action
            payload: The schedule change data
            chain_id: Which chain to append to
            actor_id: User performing the action
            actor_type: Type of actor (human, system, ai)
            reason: Justification for the action
            target_entity_type: Type of entity affected (e.g., "Assignment")
            target_entity_id: ID of the affected entity
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            The newly created ApprovalRecord

        Raises:
            IntegrityError: If sequence number conflict (concurrent append)
        """
        if isinstance(action, ApprovalAction):
            action = action.value

        # Get or create chain head
        head = self.get_or_create_chain(chain_id, actor_id)

        # Compute new record
        timestamp = datetime.utcnow()
        new_seq = head.sequence_num + 1

        record_hash = ApprovalRecord.compute_hash(
            prev_hash=head.record_hash,
            payload=payload,
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            timestamp=timestamp,
            reason=reason,
        )

        record = ApprovalRecord(
            id=uuid.uuid4(),
            chain_id=chain_id,
            sequence_num=new_seq,
            prev_record_id=head.id,
            prev_hash=head.record_hash,
            record_hash=record_hash,
            action=action,
            payload=payload,
            actor_id=actor_id,
            actor_type=actor_type,
            reason=reason,
            target_entity_type=target_entity_type,
            target_entity_id=target_entity_id,
            created_at=timestamp,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(record)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            logger.warning(
                f"Sequence conflict on chain '{chain_id}' at seq {new_seq}, retrying"
            )
            # Retry with fresh head
            return self.append_record(
                action=action,
                payload=payload,
                chain_id=chain_id,
                actor_id=actor_id,
                actor_type=actor_type,
                reason=reason,
                target_entity_type=target_entity_type,
                target_entity_id=target_entity_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        logger.info(
            f"Appended record to chain '{chain_id}' "
            f"seq={new_seq} action={action} hash={record_hash[:16]}..."
        )
        return record

    def verify_chain(
        self,
        chain_id: str = DEFAULT_CHAIN_ID,
        stop_on_first_error: bool = True,
    ) -> ChainVerificationResult:
        """
        Verify the integrity of an entire approval chain.

        Walks the chain from genesis to head, verifying:
        1. Each record's hash matches its computed value
        2. Each record's prev_hash matches the previous record's hash
        3. Sequence numbers are contiguous

        Args:
            chain_id: Which chain to verify
            stop_on_first_error: If True, stop at first invalid record

        Returns:
            ChainVerificationResult with verification status
        """
        records = (
            self.db.query(ApprovalRecord)
            .filter(ApprovalRecord.chain_id == chain_id)
            .order_by(ApprovalRecord.sequence_num)
            .all()
        )

        if not records:
            return ChainVerificationResult(
                valid=False,
                chain_id=chain_id,
                total_records=0,
                verified_count=0,
                error_message="Chain not found",
                verified_at=datetime.utcnow().isoformat(),
            )

        verified_count = 0
        prev_hash = None
        expected_seq = 0

        for record in records:
            # Check sequence continuity
            if record.sequence_num != expected_seq:
                return ChainVerificationResult(
                    valid=False,
                    chain_id=chain_id,
                    total_records=len(records),
                    verified_count=verified_count,
                    first_invalid_seq=record.sequence_num,
                    first_invalid_id=str(record.id),
                    error_message=(
                        f"Sequence gap: expected {expected_seq}, "
                        f"got {record.sequence_num}"
                    ),
                    verified_at=datetime.utcnow().isoformat(),
                )

            # Check prev_hash link (skip for genesis)
            if expected_seq > 0:
                if record.prev_hash != prev_hash:
                    return ChainVerificationResult(
                        valid=False,
                        chain_id=chain_id,
                        total_records=len(records),
                        verified_count=verified_count,
                        first_invalid_seq=record.sequence_num,
                        first_invalid_id=str(record.id),
                        error_message=(
                            f"Chain broken at seq {record.sequence_num}: "
                            f"prev_hash mismatch"
                        ),
                        verified_at=datetime.utcnow().isoformat(),
                    )

            # Verify record hash
            if not record.verify_hash():
                return ChainVerificationResult(
                    valid=False,
                    chain_id=chain_id,
                    total_records=len(records),
                    verified_count=verified_count,
                    first_invalid_seq=record.sequence_num,
                    first_invalid_id=str(record.id),
                    error_message=(
                        f"Hash mismatch at seq {record.sequence_num}: "
                        f"record has been tampered with"
                    ),
                    verified_at=datetime.utcnow().isoformat(),
                )

            verified_count += 1
            prev_hash = record.record_hash
            expected_seq += 1

        # All records verified
        genesis = records[0]
        head = records[-1]

        return ChainVerificationResult(
            valid=True,
            chain_id=chain_id,
            total_records=len(records),
            verified_count=verified_count,
            head_hash=head.record_hash,
            genesis_hash=genesis.record_hash,
            verified_at=datetime.utcnow().isoformat(),
        )

    def get_chain_stats(self, chain_id: str = DEFAULT_CHAIN_ID) -> ChainStats | None:
        """
        Get statistics about an approval chain.

        Args:
            chain_id: Which chain to analyze

        Returns:
            ChainStats or None if chain doesn't exist
        """
        # Get record counts by action type
        action_counts = (
            self.db.query(
                ApprovalRecord.action,
                func.count(ApprovalRecord.id).label("count"),
            )
            .filter(ApprovalRecord.chain_id == chain_id)
            .group_by(ApprovalRecord.action)
            .all()
        )

        if not action_counts:
            return None

        # Get genesis and head
        genesis = (
            self.db.query(ApprovalRecord)
            .filter(
                ApprovalRecord.chain_id == chain_id,
                ApprovalRecord.sequence_num == 0,
            )
            .first()
        )

        head = self._get_chain_head(chain_id)

        if not genesis or not head:
            return None

        return ChainStats(
            chain_id=chain_id,
            total_records=sum(c.count for c in action_counts),
            head_sequence=head.sequence_num,
            head_hash=head.record_hash,
            genesis_hash=genesis.record_hash,
            first_record_at=genesis.created_at,
            last_record_at=head.created_at,
            actions_by_type={ac.action: ac.count for ac in action_counts},
        )

    def get_records_by_target(
        self,
        target_entity_type: str,
        target_entity_id: str,
        chain_id: str = DEFAULT_CHAIN_ID,
    ) -> list[ApprovalRecord]:
        """
        Get all approval records for a specific entity.

        Useful for auditing all changes to a particular assignment,
        schedule run, or swap request.

        Args:
            target_entity_type: Type of entity (e.g., "Assignment")
            target_entity_id: ID of the entity
            chain_id: Which chain to search

        Returns:
            List of ApprovalRecord objects, ordered by sequence
        """
        return (
            self.db.query(ApprovalRecord)
            .filter(
                ApprovalRecord.chain_id == chain_id,
                ApprovalRecord.target_entity_type == target_entity_type,
                ApprovalRecord.target_entity_id == target_entity_id,
            )
            .order_by(ApprovalRecord.sequence_num)
            .all()
        )

    def get_records_by_action(
        self,
        action: ApprovalAction | str,
        chain_id: str = DEFAULT_CHAIN_ID,
        limit: int = 100,
    ) -> list[ApprovalRecord]:
        """
        Get approval records by action type.

        Args:
            action: The action type to filter by
            chain_id: Which chain to search
            limit: Maximum records to return

        Returns:
            List of ApprovalRecord objects, most recent first
        """
        if isinstance(action, ApprovalAction):
            action = action.value

        return (
            self.db.query(ApprovalRecord)
            .filter(
                ApprovalRecord.chain_id == chain_id,
                ApprovalRecord.action == action,
            )
            .order_by(desc(ApprovalRecord.sequence_num))
            .limit(limit)
            .all()
        )

    def seal_day(
        self,
        chain_id: str = DEFAULT_CHAIN_ID,
        seal_date: datetime | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> ApprovalRecord:
        """
        Create a daily seal record with Merkle root.

        This creates a cryptographic checkpoint that can be stored
        externally (e.g., emailed, notarized) for stronger verification.

        The seal includes:
        - All record hashes from the day
        - A Merkle root of those hashes
        - The chain head hash at seal time

        Args:
            chain_id: Which chain to seal
            seal_date: Date to seal (defaults to today)
            actor_id: User performing the seal

        Returns:
            The seal ApprovalRecord
        """
        seal_date = seal_date or datetime.utcnow()
        start_of_day = seal_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = seal_date.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Get all records from the day
        day_records = (
            self.db.query(ApprovalRecord)
            .filter(
                ApprovalRecord.chain_id == chain_id,
                ApprovalRecord.created_at >= start_of_day,
                ApprovalRecord.created_at <= end_of_day,
                ApprovalRecord.action != ApprovalAction.DAY_SEALED.value,
            )
            .order_by(ApprovalRecord.sequence_num)
            .all()
        )

        # Compute Merkle root of day's hashes
        hashes = [r.record_hash for r in day_records]
        merkle_root = self._compute_merkle_root(hashes) if hashes else None

        # Get current head
        head = self._get_chain_head(chain_id)

        payload = {
            "seal_date": seal_date.date().isoformat(),
            "records_sealed": len(day_records),
            "merkle_root": merkle_root,
            "head_hash_at_seal": head.record_hash if head else None,
            "first_seq_of_day": day_records[0].sequence_num if day_records else None,
            "last_seq_of_day": day_records[-1].sequence_num if day_records else None,
        }

        return self.append_record(
            action=ApprovalAction.DAY_SEALED,
            payload=payload,
            chain_id=chain_id,
            actor_id=actor_id,
            actor_type="system",
            reason=f"Daily seal for {seal_date.date().isoformat()}",
        )

    def _get_chain_head(self, chain_id: str) -> ApprovalRecord | None:
        """Get the most recent record in a chain."""
        return (
            self.db.query(ApprovalRecord)
            .filter(ApprovalRecord.chain_id == chain_id)
            .order_by(desc(ApprovalRecord.sequence_num))
            .first()
        )

    def _compute_merkle_root(self, hashes: list[str]) -> str:
        """
        Compute Merkle root of a list of hashes.

        Simple binary Merkle tree implementation.
        Pads with empty hashes if not power of 2.
        """
        if not hashes:
            return hashlib.sha256(b"").hexdigest()

        # Pad to power of 2
        while len(hashes) & (len(hashes) - 1):
            hashes.append(hashlib.sha256(b"").hexdigest())

        # Build tree bottom-up
        while len(hashes) > 1:
            new_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_level

        return hashes[0]


# Convenience functions for common operations


def record_schedule_approval(
    db: Session,
    schedule_run_id: uuid.UUID,
    action: ApprovalAction,
    payload: dict,
    actor_id: uuid.UUID | None = None,
    reason: str | None = None,
    ip_address: str | None = None,
) -> ApprovalRecord:
    """
    Convenience function to record a schedule-related approval.

    Args:
        db: Database session
        schedule_run_id: ID of the schedule run
        action: Type of approval action
        payload: Schedule change details
        actor_id: User performing the action
        reason: Justification
        ip_address: Client IP

    Returns:
        The created ApprovalRecord
    """
    service = ApprovalChainService(db)
    return service.append_record(
        action=action,
        payload=payload,
        target_entity_type="ScheduleRun",
        target_entity_id=str(schedule_run_id),
        actor_id=actor_id,
        reason=reason,
        ip_address=ip_address,
    )


def record_assignment_change(
    db: Session,
    assignment_id: uuid.UUID,
    action: ApprovalAction,
    old_value: dict | None,
    new_value: dict | None,
    actor_id: uuid.UUID | None = None,
    reason: str | None = None,
    ip_address: str | None = None,
) -> ApprovalRecord:
    """
    Convenience function to record an assignment change.

    Args:
        db: Database session
        assignment_id: ID of the assignment
        action: Type of change (created, modified, deleted)
        old_value: Previous state (None for creation)
        new_value: New state (None for deletion)
        actor_id: User performing the action
        reason: Justification
        ip_address: Client IP

    Returns:
        The created ApprovalRecord
    """
    service = ApprovalChainService(db)
    payload = {
        "assignment_id": str(assignment_id),
        "old_value": old_value,
        "new_value": new_value,
    }
    return service.append_record(
        action=action,
        payload=payload,
        target_entity_type="Assignment",
        target_entity_id=str(assignment_id),
        actor_id=actor_id,
        reason=reason,
        ip_address=ip_address,
    )


def verify_chain(
    db: Session, chain_id: str = DEFAULT_CHAIN_ID
) -> ChainVerificationResult:
    """
    Convenience function to verify a chain.

    Args:
        db: Database session
        chain_id: Which chain to verify

    Returns:
        ChainVerificationResult
    """
    service = ApprovalChainService(db)
    return service.verify_chain(chain_id)
