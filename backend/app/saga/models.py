"""Database models for saga orchestration.

These models persist saga execution state to enable recovery on service restart.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID, JSONType
from app.saga.types import SagaStatus, StepStatus


class SagaExecution(Base):
    """Persisted state of a saga execution.

    Enables saga recovery after service restarts or crashes.
    """

    __tablename__ = "saga_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Saga identification
    saga_name = Column(String(255), nullable=False, index=True)
    saga_version = Column(String(50), nullable=False)

    # Execution status
    status = Column(
        String(20), nullable=False, default=SagaStatus.PENDING.value, index=True
    )

    # Input and context
    input_data = Column(JSONType(), nullable=False)
    context_data = Column(JSONType(), nullable=True)
    metadata = Column(JSONType(), nullable=True)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    compensated_steps_count = Column(Integer, default=0, nullable=False)

    # Relationships
    steps = relationship(
        "SagaStepExecution",
        back_populates="saga",
        cascade="all, delete-orphan",
        order_by="SagaStepExecution.step_order",
    )

    __table_args__ = (
        Index("idx_saga_status_created", "status", "created_at"),
        Index("idx_saga_name_status", "saga_name", "status"),
        Index("idx_saga_timeout", "timeout_at"),
    )

    def __repr__(self):
        return (
            f"<SagaExecution(id='{str(self.id)[:8]}...', "
            f"name='{self.saga_name}', status='{self.status}')>"
        )

    @property
    def is_running(self) -> bool:
        """Check if saga is currently running."""
        return self.status == SagaStatus.RUNNING.value

    @property
    def is_completed(self) -> bool:
        """Check if saga completed successfully."""
        return self.status == SagaStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """Check if saga failed."""
        return self.status == SagaStatus.FAILED.value

    @property
    def is_terminal(self) -> bool:
        """Check if saga is in a terminal state."""
        return self.status in (
            SagaStatus.COMPLETED.value,
            SagaStatus.FAILED.value,
            SagaStatus.TIMEOUT.value,
            SagaStatus.CANCELLED.value,
        )

    @property
    def duration_seconds(self) -> float | None:
        """Calculate execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class SagaStepExecution(Base):
    """Persisted state of a saga step execution."""

    __tablename__ = "saga_step_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Parent saga
    saga_id = Column(
        GUID(),
        ForeignKey("saga_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Step identification
    step_name = Column(String(255), nullable=False)
    step_order = Column(Integer, nullable=False)
    parallel_group = Column(String(255), nullable=True, index=True)

    # Execution status
    status = Column(
        String(20), nullable=False, default=StepStatus.PENDING.value, index=True
    )

    # Step data
    input_data = Column(JSONType(), nullable=True)
    output_data = Column(JSONType(), nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=True)

    # Error tracking and retry
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=0, nullable=False)

    # Compensation tracking
    compensated_at = Column(DateTime, nullable=True)
    compensation_error = Column(Text, nullable=True)

    # Relationships
    saga = relationship("SagaExecution", back_populates="steps")

    __table_args__ = (
        Index("idx_step_saga_order", "saga_id", "step_order"),
        Index("idx_step_status", "status"),
        Index("idx_step_parallel_group", "parallel_group"),
    )

    def __repr__(self):
        return (
            f"<SagaStepExecution(saga_id='{str(self.saga_id)[:8]}...', "
            f"name='{self.step_name}', status='{self.status}')>"
        )

    @property
    def is_pending(self) -> bool:
        """Check if step is pending execution."""
        return self.status == StepStatus.PENDING.value

    @property
    def is_running(self) -> bool:
        """Check if step is currently running."""
        return self.status == StepStatus.RUNNING.value

    @property
    def is_completed(self) -> bool:
        """Check if step completed successfully."""
        return self.status == StepStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """Check if step failed."""
        return self.status == StepStatus.FAILED.value

    @property
    def is_compensated(self) -> bool:
        """Check if step was compensated."""
        return self.status == StepStatus.COMPENSATED.value

    @property
    def can_retry(self) -> bool:
        """Check if step can be retried."""
        return self.retry_count < self.max_retries

    @property
    def duration_seconds(self) -> float | None:
        """Calculate step execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class SagaEvent(Base):
    """Event log for saga execution (for monitoring and debugging).

    Provides detailed audit trail of all saga activities.
    """

    __tablename__ = "saga_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Associated saga and step
    saga_id = Column(
        GUID(),
        ForeignKey("saga_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_id = Column(
        GUID(),
        ForeignKey("saga_step_executions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSONType(), nullable=True)
    message = Column(Text, nullable=True)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_event_saga_time", "saga_id", "created_at"),
        Index("idx_event_type", "event_type"),
    )

    def __repr__(self):
        return (
            f"<SagaEvent(saga_id='{str(self.saga_id)[:8]}...', "
            f"type='{self.event_type}')>"
        )
