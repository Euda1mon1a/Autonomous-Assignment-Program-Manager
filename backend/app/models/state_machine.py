"""State machine persistence models."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType


class StateMachineStatus(str, Enum):
    """Status of a state machine instance."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class StateMachineInstance(Base):
    """
    Persistent state machine instance.

    Tracks the current state and context of a running state machine.
    Supports parallel state execution and complete transition history.
    """

    __tablename__ = "state_machine_instances"

    id = Column(GUID(), primary_key=True, default=uuid4)

    # Machine definition identifier
    machine_name = Column(String(100), nullable=False, index=True)

    # Current state(s) - can be multiple for parallel states
    current_state = Column(String(100), nullable=False)

    # Parallel states (if any)
    parallel_states = Column(JSONType(), nullable=True, default=list)

    # Machine status
    status = Column(
        String(20), nullable=False, default=StateMachineStatus.ACTIVE.value, index=True
    )

    # Contextual data for the state machine
    context = Column(JSONType(), nullable=False, default=dict)

    # Metadata for tracking
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(GUID(), nullable=True, index=True)

    # User who initiated/owns this state machine
    owner_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Error information if failed
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONType(), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    transitions = relationship(
        "StateMachineTransition",
        back_populates="instance",
        cascade="all, delete-orphan",
        order_by="StateMachineTransition.created_at",
    )
    owner = relationship("User", foreign_keys=[owner_id])

    __table_args__ = (
        Index("idx_state_machine_entity", "entity_type", "entity_id"),
        Index("idx_state_machine_status_created", "status", "created_at"),
    )

    def __repr__(self):
        return (
            f"<StateMachineInstance(id='{self.id}', "
            f"name='{self.machine_name}', state='{self.current_state}')>"
        )


class StateMachineTransition(Base):
    """
    Record of a state transition in a state machine.

    Provides complete audit trail of all state changes with timestamps,
    events, and context snapshots.
    """

    __tablename__ = "state_machine_transitions"

    id = Column(GUID(), primary_key=True, default=uuid4)

    # Reference to state machine instance
    instance_id = Column(
        GUID(),
        ForeignKey("state_machine_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transition details
    from_state = Column(String(100), nullable=False)
    to_state = Column(String(100), nullable=False)
    event = Column(String(100), nullable=False)

    # Guard evaluation results
    guard_passed = Column(String(100), nullable=True)
    guard_failed = Column(String(100), nullable=True)

    # Actions executed
    entry_action = Column(String(100), nullable=True)
    exit_action = Column(String(100), nullable=True)
    transition_action = Column(String(100), nullable=True)

    # Context snapshot at time of transition
    context_before = Column(JSONType(), nullable=True)
    context_after = Column(JSONType(), nullable=True)

    # User who triggered the transition
    triggered_by_id = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Error information if transition failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    instance = relationship("StateMachineInstance", back_populates="transitions")
    triggered_by = relationship("User", foreign_keys=[triggered_by_id])

    __table_args__ = (
        Index("idx_transition_instance_created", "instance_id", "created_at"),
    )

    def __repr__(self):
        return (
            f"<StateMachineTransition('{self.from_state}' -> '{self.to_state}' "
            f"on '{self.event}')>"
        )
